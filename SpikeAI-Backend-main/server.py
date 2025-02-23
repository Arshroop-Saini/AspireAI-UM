import sys
import os
from pathlib import Path
import logging
import signal
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from config.logging_config import setup_logging
import atexit
import asyncio
from config.db import get_db, close_db_connection
from config.initialize_db import initialize_indexes
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests

# Configure logging before anything else
setup_logging()

# Create app logger
app_logger = logging.getLogger('app')

# Load environment variables from the correct path
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import routes and middleware after environment is loaded
from routes.auth_route import auth_bp
from routes.profile_route import profile_bp
from routes.payment_route import payment_bp
from routes.college_list_generator_route import college_list_bp
from routes.ec_recommendation_route import ec_recommendation_bp
from routes.essay_feedback_route import essay_feedback_bp
from routes.essay_brainstorm_route import essay_brainstorm_bp
from routes.health_route import health_bp
from routes.profile_evaluation_route import profile_evaluation_bp
from middleware.error_handler import init_error_handlers

def check_expired_subscriptions():
    """Task to check and update expired subscriptions"""
    try:
        backend_url = os.environ.get('API_URL', 'http://localhost:5000')
        internal_api_key = os.environ.get('INTERNAL_API_KEY')
        
        if not internal_api_key:
            app_logger.error("INTERNAL_API_KEY not set")
            return
            
        response = requests.post(
            f"{backend_url}/api/payment/check-expired-subscriptions",
            headers={'X-API-Key': internal_api_key}
        )
        
        if response.ok:
            app_logger.info("Successfully checked expired subscriptions")
        else:
            app_logger.error(f"Failed to check expired subscriptions: {response.text}")
            
    except Exception as e:
        app_logger.error(f"Error running subscription check task: {str(e)}")

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Set up async event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Configure CORS based on environment
    is_production = os.environ.get('FLASK_ENV') == 'production'
    allowed_origins = [
        "https://spikeai.education",
        "https://www.spikeai.education",
        "https://app.spikeai.education",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "https://localhost:3000"
    ]

    # Add production URLs if in production
    if is_production:
        production_urls = os.environ.get('ALLOWED_ORIGINS', '').split(',')
        allowed_origins.extend([url.strip() for url in production_urls if url.strip()])
        app_logger.info(f"Running in production mode with additional origins: {production_urls}")

    app_logger.info(f"Configured CORS with allowed origins: {allowed_origins}")

    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": allowed_origins,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Stripe-Signature"],
                 "expose_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True
             }
         })

    # Add root route handler
    @app.route('/')
    def root():
        return jsonify({
            "status": "ok",
            "message": "SpikeAI Backend API",
            "version": "Beta v0.0.1",
            "environment": os.environ.get('FLASK_ENV', 'development')
        })

    # Add health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "healthy",
            "environment": os.environ.get('FLASK_ENV', 'development'),
            "timestamp": datetime.utcnow().isoformat()
        })

    # Initialize database once at startup
    try:
        db = get_db()
        app_logger.info("Successfully connected to MongoDB")
    except Exception as e:
        app_logger.error(f"Failed to connect to MongoDB: {str(e)}")
        sys.exit(1)

    # Register blueprints with /api prefix
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    app.register_blueprint(college_list_bp, url_prefix='/api/college-list')
    app.register_blueprint(ec_recommendation_bp, url_prefix='/api/ec-recommendation')
    app.register_blueprint(essay_feedback_bp, url_prefix='/api/essay-feedback')
    app.register_blueprint(essay_brainstorm_bp, url_prefix='/api/essay-brainstorm')
    app.register_blueprint(profile_evaluation_bp, url_prefix='/api/profile-evaluation')
    app.register_blueprint(health_bp, url_prefix='/api/health')

    # Initialize error handlers
    init_error_handlers(app)

    # Initialize subscription check scheduler
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            check_expired_subscriptions,
            trigger=CronTrigger(hour='*'),  # Run every hour
            id='check_expired_subscriptions',
            name='Check expired subscriptions',
            replace_existing=True
        )
        scheduler.start()
        app_logger.info("Successfully initialized subscription check scheduler")
    except Exception as e:
        app_logger.error(f"Error initializing subscription check scheduler: {str(e)}")

    # Cleanup function for async loop
    @atexit.register
    def cleanup():
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.stop()
        loop.close()

    return app

# Create app instance
app = create_app()

def cleanup():
    """Cleanup function to handle server shutdown"""
    app_logger.info("Cleaning up server resources...")
    close_db_connection()

if __name__ == '__main__':
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda *args: cleanup())
    signal.signal(signal.SIGINT, lambda *args: cleanup())
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Initialize database connection and indexes
    get_db()  # Ensure DB connection is established
    initialize_indexes()  # Initialize indexes after connection
    
    # Determine environment
    is_development = os.environ.get('FLASK_ENV') != 'production'
    
    try:
        # Run app with environment-specific settings and explicit IPv4
        app.run(
            host='0.0.0.0',  # Allow all incoming connections
            port=port,
            debug=is_development,
            use_reloader=is_development
        )
    except KeyboardInterrupt:
        app_logger.info("Server shutting down...")
        cleanup()
    except Exception as e:
        app_logger.error(f"Server error: {str(e)}")
        cleanup()
        raise
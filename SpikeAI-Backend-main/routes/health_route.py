from flask import Blueprint, jsonify
from config.db import get_db
import logging

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Check the health of the application and database connection"""
    try:
        # Get database connection
        db = get_db()
        # Properly ping the database
        db.client.admin.command('ping')
        logger.info("✅ Database connection healthy")
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'message': 'All systems operational'
        }), 200
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503 
from functools import wraps
from flask import jsonify, current_app
import stripe
from google.auth import exceptions as google_auth_exceptions
import logging

logger = logging.getLogger(__name__)

def handle_error(error):
    logger.error(f"Error occurred: {str(error)}")
    response = jsonify({
        'error': 'An error occurred',
        'details': str(error)
    })
    response.status_code = getattr(error, 'code', 500)
    return response

def init_error_handlers(app):
    """Initialize error handlers for the Flask app"""
    
    @app.errorhandler(google_auth_exceptions.GoogleAuthError)
    def handle_google_auth_error(e):
        logger.error(f"Google Auth Error: {str(e)}")
        return jsonify({'error': 'Google authentication failed', 'details': str(e)}), 401
        
    @app.errorhandler(ValueError)
    def handle_invalid_token(e):
        if "Invalid token" in str(e):
            logger.error(f"Invalid token error: {str(e)}")
            return jsonify({'error': 'Invalid Google token'}), 401
        raise e
        
    @app.errorhandler(stripe.error.CardError)
    def handle_card_error(e):
        logger.error(f"Stripe Card Error: {str(e)}")
        return jsonify({'error': 'Payment failed', 'details': str(e)}), 400
        
    @app.errorhandler(stripe.error.InvalidRequestError)
    def handle_invalid_request(e):
        logger.error(f"Stripe Invalid Request: {str(e)}")
        return jsonify({'error': 'Invalid request', 'details': str(e)}), 400
        
    @app.errorhandler(stripe.error.AuthenticationError)
    def handle_stripe_auth_error(e):
        logger.error(f"Stripe Auth Error: {str(e)}")
        return jsonify({'error': 'Authentication with Stripe failed'}), 500
        
    @app.errorhandler(stripe.error.APIConnectionError)
    def handle_stripe_connection_error(e):
        logger.error(f"Stripe API Connection Error: {str(e)}")
        return jsonify({'error': 'Network communication with Stripe failed'}), 500
        
    @app.errorhandler(stripe.error.StripeError)
    def handle_stripe_error(e):
        logger.error(f"Generic Stripe Error: {str(e)}")
        return jsonify({'error': 'Something went wrong with the payment'}), 500
        
    @app.errorhandler(Exception)
    def handle_generic_error(e):
        logger.error(f"Unhandled Exception: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    app.register_error_handler(Exception, handle_error)

def handle_errors(f):
    """Decorator for route handlers to catch and handle errors"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Re-raise the exception to be caught by the error handlers
            raise e
    return decorated 
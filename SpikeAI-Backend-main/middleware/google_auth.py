from functools import wraps
from flask import request, jsonify, g
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def verify_google_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        logger.debug(f"Auth header received: {auth_header}")
        
        if not auth_header:
            logger.error("No authorization header")
            return jsonify({'success': False, 'error': 'No authorization header'}), 401
            
        try:
            # Handle both "Bearer token" and just "token" formats
            token = auth_header.replace('Bearer ', '')
            logger.debug(f"Extracted token: {token[:20]}...")  # Log first 20 chars for debugging
            
            # Verify token with Google OAuth2
            logger.debug("Making request to Google OAuth2...")
            google_response = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': token},
                timeout=5
            )
            
            logger.debug(f"Google response status: {google_response.status_code}")
            logger.debug(f"Google response: {google_response.text}")
            
            if google_response.status_code != 200:
                error_text = google_response.text
                logger.error(f"Token verification failed: {error_text}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid token',
                    'details': error_text
                }), 401

            user_info = google_response.json()
            logger.debug(f"User info received: {user_info}")
            
            # Check for required fields
            required_fields = ['email', 'sub']
            missing_fields = [field for field in required_fields if field not in user_info]
            
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return jsonify({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 401
            
            # Store verified user info in Flask's g object
            g.user_email = user_info['email']
            g.user_info = user_info
            g.auth_time = datetime.utcnow()
            
            logger.debug(f"Authentication successful for user: {g.user_email}")
            return f(*args, **kwargs)
            
        except requests.exceptions.Timeout:
            logger.error("Google verification request timed out")
            return jsonify({
                'success': False,
                'error': 'Verification request timed out'
            }), 408
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during verification: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to verify token with Google'
            }), 503
        except Exception as e:
            logger.error(f"Auth Error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Authentication failed',
                'details': str(e)
            }), 401

    return decorated_function 
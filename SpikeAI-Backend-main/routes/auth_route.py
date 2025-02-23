from flask import Blueprint, request, jsonify, g
from middleware.google_auth import verify_google_token
from config.db import get_db
from models.blacklist_model import BlacklistModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)
blacklist = BlacklistModel()

@auth_bp.route('/verify-session', methods=['GET'])
@verify_google_token
def verify_session():
    """Verify if the current session is valid"""
    try:
        user_email = g.user_email
        auth0_id = g.user_info.get('sub')  # Get the Google OAuth sub as auth0_id
        logger.info(f"Verifying session for: {user_email} with auth0_id: {auth0_id}")
        
        if not auth0_id:
            return jsonify({
                'success': False,
                'error': 'No auth0_id found in token'
            }), 401
        
        db = get_db()
        # First try to find by auth0_id, then by email as fallback
        user = db.students.find_one({'auth0_id': auth0_id}) or db.students.find_one({'email': user_email})
        
        if not user:
            # Redirect to sync-user endpoint for new user creation
            logger.info(f"User not found, redirecting to sync-user: {auth0_id}")
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
            
        # Update last login time
        db.students.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        return jsonify({
            'success': True,
            'user': {
                'email': user['email'],
                'name': user['name'],
                'picture': user.get('picture'),
                'auth0_id': user['auth0_id']
            }
        })
        
    except Exception as e:
        logger.error(f"Session verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/signout', methods=['POST'])
@verify_google_token
def signout():
    try:
        user_email = g.user_email
        logger.info(f"User signing out: {user_email}")
        
        db = get_db()
        db.students.update_one(
            {'email': user_email},
            {'$set': {'last_logout': datetime.utcnow()}}
        )
        
        return jsonify({
            'success': True,
            'message': 'Successfully signed out'
        })
        
    except Exception as e:
        logger.error(f"Error during signout: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 
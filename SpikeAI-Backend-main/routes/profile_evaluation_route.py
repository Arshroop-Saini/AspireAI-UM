from flask import Blueprint, jsonify, g
from middleware.google_auth import verify_google_token
from middleware.subscription_check import requires_subscription
from services.profile_evaluation_service import ProfileEvaluationService
import logging
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

profile_evaluation_bp = Blueprint('profile_evaluation', __name__)

@profile_evaluation_bp.route('/', methods=['POST'])
@verify_google_token
def evaluate_profile():
    """Evaluate student profile and generate scores"""
    try:
        # Get auth0_id from g.user_info (set by verify_google_token)
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("No auth0_id found in user info")
            return jsonify({'error': 'auth0_id is required'}), 400

        # Create event loop and run evaluation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(ProfileEvaluationService.evaluate_profile(auth0_id))
        loop.close()
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
            
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in evaluate_profile route: {str(e)}")
        return jsonify({'error': str(e)}), 500 
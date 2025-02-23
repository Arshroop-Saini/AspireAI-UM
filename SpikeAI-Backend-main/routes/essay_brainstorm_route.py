from flask import Blueprint, jsonify, request, g
from middleware.google_auth import verify_google_token
from middleware.subscription_check import requires_subscription
from middleware.essay_brainstorm_memory import sync_with_mem0
from middleware.essay_brainstorm_validation import validate_essay_brainstorm_profile
from controllers.essay_brainstorm_controller import (
    generate_essay_ideas,
    get_essay_brainstorm_threads,
    delete_essay_brainstorm_thread,
    create_essay_brainstorm_thread
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

essay_brainstorm_bp = Blueprint('essay_brainstorm', __name__)

@essay_brainstorm_bp.route('/threads', methods=['GET'])
@verify_google_token
def get_threads():
    """Get all essay brainstorming threads for a user"""
    try:
        # Get auth0_id from g.user_info (set by verify_google_token)
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("Missing auth0_id in get_threads request")
            return jsonify({'error': 'auth0_id is required'}), 400
            
        result = get_essay_brainstorm_threads(auth0_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_threads: {str(e)}")
        return jsonify({'error': str(e)}), 500

@essay_brainstorm_bp.route('/threads/<thread_id>', methods=['DELETE'])
@verify_google_token
def delete_thread(thread_id):
    """Delete an essay brainstorming thread"""
    try:
        # Get auth0_id from g.user_info
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("Missing auth0_id in delete_thread request")
            return jsonify({'error': 'auth0_id is required'}), 400
            
        logger.info(f"Processing delete request for thread {thread_id}")
        success = delete_essay_brainstorm_thread(thread_id, auth0_id)
        
        if success:
            logger.info(f"Successfully deleted thread {thread_id}")
            return '', 204  # Return 204 No Content for successful deletion
        else:
            logger.error(f"Failed to delete thread {thread_id} - thread not found or could not be deleted")
            return jsonify({'error': 'Thread not found or could not be deleted'}), 404
            
    except Exception as e:
        logger.error(f"Error in delete_thread: {str(e)}")
        return jsonify({'error': str(e)}), 500

@essay_brainstorm_bp.route('/', methods=['POST'])
@verify_google_token
@requires_subscription
@validate_essay_brainstorm_profile()
@sync_with_mem0
def brainstorm_essay():
    """Route for generating essay brainstorming ideas"""
    try:
        # Get request data
        data = request.get_json() or {}
        college_name = data.get('college_name')
        essay_prompt = data.get('essay_prompt')
        thread_id = data.get('thread_id')
        word_limit = data.get('word_limit')  # Extract word limit from request
        is_new_thread = data.get('is_new_thread', True)  # Default to True for backward compatibility
        
        # Get auth0_id from g.user_info
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("Missing auth0_id in brainstorm_essay request")
            return jsonify({'error': 'auth0_id is required'}), 400
        
        # Validate request consistency
        if is_new_thread and thread_id:
            logger.error("thread_id provided for new thread")
            return jsonify({
                'success': False,
                'error': 'thread_id should not be provided for new threads'
            }), 400
        if not is_new_thread and not thread_id:
            logger.error("thread_id missing for existing thread")
            return jsonify({
                'success': False,
                'error': 'thread_id is required for existing threads'
            }), 400
        
        # Validate required fields for new threads
        if is_new_thread and (not college_name or not essay_prompt):
            return jsonify({
                'success': False,
                'error': 'College name and essay prompt are required for new threads'
            }), 400
        
        # Pass to controller with user ID
        result = generate_essay_ideas(
            {
                'college_name': college_name,
                'essay_prompt': essay_prompt,
                'thread_id': thread_id,
                'is_new_thread': is_new_thread,
                'word_limit': word_limit  # Pass word limit to controller
            },
            auth0_id
        )
        
        if not result.get('success'):
            return jsonify(result), 400
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in brainstorm_essay route: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@essay_brainstorm_bp.route('/threads', methods=['POST'])
@verify_google_token
@requires_subscription
def create_thread():
    """Create a new essay brainstorming thread"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            return jsonify({
                "success": False,
                "error": "User ID not found"
            }), 401

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400

        # Create thread with user ID
        result = create_essay_brainstorm_thread(data, auth0_id)
        
        if not result.get('success'):
            return jsonify(result), 400
            
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in create_thread: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
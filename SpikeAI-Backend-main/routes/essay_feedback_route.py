from flask import Blueprint, request, jsonify, g
from middleware.google_auth import verify_google_token
from middleware.subscription_check import requires_subscription
from middleware.essay_feedback_memory import store_feedback_memory
from middleware.essay_feedback_validation import validate_essay_feedback_profile
from controllers.essay_feedback_controller import (
    generate_essay_feedback,
    validate_essay_data,
    get_essay_feedback_threads,
    create_essay_feedback_thread,
    delete_essay_feedback_thread,
    add_feedback_to_thread
)
import logging

logger = logging.getLogger(__name__)
essay_feedback_bp = Blueprint('essay_feedback', __name__)

@essay_feedback_bp.route('/threads', methods=['GET'])
@verify_google_token
def get_threads():
    """Get all essay feedback threads for a user"""
    try:
        # Get auth0_id from g.user_info (set by verify_google_token)
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            return jsonify({'error': 'auth0_id is required'}), 400
            
        result = get_essay_feedback_threads(auth0_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_threads: {str(e)}")
        return jsonify({'error': str(e)}), 500

@essay_feedback_bp.route('/threads', methods=['POST'])
@verify_google_token
@requires_subscription
def create_thread():
    """Create a new essay feedback thread"""
    try:
        data = request.json
        auth0_id = g.user_info.get('sub')
        
        if not auth0_id:
            return jsonify({'error': 'auth0_id is required'}), 400
            
        result = create_essay_feedback_thread(data, auth0_id)
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in create_thread: {str(e)}")
        return jsonify({'error': str(e)}), 500

@essay_feedback_bp.route('/threads/<thread_id>', methods=['DELETE'])
@verify_google_token
def delete_thread(thread_id):
    """Delete an essay feedback thread"""
    try:
        auth0_id = g.user_info.get('sub')
        
        if not auth0_id:
            return jsonify({'error': 'auth0_id is required'}), 400
            
        success = delete_essay_feedback_thread(thread_id, auth0_id)
        if success:
            return '', 204
        return jsonify({'error': 'Failed to delete thread'}), 400
        
    except Exception as e:
        logger.error(f"Error in delete_thread: {str(e)}")
        return jsonify({'error': str(e)}), 500

@essay_feedback_bp.route('/threads/<thread_id>', methods=['GET'])
@verify_google_token
def get_thread(thread_id):
    """Get detailed information about a specific thread"""
    try:
        auth0_id = g.user_info.get('sub')
        
        if not auth0_id:
            return jsonify({'error': 'auth0_id is required'}), 400
            
        result = get_essay_feedback_threads(auth0_id)
        if not result.get('success'):
            return jsonify({'error': 'Failed to get threads'}), 500
            
        # Find the specific thread
        thread = next((t for t in result['threads'] if t['thread_id'] == thread_id), None)
        if not thread:
            return jsonify({'error': 'Thread not found'}), 404
            
        return jsonify({
            'success': True,
            'thread': thread
        })
        
    except Exception as e:
        logger.error(f"Error in get_thread: {str(e)}")
        return jsonify({'error': str(e)}), 500

@essay_feedback_bp.route('/', methods=['POST'])
@verify_google_token
@requires_subscription
@validate_essay_feedback_profile()
@store_feedback_memory
def get_essay_feedback():
    """Generate feedback for an essay and create/update thread"""
    try:
        data = request.json
        auth0_id = g.user_info.get('sub')
        
        if not auth0_id:
            return jsonify({'error': 'auth0_id is required'}), 400

        # Validate basic request structure
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid request format'}), 400

        # Validate is_new_thread is present and is boolean
        if 'is_new_thread' not in data:
            return jsonify({'error': 'is_new_thread must be provided'}), 400
            
        is_new_thread = bool(data['is_new_thread'])
        thread_id = data.get('thread_id')

        # Validate request consistency
        if is_new_thread and thread_id:
            return jsonify({'error': 'thread_id should not be provided for new threads'}), 400
        if not is_new_thread and not thread_id:
            return jsonify({'error': 'thread_id is required for existing threads'}), 400

        # For new threads
        if is_new_thread:
            # Validate all required fields for new thread
            validation_result = validate_essay_data(data, is_new_thread=True)
            if not validation_result.get('success'):
                return jsonify(validation_result), 400
                
            # Create new thread
            thread_result = create_essay_feedback_thread(data, auth0_id)
            if not thread_result.get('success'):
                return jsonify({'error': 'Failed to create thread'}), 500
            thread_id = thread_result['thread_id']

        # Generate feedback
        feedback_result = generate_essay_feedback(data, auth0_id)
        
        if not feedback_result.get('success'):
            logger.error(f"Failed to generate feedback: {feedback_result.get('error')}")
            return jsonify({'error': feedback_result.get('error', 'Failed to generate feedback')}), 500
            
        # Add feedback to thread with current feedback questions
        add_result = add_feedback_to_thread(
            thread_id,
            feedback_result['data']['feedback'],
            auth0_id,
            data.get('feedback_questions', [])
        )
        
        if not add_result.get('success'):
            logger.error(f"Failed to add feedback to thread: {add_result.get('error')}")
            return jsonify({'error': 'Failed to add feedback to thread'}), 500
            
        # Return response with feedback and thread_id
        response_data = {
            'success': True,
            'data': {
                'feedback': feedback_result['data']['feedback'],
                'thread_id': thread_id
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_essay_feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500
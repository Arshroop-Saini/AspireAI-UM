from flask import Blueprint, jsonify, request, g
from middleware.google_auth import verify_google_token
from middleware.subscription_check import requires_subscription
from middleware.ec_suggestions_memory import sync_with_mem0
from middleware.ec_suggestions_validation import validate_ec_suggestions_profile
from controllers.ec_recommendation_controller import generate_ec_recommendations
from middleware.ec_suggestions_memory import sync_with_mem0
from models.student_model import Student
from models.crew_suggestions_model import CrewSuggestions
from models.crew_suggestions_temp_model import CrewSuggestionsTemp
import logging
from datetime import datetime

logger = logging.getLogger('app')
ec_recommendation_bp = Blueprint('ec_recommendation', __name__)

@ec_recommendation_bp.route('/', methods=['POST'])
@verify_google_token
@requires_subscription
@validate_ec_suggestions_profile()  # Add validation before running the crew
@sync_with_mem0  # This will run after the response is generated
def generate_recommendations():
    """Route for generating EC activity recommendations"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        
        if not auth0_id:
            return jsonify({
                "success": False,
                "error": "User ID not found"
            }), 401

        # Move any existing temp suggestions to permanent before generating new ones
        try:
            CrewSuggestionsTemp.move_to_permanent(auth0_id)
        except Exception as e:
            logger.error(f"Error moving suggestions to permanent: {str(e)}")
            # Don't fail the request if this fails

        # Get activity type and hours per week from request
        data = request.get_json()
        activity_type = data.get('activity_type')
        hrs_per_wk = data.get('hrs_per_wk')

        if not activity_type or not hrs_per_wk:
            return jsonify({
                "success": False,
                "error": "Activity type and hours per week are required"
            }), 400

        # Pass to controller
        result = generate_ec_recommendations(auth0_id, activity_type, hrs_per_wk)

        # If successful, store suggestions in CrewSuggestionsTemp database
        if result.get('success') and result.get('data', {}).get('recommendations'):
            try:
                # Parse the recommendations into structured data
                ec_suggestions = parse_ec_suggestions(result['data']['recommendations'])
                
                # Store in CrewSuggestionsTemp database using save_suggestions method
                if not CrewSuggestionsTemp.save_suggestions(auth0_id, ec_suggestions, suggestion_type='ec'):
                    logger.error(f"Failed to save suggestions for user {auth0_id}")
                    # Add error info to response but don't fail the request
                    result['warning'] = "Generated suggestions but failed to save them temporarily"
            except Exception as e:
                logger.error(f"Error storing temporary suggestions: {str(e)}")
                result['warning'] = "Generated suggestions but failed to save them temporarily"

        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating EC recommendations: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate EC recommendations"
        }), 500

def parse_ec_suggestions(recommendations: str) -> list:
    """Parse the EC recommendations string into structured data"""
    suggestions = []
    
    # Remove markdown formatting if present
    recommendations = recommendations.replace('```plaintext', '').replace('```', '').strip()
    
    current_suggestion = None
    for line in recommendations.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # New suggestion starts with a number
        if line[0].isdigit() and '. ' in line:
            if current_suggestion and all(k in current_suggestion for k in ['name', 'description', 'hours_per_week', 'position']):
                suggestions.append(current_suggestion)
            
            # Parse the first line which contains name and type
            parts = line.split('|')
            name = parts[0].split('.', 1)[1].strip()
            activity_type = parts[1].strip() if len(parts) > 1 else 'Other'
            
            current_suggestion = {
                'name': name,
                'activity_type': activity_type,
                'added_at': datetime.utcnow()
            }
        elif current_suggestion:
            # Parse other fields
            if line.startswith('Hours per Week:'):
                try:
                    hours = int(line.replace('Hours per Week:', '').strip())
                    current_suggestion['hours_per_week'] = hours
                except ValueError:
                    current_suggestion['hours_per_week'] = 0
            elif line.startswith('Position:'):
                current_suggestion['position'] = line.replace('Position:', '').strip()
            elif line.startswith('Description:'):
                current_suggestion['description'] = line.replace('Description:', '').strip()
    
    # Add the last suggestion if complete
    if current_suggestion and all(k in current_suggestion for k in ['name', 'description', 'hours_per_week', 'position']):
        suggestions.append(current_suggestion)
    
    return suggestions

@ec_recommendation_bp.route('/current-suggestions', methods=['GET'])
@verify_google_token
@requires_subscription
def get_current_suggestions():
    """Get current EC suggestions from temporary storage"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            return jsonify({
                'success': False,
                'error': 'User ID not found'
            }), 400

        # Get suggestions from temporary storage
        temp_suggestions = CrewSuggestionsTemp.get_by_auth0_id(auth0_id)
        
        if not temp_suggestions:
            return jsonify({
                'success': True,
                'data': {
                    'suggestions': [],
                    'message': 'No current suggestions. Generate new suggestions to see matches.'
                }
            })

        # Format suggestions for response
        suggestions = temp_suggestions.get('ec_suggestions', [])
        
        # Ensure each suggestion has the required fields
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append({
                'name': suggestion.get('name'),
                'description': suggestion.get('description'),
                'activity_type': suggestion.get('activity_type', 'Other'),
                'hours_per_week': suggestion.get('hours_per_week', 0),
                'added_at': suggestion.get('added_at', datetime.utcnow().isoformat())
            })

        return jsonify({
            'success': True,
            'data': {
                'suggestions': formatted_suggestions,
                'total': len(formatted_suggestions),
                'message': None
            }
        })

    except Exception as e:
        logger.error(f"Error getting current suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve current suggestions'
        }), 500

@ec_recommendation_bp.route('/past-suggestions', methods=['GET'])
@verify_google_token
@requires_subscription
def get_past_suggestions():
    """Get past EC suggestions from permanent storage with pagination"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            return jsonify({
                'success': False,
                'error': 'User ID not found'
            }), 400

        # Get page from request args
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of activities per page

        # Get suggestions from permanent storage
        past_suggestions = CrewSuggestions.get_by_auth0_id(auth0_id)
        
        if not past_suggestions:
            return jsonify({
                'success': True,
                'data': {
                    'suggestions': [],
                    'total_pages': 0,
                    'current_page': page,
                    'total': 0,
                    'message': 'No past suggestions found.'
                }
            })

        # Get all suggestions and apply pagination
        suggestions = past_suggestions.get('ec_suggestions', [])
        
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_suggestions = suggestions[start_idx:end_idx]
        total_pages = (len(suggestions) + per_page - 1) // per_page

        # Format suggestions for response
        formatted_suggestions = []
        for suggestion in paginated_suggestions:
            formatted_suggestions.append({
                'name': suggestion.get('name'),
                'description': suggestion.get('description'),
                'activity_type': suggestion.get('activity_type', 'Other'),
                'hours_per_week': suggestion.get('hours_per_week', 0),
                'added_at': suggestion.get('added_at', datetime.utcnow().isoformat())
            })

        return jsonify({
            'success': True,
            'data': {
                'suggestions': formatted_suggestions,
                'total_pages': total_pages,
                'current_page': page,
                'total': len(suggestions),
                'message': None
            }
        })

    except Exception as e:
        logger.error(f"Error getting past suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve past suggestions'
        }), 500

@ec_recommendation_bp.route('/add-target', methods=['POST'])
@verify_google_token  # Add middleware to sync with mem0 profile
def add_to_target_activities():
    """Add an EC activity to student's target activities"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("User ID not found in token")
            return jsonify({'success': False, 'error': 'User ID not found'}), 401

        data = request.get_json()
        activity_name = data.get('activity_name')
        activity_data = data.get('activity_data')
        source = data.get('source', 'temp')  # 'temp' or 'permanent'
        
        if not activity_name or not activity_data:
            logger.error("Activity name or data not provided in request")
            return jsonify({'success': False, 'error': 'Activity name and data are required'}), 400

        logger.info(f"Attempting to add activity {activity_name} from {source} source for user {auth0_id}")

        # First try to add to target activities using the complete activity data
        logger.info(f"Adding activity {activity_name} to target list for user {auth0_id}")
        success = Student.add_target_activity(auth0_id, activity_data)
        
        if success:
            # Only remove from source after successful addition to target
            if source == 'temp':
                CrewSuggestionsTemp.remove_activity(auth0_id, activity_name)
                logger.info(f"Removed activity {activity_name} from temp suggestions")
            else:
                CrewSuggestions.remove_activity(auth0_id, activity_name)
                logger.info(f"Removed activity {activity_name} from permanent suggestions")
                
            logger.info(f"Successfully added activity {activity_name} to target list for user {auth0_id}")
            return jsonify({'success': True})
        else:
            logger.error(f"Failed to add activity {activity_name} to target list for user {auth0_id}")
            return jsonify({'success': False, 'error': 'Failed to add activity to target list'}), 500

    except Exception as e:
        logger.error(f"Error adding activity to target list: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ec_recommendation_bp.route('/delete-activity', methods=['POST'])
@verify_google_token
def delete_activity():
    """Delete an activity from either target list, past suggestions, or current suggestions"""
    try:
        logger.info("Received delete-activity request")
        
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        logger.info(f"Processing delete request for user: {auth0_id}")
        
        if not auth0_id:
            logger.error("User ID not found in token")
            return jsonify({'success': False, 'error': 'User ID not found'}), 401

        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        activity_name = data.get('activity_name')
        source = data.get('source')  # 'target', 'past', or 'current'
        
        logger.info(f"Attempting to delete activity: {activity_name} from source: {source}")
        
        if not all([activity_name, source]):
            logger.error(f"Missing required fields. activity_name: {activity_name}, source: {source}")
            return jsonify({
                'success': False,
                'error': 'Missing required fields: activity_name or source'
            }), 400

        if source not in ['target', 'past', 'current']:
            logger.error(f"Invalid source: {source}")
            return jsonify({
                'success': False,
                'error': 'Invalid source. Must be one of: target, past, current'
            }), 400

        # Delete from appropriate source
        success = False
        if source == 'target':
            success = Student.remove_target_activity(auth0_id, activity_name)
        elif source == 'past':
            success = CrewSuggestions.remove_activity(auth0_id, activity_name)
        else:  # current
            success = CrewSuggestionsTemp.remove_activity(auth0_id, activity_name)

        if success:
            logger.info(f"Successfully deleted activity {activity_name} from {source}")
            return jsonify({'success': True})
        else:
            logger.error(f"Failed to delete activity {activity_name} from {source}")
            return jsonify({
                'success': False,
                'error': f'Failed to delete activity from {source} list'
            }), 500

    except Exception as e:
        logger.error(f"Error deleting activity: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ec_recommendation_bp.route('/target-activities', methods=['GET'])
@verify_google_token
@requires_subscription
def get_target_activities():
    """Get target activities from student profile"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            return jsonify({
                'success': False,
                'error': 'User ID not found'
            }), 400

        # Get page from request args
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of activities per page

        # Get student data
        student = Student.get_by_auth0_id(auth0_id)
        if not student:
            return jsonify({
                'success': False,
                'error': 'Student not found'
            }), 404

        # Get target activities
        target_activities = student.get('target_activities', [])
        
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_activities = target_activities[start_idx:end_idx]
        total_pages = (len(target_activities) + per_page - 1) // per_page

        # Format activities for response
        formatted_activities = []
        for activity in paginated_activities:
            formatted_activities.append({
                'name': activity.get('name'),
                'description': activity.get('description'),
                'hours_per_week': activity.get('hours_per_week'),
                'position': activity.get('position'),
                'activity_type': activity.get('activity_type'),
                'added_at': activity.get('added_at', datetime.utcnow().isoformat())
            })

        return jsonify({
            'success': True,
            'data': {
                'activities': formatted_activities,
                'total_pages': total_pages,
                'current_page': page,
                'total': len(target_activities)
            }
        })

    except Exception as e:
        logger.error(f"Error getting target activities: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve target activities'
        }), 500
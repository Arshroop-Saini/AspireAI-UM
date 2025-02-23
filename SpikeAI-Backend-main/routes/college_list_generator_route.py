from flask import Blueprint, jsonify, request, g
from middleware.google_auth import verify_google_token
from middleware.subscription_check import requires_subscription
from controllers.college_list_generator_controller import generate_college_list
from middleware.college_suggestions_memory import sync_with_mem0
from models.student_model import Student
from models.crew_suggestions_model import CrewSuggestions
from models.crew_suggestions_temp_model import CrewSuggestionsTemp
import logging
from datetime import datetime
import re

logger = logging.getLogger('app')
college_list_bp = Blueprint('college_list', __name__)

@college_list_bp.route('/', methods=['POST'])
@verify_google_token
@requires_subscription
@sync_with_mem0  # This will run after the response is generated
def generate_list():
    """Route for generating college list recommendations"""
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

        # Get college type from request if provided
        college_type = request.json.get('college_type', None)

        # Pass to controller
        result = generate_college_list(auth0_id, college_type)

        # If successful, store suggestions in CrewSuggestionsTemp database
        if result.get('success') and result.get('data', {}).get('college_list'):
            try:
                # Parse the college list into structured data
                college_suggestions = parse_college_suggestions(result['data']['college_list'])
                
                # Store in CrewSuggestionsTemp database using new method
                if not CrewSuggestionsTemp.save_suggestions(auth0_id, college_suggestions):
                    logger.error(f"Failed to save suggestions for user {auth0_id}")
                    # Add error info to response but don't fail the request
                    result['warning'] = "Generated suggestions but failed to save them temporarily"
            except Exception as e:
                logger.error(f"Error storing temporary suggestions: {str(e)}")
                result['warning'] = "Generated suggestions but failed to save them temporarily"

        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating college list: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate college list"
        }), 500

def parse_college_suggestions(college_list: str) -> list:
    """Parse the college list string into structured data.
    Handles various LLM response formats including:
    1. "LIMITED SUGGESTIONS - Modify preferences to get more matches:"
    2. "Available new matches:"
    3. Direct numbered list format
    4. Match # format
    """
    suggestions = []
    lines = college_list.split('\n')
    
    # Find where the actual college list starts
    start_idx = 0
    for i, line in enumerate(lines):
        line = line.strip().lower()
        if any(marker in line for marker in [
            'available new matches:',
            'limited suggestions',
            'match #',
            '1.'  # Direct numbered list
        ]):
            start_idx = i
            break
    
    # Process each line after the start marker
    current_college = None
    for line in lines[start_idx:]:
        line = line.strip()
        if not line:
            continue
            
        # Skip header lines
        if any(header in line.lower() for header in [
            'available new matches:',
            'limited suggestions',
            'modify preferences'
        ]):
            continue
        
        # Try to extract college info based on different formats
        
        # Format 1: "1. University Name | Public (reach)"
        if '|' in line:
            parts = line.split('|')
            if len(parts) == 2:
                name = parts[0].split('.', 1)[1].strip() if '.' in parts[0] else parts[0].strip()
                college_type = parts[1].strip()
                suggestions.append({
                    'name': name,
                    'type': college_type,
                    'added_at': datetime.utcnow()
                })
                continue
        
        # Format 2: "Match #1: University Name (reach)"
        match_pattern = re.search(r'(?:Match #\d+:)?\s*([^(]+)\s*\((\w+)\)', line)
        if match_pattern:
            name = match_pattern.group(1).strip()
            category = match_pattern.group(2).strip()
            suggestions.append({
                'name': name,
                'type': f'Public ({category})',  # Default to Public if not specified
                'added_at': datetime.utcnow()
            })
            continue
            
        # Format 3: Numbered list without type "1. University Name"
        if re.match(r'^\d+\.\s+', line):
            name = re.sub(r'^\d+\.\s+', '', line).strip()
            # If we can't determine the type, default to "target"
            suggestions.append({
                'name': name,
                'type': 'Public (target)',  # Default type
                'added_at': datetime.utcnow()
            })
            continue
            
        # Format 4: Just university name with type in parentheses
        name_type_pattern = re.match(r'^([^(]+)\s*\((\w+)\)$', line)
        if name_type_pattern:
            name = name_type_pattern.group(1).strip()
            category = name_type_pattern.group(2).strip()
            suggestions.append({
                'name': name,
                'type': f'Public ({category})',
                'added_at': datetime.utcnow()
            })
    
    # Filter out any suggestions without a name
    suggestions = [s for s in suggestions if s['name']]
    
    # Log the parsed suggestions for debugging
    logger.info(f"Parsed {len(suggestions)} suggestions from college list")
    for suggestion in suggestions:
        logger.info(f"Parsed suggestion: {suggestion}")
    
    return suggestions

@college_list_bp.route('/current-suggestions', methods=['GET'])
@verify_google_token
@requires_subscription
def get_current_suggestions():
    """Get current college suggestions from temporary storage"""
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
        suggestions = temp_suggestions.get('college_suggestions', [])
        
        # Ensure each suggestion has the required fields
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append({
                'name': suggestion.get('name'),
                'type': suggestion.get('type'),
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

@college_list_bp.route('/add-target', methods=['POST'])
@verify_google_token # This will sync the target colleges in the student profile
def add_to_target_colleges():
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("User ID not found in token")
            return jsonify({'success': False, 'error': 'User ID not found'}), 401

        data = request.get_json()
        college_name = data.get('college_name')
        source = data.get('source', 'temp')  # 'temp' or 'permanent'
        
        if not college_name:
            logger.error("College name not provided in request")
            return jsonify({'success': False, 'error': 'College name is required'}), 400

        logger.info(f"Attempting to add college {college_name} from {source} source for user {auth0_id}")

        # Get college data from appropriate source
        college_data = None
        if source == 'temp':
            suggestions = CrewSuggestionsTemp.get_by_auth0_id(auth0_id)
            if suggestions:
                for college in suggestions.get('college_suggestions', []):
                    if college['name'] == college_name:
                        college_data = college
                        break
        else:
            suggestions = CrewSuggestions.get_by_auth0_id(auth0_id)
            if suggestions:
                for college in suggestions.get('college_suggestions', []):
                    if college['name'] == college_name:
                        college_data = college
                        break

        if not college_data:
            logger.error(f"College {college_name} not found in {source} suggestions for user {auth0_id}")
            return jsonify({'success': False, 'error': 'College not found in suggestions'}), 404

        # First try to add to target colleges
        logger.info(f"Adding college {college_name} to target list for user {auth0_id}")
        success = Student.add_target_college(auth0_id, college_data)
        
        if success:
            # Only remove from source after successful addition to target
            if source == 'temp':
                CrewSuggestionsTemp.remove_college(auth0_id, college_name)
                logger.info(f"Removed college {college_name} from temp suggestions")
            else:
                CrewSuggestions.remove_college(auth0_id, college_name)
                logger.info(f"Removed college {college_name} from permanent suggestions")
                
            logger.info(f"Successfully added college {college_name} to target list for user {auth0_id}")
            return jsonify({'success': True})
        else:
            logger.error(f"Failed to add college {college_name} to target list for user {auth0_id}")
            return jsonify({'success': False, 'error': 'Failed to add college to target list'}), 500

    except Exception as e:
        logger.error(f"Error adding college to target list: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@college_list_bp.route('/past-suggestions', methods=['GET'])
@verify_google_token
@requires_subscription
def get_past_suggestions():
    """Get paginated past suggestions"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("User ID not found in token")
            return jsonify({'error': 'User ID not found'}), 401
        
        logger.info(f"Fetching past suggestions for user {auth0_id}")
        
        # Get paginated suggestions
        result = CrewSuggestions.get_paginated_suggestions(auth0_id, page=1, per_page=10)
        if not result:
            logger.info(f"No past suggestions found for user {auth0_id}")
            return jsonify({
                'suggestions': [],
                'total': 0,
                'page': 1,
                'per_page': 10,
                'total_pages': 0
            }), 200
        
        logger.info(f"Found {len(result.get('suggestions', []))} past suggestions for user {auth0_id}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting past suggestions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@college_list_bp.route('/target-colleges', methods=['GET'])
@verify_google_token
@requires_subscription
def get_target_colleges():
    """Get paginated target colleges"""
    try:
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            logger.error("User ID not found in token")
            return jsonify({'error': 'User ID not found'}), 401
        
        logger.info(f"Fetching target colleges for user {auth0_id}")
        
        # Get page and per_page from query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get paginated target colleges
        result = Student.get_paginated_target_colleges(auth0_id, page=page, per_page=per_page)
        if not result:
            logger.info(f"No target colleges found for user {auth0_id}")
            return jsonify({
                'colleges': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            }), 200
        
        logger.info(f"Found {len(result.get('colleges', []))} target colleges for user {auth0_id}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting target colleges: {str(e)}")
        return jsonify({'error': str(e)}), 500

@college_list_bp.route('/migrate-target-colleges', methods=['POST'])
@verify_google_token
def migrate_target_colleges():
    """Migrate target_colleges structure for all students"""
    try:
        # Only allow admin users to trigger migration
        auth0_id = g.user_info.get('sub')
        if not auth0_id:
            return jsonify({'success': False, 'error': 'User ID not found'}), 401

        success = Student.migrate_target_colleges_structure()
        if not success:
            return jsonify({'success': False, 'error': 'Migration failed'}), 500

        return jsonify({'success': True, 'message': 'Migration completed successfully'})

    except Exception as e:
        logger.error(f"Error during target_colleges migration: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@college_list_bp.route('/delete-college', methods=['POST'])
@verify_google_token
def delete_college():
    """Delete a college from either target list, past suggestions, or current suggestions"""
    try:
        logger.info("Received delete-college request")
        
        # Get auth0_id from token
        auth0_id = g.user_info.get('sub')
        logger.info(f"Processing delete request for user: {auth0_id}")
        
        if not auth0_id:
            logger.error("User ID not found in token")
            return jsonify({'success': False, 'error': 'User ID not found'}), 401

        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        college_name = data.get('college_name')
        source = data.get('source')  # 'target', 'past', or 'current'
        
        logger.info(f"Attempting to delete college: {college_name} from source: {source}")
        
        if not all([college_name, source]):
            logger.error(f"Missing required fields. college_name: {college_name}, source: {source}")
            return jsonify({
                'success': False,
                'error': 'Missing required fields: college_name or source'
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
            success = Student.remove_target_college(auth0_id, college_name)
        elif source == 'past':
            success = CrewSuggestions.remove_college(auth0_id, college_name)
        else:  # current
            success = CrewSuggestionsTemp.remove_college(auth0_id, college_name)

        if success:
            logger.info(f"Successfully deleted college {college_name} from {source}")
            return jsonify({'success': True})
        else:
            logger.error(f"Failed to delete college {college_name} from {source}")
            return jsonify({
                'success': False,
                'error': f'Failed to delete college from {source} list'
            }), 500

    except Exception as e:
        logger.error(f"Error deleting college: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
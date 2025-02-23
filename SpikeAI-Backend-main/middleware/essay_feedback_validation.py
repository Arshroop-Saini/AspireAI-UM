from functools import wraps
from flask import g, jsonify
import logging
from models.student_model import Student

logger = logging.getLogger(__name__)

def validate_essay_feedback_profile():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get auth0_id from token
                auth0_id = g.user_info.get('sub')
                if not auth0_id:
                    return jsonify({
                        "success": False,
                        "error": "User ID not found",
                        "incomplete_profile": True
                    }), 401

                # Get student profile
                student = Student.get_collection().find_one({'auth0_id': auth0_id})
                if not student:
                    return jsonify({
                        "success": False,
                        "error": "Student profile not found",
                        "incomplete_profile": True
                    }), 404

                # Required fields for essay feedback
                required_fields = {
                    'name': 'Name',
                    'major': 'Major',
                    'personality_type': 'Personality Type',
                    'extracurriculars': 'Extracurricular Activities',
                    'student_context': 'Background Context',
                    'student_theme': 'Student Theme',
                    'awards': 'Awards and Achievements',  # Additional field for essay feedback
                    'hooks': 'Personal Hooks'  # Additional field for essay feedback
                }

                missing_fields = []
                for field, display_name in required_fields.items():
                    if field not in student or not student[field]:
                        missing_fields.append(display_name)
                    # Special check for student_context
                    elif field == 'student_context':
                        context = student[field]
                        if not any(context.get(key) for key in ['international_student', 'first_generation', 'ethnicity']):
                            missing_fields.append('Student Background Information')

                if missing_fields:
                    return jsonify({
                        "success": False,
                        "error": f"Please complete the following fields in your profile: {', '.join(missing_fields)}",
                        "incomplete_profile": True,
                        "missing_fields": missing_fields
                    }), 400

                # If all checks pass, proceed with the request
                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Error in essay feedback validation: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": "Error validating student profile",
                    "incomplete_profile": True
                }), 500

        return decorated_function
    return decorator 
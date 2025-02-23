import logging
import json
from datetime import datetime
from functools import wraps
from flask import g
from models.student_model import Student

logger = logging.getLogger(__name__)

class ECSuggestionsValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def json_serial(self, obj):
        if isinstance(obj, (datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def validate_student_profile(self, student):
        missing_fields = []
        student_name = student.get('name', 'Student')

        # Check basic profile information
        if not student.get('major'):
            missing_fields.append('Major')
        if not student.get('personality_type'):
            missing_fields.append('Personality Type')

        # Check extracurriculars
        extracurriculars = student.get('extracurriculars', [])
        if not extracurriculars:
            missing_fields.append('Current Extracurricular Activities')
        
        # Check student statistics
        stats = student.get('student_statistics', {})
        if not stats:
            missing_fields.append('Student Statistics')
        else:
            if stats.get('class_rank', 0) == 0:
                missing_fields.append('Class Rank')
            if stats.get('unweight_gpa', 0) == 0:
                missing_fields.append('Unweighted GPA')
            if stats.get('weight_gpa', 0) == 0:
                missing_fields.append('Weighted GPA')

        # Check student context
        context = student.get('student_context', {})
        if not context:
            missing_fields.append('Student Context')
        else:
            if context.get('international_student') is None:
                missing_fields.append('International Student Status')
            if context.get('first_generation') is None:
                missing_fields.append('First Generation Status')
            if not context.get('ethnicity'):
                missing_fields.append('Ethnicity')

        # Check student theme
        if not student.get('student_theme', '').strip():
            missing_fields.append('Student Theme')

        if missing_fields:
            error_msg = f"{student_name}, please complete the following fields in your profile to help me provide the best extracurricular activity recommendations:\n\n" + "\n".join(f"- {field}" for field in missing_fields)
            self.logger.warning(f"EC Suggestions validation failed with missing fields: {missing_fields}")
            return [error_msg]

        self.logger.info("EC Suggestions profile validation successful")
        return []

def validate_ec_suggestions_profile():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get auth0_id from g.user_info (set by verify_google_token)
                auth0_id = g.user_info.get('sub')
                if not auth0_id:
                    logger.error("No auth0_id found in user info")
                    return {"error": "User not authenticated"}, 401

                # Get student from database
                student = Student.get_collection().find_one({'auth0_id': auth0_id})
                if not student:
                    logger.error(f"Student not found with auth0_id: {auth0_id}")
                    return {"error": "Student not found"}, 404

                # Validate student profile
                validator = ECSuggestionsValidator()
                validation_errors = validator.validate_student_profile(student)
                
                if validation_errors:
                    return {
                        "error": "Profile incomplete",
                        "message": validation_errors[0],
                        "incomplete_profile": True
                    }, 400

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"Error in EC suggestions validation: {str(e)}")
                return {"error": str(e)}, 500

        return decorated_function
    return decorator 
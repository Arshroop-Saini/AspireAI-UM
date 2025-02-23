import logging
import json
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class CollegeListValidator:
    def __init__(self):
        self.inputs = {}
        self.logger = logging.getLogger(__name__)


    def validate_student_profile(self, student):
        """Validate that the student profile has all required fields and non-default values."""
        if not student:
            return ["Student profile is empty"]
           
        self.logger.debug(f"Starting validation for student profile: {json.dumps(student, indent=2, default=json_serial)}")
        self.logger.debug(f"Target colleges in profile: {student.get('target_colleges')}")
        missing_fields = []
        student_name = student.get('name', 'Student')
       
        # Initialize target_colleges if not present
        if 'target_colleges' not in student:
            student['target_colleges'] = []
            self.logger.debug("Initialized target_colleges as empty list")
        elif not isinstance(student['target_colleges'], list):
            student['target_colleges'] = list(student['target_colleges'])
            self.logger.debug("Converted target_colleges to list")
       
        # Check student_context required fields
        context = student.get('student_context', {})
        if not context:
            missing_fields.append('Student Context')
        else:
            # Required string fields - check for empty strings
            if not context.get('country', '').strip():
                missing_fields.append('Country')
            if not context.get('ethnicity', '').strip():
                missing_fields.append('Ethnicity')
            if not context.get('gender', '').strip():
                missing_fields.append('Gender')
           
            # Required numeric fields - check for 0 (default value)
            if context.get('estimated_contribution', 0) == 0:
                missing_fields.append('Estimated Contribution')
           
            # Required boolean fields - check for None values
            if context.get('financial_aid_required') is None:
                missing_fields.append('Financial Aid Required (needs to be explicitly set)')
            if context.get('first_generation') is None:
                missing_fields.append('First Generation Status (needs to be explicitly set)')
            if context.get('international_student') is None:
                missing_fields.append('International Student Status (needs to be explicitly set)')
       
        # Check student_statistics
        stats = student.get('student_statistics', {})
        if not stats:
            missing_fields.append('Student Statistics')
        else:
            # Required numeric fields - check for 0 (default values)
            self.logger.debug(f"Checking student statistics: {json.dumps(stats, indent=2, default=json_serial)}")
            if stats.get('class_rank', 0) == 0:
                missing_fields.append('Class Rank')
            if stats.get('unweight_gpa', 0) == 0:
                missing_fields.append('Unweighted GPA')
            if stats.get('weight_gpa', 0) == 0:
                missing_fields.append('Weighted GPA')
            # Convert SAT score to int for comparison
            sat_score = stats.get('sat_score')
            try:
                sat_score = int(sat_score) if sat_score is not None else 0
            except (ValueError, TypeError):
                sat_score = 0
            if sat_score == 0:
                missing_fields.append('SAT Score')
                self.logger.debug("SAT Score validation failed: score is 0 or invalid")
       
        # Check student_preferences arrays (empty lists are default)
        prefs = student.get('student_preferences', {})
        if not prefs:
            missing_fields.append('Student Preferences')
        else:
            if not prefs.get('campus_sizes', []):
                missing_fields.append('Campus Sizes')
            if not prefs.get('college_types', []):
                missing_fields.append('College Types')
            if not prefs.get('preferred_regions', []):
                missing_fields.append('Preferred Regions')
            if not prefs.get('preferred_states', []):
                missing_fields.append('Preferred States')
       
        # Check student_theme (empty string is default)
        if not student.get('student_theme', '').strip():
            missing_fields.append('Student Theme')
       
        # Check hooks (empty list is default)
        if not student.get('hooks', []):
            missing_fields.append('Hooks')
       
        if missing_fields:
            error_msg = f"{student_name}, please complete the following fields in your profile to help me provide the best college recommendations:\n\n" + "\n".join(f"- {field}" for field in missing_fields)
            self.logger.warning(f"Validation failed with missing fields: {missing_fields}")
            return [error_msg]
       
        self.logger.info("Profile validation successful")
        return []


    def store_student_profile(self, student_profile):
        """Store student profile in the inputs dictionary."""
        try:
            self.logger.debug(f"Attempting to store student profile: {json.dumps(student_profile, indent=2, default=json_serial)}")
           
            # Store all relevant sections in inputs
            self.inputs.update({
                'student_context': student_profile.get('student_context', {}),
                'student_statistics': student_profile.get('student_statistics', {}),
                'student_preferences': student_profile.get('student_preferences', {}),
                'student_theme': student_profile.get('student_theme'),
                'hooks': student_profile.get('hooks', []),
                'target_colleges': student_profile.get('target_colleges', [])
            })


            self.logger.info("Student profile stored successfully")
            self.logger.debug(f"Stored inputs: {json.dumps(self.inputs, indent=2, default=json_serial)}")
            return []
        except Exception as e:
            error_msg = f"Error storing student profile: {str(e)}"
            self.logger.error(error_msg)
            return [error_msg]
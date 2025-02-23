from datetime import datetime
from models.student_model import Student
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

def get_user_profile(auth0_id):
    try:
        student = Student.get_by_auth0_id(auth0_id)
        
        if not student:
            return None, "User not found"
        
        # The student model now has proper to_dict() method that handles all fields
        return student.to_dict(), None

    except Exception as e:
        print(f"Error in get_user_profile: {str(e)}")
        return None, str(e)

def update_user_profile(auth0_id, update_data):
    try:
        logger.info(f"Starting profile update for auth0_id: {auth0_id}")
        logger.info(f"Update data received: {update_data}")
        logger.info(f"Name in update data: {update_data.get('name')}")  # Log name specifically
        
        student_data = Student.get_by_auth0_id(auth0_id)
        logger.info(f"Current student data: {student_data}")
        logger.info(f"Current name in DB: {student_data.get('name')}")  # Log current name
        
        if not student_data:
            return None, "User not found"

        # Create Student instance from data
        student = Student(student_data)
        
        # Update allowed fields
        allowed_fields = [
            'name', 'email', 'major', 'extracurriculars', 'awards',
            'personality_type', 'picture', 'target_colleges',
            'supplemental_essays', 'student_context', 'student_statistics',
            'student_preferences', 'student_theme', 'hooks'
        ]

        # Filter out non-allowed fields but preserve auth0_id and name
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        filtered_data['auth0_id'] = student_data['auth0_id']  # Preserve auth0_id
        
        # Ensure name is included if it was in the update data
        if 'name' in update_data:
            logger.info(f"Setting name in filtered data to: {update_data['name']}")
            filtered_data['name'] = update_data['name']
            
        logger.info(f"Filtered data to update: {filtered_data}")

        # Validate nested objects structure
        if 'student_context' in filtered_data:
            required_context_fields = [
                'country', 'estimated_contribution', 'financial_aid_required',
                'first_generation', 'ethnicity', 'gender', 'international_student'
            ]
            if not all(field in filtered_data['student_context'] for field in required_context_fields):
                return None, "Invalid student_context structure"

        if 'student_statistics' in filtered_data:
            required_stats_fields = ['class_rank', 'unweight_gpa', 'weight_gpa', 'sat_score']
            if not all(field in filtered_data['student_statistics'] for field in required_stats_fields):
                return None, "Invalid student_statistics structure"

        if 'student_preferences' in filtered_data:
            required_pref_fields = ['campus_sizes', 'college_types', 'preferred_regions', 'preferred_states']
            if not all(field in filtered_data['student_preferences'] for field in required_pref_fields):
                return None, "Invalid student_preferences structure"

        try:
            # Update the student profile with filtered data
            student.update_data(filtered_data)
            logger.info(f"Updated student data in memory: {student.to_dict()}")
            
            # Save the changes
            save_result = student.save()
            logger.info(f"Save result: {save_result}")
            
            if not save_result:
                logger.error("Failed to save profile changes - no documents modified")
                return None, "Failed to save profile changes"

            # Verify the update in database
            updated_student = Student.get_by_auth0_id(auth0_id)
            logger.info(f"Verified updated student data in DB: {updated_student}")

            # Return the updated profile
            return student.to_dict(), None
            
        except Exception as e:
            logger.error(f"Error updating student profile: {str(e)}")
            return None, f"Failed to update profile: {str(e)}"

    except Exception as e:
        logger.error(f"Error in update_user_profile: {str(e)}")
        return None, str(e) 
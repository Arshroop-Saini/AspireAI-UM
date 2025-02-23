from typing import Type, Optional
from crewai.tools import BaseTool
import logging
from typing import Any
from pydantic import BaseModel, Field
from models.student_model import Student

logger = logging.getLogger(__name__)

class StudentProfileInput(BaseModel):
    auth0_id: str = Field(description="The auth0_id of the student to search for")

class StudentProfileMemoryTool(BaseTool):
    """Tool for retrieving student profile information from MongoDB."""
    
    name: str = "StudentProfileMemoryTool"
    description: str = """
    Use this tool to retrieve student profile information from the database.
    The tool will fetch various fields and categories of student data including:
        - student_statistics (GPA, SAT scores, etc.)
        - student_preferences (college types, campus sizes, etc.)
        - student_basic_info (name, email, etc.)
        - student_context (background information)
        - student_theme
        - hooks
        - personality_type
        - target_colleges
        - extracurriculars
        - awards
    """

    def __init__(self) -> None:
        super().__init__()
        self.args_schema = StudentProfileInput
        logger.info("Initialized StudentProfileMemoryTool")

    def _run(self, auth0_id: str) -> str:
        """Execute the database query for student profile information."""
        if not auth0_id:
            logger.error("No auth0_id provided")
            return "Error: auth0_id is required"

        try:
            logger.info(f"Fetching profile data for auth0_id: {auth0_id}")
            student = Student.get_by_auth0_id(auth0_id)
            
            if not student:
                logger.warning(f"No student found with auth0_id: {auth0_id}")
                return "No student profile found"
            
            # Convert the student data to a formatted string
            profile_info = []
            
            # Basic Info
            if student.get('name'):
                profile_info.append(f"Name: {student['name']}")
            if student.get('email'):
                profile_info.append(f"Email: {student['email']}")
            if student.get('major'):
                profile_info.append(f"Major: {student['major']}")
            if student.get('personality_type'):
                profile_info.append(f"Personality Type: {student['personality_type']}")
            
            # Academic Info
            stats = student.get('student_statistics', {})
            if stats:
                academic_info = []
                if stats.get('weight_gpa'):
                    academic_info.append(f"Weighted GPA: {stats['weight_gpa']}")
                if stats.get('unweight_gpa'):
                    academic_info.append(f"Unweighted GPA: {stats['unweight_gpa']}")
                if stats.get('sat_score'):
                    academic_info.append(f"SAT Score: {stats['sat_score']}")
                if stats.get('class_rank'):
                    academic_info.append(f"Class Rank: {stats['class_rank']}")
                if academic_info:
                    profile_info.append("Academic Profile: " + ", ".join(academic_info))
            
            # Student Context
            context = student.get('student_context', {})
            if context:
                context_info = []
                if context.get('international_student'):
                    context_info.append("International student")
                if context.get('first_generation'):
                    context_info.append("First-generation student")
                if context.get('financial_aid_required'):
                    context_info.append("Requires financial aid")
                if context.get('country'):
                    context_info.append(f"From {context['country']}")
                if context.get('ethnicity'):
                    context_info.append(f"Ethnicity: {context['ethnicity']}")
                if context.get('gender'):
                    context_info.append(f"Gender: {context['gender']}")
                if context.get('estimated_contribution'):
                    context_info.append(f"Estimated Contribution: ${context['estimated_contribution']:,}")
                if context_info:
                    profile_info.append("Background: " + ", ".join(context_info))
            
            # Preferences
            prefs = student.get('student_preferences', {})
            if prefs:
                if prefs.get('college_types'):
                    profile_info.append(f"Preferred college types: {', '.join(prefs['college_types'])}")
                if prefs.get('campus_sizes'):
                    profile_info.append(f"Preferred campus sizes: {', '.join(prefs['campus_sizes'])}")
                if prefs.get('preferred_regions'):
                    profile_info.append(f"Preferred regions: {', '.join(prefs['preferred_regions'])}")
                if prefs.get('preferred_states'):
                    profile_info.append(f"Preferred states: {', '.join(prefs['preferred_states'])}")
            
            # Activities and Achievements
            if student.get('extracurriculars'):
                activities = []
                for activity in student['extracurriculars']:
                    if isinstance(activity, dict):
                        activity_str = f"{activity.get('name', '')}"
                        if activity.get('activity_type'):
                            activity_str += f" ({activity['activity_type']})"
                        if activity.get('position_leadership'):
                            activity_str += f" - Position: {activity['position_leadership']}"
                        if activity.get('organization_description'):
                            activity_str += f" - Organization: {activity['organization_description']}"
                        if activity.get('activity_description'):
                            activity_str += f" - Description: {activity['activity_description']}"
                        activities.append(activity_str)
                if activities:
                    profile_info.append(f"Extracurriculars: {'; '.join(activities)}")
            
            if student.get('awards'):
                awards = []
                for award in student['awards']:
                    if isinstance(award, dict):
                        award_str = f"{award.get('title', '')}"
                        if award.get('grade_levels'):
                            award_str += f" - Grades: {', '.join(award['grade_levels'])}"
                        if award.get('recognition_levels'):
                            award_str += f" - Recognition: {', '.join(award['recognition_levels'])}"
                        awards.append(award_str)
                if awards:
                    profile_info.append(f"Awards: {'; '.join(awards)}")
            
            if student.get('hooks'):
                profile_info.append(f"Hooks: {', '.join(student['hooks'])}")
            
            if student.get('target_colleges'):
                college_names = [college['name'] for college in student['target_colleges']]
                profile_info.append(f"Target Colleges: {', '.join(college_names)}")
            
            if student.get('student_theme'):
                profile_info.append(f"Theme: {student['student_theme']}")
            
            formatted_profile = "\n".join(profile_info)
            logger.info("Successfully retrieved and formatted student profile")
            return formatted_profile
            
        except Exception as e:
            logger.error(f"Error in _run: {str(e)}")
            return f"Error retrieving student profile: {str(e)}"

    async def _arun(self, auth0_id: str) -> str:
        """Async version of the profile retrieval - not implemented."""
        raise NotImplementedError("Async version not implemented")
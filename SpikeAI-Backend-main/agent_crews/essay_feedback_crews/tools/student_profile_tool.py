from typing import Type, Optional
from crewai.tools import BaseTool
import logging
from typing import Any
from pydantic import BaseModel, Field
from models.student_model import Student

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class StudentProfileInput(BaseModel):
    auth0_id: str = Field(description="The auth0_id of the student to search for")

class StudentProfileTool(BaseTool):
    """Tool for retrieving specific student profile information from MongoDB for essay analysis."""
    
    name: str = "StudentProfileTool"
    description: str = """
    Use this tool to retrieve essential student profile information from MongoDB for essay analysis.
    The tool will fetch the following specific fields:
        - name
        - major
        - extracurriculars
        - awards
        - student_theme
        - hooks
        - personality_type
        - student_context (all fields)
    """

    def __init__(self) -> None:
        super().__init__()
        self.args_schema = StudentProfileInput
        logger.info("Initialized StudentProfileTool")

    def _run(self, auth0_id: str) -> str:
        """Execute the database query for specific student profile information."""
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
            if student.get('major'):
                profile_info.append(f"Major: {student['major']}")
            if student.get('personality_type'):
                profile_info.append(f"Personality Type: {student['personality_type']}")
            
            # Student Context (all fields)
            context = student.get('student_context', {})
            if context:
                context_info = []
                for key, value in context.items():
                    if value is not None:
                        if isinstance(value, bool):
                            if value:
                                context_info.append(key.replace('_', ' ').title())
                        elif isinstance(value, (int, float)) and key == 'estimated_contribution':
                            context_info.append(f"{key.replace('_', ' ').title()}: ${value:,}")
                        else:
                            context_info.append(f"{key.replace('_', ' ').title()}: {value}")
                if context_info:
                    profile_info.append("Background Context: " + ", ".join(context_info))
            
            # Activities and Achievements
            if student.get('extracurriculars'):
                activities = []
                for activity in student['extracurriculars']:
                    if isinstance(activity, dict):
                        activity_str = f"{activity.get('name', '')}"
                        if activity.get('position_leadership'):
                            activity_str += f" - Position: {activity['position_leadership']}"
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
                        if award.get('recognition_levels'):
                            award_str += f" - Recognition: {', '.join(award['recognition_levels'])}"
                        awards.append(award_str)
                if awards:
                    profile_info.append(f"Awards: {'; '.join(awards)}")
            
            if student.get('hooks'):
                profile_info.append(f"Hooks: {', '.join(student['hooks'])}")
            
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
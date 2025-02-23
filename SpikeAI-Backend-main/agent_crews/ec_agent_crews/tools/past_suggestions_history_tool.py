from typing import Type, Optional
from crewai.tools import BaseTool
from mem0 import MemoryClient
import os
import logging
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class StudentProfileInput(BaseModel):
    auth0_id: str = Field(description="The auth0_id of the student to search for")
    activity_type: str = Field(description="The type of activity to search for")

class PastSuggestionsHistoryTool(BaseTool):
    """Tool for searching past college suggestions from Mem0 memory."""
    
    name: str = "PastSuggestionsHistoryTool"
    description: str = """
    Use this tool to search for past EC suggestions stored in memory.
    The tool will search through various fields and categories of student data including:
    - ec_suggestions
    - activity types
    You can filter suggestions by activity type to get relevant past activities.
    """

    def __init__(self) -> None:
        super().__init__()
        try:
            self._client = MemoryClient(api_key=os.environ.get("MEM0_API_KEY", "m0-DF90O1P1ad5pbj0DMspbqyor68M4VMpcelQeIMIh"))
            self.args_schema = StudentProfileInput
            logger.info("Initialized PastSuggestionsHistoryTool")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryClient: {str(e)}")
            raise

    def _run(self, auth0_id: str, activity_type: str) -> str:
        """Execute the memory search for student profile information with activity type filtering."""
        if not auth0_id:
            logger.error("No auth0_id provided")
            return "Error: auth0_id is required"

        if not activity_type:
            logger.error("No activity_type provided")
            return "Error: activity_type is required"

        try:
            logger.info(f"Searching for past {activity_type} suggestions for auth0_id: {auth0_id}")
            
            # Create filter for activity type in metadata
            filters = {
                "metadata": {
                    "activity_types": {
                        "$contains": activity_type
                    }
                }
            }

            # Get results with activity type filter
            results = self._client.get_all(
                user_id=auth0_id,
                agent_id=f"ec_expert_agent_{auth0_id}",
                filters=filters
            )

            if not results:
                logger.info(f"No past suggestions found for activity type: {activity_type}")
                return f"No past suggestions found for activity type: {activity_type}"

            # Process results to extract unique activities of the specified type
            unique_activities = set()  # Use a set to automatically deduplicate
            for result in results:
                if 'metadata' in result and 'activity_types' in result['metadata']:
                    activity_types = result['metadata']['activity_types']
                    # Extract activities that match the requested type
                    for activity_name, stored_type in activity_types.items():
                        if stored_type == activity_type:
                            unique_activities.add(activity_name)

            if not unique_activities:
                return f"Found results but no activities matched type: {activity_type}"

            # Convert set back to sorted list for consistent output
            sorted_activities = sorted(unique_activities)
            activities_str = "\n".join(f"- {activity}" for activity in sorted_activities)
            return f"Found {len(sorted_activities)} activities of type {activity_type}:\n{activities_str}"

        except Exception as e:
            logger.error(f"Error in _run: {str(e)}")
            return f"Error searching for past suggestions: {str(e)}"

    async def _arun(self, auth0_id: str, activity_type: str) -> str:
        """Async version of the search - not implemented."""
        raise NotImplementedError("Async version not implemented")
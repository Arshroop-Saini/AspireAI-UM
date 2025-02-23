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

class PastSuggestionsHistoryTool(BaseTool):
    """Tool for searching past college suggestions from Mem0 memory."""
    

    name: str = "PastSuggestionsHistoryTool"
    description: str = """
    Use this tool to search for past college suggestions stored in memory.
    The tool will search through various fields and categories of student data including:
    - college_list_suggestions
    - target_colleges
    """

    def __init__(self) -> None:
        super().__init__()
        try:
            self._client = MemoryClient(api_key="m0-DF90O1P1ad5pbj0DMspbqyor68M4VMpcelQeIMIh")
            self.args_schema = StudentProfileInput
            logger.info("Initialized StudentProfileMemoryTool")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryClient: {str(e)}")
            raise

    def _run(self, auth0_id: str) -> str:
        """Execute the memory search for student profile information."""
        if not auth0_id:
            logger.error("No auth0_id provided")
            return "Error: auth0_id is required"

        try:
            logger.info(f"Searching for past college suggestions for auth0_id: {auth0_id}")
            results = self._client.get_all(
                user_id=auth0_id,
                agent_id=f"college_expert_agent_{auth0_id}",
            )

            logger.info(f"Raw search results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error in _run: {str(e)}")
            raise
   

    async def _arun(self, auth0_id: str) -> str:
        """Async version of the search - not implemented."""
        raise NotImplementedError("Async version not implemented")
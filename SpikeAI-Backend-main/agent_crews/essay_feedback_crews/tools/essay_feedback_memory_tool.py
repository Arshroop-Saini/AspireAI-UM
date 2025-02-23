from typing import Type, Optional
from crewai.tools import BaseTool
from mem0 import MemoryClient
import os
import logging
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to see all logs

class ThreadMemoryInput(BaseModel):
    auth0_id: str = Field(description="The auth0_id of the user")
    thread_id: str = Field(description="The ID of the essay feedback thread")

class EssayFeedbackMemoryTool(BaseTool):
    """Tool for retrieving essay feedback history from memory."""
    
    name: str = "essay_feedback_memory"
    description: str = """
    Use this tool to retrieve the history of feedback for a specific essay thread.
    The tool will search through feedback history and return all previous feedback in chronological order.
    """

    def __init__(self) -> None:
        """Initialize the tool."""
        super().__init__()
        try:
            self._client = MemoryClient(api_key="m0-DF90O1P1ad5pbj0DMspbqyor68M4VMpcelQeIMIh")
            self.args_schema = ThreadMemoryInput
            logger.info("✅ Initialized EssayFeedbackMemoryTool")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MemoryClient: {str(e)}")
            raise

    def _run(self, auth0_id: str, thread_id: str) -> str:
        """Execute the memory search for essay feedback history."""
        try:
            logger.debug(f"🔍 EssayFeedbackMemoryTool._run called with auth0_id: {auth0_id}, thread_id: {thread_id}")
            
            if not auth0_id or not thread_id:
                logger.error("❌ Missing required parameters")
                return "Error: auth0_id and thread_id are required"

            logger.info(f"🔎 Searching for feedback history - auth0_id: {auth0_id}, thread_id: {thread_id}")
            
            # Get all memories for this thread
            results = self._client.get_all(
                user_id=auth0_id,
                agent_id=f"essay_feedback_{thread_id}",
                filters={
                    "metadata": {
                        "thread_id": thread_id,
                        "type": "essay_feedback"
                    }
                }
            )
            logger.debug(f"📊 Raw search results: {results}")

            if not results:
                logger.info("ℹ️ No previous feedback found")
                return "No previous feedback found for this thread."

            # Simply return the raw results for the agent to process
            return str(results)
            
        except Exception as e:
            logger.error(f"❌ Error in _run: {str(e)}")
            return f"Error retrieving feedback memory: {str(e)}"

    async def _arun(self, auth0_id: str, thread_id: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("EssayFeedbackMemoryTool does not support async")
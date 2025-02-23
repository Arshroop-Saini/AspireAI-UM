from typing import Type, Optional
from crewai.tools import BaseTool
from mem0 import MemoryClient
import os
import logging
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to see all logs

class IdeasHistoryInput(BaseModel):
    auth0_id: str = Field(description="The auth0_id of the user")
    thread_id: str = Field(description="The ID of the essay brainstorming thread")

class IdeasHistoryTool(BaseTool):
    """Tool for retrieving essay brainstorming history from memory."""
    
    name: str = "ideas_history_tool"
    description: str = """
    Use this tool to retrieve the history of brainstorming ideas for a specific essay thread.
    The tool will search through brainstorming history and return:
    - Past essay ideas and themes
    - Previous brainstorming approaches
    - Chronological history of ideas
    - Successful patterns and concepts
    """

    def __init__(self) -> None:
        """Initialize the tool."""
        super().__init__()
        try:
            self._client = MemoryClient(api_key="m0-DF90O1P1ad5pbj0DMspbqyor68M4VMpcelQeIMIh")
            self.args_schema = IdeasHistoryInput
            logger.info("✅ Initialized IdeasHistoryTool")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MemoryClient: {str(e)}")
            raise

    def _run(self, auth0_id: str, thread_id: str) -> str:
        """Execute the memory search for essay brainstorming history."""
        try:
            logger.debug(f"🔍 IdeasHistoryTool._run called with auth0_id: {auth0_id}, thread_id: {thread_id}")
            
            if not auth0_id or not thread_id:
                logger.error("❌ Missing required parameters")
                return "Error: auth0_id and thread_id are required"

            logger.info(f"🔎 Searching for brainstorming history - auth0_id: {auth0_id}, thread_id: {thread_id}")
            
            # Get all memories for this thread
            results = self._client.get_all(
                user_id=auth0_id,
                agent_id=f"essay_brainstorm_{thread_id}",
                filters={
                    "metadata": {
                        "thread_id": thread_id,
                        "type": "essay_brainstorm"
                    }
                }
            )
            logger.debug(f"📊 Raw search results: {results}")

            if not results:
                logger.info("ℹ️ No brainstorming history found")
                return "No previous brainstorming ideas found for this thread."

            # Return the raw results for the agent to process
            return str(results)
            
        except Exception as e:
            logger.error(f"❌ Error in _run: {str(e)}")
            return f"Error retrieving brainstorming history: {str(e)}"

    async def _arun(self, auth0_id: str, thread_id: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("IdeasHistoryTool does not support async") 
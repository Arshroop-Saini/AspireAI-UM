from typing import Type, Optional
from crewai.tools import BaseTool
import logging
from typing import Any
from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchRun

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CollegeSearchInput(BaseModel):
    query: str = Field(description="The search query about college essays")
    college_name: str = Field(description="The name of the college to research")

class CollegeSearchTool(BaseTool):
    """Tool for searching college essay information and requirements online."""
    
    name: str = "CollegeSearchTool"
    description: str = """
    Use this tool to search for college-specific essay information online.
    The tool will search for:
        - College essay requirements
        - Writing style preferences
        - Successful essay examples
        - Expert advice and tips
        - Common mistakes to avoid
        
    Guidelines for effective queries:
    1. Use specific search terms: "[college name] essay requirements"
    2. Include specific aspects: "[college name] essay style preferences"
    3. Include examples: "[college name] successful essay examples"
    4. Include tips: "[college name] essay writing tips"
    5. Include mistakes: "[college name] common essay mistakes"
    6. Include deadlines: "[college name] essay deadlines"
    7. Include prompts: "[college name] essay prompts"
    8. Include word limits: "[college name] essay word limits"
    """

    def __init__(self) -> None:
        super().__init__()
        self._search = DuckDuckGoSearchRun()
        self.args_schema = CollegeSearchInput
        logger.info("Initialized CollegeSearchTool")

    def _run(self, query: str, college_name: str) -> str:
        """Execute the search for college essay information."""
        if not query or not college_name:
            logger.error("Missing required parameters")
            return "Error: Both query and college_name are required"

        try:
            logger.info(f"Searching for {college_name} essay information: {query}")
            
            # Format the search query
            formatted_query = f"{college_name} {query} college essay tips requirements"
            
            # Perform search and format results
            results = self._search.run(formatted_query)
            
            # Clean and format results
            cleaned_results = results.replace("...", ".\n").replace(". ", ".\n")
            
            logger.info("Successfully retrieved search results")
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Error in _run: {str(e)}")
            return f"Error performing search: {str(e)}"

    async def _arun(self, query: str, college_name: str) -> str:
        """Async version of the search - not implemented."""
        raise NotImplementedError("Async version not implemented") 
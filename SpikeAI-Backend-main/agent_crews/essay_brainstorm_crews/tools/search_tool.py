from typing import Type, Optional
from crewai.tools import BaseTool
import logging
from typing import Any
from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchRun

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CollegeSearchInput(BaseModel):
    query: str = Field(description="The search query about essay brainstorming")
    college_name: str = Field(description="The name of the college to research")

class CollegeSearchTool(BaseTool):
    """Tool for searching college essay brainstorming information and ideas online."""
    
    name: str = "CollegeSearchTool"
    description: str = """
    Use this tool to search for college-specific essay brainstorming information online.
    The tool will search for:
        - College essay topics and themes
        - Successful essay ideas and approaches
        - Personal story examples
        - Brainstorming techniques
        - Topic selection strategies
        - Unique angles and perspectives
        - Student experiences
        - Value alignment ideas
        
    Guidelines for effective queries:
    1. Use specific search terms: "[college name] essay topics"
    2. Include themes: "[college name] successful essay themes"
    3. Include examples: "[college name] unique essay ideas"
    4. Include values: "[college name] essay values alignment"
    5. Include experiences: "[college name] student essay stories"
    6. Include strategies: "[college name] essay brainstorming techniques"
    7. Include perspectives: "[college name] essay unique angles"
    8. Include impact: "[college name] impactful essay topics"
    """

    def __init__(self) -> None:
        super().__init__()
        self._search = DuckDuckGoSearchRun()
        self.args_schema = CollegeSearchInput
        logger.info("✅ Initialized CollegeSearchTool")

    def _run(self, query: str, college_name: str) -> str:
        """Execute the search for essay brainstorming information."""
        if not query or not college_name:
            logger.error("❌ Missing required parameters")
            return "Error: Both query and college_name are required"

        try:
            logger.info(f"🔍 Searching for {college_name} essay brainstorming: {query}")
            
            # Format the search query
            formatted_query = f"{college_name} {query} college essay ideas topics brainstorming examples"
            
            # Perform search and format results
            results = self._search.run(formatted_query)
            
            # Clean and format results
            cleaned_results = results.replace("...", ".\n").replace(". ", ".\n")
            
            logger.info("✅ Successfully retrieved search results")
            return cleaned_results
            
        except Exception as e:
            logger.error(f"❌ Error in _run: {str(e)}")
            return f"Error performing search: {str(e)}"

    async def _arun(self, query: str, college_name: str) -> str:
        """Async version of the search - not implemented."""
        raise NotImplementedError("Async version not implemented") 
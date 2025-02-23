from typing import Dict, Union
from langchain_community.tools import DuckDuckGoSearchRun
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")

class SearchTool(BaseTool):
    """Search for college information using specific queries.
    
    Guidelines for effective queries:
    - Include name of the university or college if relevant
    - ec that got students into [college name]
    - ec that worked for [college name]
    - ec that got students into [college name]
    """
    


    name: str = "SearchTool"
    description: str = """
    This tool can be used to search the web for gathering information about anything related extracurricular activities.
    """



    def __init__(self) -> None:
        super().__init__()
        self._search = DuckDuckGoSearchRun()
        self.args_schema = SearchInput


    def _run(self, query: str) -> str:
        """Execute the search with proper query formatting."""
        try:
            search_query = str(query)
            # Perform search and format results
            results = self._search.run(search_query)
            
            # Clean and format results
            cleaned_results = results.replace("...", ".\n").replace(". ", ".\n")
            
            return cleaned_results
            
        except Exception as e:
            return f"Error performing search: {str(e)}"

    async def _arun(self, query: str) -> str:
        """Async version of the search - not implemented."""
        raise NotImplementedError("Async version not implemented") 
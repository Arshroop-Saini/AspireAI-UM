from typing import Dict, Union
from langchain_community.tools import DuckDuckGoSearchRun
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")

class SearchTool(BaseTool):
    """Search for college information using specific queries.
    
    Guidelines for effective queries:
    1. Use specific search terms: "[college name] + [specific aspect]"
    2. Include location if relevant: "colleges in [state/region]"
    3. Include program specifics: "[field] programs at [college]"
    4. Include admission criteria: "[college] admission requirements"
    5. Include financial aspects: "[college] financial aid international students"
    6. Include statistics: "[college] SAT scores GPA requirements"
    7. Include deadlines: "[college] application deadlines"
    8. Include size: "[college] student body size"
    9. Include location: "[college] location"
    10. Include type: "[college] type"
    11. Include scholarships: "[college] scholarships"
    12. Include financial aid: "[college] financial aid"
    13. Include admission requirements: "[college] admission requirements"
    14. Include rankings: "[college] rankings"
    15. Include reviews: "[college] reviews"
    16. Include statistics: "[college] SAT scores GPA requirements"
    """
    


    name: str = "SearchTool"
    description: str = """
    This tool can be used to search the web for gathering information about anything related to colleges and universities.
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
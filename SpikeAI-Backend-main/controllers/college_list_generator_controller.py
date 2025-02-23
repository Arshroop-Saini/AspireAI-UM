from typing import Dict, Any
from models.student_model import Student
from models.crew_suggestions_model import CrewSuggestions
from models.crew_suggestions_temp_model import CrewSuggestionsTemp
from agent_crews.list_agent_crews.crew import MatchToProposalCrew
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_college_list(output: str) -> list:
    """Parse the college list output from the crew into a structured format"""
    colleges = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        # Match lines like "1. Harvard University | Reach"
        if line and any(char.isdigit() for char in line):
            parts = line.split('|')
            if len(parts) == 2:
                name = parts[0].strip().split('.', 1)[1].strip()
                college_type = parts[1].strip()
                colleges.append({
                    'name': name,
                    'type': college_type,
                    'added_at': datetime.utcnow()
                })
    
    return colleges

def generate_college_list(auth0_id: str, college_type: str = None) -> dict:
    """Controller for matching student profile to colleges with retry logic"""
    try:
        logger.info(f"Received request with auth0_id: {auth0_id}")
        
        # Get student data from database using full auth0_id
        student = Student.get_by_auth0_id(auth0_id)
        logger.info(f"Retrieved student data: {student is not None}")
        
        if not student:
            logger.error(f"No student found with auth0_id: {auth0_id}")
            return {
                "success": False,
                "error": "Student profile not found"
            }

        # Initialize crew with inputs
        inputs = {
            'auth0_id': auth0_id,
            'college_type': college_type.lower() if college_type else 'all'
        }
        
        # Initialize crew
        crew = MatchToProposalCrew(inputs=inputs)
        
        try:
            # First attempt - full process
            crew_instance = crew.crew()
            
            # Check if crew_instance is a dict (error response)
            if isinstance(crew_instance, dict):
                logger.info(f"Crew returned error response: {crew_instance}")
                return crew_instance
                
            result = crew_instance.kickoff()
            
            # Process the result
            if hasattr(result, 'raw_output'):
                output = result.raw_output
            elif hasattr(result, 'final_answer'):
                output = result.final_answer
            else:
                output = str(result)

            # Parse the college list
            colleges = parse_college_list(output)
            
            # Move current temp suggestions to permanent storage
            try:
                CrewSuggestionsTemp.move_to_permanent(auth0_id)
                logger.info("✅ Moved previous suggestions to permanent storage")
            except Exception as e:
                logger.error(f"❌ Error moving suggestions to permanent: {str(e)}")

            # Save new suggestions to temporary storage
            try:
                success = CrewSuggestionsTemp.save_suggestions(auth0_id, colleges)
                if not success:
                    logger.warning("⚠️ Failed to save suggestions temporarily")
            except Exception as e:
                logger.error(f"❌ Error saving temporary suggestions: {str(e)}")

            # Return formatted response for middleware consumption
            return {
                "success": True,
                "data": {
                    "college_list": output  # This format matches what middleware expects
                }
            }
            
        except Exception as e:
            logger.error(f"Initial attempt failed: {str(e)}")
            
            # Determine which task failed and retry accordingly
            error_msg = str(e).lower()
            
            if "profile" in error_msg or "analyzer" in error_msg:
                logger.info("Retrying student profile analysis...")
                try:
                    crew_instance = crew.crew()
                    # Retry profile analysis
                    result = crew_instance.replay(task_id='analyze_profile_task', inputs=inputs)
                    if result:
                        # If profile analysis succeeds, continue with college research
                        result = crew_instance.replay(task_id='research_colleges', inputs=inputs)
                except Exception as retry_e:
                    logger.error(f"Profile analysis retry failed: {str(retry_e)}")
                    raise retry_e
                    
            elif "college" in error_msg or "research" in error_msg:
                logger.info("Retrying college research...")
                try:
                    crew_instance = crew.crew()
                    # Retry college research
                    result = crew_instance.replay(task_id='research_colleges', inputs=inputs)
                except Exception as retry_e:
                    logger.error(f"College research retry failed: {str(retry_e)}")
                    raise retry_e

            # Handle retry result
            if result:
                if hasattr(result, 'raw_output'):
                    output = result.raw_output
                elif hasattr(result, 'final_answer'):
                    output = result.final_answer
                else:
                    output = str(result)

                # Parse and save retry results
                colleges = parse_college_list(output)
                try:
                    CrewSuggestionsTemp.move_to_permanent(auth0_id)
                    CrewSuggestionsTemp.save_suggestions(auth0_id, colleges)
                except Exception as save_e:
                    logger.error(f"❌ Error saving retry suggestions: {str(save_e)}")

                return {
                    "success": True,
                    "data": {
                        "college_list": output
                    }
                }

            return {
                "success": False,
                "error": "Failed to generate recommendations after retries"
            }
            
    except Exception as e:
        logger.error(f"Error in college matching: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }
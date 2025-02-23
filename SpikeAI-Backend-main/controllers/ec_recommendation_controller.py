from typing import Dict, Any, List
from models.student_model import Student
from models.crew_suggestions_model import CrewSuggestions
from models.crew_suggestions_temp_model import CrewSuggestionsTemp
from agent_crews.ec_agent_crews.crew import ECRecommendationCrew
import logging
import traceback
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def parse_ec_recommendations(output: str) -> List[Dict[str, Any]]:
    """Parse the output from the crew into a structured format"""
    try:
        recommendations = []
        lines = output.strip().split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Start of a new recommendation
            if line.startswith('Activity Name:'):
                # Save previous recommendation if exists
                if current_rec and all(k in current_rec for k in ['name', 'description', 'hours_per_week', 'position']):
                    recommendations.append(current_rec)
                current_rec = {'added_at': datetime.utcnow()}
                current_rec['name'] = line.replace('Activity Name:', '').strip()
            elif line.startswith('Position:'):
                current_rec['position'] = line.replace('Position:', '').strip()
            elif line.startswith('Hours per Week:'):
                try:
                    hours_str = line.replace('Hours per Week:', '').strip()
                    # Extract the first number from the string
                    hours = int(re.search(r'\d+', hours_str).group())
                    current_rec['hours_per_week'] = hours
                except (ValueError, AttributeError):
                    current_rec['hours_per_week'] = 0
            elif line.startswith('Description:'):
                current_rec['description'] = line.replace('Description:', '').strip()
        
        # Add the last recommendation if complete
        if current_rec and all(k in current_rec for k in ['name', 'description', 'hours_per_week', 'position']):
            recommendations.append(current_rec)
            
        logger.info(f"✅ Successfully parsed {len(recommendations)} EC recommendations")
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error parsing EC recommendations: {str(e)}")
        return []

def generate_ec_recommendations(auth0_id: str, activity_type: str, hrs_per_wk: int) -> dict:
    """Controller for generating EC recommendations with retry logic"""
    try:
        logger.info(f"Received request with auth0_id: {auth0_id}, activity_type: {activity_type}, hrs_per_wk: {hrs_per_wk}")
        
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
            'activity_type': activity_type.lower(),
            'hrs_per_wk': hrs_per_wk
        }
        
        # Initialize crew
        crew = ECRecommendationCrew(inputs=inputs)
        result = None  # Initialize result variable
        
        try:
            # First attempt - full process
            crew_instance = crew.crew()
            
            # Check if crew_instance is a dict (error response)
            if isinstance(crew_instance, dict):
                logger.info(f"Crew returned error response: {crew_instance}")
                return crew_instance
                
            result = crew_instance.kickoff()
            
            # Process the result
            if result:
                if hasattr(result, 'raw_output'):
                    output = result.raw_output
                elif hasattr(result, 'final_answer'):
                    output = result.final_answer
                else:
                    output = str(result)

                # Parse the recommendations
                recommendations = parse_ec_recommendations(output)
                
                # Move current temp suggestions to permanent storage
                try:
                    CrewSuggestionsTemp.move_to_permanent(auth0_id)
                    logger.info("✅ Moved previous suggestions to permanent storage")
                except Exception as e:
                    logger.error(f"❌ Error moving suggestions to permanent: {str(e)}")

                # Save new suggestions to temporary storage
                try:
                    success = CrewSuggestionsTemp.save_suggestions(auth0_id, recommendations)
                    if not success:
                        logger.warning("⚠️ Failed to save suggestions temporarily")
                except Exception as e:
                    logger.error(f"❌ Error saving temporary suggestions: {str(e)}")

                # Return formatted response for middleware consumption
                return {
                    "success": True,
                    "data": {
                        "recommendations": output  # This format matches what middleware expects
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate recommendations - no result returned"
                }
            
        except Exception as e:
            logger.error(f"Initial attempt failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Determine which task failed and retry accordingly
            error_msg = str(e).lower()
            
            if "profile" in error_msg or "cv" in error_msg:
                logger.info("Retrying student profile analysis...")
                try:
                    crew_instance = crew.crew()
                    # Retry profile analysis
                    result = crew_instance.replay(task_id='analyze_student_profile_task', inputs=inputs)
                    if result:
                        # Continue with remaining tasks
                        result = crew_instance.replay(task_id='check_past_suggestions_task', inputs=inputs)
                        if result:
                            result = crew_instance.replay(task_id='scout_activities_task', inputs=inputs)
                            if result:
                                result = crew_instance.replay(task_id='generate_recommendations_task', inputs=inputs)
                except Exception as retry_e:
                    logger.error(f"Profile analysis retry failed: {str(retry_e)}")
                    return {
                        "success": False,
                        "error": f"Profile analysis retry failed: {str(retry_e)}"
                    }
                    
            elif "past" in error_msg or "suggestions" in error_msg:
                logger.info("Retrying from past suggestions check...")
                try:
                    crew_instance = crew.crew()
                    result = crew_instance.replay(task_id='check_past_suggestions_task', inputs=inputs)
                    if result:
                        result = crew_instance.replay(task_id='scout_activities_task', inputs=inputs)
                        if result:
                            result = crew_instance.replay(task_id='generate_recommendations_task', inputs=inputs)
                except Exception as retry_e:
                    logger.error(f"Past suggestions check retry failed: {str(retry_e)}")
                    return {
                        "success": False,
                        "error": f"Past suggestions check retry failed: {str(retry_e)}"
                    }
                    
            elif "scout" in error_msg or "activities" in error_msg:
                logger.info("Retrying from activities scouting...")
                try:
                    crew_instance = crew.crew()
                    result = crew_instance.replay(task_id='scout_activities_task', inputs=inputs)
                    if result:
                        result = crew_instance.replay(task_id='generate_recommendations_task', inputs=inputs)
                except Exception as retry_e:
                    logger.error(f"Activities scouting retry failed: {str(retry_e)}")
                    return {
                        "success": False,
                        "error": f"Activities scouting retry failed: {str(retry_e)}"
                    }

            # Handle retry result
            if result:
                if hasattr(result, 'raw_output'):
                    output = result.raw_output
                elif hasattr(result, 'final_answer'):
                    output = result.final_answer
                else:
                    output = str(result)

                # Parse and save retry results
                recommendations = parse_ec_recommendations(output)
                try:
                    CrewSuggestionsTemp.move_to_permanent(auth0_id)
                    CrewSuggestionsTemp.save_suggestions(auth0_id, recommendations)
                except Exception as save_e:
                    logger.error(f"❌ Error saving retry suggestions: {str(save_e)}")

                return {
                    "success": True,
                    "data": {
                        "recommendations": output
                    }
                }

            return {
                "success": False,
                "error": "Failed to generate recommendations after retries"
            }
            
    except Exception as e:
        logger.error(f"Error in EC recommendations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }
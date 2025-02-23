from functools import wraps
from flask import g, jsonify
from mem0 import MemoryClient
import os
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def sync_with_mem0(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Execute the route function first to get the crew's response
            response = f(*args, **kwargs)
            
            # Get auth0_id from g.user_info (set by verify_google_token)
            auth0_id = g.user_info.get('sub')
            if not auth0_id:
                logger.error("No auth0_id found in user info")
                return response

            try:
                # Initialize memory client
                client = MemoryClient(api_key=os.environ.get("MEM0_API_KEY"))
                logger.info(f"Initialized memory client for {auth0_id}")

                # Handle both direct dict and jsonified responses
                if hasattr(response, 'get_json'):
                    response_data = response.get_json()
                elif isinstance(response, tuple):
                    response_data = response[0]
                else:
                    response_data = response

                if not isinstance(response_data, dict) or 'data' not in response_data:
                    logger.error("Invalid response format")
                    return response

                college_list_str = response_data.get('data', {}).get('college_list', '')
                if not college_list_str:
                    logger.error("No college list found in response")
                    return response

                # Convert string format to list
                colleges = [
                    college.strip().replace(f"{i+1}. ", "").strip()
                    for i, college in enumerate(college_list_str.split('\n'))
                    if college.strip()
                ]

                if not colleges:
                    logger.error("No valid colleges found in response")
                    return response

                # Format colleges for storage with just names
                colleges_str = "\n".join(colleges)

                # Define includes with both descriptive text and examples
                includes = """
                Full, official names of higher education institutions in the United States.
                Each name should be complete and formal, without abbreviations.
                Examples of correct format:
                - Massachusetts Institute of Technology (not MIT)
                - University of California, Berkeley (not UC Berkeley)
                - The Ohio State University (not Ohio State)
                
                The names should follow these patterns:
                - "[Name] University"
                - "University of [Name]"
                - "[Name] College"
                - "The [Name] University"
                - "[Name] Institute of Technology"
                - "[Name] College of [Type]"
                """

                # Define excludes to prevent storing additional details
                excludes = """
                Exclude any information besides the official college name:
                - SAT scores and ranges
                - GPA requirements and ranges
                - Tuition and financial information (costs, scholarships, aid)
                - Application deadlines and dates
                - Enrollment statistics and student body size
                - Geographic information (city, state, region)
                - Institution type (public/private/community)
                - Campus characteristics and size
                - Links and URLs
                - Acceptance rates and admission statistics
                - Program details and majors
                - Rankings and ratings
                - Abbreviations (e.g., MIT, UCLA)
                - Informal names or nicknames
                - Additional descriptive text or commentary
                - Dates of suggestion or timestamps
                """

                # Add to memory with includes and excludes for precise storage
                client.add(
                    messages=[{
                        "role": "system",
                        "content": "Here are the name/names of colleges suggested by the college expert agent"
                    }, {
                        "role": "assistant",
                        "content": colleges_str
                    }],
                    user_id=auth0_id,
                    agent_id=f"college_expert_agent_{auth0_id}",
                    includes=includes,
                    excludes=excludes,
                    metadata={
                        "type": "college_list_suggestions",
                        "created_at": datetime.utcnow().isoformat(),
                        "total_suggestions": len(colleges)
                    }
                )
                logger.info(f"✅ Successfully stored {len(colleges)} colleges in memory for {auth0_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing or storing college list: {str(e)}")
                # Don't fail the request if memory storage fails
                return response

            return response

        except Exception as e:
            logger.error(f"❌ Error in college suggestions memory: {str(e)}")
            return {"error": str(e)}, 500
        

    return decorated_function
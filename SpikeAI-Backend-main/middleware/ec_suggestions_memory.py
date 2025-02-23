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

                recommendations_str = response_data.get('data', {}).get('recommendations', '')
                if not recommendations_str:
                    logger.error("No recommendations found in response")
                    return response

                # Remove markdown formatting if present
                recommendations_str = recommendations_str.replace('```plaintext', '').replace('```', '').strip()

                # Parse activities from recommendations
                activities = []
                current_activity = None
                
                for line in recommendations_str.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Start of a new activity
                    if line.startswith('Activity Name:'):
                        if current_activity:
                            activities.append(current_activity['name'])
                        current_activity = {'name': line.replace('Activity Name:', '').strip()}
                    elif line[0].isdigit() and '. ' in line:
                        # Alternative format: numbered list with pipe separator
                        parts = line.split('|')
                        if len(parts) >= 1:
                            name = parts[0].split('.', 1)[1].strip()
                            activities.append(name)

                # Add the last activity if exists
                if current_activity and current_activity['name']:
                    activities.append(current_activity['name'])

                if not activities:
                    logger.error("No valid activities found in response")
                    return response

                # Format activities for storage
                activities_str = "\n".join(activities)

                # Define includes with focus on activity names only
                includes = """
                Only store the activity names, which should be:
                - Clear and descriptive
                - Complete activity titles
                - No additional details or formatting
                
                Examples:
                - Climate Change Research Internship
                - Neuroscience Laboratory Project
                - Community Water Quality Study
                """

                # Define excludes to prevent storing any additional details
                excludes = """
                Exclude all additional information such as:
                - Positions or roles
                - Descriptions
                - Hours or time commitments
                - Markdown formatting
                - Numbering
                - Additional commentary
                - Any other metadata
                """

                # Add to memory with includes and excludes for precise storage
                client.add(
                    messages=[{
                        "role": "system",
                        "content": "Extracurricular Activity Names"
                    }, {
                        "role": "assistant",
                        "content": activities_str
                    }],
                    user_id=auth0_id,
                    agent_id=f"ec_expert_agent_{auth0_id}",
                    includes=includes,
                    excludes=excludes,
                    metadata={
                        "type": "ec_suggestion",
                        "created_at": datetime.utcnow().isoformat(),
                        "total_suggestions": len(activities)
                    }
                )
                logger.info(f"✅ Successfully stored {len(activities)} activities in memory for {auth0_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing or storing activity list: {str(e)}")
                # Don't fail the request if memory storage fails
                return response

            return response

        except Exception as e:
            logger.error(f"❌ Error in EC suggestions memory: {str(e)}")
            return {"error": str(e)}, 500

    return decorated_function
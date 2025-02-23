from functools import wraps
from flask import g
from mem0 import MemoryClient
import os
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Hardcoded Mem0 API key
MEM0_API_KEY = "m0-DF90O1P1ad5pbj0DMspbqyor68M4VMpcelQeIMIh"

def sync_with_mem0(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Execute the route function first
            response = f(*args, **kwargs)
            
            # Get auth0_id from g.user_info (set by verify_google_token)
            auth0_id = g.user_info.get('sub')
            if not auth0_id:
                logger.error("No auth0_id found in user info")
                return response

            try:
                # Initialize memory client with hardcoded key
                client = MemoryClient(api_key=MEM0_API_KEY)
                logger.info(f"Initialized memory client for {auth0_id}")

                # Handle both direct dict and jsonified responses
                if hasattr(response, 'get_json'):
                    response_data = response.get_json()
                elif isinstance(response, tuple):
                    response_data = response[0]
                else:
                    response_data = response

                # Validate response format and success
                if not isinstance(response_data, dict):
                    logger.error("Invalid response format - not a dictionary")
                    return response

                if not response_data.get('success', False):
                    logger.info("Skipping memory storage for unsuccessful response")
                    return response

                # Extract data from response
                data = response_data.get('data', {})
                if not isinstance(data, dict):
                    logger.error("Invalid data format in response")
                    return response

                # Get thread_id and essay ideas
                thread_id = data.get('thread_id')
                essay_ideas = data.get('essay_ideas', [])

                # Validate required data
                if not thread_id:
                    logger.error("Missing thread_id in response")
                    return response

                if not essay_ideas or not isinstance(essay_ideas, list):
                    logger.error("Invalid or missing essay_ideas in response")
                    return response

                # Format ideas for storage, ensuring each idea has content
                valid_ideas = []
                for idea in essay_ideas:
                    if isinstance(idea, dict) and idea.get('content'):
                        content = idea['content'].strip()
                        if content:
                            valid_ideas.append(content)

                if not valid_ideas:
                    logger.error("No valid ideas to store after filtering")
                    return response

                # Format ideas as a numbered list
                ideas_str = "\n".join(f"{i+1}. {idea}" for i, idea in enumerate(valid_ideas))

                # Define includes with focus on brainstorming content
                includes = """
                Include only the essential brainstorming elements:
                - Main essay topic ideas
                - Key personal experiences
                - Unique angles and perspectives
                - Supporting examples and stories
                - Theme connections
                - Values demonstrated
                - Core message of each idea
                - Personal narrative elements
                """

                # Define excludes to prevent storing unnecessary details
                excludes = """
                Exclude the following:
                - Formatting and markdown
                - Redundant phrases and fillers
                - Technical metadata
                - System messages
                - Timestamps and IDs
                - Raw prompt text
                - College information
                - Generic advice
                - Placeholder text
                """

                # Store ideas in memory with improved metadata
                client.add(
                    messages=[{
                        "role": "system",
                        "content": "Essay brainstorming ideas and analysis"
                    }, {
                        "role": "assistant",
                        "content": ideas_str
                    }],
                    user_id=auth0_id,
                    agent_id=f"essay_brainstorm_{thread_id}",
                    includes=includes,
                    excludes=excludes,
                    metadata={
                        "type": "essay_brainstorm",
                        "thread_id": thread_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "idea_count": len(valid_ideas),
                        "source": "brainstorm_crew"
                    }
                )

                logger.info(f"✅ Successfully stored {len(valid_ideas)} essay ideas for thread {thread_id}")
                return response

            except Exception as e:
                logger.error(f"❌ Error storing brainstorm memory: {str(e)}")
                logger.exception(e)  # Log full traceback
                return response

        except Exception as e:
            logger.error(f"❌ Error in brainstorm memory middleware: {str(e)}")
            logger.exception(e)  # Log full traceback
            return response

    return decorated_function 
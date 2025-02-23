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

def store_feedback_memory(f):
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

                if not isinstance(response_data, dict) or 'data' not in response_data:
                    logger.error("Invalid response format")
                    return response

                # Get thread_id and feedback from response
                thread_id = response_data.get('data', {}).get('thread_id')
                feedback = response_data.get('data', {}).get('feedback')

                if not thread_id or not feedback:
                    logger.error("Missing thread_id or feedback")
                    return response

                # Create unique agent_id for this thread
                agent_id = f"essay_feedback_{thread_id}"

                # Define includes with focus on feedback content
                includes = """
                Include only the essential feedback elements:
                - Main points and recommendations
                - Key suggestions for improvement
                - Specific strengths identified
                - Areas needing attention
                - Progress noted from previous feedback
                """

                # Define excludes to prevent storing unnecessary details
                excludes = """
                Exclude the following:
                - Formatting and markdown
                - Redundant phrases and fillers
                - Technical metadata
                - System messages
                - Timestamps and IDs
                - Raw essay text
                - Prompt text
                """

                # Store feedback in memory
                client.add(
                    messages=[{
                        "role": "system",
                        "content": "Essay feedback and analysis"
                    }, {
                        "role": "assistant",
                        "content": feedback
                    }],
                    user_id=auth0_id,
                    agent_id=agent_id,
                    includes=includes,
                    excludes=excludes,
                    metadata={
                        "type": "essay_feedback",
                        "thread_id": thread_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

                logger.info(f"✅ Successfully stored feedback for thread {thread_id}")
                return response

            except Exception as e:
                logger.error(f"❌ Error storing feedback memory: {str(e)}")
                return response

        except Exception as e:
            logger.error(f"❌ Error in feedback memory middleware: {str(e)}")
            return response

    return decorated_function 
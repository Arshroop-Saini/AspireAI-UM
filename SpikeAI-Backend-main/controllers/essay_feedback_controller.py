from agent_crews.essay_feedback_crews.crew import EssayFeedbackCrew
from models.crew_suggestions_model import CrewSuggestions
from datetime import datetime
import logging
import os
from typing import Dict, Any
import uuid

logger = logging.getLogger(__name__)

def parse_feedback(output: str, feedback_questions: list = None) -> dict:
    """Parse the feedback output from the crew into a structured format"""
    return {
        'content': output,
        'created_at': datetime.utcnow(),
        'feedback_questions': feedback_questions or ["Provide general feedback on the essay"]
    }

def get_essay_feedback_threads(auth0_id: str) -> dict:
    """Get all essay feedback threads for a user"""
    try:
        # Get user's crew suggestions document
        crew_suggestions = CrewSuggestions.get_collection().find_one({'auth0_id': auth0_id})
        
        if not crew_suggestions:
            return {
                'success': True,
                'threads': []
            }
            
        # Return threads sorted by created_at in descending order
        threads = sorted(
            crew_suggestions.get('essay_feedback', []),
            key=lambda x: x['created_at'],
            reverse=True
        )
        
        return {
            'success': True,
            'threads': threads
        }
        
    except Exception as e:
        logger.error(f"Error getting essay feedback threads: {str(e)}")
        raise

def create_essay_feedback_thread(thread_data: Dict[str, Any], auth0_id: str) -> dict:
    """Create a new essay feedback thread"""
    try:
        # Validate required fields
        required_fields = ['college_name', 'prompt', 'essay_text', 'word_count']
        if not all(field in thread_data for field in required_fields):
            missing = [field for field in required_fields if field not in thread_data]
            logger.error(f"Missing required fields: {missing}")
            raise ValueError(f"Missing required fields: {missing}")
            
        # Create inputs object with only user-provided data
        inputs = {
            'thread_id': str(uuid.uuid4()),  # Generate new UUID
            'college_name': thread_data['college_name'],
            'prompt': thread_data['prompt'],
            'essay_text': thread_data['essay_text'],
            'word_count': thread_data['word_count'],
            'feedback_questions': thread_data.get('feedback_questions', []),
            'feedbacks': []
        }
        
        # Add metadata for database
        thread_doc = {
            **inputs,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'pending',
            'auth0_id': auth0_id
        }
        
        # Update crew suggestions document
        result = CrewSuggestions.get_collection().update_one(
            {'auth0_id': auth0_id},
            {
                '$push': {'essay_feedback': thread_doc},
                '$set': {'updated_at': datetime.utcnow()}
            },
            upsert=True
        )
        
        if result.modified_count == 0 and not result.upserted_id:
            raise Exception("Failed to create thread")
            
        return {
            'success': True,
            'thread_id': inputs['thread_id'],
            'thread': thread_doc
        }
        
    except ValueError as ve:
        logger.error(f"Validation error in create_essay_feedback_thread: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Error creating essay feedback thread: {str(e)}")
        raise

def delete_essay_feedback_thread(thread_id: str, auth0_id: str) -> bool:
    """Delete an essay feedback thread"""
    try:
        # Remove thread from array
        result = CrewSuggestions.get_collection().update_one(
            {'auth0_id': auth0_id},
            {
                '$pull': {'essay_feedback': {'thread_id': thread_id}},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        if result.modified_count == 0:
            raise Exception("Thread not found or already deleted")
            
        return True
        
    except Exception as e:
        logger.error(f"Error deleting essay feedback thread: {str(e)}")
        raise

def add_feedback_to_thread(thread_id: str, feedback: str, auth0_id: str, feedback_questions: list = None) -> dict:
    """Add feedback to an existing thread"""
    try:
        # Get the thread to verify it exists
        thread = CrewSuggestions.get_collection().find_one(
            {
                'auth0_id': auth0_id,
                'essay_feedback.thread_id': thread_id
            },
            {'essay_feedback.$': 1}
        )
        
        if not thread or 'essay_feedback' not in thread or not thread['essay_feedback']:
            raise Exception("Thread not found")
            
        # Create feedback object with current questions
        feedback_obj = parse_feedback(feedback, feedback_questions)
        
        # Add feedback to thread and update status
        result = CrewSuggestions.get_collection().update_one(
            {
                'auth0_id': auth0_id,
                'essay_feedback.thread_id': thread_id
            },
            {
                '$push': {'essay_feedback.$.feedbacks': feedback_obj},
                '$set': {
                    'essay_feedback.$.status': 'completed',
                    'essay_feedback.$.updated_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise Exception("Thread not found")
            
        return {
            'success': True,
            'feedback': feedback_obj
        }
        
    except Exception as e:
        logger.error(f"Error adding feedback to thread: {str(e)}")
        raise

def generate_essay_feedback(essay_data: Dict[str, Any], auth0_id: str) -> dict:
    """
    Generate feedback for a college essay
    """
    try:
        # Set default feedback_questions if not provided
        if 'feedback_questions' not in essay_data or not essay_data['feedback_questions']:
            essay_data['feedback_questions'] = ["Provide general feedback on the essay"]
        
        # Prepare inputs with only required fields
        inputs = {
            'college_name': essay_data['college_name'],
            'prompt': essay_data['prompt'],
            'essay_text': essay_data['essay_text'],
            'word_count': essay_data['word_count'],
            'feedback_questions': essay_data['feedback_questions'],
            'auth0_id': auth0_id,
            'thread_id': essay_data.get('thread_id')
        }
        
        logger.info(f"Initializing EssayFeedbackCrew for auth0_id: {auth0_id}")
        
        # Initialize crew
        crew = EssayFeedbackCrew(inputs=inputs)
        crew_instance = crew.crew()
        
        try:
            # Execute crew tasks
            result = crew_instance.kickoff()
            
            if not result:
                logger.error("Crew execution returned no result")
                return {
                    "success": False,
                    "error": "Failed to generate feedback - no result from crew"
                }
            
            # Extract feedback from result
            feedback = ""
            if hasattr(result, 'raw_output'):
                feedback = result.raw_output
            elif hasattr(result, 'final_answer'):
                feedback = result.final_answer
            else:
                feedback = str(result)
            
            if not feedback.strip():
                return {
                    "success": False,
                    "error": "Generated feedback is empty"
                }
                
            logger.info("Successfully generated feedback")
            return {
                "success": True,
                "data": {
                    "feedback": feedback
                }
            }
            
        except Exception as e:
            logger.error(f"Error in crew execution: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate feedback: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Error in generate_essay_feedback: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def validate_essay_data(essay_data: Dict[str, Any], is_new_thread: bool = False) -> Dict[str, Any]:
    """
    Validate the essay data input
    
    For new threads (is_new_thread=True):
    Required fields:
    - college_name: Name of the college
    - prompt: Essay prompt
    - essay_text: The essay content
    - word_count: Number of words in the essay
    
    For existing threads (is_new_thread=False):
    - No required fields, will use thread's existing data
    """
    # Only validate required fields for new threads
    if is_new_thread:
        required_fields = [
            'college_name',
            'prompt',
            'essay_text',
            'word_count'
        ]
        
        # Check for missing required fields
        missing_fields = [field for field in required_fields if field not in essay_data]
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "message": "Invalid essay data"
            }
        
        # Validate word count is numeric
        try:
            word_count = int(essay_data['word_count'])
            if word_count <= 0:
                return {
                    "success": False,
                    "error": "Word count must be positive",
                    "message": "Invalid word count"
                }
        except ValueError:
            return {
                "success": False,
                "error": "Word count must be a number",
                "message": "Invalid word count format"
            }
        
        # Validate essay text is not empty
        if not essay_data['essay_text'].strip():
            return {
                "success": False,
                "error": "Essay text cannot be empty",
                "message": "Missing essay content"
            }
        
        # Validate college name is not empty
        if not essay_data['college_name'].strip():
            return {
                "success": False,
                "error": "College name cannot be empty",
                "message": "Missing college name"
            }
        
        # Validate prompt is not empty
        if not essay_data['prompt'].strip():
            return {
                "success": False,
                "error": "Essay prompt cannot be empty",
                "message": "Missing essay prompt"
            }
    
    return {
        "success": True,
        "message": "Essay data validation successful"
    }
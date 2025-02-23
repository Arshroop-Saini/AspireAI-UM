from flask import jsonify
from typing import Dict, Any
from models.student_model import Student
from agent_crews.essay_brainstorm_crews.crew import EssayBrainstormCrew
from models.crew_suggestions_model import CrewSuggestions
from bson import ObjectId
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def parse_ideas(output) -> dict:
    """Parse the ideas output from the crew into a structured format"""
    try:
        # Extract the actual ideas content
        if hasattr(output, 'raw_output'):
            content = output.raw_output
        elif hasattr(output, 'final_answer'):
            content = output.final_answer
        else:
            content = str(output)

        if not content or not isinstance(content, str):
            raise ValueError("Invalid output format")

        if not content.strip():
            raise ValueError("No content found in output")

        # Split into lines and filter out empty lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Extract ideas from numbered list (1. 2. 3. etc.)
        ideas = []
        for line in lines:
            # Check for numbered idea
            if line[0].isdigit() and '. ' in line:
                # Remove the number and dot, then strip whitespace
                idea = {
                    'content': line.split('. ', 1)[1].strip(),
                    'created_at': datetime.utcnow()
                }
                ideas.append(idea)

        if not ideas:
            raise ValueError("No valid ideas found in output")

        # Return parsed ideas
        return {
            'ideas': ideas,
            'status': 'completed'
        }
    except Exception as e:
        logger.error(f"Error parsing ideas: {str(e)}")
        raise

def get_essay_brainstorm_threads(auth0_id: str) -> dict:
    """Get all essay brainstorming threads for a user"""
    try:
        # Get suggestions from database
        suggestions = CrewSuggestions.get_by_auth0_id(auth0_id)
        if not suggestions:
            return {
                'success': True,
                'threads': []
            }
        
        return {
            'success': True,
            'threads': suggestions.get('essay_brainstorm', [])
        }
    except Exception as e:
        logger.error(f"Error getting brainstorm threads: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def create_essay_brainstorm_thread(data: Dict[str, Any], auth0_id: str) -> dict:
    """Create a new essay brainstorming thread"""
    try:
        # Validate required fields
        if not data.get('college_name') or not data.get('essay_prompt'):
            return {
                'success': False,
                'error': 'College name and essay prompt are required'
            }

        # Get or create suggestions document
        suggestions = CrewSuggestions.get_by_auth0_id(auth0_id)
        if not suggestions:
            suggestions = CrewSuggestions({
                'auth0_id': auth0_id,
                'essay_brainstorm': []
            })

        # Create new thread
        new_thread = {
            'thread_id': data.get('thread_id'),  # Use provided thread_id from frontend
            'college_name': data.get('college_name'),
            'essay_prompt': data.get('essay_prompt'),
            'word_limit': data.get('word_limit', 0),
            'ideas': [],  # Initialize empty ideas list
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }

        # Add thread to suggestions
        if 'essay_brainstorm' not in suggestions:
            suggestions['essay_brainstorm'] = []
        suggestions['essay_brainstorm'].append(new_thread)

        # Save to database
        if not suggestions.save():
            return {
                'success': False,
                'error': 'Failed to save thread'
            }

        return {
            'success': True,
            'thread': new_thread
        }

    except Exception as e:
        logger.error(f"Error creating essay brainstorm thread: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def delete_essay_brainstorm_thread(thread_id: str, auth0_id: str) -> bool:
    """Delete an essay brainstorming thread"""
    try:
        logger.info(f"Attempting to delete thread {thread_id} for user {auth0_id}")
        
        # Get suggestions document first to verify thread exists
        suggestions = CrewSuggestions.get_by_auth0_id(auth0_id)
        if not suggestions:
            logger.error(f"No suggestions document found for user {auth0_id}")
            return False
            
        # Check if thread exists
        thread_exists = any(thread.get('thread_id') == thread_id for thread in suggestions.get('essay_brainstorm', []))
        if not thread_exists:
            logger.error(f"Thread {thread_id} not found for user {auth0_id}")
            return False
        
        # Remove thread from array using $pull operator
        result = CrewSuggestions.get_collection().update_one(
            {'auth0_id': auth0_id},
            {
                '$pull': {'essay_brainstorm': {'thread_id': thread_id}},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.info(f"Successfully deleted thread {thread_id}")
        else:
            logger.error(f"Failed to delete thread {thread_id} - no documents modified")
            
        return success
        
    except Exception as e:
        logger.error(f"Error deleting essay brainstorm thread: {str(e)}")
        return False

def add_ideas_to_thread(thread_id: str, ideas: list, auth0_id: str) -> dict:
    """Add generated ideas to a thread"""
    try:
        # Get suggestions document
        suggestions = CrewSuggestions.get_by_auth0_id(auth0_id)
        if not suggestions:
            raise Exception("No suggestions found for user")

        # Find and update the thread
        thread_updated = False
        for thread in suggestions.get('essay_brainstorm', []):
            if thread.get('thread_id') == thread_id:
                # Initialize ideas array if not exists
                if 'ideas' not in thread:
                    thread['ideas'] = []
                # Add each idea directly (they already have content and created_at)
                thread['ideas'].extend(ideas)
                thread['updated_at'] = datetime.utcnow()
                thread['status'] = 'completed'
                thread_updated = True
                break

        if not thread_updated:
            raise Exception("Thread not found")

        # Save changes
        if suggestions.save():
            return {
                'success': True,
                'ideas': ideas
            }
        else:
            raise Exception("Failed to save ideas")
        
    except Exception as e:
        logger.error(f"Error adding ideas to thread: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_essay_ideas(essay_data: Dict[str, Any], auth0_id: str) -> dict:
    """Generate essay ideas using the Essay Brainstorming crew"""
    try:
        logger.info(f"Initializing essay brainstorming process for auth0_id: {auth0_id}")
        
        # Validate student profile exists and has required fields
        student = Student.get_by_auth0_id(auth0_id)
        if not student or not isinstance(student, dict):
            logger.error(f"No student profile found for auth0_id: {auth0_id}")
            return {
                'success': False,
                'error': 'Student profile not found. Please complete your profile first.'
            }

        # Check for required profile fields
        required_fields = ['name', 'major']
        missing_fields = [field for field in required_fields if not student.get(field)]
        if missing_fields:
            logger.error(f"Missing required profile fields: {', '.join(missing_fields)}")
            return {
                'success': False,
                'error': f"Please complete these required profile fields: {', '.join(missing_fields)}"
            }

        # Validate request data
        is_new_thread = essay_data.get('is_new_thread', True)  # Default to True for backward compatibility
        thread_id = essay_data.get('thread_id')

        # Validate thread_id based on is_new_thread flag
        if is_new_thread and thread_id:
            logger.error("thread_id provided for new thread")
            return {
                'success': False,
                'error': 'thread_id should not be provided for new threads'
            }
        if not is_new_thread and not thread_id:
            logger.error("thread_id missing for existing thread")
            return {
                'success': False,
                'error': 'thread_id is required for existing threads'
            }

        # For new threads, create thread first
        if is_new_thread:
            # Validate required fields for new thread
            required_fields = ['college_name', 'essay_prompt']
            missing_fields = [field for field in required_fields if not essay_data.get(field)]
            if missing_fields:
                return {
                    'success': False,
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                }
                
            thread_result = create_essay_brainstorm_thread(essay_data, auth0_id)
            if not thread_result.get('success'):
                return thread_result
            thread_id = thread_result.get('thread_id')
            if not thread_id:
                return {
                    'success': False,
                    'error': 'Failed to create thread'
                }
        else:
            # Verify thread exists for existing threads
            suggestions = CrewSuggestions.get_by_auth0_id(auth0_id)
            if not suggestions:
                return {
                    'success': False,
                    'error': 'No suggestions found for user'
                }
            thread = next((t for t in suggestions.get('essay_brainstorm', []) if t.get('thread_id') == thread_id), None)
            if not thread:
                return {
                    'success': False,
                    'error': 'Thread not found'
                }
            # Use existing thread data if fields not provided
            essay_data['college_name'] = essay_data.get('college_name') or thread.get('college_name')
            essay_data['essay_prompt'] = essay_data.get('essay_prompt') or thread.get('essay_prompt')
            essay_data['word_limit'] = essay_data.get('word_limit') or thread.get('word_limit')
        
        # Initialize crew with inputs including the thread_id
        crew = EssayBrainstormCrew(inputs={
            'auth0_id': auth0_id,
            'college_name': essay_data.get('college_name'),
            'essay_prompt': essay_data.get('essay_prompt'),
            'word_limit': essay_data.get('word_limit'),
            'thread_id': thread_id
        })
        
        # Get crew instance
        crew_instance = crew.crew()
        if not crew_instance or (isinstance(crew_instance, dict) and not crew_instance.get('success')):
            error_msg = crew_instance.get('error', 'Failed to create crew') if isinstance(crew_instance, dict) else 'Failed to create crew'
            return {
                'success': False,
                'error': error_msg
            }
            
        try:
            # Run the crew tasks
            result = crew_instance.kickoff()
            
            if not result:
                return {
                    'success': False,
                    'error': 'Failed to generate essay ideas'
                }
            
            # Parse results
            try:
                parsed_ideas = parse_ideas(result)
                if not parsed_ideas or not parsed_ideas.get('ideas'):
                    raise ValueError("No valid ideas found in output")
                
                # Add ideas to the thread
                add_result = add_ideas_to_thread(thread_id, parsed_ideas.get('ideas', []), auth0_id)
                if not add_result.get('success'):
                    return add_result
                    
                return {
                    'success': True,
                    'data': {
                        'thread_id': thread_id,
                        'essay_ideas': parsed_ideas.get('ideas', [])
                    }
                }
            except Exception as e:
                logger.error(f"Error parsing ideas: {str(e)}")
                return {
                    'success': False,
                    'error': f"Failed to parse ideas: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Error in crew execution: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to generate ideas: {str(e)}"
            }
        
    except Exception as e:
        logger.error(f"Error generating essay ideas: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def validate_essay_data(essay_data: Dict[str, Any], is_new_thread: bool = False) -> Dict[str, Any]:
    """Validate essay data before processing"""
    try:
        # Required fields
        required_fields = ['college_name', 'essay_prompt']
        
        # Check required fields
        missing_fields = [field for field in required_fields if not essay_data.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        # If not a new thread, thread_id is required
        if not is_new_thread and not essay_data.get('thread_id'):
            raise ValueError("thread_id is required for existing threads")
            
        return essay_data
        
    except Exception as e:
        logger.error(f"Error validating essay data: {str(e)}")
        raise 
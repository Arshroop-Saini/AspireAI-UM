from functools import wraps
from flask import g, request
import logging
import asyncio
from openai import AsyncOpenAI
import os
from config.db import get_db
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize OpenAI client with the new format
client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def get_changed_profile_fields(old_data, new_data, fields_to_check):
    """Compare old and new profile data to find changed fields"""
    if not old_data or not new_data:
        logger.debug("❌ Either old_data or new_data is missing")
        return []
        
    changed_fields = []
    
    def normalize_value(value):
        """Normalize values for comparison by converting ObjectId to string and handling nested dicts"""
        if hasattr(value, '__str__'):  # Handle ObjectId
            value = str(value)
        if isinstance(value, dict):
            return {k: normalize_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [normalize_value(item) for item in value]
        return value
    
    logger.debug(f"🔍 Checking only these monitored fields: {fields_to_check}")
    
    # Only process fields that we're actually monitoring
    for field in fields_to_check:
        logger.debug(f"🔎 Checking field: {field}")
        
        # Skip if field is not in monitored fields
        if field not in monitored_fields:
            logger.debug(f"⏭️ Skipping non-monitored field: {field}")
            continue
            
        old_value = normalize_value(old_data.get(field))
        new_value = normalize_value(new_data.get(field))
        
        logger.debug(f"📊 Comparing values for {field}:")
        logger.debug(f"  Old: {type(old_value)} = {old_value}")
        logger.debug(f"  New: {type(new_value)} = {new_value}")
        
        # Skip if both values are empty/None/empty strings/empty lists/empty dicts
        if not old_value and not new_value:
            logger.debug(f"⏭️ Both values are empty for {field}, skipping")
            continue
            
        # For empty lists/dicts, convert to None for comparison
        if isinstance(old_value, (list, dict)) and not old_value:
            old_value = None
        if isinstance(new_value, (list, dict)) and not new_value:
            new_value = None
            
        # Only consider it changed if values are actually different
        if old_value != new_value:
            logger.debug(f"✨ Found change in {field}")
            changed_fields.append(field)
        else:
            logger.debug(f"🟰 No change in {field}")
    
    logger.debug(f"📝 Final changed fields: {changed_fields}")
    return changed_fields

# Define monitored fields at module level
monitored_fields = [
    'extracurriculars', 
    'awards', 
    'personality_type', 
    'student_context',
    'major',
    'student_statistics'
]

async def generate_theme(profile_data):
    """Generate theme using OpenAI API"""
    try:
        # Prepare the context from profile data
        context = {
            'extracurriculars': profile_data.get('extracurriculars', []),
            'awards': profile_data.get('awards', []),
            'personality_type': profile_data.get('personality_type', ''),
            'student_context': profile_data.get('student_context', {}),
            'major': profile_data.get('major', ''),
            'student_statistics': profile_data.get('student_statistics', {})
        }

        # Create prompt for OpenAI with explicit character limit instruction
        prompt = f"""Generate a compelling theme for this student's college application profile. 
        CRITICAL: Your response MUST be LESS THAN 250 characters total - this is a strict limit.
        
        Profile Details:
        - Major: {context['major']}
        - Academic Stats: {context['student_statistics']}
        - Extracurriculars: {context['extracurriculars']}
        - Awards: {context['awards']}
        - Personality Type: {context['personality_type']}
        - Background Context: {context['student_context']}

        Create a concise theme (under 250 characters) that captures their unique story, strengths, and values.
        Focus on what makes them stand out. Be specific but brief.
        """

        # Call OpenAI API with the new format
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a skilled profile analyst who creates compelling themes for college applications. You MUST keep responses under 250 characters."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,  # Limit to ensure theme is concise
            temperature=0.7
        )

        theme = response.choices[0].message.content.strip()
        
        # Ensure theme is within character limit
        if len(theme) > 250:
            theme = theme[:247] + "..."
            logger.warning(f"Theme exceeded 250 characters (was {len(theme)}), truncating...")
            
        return theme

    except Exception as e:
        logger.error(f"Error generating theme: {str(e)}")
        return None

async def update_profile_theme(auth0_id, theme):
    """Update the student_theme in MongoDB"""
    try:
        db = get_db()
        result = db.students.update_one(
            {'auth0_id': auth0_id},
            {
                '$set': {
                    'student_theme': theme,
                    'theme_updated_at': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating theme in database: {str(e)}")
        return False

def analyze_profile_theme(f):
    """Middleware to analyze profile changes and update theme"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the request data BEFORE executing the route
            request_data = request.get_json() or {}
            
            # Check if any monitored fields are in the request data
            changed_fields = [field for field in monitored_fields if field in request_data]
            logger.debug(f"🔍 Fields in update request: {list(request_data.keys())}")
            logger.debug(f"🎯 Monitored fields being updated: {changed_fields}")
            
            # Execute the original route function
            response = f(*args, **kwargs)
            
            # Only proceed if the update was successful
            if response.status_code == 200:
                data = response.get_json()
                
                if data.get('success') and changed_fields:
                    logger.info(f"🔄 Changes detected in monitored fields: {changed_fields}")
                    auth0_id = g.user_info.get('sub')
                    new_profile = data.get('profile', {})
                    
                    async def process_theme():
                        try:
                            logger.info("⚡ Starting async theme generation")
                            new_theme = await generate_theme(new_profile)
                            if new_theme:
                                logger.info(f"✨ Generated theme: {new_theme}")
                                success = await update_profile_theme(auth0_id, new_theme)
                                if success:
                                    logger.info("💾 Theme successfully saved to database")
                                else:
                                    logger.error("❌ Failed to save theme to database")
                            else:
                                logger.error("❌ Theme generation returned None")
                        except Exception as e:
                            logger.error(f"❌ Error in process_theme: {str(e)}")
                            logger.exception("Detailed error:")
                    
                    try:
                        # Create new event loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Run the async task
                        loop.run_until_complete(process_theme())
                        
                        # Clean up
                        loop.close()
                    except Exception as e:
                        logger.error(f"❌ Error in async execution: {str(e)}")
                else:
                    logger.info("⏭️ No monitored fields were updated")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in theme analysis middleware: {str(e)}")
            logger.exception("Detailed middleware error:")
            return response
        
    return decorated_function 
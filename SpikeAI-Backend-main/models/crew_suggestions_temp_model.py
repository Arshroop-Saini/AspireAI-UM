from datetime import datetime
from config.db import get_db
from bson import ObjectId
import logging
import time
from typing import Optional, List, Dict, Any
from models.crew_suggestions_model import CrewSuggestions
from pymongo import ASCENDING, DESCENDING

logger = logging.getLogger(__name__)

class CrewSuggestionsTemp(CrewSuggestions):
    collection_name = 'crewSuggestionsTemp'

    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection for temporary crew suggestions"""
        try:
            db = get_db()
            logger.info(f"✅ Successfully accessed {cls.collection_name} collection")
            return db[cls.collection_name]
        except Exception as e:
            logger.error(f"❌ Error accessing {cls.collection_name} collection: {str(e)}")
            raise

    @classmethod
    def create_indexes(cls):
        """Create required indexes for the collection"""
        try:
            collection = cls.get_collection()
            
            # Drop existing indexes except _id
            existing_indexes = collection.list_indexes()
            for index in existing_indexes:
                if index['name'] != '_id_':  # Don't drop the _id index
                    collection.drop_index(index['name'])
                    logger.info(f"Dropped existing index: {index['name']}")
            
            # Create compound index on auth0_id and timestamp
            collection.create_index(
                [("auth0_id", ASCENDING), ("updated_at", DESCENDING)],
                name="user_temp_suggestions_idx"
            )
            
            # Create compound text index for both college and activity names
            collection.create_index([
                ('college_suggestions.name', 'text'),
                ('ec_suggestions.name', 'text')
            ], name="temp_suggestions_name_text_idx")
            
            logger.info(f"✅ Created indexes for {cls.collection_name} collection")
        except Exception as e:
            logger.error(f"❌ Error creating indexes for {cls.collection_name}: {str(e)}")
            raise

    @classmethod
    def get_suggestions_by_user_id(cls, user_id):
        """Get temporary suggestions for a specific user"""
        try:
            collection = cls.get_collection()
            suggestions = collection.find_one({"user_id": user_id})
            
            if suggestions:
                logger.info(f"✅ Found temporary suggestions for user {user_id}")
                return {
                    'college_suggestions': suggestions.get("college_suggestions", []),
                    'ec_suggestions': suggestions.get("ec_suggestions", [])
                }
            else:
                logger.info(f"No temporary suggestions found for user {user_id}")
                return {
                    'college_suggestions': [],
                    'ec_suggestions': []
                }
                
        except Exception as e:
            logger.error(f"❌ Error fetching temporary suggestions for user {user_id}: {str(e)}")
            raise

    @classmethod
    def move_to_permanent(cls, auth0_id: str) -> bool:
        """Move suggestions from temporary to permanent collection"""
        try:
            db = get_db()
            
            # Get current temp suggestions
            temp_suggestions = cls.get_by_auth0_id(auth0_id)
            if not temp_suggestions:
                return True  # No suggestions to move
            
            # Handle college suggestions
            college_suggestions = temp_suggestions.get('college_suggestions', [])
            if college_suggestions:
                # Ensure all suggestions have added_at field
                for college in college_suggestions:
                    if 'added_at' not in college:
                        college['added_at'] = datetime.utcnow()
                
                # Move college suggestions to permanent collection
                result = db[CrewSuggestions.collection_name].update_one(
                    {'auth0_id': auth0_id},
                    {
                        '$push': {
                            'college_suggestions': {
                                '$each': college_suggestions
                            }
                        },
                        '$set': {'updated_at': datetime.utcnow()}
                    },
                    upsert=True
                )
                
                if not (result.modified_count > 0 or result.upserted_id):
                    return False
            
            # Handle EC suggestions
            ec_suggestions = temp_suggestions.get('ec_suggestions', [])
            if ec_suggestions:
                # Ensure all suggestions have added_at field
                for activity in ec_suggestions:
                    if 'added_at' not in activity:
                        activity['added_at'] = datetime.utcnow()
                
                # Move EC suggestions to permanent collection
                result = db[CrewSuggestions.collection_name].update_one(
                    {'auth0_id': auth0_id},
                    {
                        '$push': {
                            'ec_suggestions': {
                                '$each': ec_suggestions
                            }
                        },
                        '$set': {'updated_at': datetime.utcnow()}
                    },
                    upsert=True
                )
                
                if not (result.modified_count > 0 or result.upserted_id):
                    return False
            
            # Clear temporary suggestions
            return cls.clear_suggestions(auth0_id)
            
        except Exception as e:
            logger.error(f"Error moving suggestions to permanent: {str(e)}")
            return False

    @classmethod
    def clear_suggestions(cls, auth0_id: str) -> bool:
        """Clear temporary suggestions for a user"""
        try:
            db = get_db()
            result = db[cls.collection_name].update_one(
                {'auth0_id': auth0_id},
                {
                    '$set': {
                        'college_suggestions': [],
                        'ec_suggestions': [],
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            logger.info(f"Cleared suggestions for user {auth0_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error clearing temporary suggestions: {str(e)}")
            return False

    @classmethod
    def save_suggestions(cls, auth0_id: str, suggestions: list, suggestion_type: str = 'college') -> bool:
        """Save new suggestions to temporary storage"""
        try:
            if not suggestions:
                logger.warning(f"No suggestions provided to save for user {auth0_id}")
                return False

            db = get_db()
            
            # Add timestamp to each suggestion
            for suggestion in suggestions:
                suggestion['added_at'] = datetime.utcnow()
                
                # Validate suggestion structure based on type
                if suggestion_type == 'ec':
                    if not cls.validate_activity_data(suggestion):
                        logger.error(f"Invalid EC activity data structure: {suggestion}")
                        return False
                elif suggestion_type == 'college':
                    if not cls.validate_college_data(suggestion):
                        logger.error(f"Invalid college data structure: {suggestion}")
                        return False
            
            # Save to temporary collection based on suggestion type
            field_name = 'college_suggestions' if suggestion_type == 'college' else 'ec_suggestions'
            
            result = db[cls.collection_name].update_one(
                {'auth0_id': auth0_id},
                {
                    '$set': {
                        field_name: suggestions,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id:
                logger.info(f"✅ Successfully saved {len(suggestions)} {suggestion_type} suggestions for user {auth0_id}")
                return True
            
            logger.warning(f"No changes made when saving {suggestion_type} suggestions for user {auth0_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error saving temporary {suggestion_type} suggestions for user {auth0_id}: {str(e)}")
            return False

    @classmethod
    def remove_activity(cls, auth0_id: str, activity_name: str) -> bool:
        """Remove an activity from temporary suggestions"""
        try:
            db = get_db()
            # Only remove the specific activity using $pull
            result = db[cls.collection_name].update_one(
                {'auth0_id': auth0_id},
                {
                    '$pull': {
                        'ec_suggestions': {'name': activity_name}
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Removed activity {activity_name} from temp suggestions")
            else:
                logger.error(f"Failed to remove activity {activity_name} from temp suggestions")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error removing activity from temp suggestions: {str(e)}")
            return False

    @classmethod
    def remove_college(cls, auth0_id: str, college_name: str) -> bool:
        """Remove a college from temporary suggestions"""
        try:
            db = get_db()
            result = db[cls.collection_name].update_one(
                {'auth0_id': auth0_id},
                {
                    '$pull': {
                        'college_suggestions': {'name': college_name}
                    },
                    '$set': {
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Successfully removed college {college_name} from temp suggestions")
            else:
                logger.error(f"Failed to remove college {college_name} from temp suggestions")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error removing college from temp suggestions: {str(e)}")
            return False 
from datetime import datetime
from config.db import get_db
from bson import ObjectId
import logging
import time
from typing import Optional, List, Dict, Any
from pymongo import ASCENDING, DESCENDING

logger = logging.getLogger(__name__)

class CrewSuggestions(dict):
    collection_name = 'crewSuggestions'
    max_retries = 3
    retry_delay = 1  # seconds

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            super().__init__(args[0])
        else:
            super().__init__(*args, **kwargs)
        
        # Set default values if not present
        self.setdefault('created_at', datetime.utcnow())
        self.setdefault('updated_at', datetime.utcnow())
        self.setdefault('college_suggestions', [])
        self.setdefault('ec_suggestions', [])
        self.setdefault('essay_feedback', [])  # Add default empty array for essay feedback
        self.setdefault('essay_brainstorm', [])  # Add default empty array for essay brainstorming

    schema = {
        'auth0_id': str,  # Link to student
        'college_suggestions': [{
            'name': str,
            'type': str,  # 'safety', 'target', or 'reach'
            'added_at': datetime
        }],
        'ec_suggestions': [{
            'name': str,
            'description': str,
            'hours_per_week': int,
            'position': str,
            'added_at': datetime
        }],
        'essay_feedback': [{
            'thread_id': str,  # Unique ID for the thread
            'college_name': str,
            'prompt': str,
            'essay_text': str,
            'word_count': int,
            'feedback_questions': List[str],
            'feedbacks': [{
                'content': str,
                'created_at': datetime
            }],
            'created_at': datetime,
            'updated_at': datetime,
            'status': str  # 'pending', 'completed', 'error'
        }],
        'essay_brainstorm': [{  # New field for essay brainstorming
            'thread_id': str,  # Unique ID for the thread
            'college_name': str,
            'prompt': str,
            'ideas': [{  # Array of generated ideas
                'content': str,
                'created_at': datetime
            }],
            'created_at': datetime,
            'updated_at': datetime,
            'status': str  # 'pending', 'completed', 'error'
        }],
        'created_at': datetime,
        'updated_at': datetime
    }

    @staticmethod
    def validate_college_data(college_data: Dict[str, Any]) -> bool:
        """Validate college data structure"""
        required_fields = ['name', 'type', 'added_at']

        # Check required fields
        if not all(field in college_data for field in required_fields):
            return False

        # Validate type value - now accepts format like "Public (reach)"
        college_type = college_data['type'].lower()
        if not any(category in college_type for category in ['reach', 'target', 'safety']):
            return False

        # Ensure added_at is a datetime object
        if not isinstance(college_data['added_at'], datetime):
            return False

        return True

    @staticmethod
    def validate_activity_data(activity_data: Dict[str, Any]) -> bool:
        """Validate activity data structure"""
        required_fields = ['name', 'description', 'hours_per_week', 'position', 'added_at']

        # Check required fields
        if not all(field in activity_data for field in required_fields):
            return False

        # Ensure added_at is a datetime object
        if not isinstance(activity_data['added_at'], datetime):
            return False

        # Ensure hours_per_week is an integer
        if not isinstance(activity_data['hours_per_week'], int):
            return False

        return True

    @staticmethod
    def validate_essay_feedback_data(feedback_data: Dict[str, Any]) -> bool:
        """Validate essay feedback data structure"""
        required_fields = ['thread_id', 'college_name', 'prompt', 'essay_text', 'word_count', 'feedbacks']
        
        # Check required fields
        if not all(field in feedback_data for field in required_fields):
            return False
            
        # Validate feedbacks array
        if not isinstance(feedback_data['feedbacks'], list):
            return False
            
        for feedback in feedback_data['feedbacks']:
            if not isinstance(feedback, dict) or 'content' not in feedback or 'created_at' not in feedback:
                return False
            if not isinstance(feedback['created_at'], datetime):
                return False
                
        # Validate dates
        if not isinstance(feedback_data.get('created_at'), datetime):
            return False
        if not isinstance(feedback_data.get('updated_at'), datetime):
            return False
            
        return True

    @staticmethod
    def validate_essay_brainstorm_data(brainstorm_data: Dict[str, Any]) -> bool:
        """Validate essay brainstorming data structure"""
        required_fields = ['thread_id', 'college_name', 'prompt', 'ideas']
        
        # Check required fields
        if not all(field in brainstorm_data for field in required_fields):
            return False
            
        # Validate ideas array
        if not isinstance(brainstorm_data['ideas'], list):
            return False
            
        for idea in brainstorm_data['ideas']:
            if not isinstance(idea, dict) or 'content' not in idea or 'created_at' not in idea:
                return False
            if not isinstance(idea['created_at'], datetime):
                return False
                
        # Validate dates
        if not isinstance(brainstorm_data.get('created_at'), datetime):
            return False
        if not isinstance(brainstorm_data.get('updated_at'), datetime):
            return False
            
        return True

    def _execute_with_retry(self, operation):
        """Execute database operation with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Retry attempt {attempt + 1} of {self.max_retries}...")
                time.sleep(self.retry_delay)

    def save(self):
        """Save the current suggestions instance to the database"""
        try:
            db = get_db()
            self['updated_at'] = datetime.utcnow()
            
            # Convert string _id back to ObjectId for update
            _id = self.get('_id')
            if isinstance(_id, str):
                _id = ObjectId(_id)
            elif not _id:
                logger.error("No _id found in suggestions object")
                return False
            
            # Remove _id from update data
            update_data = self.copy()
            if '_id' in update_data:
                del update_data['_id']
            
            # Ensure auth0_id exists in the update
            auth0_id = update_data.get('auth0_id')
            if not auth0_id:
                logger.error("No auth0_id in update data")
                return False
            
            # Validate college suggestions
            for college in update_data.get('college_suggestions', []):
                if not self.validate_college_data(college):
                    logger.error(f"Invalid college data structure: {college}")
                    return False

            def db_operation():
                result = db[self.collection_name].update_one(
                    {'_id': _id},
                    {'$set': update_data},
                    upsert=True
                )
                return result.modified_count > 0 or result.upserted_id is not None

            return self._execute_with_retry(db_operation)
            
        except Exception as e:
            logger.error(f"Error saving suggestions: {str(e)}")
            raise

    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection for crew suggestions"""
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
            
            # Create compound index on auth0_id and updated_at
            collection.create_index(
                [("auth0_id", ASCENDING), ("updated_at", DESCENDING)],
                name="user_suggestions_idx"
            )
            
            # Create compound text index for both college and activity names
            collection.create_index([
                ('college_suggestions.name', 'text'),
                ('ec_suggestions.name', 'text')
            ], name="suggestions_name_text_idx")
            
            logger.info(f"✅ Created indexes for {cls.collection_name} collection")
        except Exception as e:
            logger.error(f"❌ Error creating indexes for {cls.collection_name}: {str(e)}")
            raise

    @classmethod
    def get_by_auth0_id(cls, auth0_id: str) -> Optional['CrewSuggestions']:
        """Get suggestions by auth0_id"""
        try:
            def db_operation():
                db = get_db()
                suggestions = db[cls.collection_name].find_one({'auth0_id': auth0_id})
                return cls(suggestions) if suggestions else None

            return cls()._execute_with_retry(db_operation)
        except Exception as e:
            logger.error(f"Error getting suggestions by auth0_id: {str(e)}")
            raise

    @classmethod
    def update_suggestions(cls, auth0_id: str, college_suggestions: List[Dict[str, Any]]) -> bool:
        """Update college suggestions for a student"""
        try:
            # Add added_at field if not present
            for college in college_suggestions:
                if 'added_at' not in college:
                    college['added_at'] = datetime.utcnow()

            # Validate all college data before updating
            instance = cls()
            for college in college_suggestions:
                if not instance.validate_college_data(college):
                    logger.error(f"Invalid college data structure: {college}")
                    return False

            def db_operation():
                db = get_db()
                # Check for duplicates
                existing = db[cls.collection_name].find_one({
                    'auth0_id': auth0_id,
                    'college_suggestions.name': {
                        '$in': [college['name'] for college in college_suggestions]
                    }
                })
                if existing:
                    logger.warning(f"Found duplicate colleges for auth0_id: {auth0_id}")

                result = db[cls.collection_name].update_one(
                    {'auth0_id': auth0_id},
                    {
                        '$set': {
                            'college_suggestions': college_suggestions,
                            'updated_at': datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                return result.modified_count > 0 or result.upserted_id is not None

            return instance._execute_with_retry(db_operation)
        except Exception as e:
            logger.error(f"Error updating suggestions: {str(e)}")
            raise

    @classmethod
    def remove_college(cls, auth0_id: str, college_name: str) -> bool:
        """Remove a college from suggestions"""
        try:
            db = get_db()
            
            # First check if the college exists
            existing = db[cls.collection_name].find_one({
                'auth0_id': auth0_id,
                'college_suggestions.name': college_name
            })
            
            if not existing:
                logger.warning(f"College {college_name} not found in suggestions for user {auth0_id}")
                return False

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
                logger.info(f"✅ Successfully removed college {college_name} from suggestions")
            else:
                logger.error(f"Failed to remove college {college_name} from suggestions")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error removing college from suggestions: {str(e)}")
            return False

    @classmethod
    def update_ec_suggestions(cls, auth0_id: str, ec_suggestions: List[Dict[str, Any]]) -> bool:
        """Update EC suggestions for a student"""
        try:
            # Add added_at field if not present
            for activity in ec_suggestions:
                if 'added_at' not in activity:
                    activity['added_at'] = datetime.utcnow()

            # Validate all activity data before updating
            instance = cls()
            for activity in ec_suggestions:
                if not instance.validate_activity_data(activity):
                    logger.error(f"Invalid activity data structure: {activity}")
                    return False

            def db_operation():
                db = get_db()
                # Check for duplicates
                existing = db[cls.collection_name].find_one({
                    'auth0_id': auth0_id,
                    'ec_suggestions.name': {
                        '$in': [activity['name'] for activity in ec_suggestions]
                    }
                })
                if existing:
                    logger.warning(f"Found duplicate activities for auth0_id: {auth0_id}")

                result = db[cls.collection_name].update_one(
                    {'auth0_id': auth0_id},
                    {
                        '$set': {
                            'ec_suggestions': ec_suggestions,
                            'updated_at': datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                return result.modified_count > 0 or result.upserted_id is not None

            return instance._execute_with_retry(db_operation)
        except Exception as e:
            logger.error(f"Error updating EC suggestions: {str(e)}")
            raise

    @classmethod
    def remove_activity(cls, auth0_id: str, activity_name: str) -> bool:
        """Remove an activity from suggestions"""
        try:
            db = get_db()
            
            # First check if the activity exists
            existing = db[cls.collection_name].find_one({
                'auth0_id': auth0_id,
                'ec_suggestions.name': activity_name
            })
            
            if not existing:
                logger.warning(f"Activity {activity_name} not found in suggestions for user {auth0_id}")
                return False

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
                logger.info(f"✅ Successfully removed activity {activity_name} from suggestions")
            else:
                logger.error(f"Failed to remove activity {activity_name} from suggestions")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error removing activity from suggestions: {str(e)}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the suggestions instance to a dictionary"""
        data = dict(self)
        
        # Convert ObjectId to string
        if '_id' in data:
            data['_id'] = str(data['_id'])
        
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'updated_at']:
            if key in data and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        
        return data 

    @classmethod
    def get_paginated_suggestions(cls, auth0_id: str, page: int = 1, per_page: int = 10) -> dict:
        """Get paginated suggestions for a student"""
        try:
            def db_operation():
                db = get_db()
                # Calculate skip value
                skip = (page - 1) * per_page

                # Get total count
                total = db[cls.collection_name].count_documents({
                    'auth0_id': auth0_id
                })

                # Get paginated suggestions
                cursor = db[cls.collection_name].find(
                    {'auth0_id': auth0_id}
                ).sort(
                    'updated_at', -1  # Sort by most recent first
                ).skip(skip).limit(per_page)

                suggestions = []
                for doc in cursor:
                    suggestions.extend(doc.get('college_suggestions', []))

                return {
                    'suggestions': suggestions,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }

            return cls()._execute_with_retry(db_operation)
        except Exception as e:
            logger.error(f"Error getting paginated suggestions: {str(e)}")
            raise 
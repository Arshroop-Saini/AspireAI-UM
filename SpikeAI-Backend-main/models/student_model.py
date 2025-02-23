from datetime import datetime
from config.db import get_db
from bson import ObjectId
import logging
from pymongo import ASCENDING, DESCENDING

logger = logging.getLogger(__name__)

class Student(dict):
    collection_name = 'students'

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            # If first argument is a dictionary, use it to initialize
            super().__init__(args[0])
        else:
            super().__init__(*args, **kwargs)
        
        # Set default values if not present
        self.setdefault('created_at', datetime.utcnow())
        self.setdefault('updated_at', datetime.utcnow())
        self.setdefault('hooks', [])  # Initialize hooks if not present
        
        # Initialize target_colleges with proper structure if not present or empty
        if 'target_colleges' not in self or not isinstance(self.get('target_colleges'), list):
            self['target_colleges'] = []
        
        # Initialize target_activities with proper structure if not present or empty
        if 'target_activities' not in self or not isinstance(self.get('target_activities'), list):
            self['target_activities'] = []
        
        # Ensure each college in target_colleges has proper structure
        if self['target_colleges']:
            formatted_colleges = []
            for college in self['target_colleges']:
                if isinstance(college, dict):
                    formatted_college = {
                        'name': college.get('name', ''),
                        'stats': {
                            'satRange': college.get('stats', {}).get('satRange', ''),
                            'gpaRange': college.get('stats', {}).get('gpaRange', ''),
                            'totalCost': college.get('stats', {}).get('totalCost', ''),
                            'scholarships': college.get('stats', {}).get('scholarships', ''),
                            'applicationDeadlines': college.get('stats', {}).get('applicationDeadlines', ''),
                            'costCalculator': college.get('stats', {}).get('costCalculator', ''),
                            'size': college.get('stats', {}).get('size', ''),
                            'location': college.get('stats', {}).get('location', ''),
                            'type': college.get('stats', {}).get('type', '')
                        },
                        'added_at': college.get('added_at', datetime.utcnow())
                    }
                    formatted_colleges.append(formatted_college)
            self['target_colleges'] = formatted_colleges
            
        # Ensure each activity in target_activities has proper structure
        if self['target_activities']:
            formatted_activities = []
            for activity in self['target_activities']:
                if isinstance(activity, dict):
                    formatted_activity = {
                        'name': activity.get('name', ''),
                        'description': activity.get('description', ''),
                        'hours_per_week': activity.get('hours_per_week', 0),
                        'position': activity.get('position', ''),
                        'added_at': activity.get('added_at', datetime.utcnow())
                    }
                    formatted_activities.append(formatted_activity)
            self['target_activities'] = formatted_activities

    def update_data(self, data):
        """Update the student instance with new data"""
        if not isinstance(data, dict):
            raise ValueError("Update data must be a dictionary")
        
        # Update the dictionary with new data
        for key, value in data.items():
            self[key] = value
        
        # Always update the updated_at timestamp
        self['updated_at'] = datetime.utcnow()
        
        return self

    def save(self):
        """Save the current student instance to the database"""
        try:
            db = get_db()
            self['updated_at'] = datetime.utcnow()
            
            # Convert string _id back to ObjectId for update
            _id = self.get('_id')
            if isinstance(_id, str):
                _id = ObjectId(_id)
            elif not _id:
                logger.error("No _id found in student object")
                return False
            
            # Remove _id from update data
            update_data = self.copy()
            if '_id' in update_data:
                del update_data['_id']
            
            # Log name specifically
            logger.info(f"Name in update_data before save: {update_data.get('name')}")
            logger.info(f"Saving student data to DB. ID: {_id}, Data: {update_data}")
            
            # Ensure auth0_id exists in the update
            auth0_id = update_data.get('auth0_id')
            if not auth0_id:
                logger.error("No auth0_id in update data")
                return False
            
            # Use only _id for the update query
            result = db[self.collection_name].update_one(
                {'_id': _id},
                {'$set': update_data}
            )
            
            success = result.modified_count > 0
            logger.info(f"Save result - Modified count: {result.modified_count}, Success: {success}")
            
            if not success:
                # Double check if the document exists and what's different
                existing = db[self.collection_name].find_one({'_id': _id})
                if not existing:
                    logger.error(f"Document with _id {_id} not found in database")
                else:
                    logger.info(f"Document exists but no changes were made. Current name in DB: {existing.get('name')}")
                    logger.info(f"Attempted to update with name: {update_data.get('name')}")
                    # Check if values are actually different
                    if existing.get('name') != update_data.get('name'):
                        logger.info("Name values are different but update didn't work")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving student: {str(e)}")
            raise

    schema = {
        'email': str,
        'name': str,
        'picture': str,
        'major': str,
        'extracurriculars': [{
            'name': str,
            'activity_type': str,  # Dropdown for activity type
            'position_leadership': str,  # Max 50 characters
            'organization_description': str,  # Max 100 characters
            'activity_description': str,  # Description of the activity
            'added_at': datetime
        }],
        'awards': [{
            'title': str,
            'grade_levels': list,  # List of selected grades (9, 10, 11, 12, Post-graduate)
            'recognition_levels': list,  # List of selected levels (School, State/Regional, National, International)
            'added_at': datetime
        }],
        'personality_type': str,
        'student_context': {
            'country': str,
            'estimated_contribution': float,
            'financial_aid_required': bool,
            'first_generation': bool,
            'ethnicity': str,
            'gender': str,
            'international_student': bool
        },
        'student_statistics': {
            'class_rank': int,
            'unweight_gpa': float,
            'weight_gpa': float,
            'sat_score': int
        },
        'student_preferences': {
            'campus_sizes': list,
            'college_types': list,
            'preferred_regions': list,
            'preferred_states': list
        },
        'evaluation_scores': {
            'testing_score': float,
            'hsr_score': float,
            'ecs_score': float,
            'spiv_score': float,
            'eval_score': float,
            'last_evaluated': datetime
        },
        'student_theme': str,
        'target_colleges': [{
            'name': str,
            'type': str,
            'added_at': datetime
        }],
        'target_activities': [{
            'name': str,
            'description': str,
            'hours_per_week': int,
            'position': str,
            'added_at': datetime
        }],
        'subscription': {
            'stripe_subscription_id': str,
            'stripe_customer_id': str,
            'status': str,
            'plan': str,
            'current_period_end': datetime,
            'cancel_at_period_end': bool,
            'features': list,
            'last_payment_status': str,
            'last_payment_date': datetime,
            'last_payment_attempt': datetime,
            'created_at': datetime,
            'updated_at': datetime
        },
        'created_at': datetime,
        'updated_at': datetime
    }

    subscription_schema = {
        'is_subscribed': bool,
        'stripe_customer_id': str,
        'stripe_subscription_id': str,
        'plan_type': str,  # 'monthly' or 'yearly'
        'status': str,  # 'active', 'cancelled', 'past_due', 'incomplete'
        'current_period_start': datetime,
        'current_period_end': datetime,
        'cancel_at_period_end': bool,
        'created_at': datetime,
        'updated_at': datetime,
        'trial_end': datetime,
        'price_id': str,
        'payment_status': str,  # 'paid', 'unpaid', 'no_payment_required'
        'features': list
    }

    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection for students"""
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
            
            # Create index on auth0_id
            collection.create_index(
                [("auth0_id", ASCENDING)],
                unique=True,
                name="student_auth0_idx"
            )
            
            logger.info(f"✅ Created indexes for {cls.collection_name} collection")
        except Exception as e:
            logger.error(f"❌ Error creating indexes for {cls.collection_name}: {str(e)}")
            raise

    @classmethod
    def get_target_colleges(cls, auth0_id):
        """Get target colleges for a specific student"""
        try:
            collection = cls.get_collection()
            student = collection.find_one({"auth0_id": auth0_id})
            
            if student:
                logger.info(f"✅ Found target colleges for student {auth0_id}")
                return student.get("target_colleges", [])
            else:
                logger.info(f"No target colleges found for student {auth0_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching target colleges for student {auth0_id}: {str(e)}")
            raise

    @classmethod
    def get_target_activities(cls, auth0_id):
        """Get target activities for a specific student"""
        try:
            collection = cls.get_collection()
            student = collection.find_one({"auth0_id": auth0_id})
            
            if student:
                logger.info(f"✅ Found target activities for student {auth0_id}")
                return student.get("target_activities", [])
            else:
                logger.info(f"No target activities found for student {auth0_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching target activities for student {auth0_id}: {str(e)}")
            raise

    @classmethod
    def get_by_email(cls, email):
        """Get student by email"""
        db = get_db()
        return db[cls.collection_name].find_one({'email': email})

    @classmethod
    def get_by_stripe_customer_id(cls, customer_id):
        """Get student by Stripe customer ID"""
        db = get_db()
        return db[cls.collection_name].find_one({'subscription.stripe_customer_id': customer_id})

    @classmethod
    def get_by_stripe_subscription_id(cls, subscription_id):
        """Get student by Stripe subscription ID"""
        db = get_db()
        return db[cls.collection_name].find_one({'subscription.stripe_subscription_id': subscription_id})

    @classmethod
    def create(cls, data):
        """Create a new student"""
        db = get_db()
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        
        # Initialize target_colleges with proper structure
        if 'target_colleges' not in data or not isinstance(data['target_colleges'], list):
            data['target_colleges'] = []
        else:
            # Ensure each college has proper structure
            formatted_colleges = []
            for college in data['target_colleges']:
                if isinstance(college, dict):
                    formatted_college = {
                        'name': college.get('name', ''),
                        'stats': {
                            'satRange': college.get('stats', {}).get('satRange', ''),
                            'gpaRange': college.get('stats', {}).get('gpaRange', ''),
                            'totalCost': college.get('stats', {}).get('totalCost', ''),
                            'scholarships': college.get('stats', {}).get('scholarships', ''),
                            'applicationDeadlines': college.get('stats', {}).get('applicationDeadlines', ''),
                            'costCalculator': college.get('stats', {}).get('costCalculator', ''),
                            'size': college.get('stats', {}).get('size', ''),
                            'location': college.get('stats', {}).get('location', ''),
                            'type': college.get('stats', {}).get('type', '')
                        },
                        'added_at': college.get('added_at', datetime.utcnow())
                    }
                    formatted_colleges.append(formatted_college)
            data['target_colleges'] = formatted_colleges
        
        # Initialize target_activities with proper structure
        if 'target_activities' not in data or not isinstance(data['target_activities'], list):
            data['target_activities'] = []
        else:
            # Ensure each activity has proper structure
            formatted_activities = []
            for activity in data['target_activities']:
                if isinstance(activity, dict):
                    formatted_activity = {
                        'name': activity.get('name', ''),
                        'description': activity.get('description', ''),
                        'hours_per_week': activity.get('hours_per_week', 0),
                        'position': activity.get('position', ''),
                        'added_at': activity.get('added_at', datetime.utcnow())
                    }
                    formatted_activities.append(formatted_activity)
            data['target_activities'] = formatted_activities
        
        # Initialize subscription with default values
        data['subscription'] = {
            'stripe_subscription_id': None,
            'stripe_customer_id': None,
            'status': 'inactive',
            'plan': None,
            'current_period_end': None,
            'cancel_at_period_end': False,
            'features': [],
            'last_payment_status': None,
            'last_payment_date': None,
            'last_payment_attempt': None,
            'created_at': None,
            'updated_at': None
        }
        
        result = db[cls.collection_name].insert_one(data)
        return result.inserted_id

    @classmethod
    def update(cls, email, data):
        """Update a student"""
        db = get_db()
        
        # Ensure target_colleges maintains its structure if present in update
        if 'target_colleges' in data:
            # If target_colleges is None or not a list, initialize it
            if not data['target_colleges'] or not isinstance(data['target_colleges'], list):
                data['target_colleges'] = []
            else:
                # Ensure each college in the list has the correct structure
                formatted_colleges = []
                for college in data['target_colleges']:
                    if isinstance(college, dict):
                        formatted_college = {
                            'name': college.get('name', ''),
                            'stats': {
                                'satRange': college.get('stats', {}).get('satRange', ''),
                                'gpaRange': college.get('stats', {}).get('gpaRange', ''),
                                'totalCost': college.get('stats', {}).get('totalCost', ''),
                                'scholarships': college.get('stats', {}).get('scholarships', ''),
                                'applicationDeadlines': college.get('stats', {}).get('applicationDeadlines', ''),
                                'costCalculator': college.get('stats', {}).get('costCalculator', ''),
                                'size': college.get('stats', {}).get('size', ''),
                                'location': college.get('stats', {}).get('location', ''),
                                'type': college.get('stats', {}).get('type', '')
                            },
                            'added_at': college.get('added_at', datetime.utcnow())
                        }
                        formatted_colleges.append(formatted_college)
                data['target_colleges'] = formatted_colleges

        # Ensure target_activities maintains its structure if present in update
        if 'target_activities' in data:
            # If target_activities is None or not a list, initialize it
            if not data['target_activities'] or not isinstance(data['target_activities'], list):
                data['target_activities'] = []
            else:
                # Ensure each activity in the list has the correct structure
                formatted_activities = []
                for activity in data['target_activities']:
                    if isinstance(activity, dict):
                        formatted_activity = {
                            'name': activity.get('name', ''),
                            'description': activity.get('description', ''),
                            'hours_per_week': activity.get('hours_per_week', 0),
                            'position': activity.get('position', ''),
                            'added_at': activity.get('added_at', datetime.utcnow())
                        }
                        formatted_activities.append(formatted_activity)
                data['target_activities'] = formatted_activities

        data['updated_at'] = datetime.utcnow()
        result = db[cls.collection_name].update_one(
            {'email': email},
            {'$set': data}
        )
        return result.modified_count > 0

    @classmethod
    def update_subscription(cls, email: str, subscription_data: dict):
        """Update student's subscription details"""
        try:
            db = get_db()
            logger.info(f"Updating subscription for {email} with data: {subscription_data}")
            
            # Format dates
            if 'current_period_start' in subscription_data:
                subscription_data['current_period_start'] = datetime.fromtimestamp(subscription_data['current_period_start'])
            if 'current_period_end' in subscription_data:
                subscription_data['current_period_end'] = datetime.fromtimestamp(subscription_data['current_period_end'])
            
            subscription_data['updated_at'] = datetime.utcnow()

            # Update subscription
            result = db[cls.collection_name].update_one(
                {'email': email},
                {'$set': {
                    'subscription': subscription_data,
                    'updated_at': datetime.utcnow()
                }}
            )
            
            if result.modified_count > 0:
                logger.info(f"Successfully updated subscription for {email}")
            else:
                logger.warning(f"No subscription update performed for {email}. Document might not exist.")
            
            # Verify the update
            updated_student = db[cls.collection_name].find_one({'email': email})
            logger.info(f"Updated student subscription status: {updated_student.get('subscription', {})}")
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            raise

    @classmethod
    def get_subscription_status(cls, email: str) -> dict:
        """Get student's subscription status"""
        try:
            db = get_db()
            student = db[cls.collection_name].find_one(
                {'email': email},
                {'subscription': 1}
            )
            return student.get('subscription', {}) if student else {}
        except Exception as e:
            print(f"Error getting subscription status: {str(e)}")
            raise

    @classmethod
    def cancel_subscription(cls, email):
        """Cancel student's subscription"""
        db = get_db()
        result = db[cls.collection_name].update_one(
            {'email': email},
            {
                '$set': {
                    'subscription.status': 'cancelled',
                    'subscription.updated_at': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    @classmethod
    def get_active_subscriptions(cls):
        """Get all students with active subscriptions"""
        db = get_db()
        return list(db[cls.collection_name].find({
            'subscription.status': 'active'
        }))

    @classmethod
    def verify_subscription(cls, email: str) -> bool:
        """Verify if a student has an active subscription"""
        try:
            db = get_db()
            student = db[cls.collection_name].find_one(
                {
                    'email': email,
                    'subscription.is_subscribed': True,
                    'subscription.status': 'active'
                }
            )
            return bool(student)
        except Exception as e:
            logger.error(f"Error verifying subscription: {str(e)}")
            return False

    @classmethod
    def get_user_by_auth0_id(cls, auth0_id: str):
        """Get user by auth0_id"""
        try:
            db = get_db()
            
            # Extract numeric ID - everything after the last '|'
            numeric_id = auth0_id.split('|')[-1] if '|' in auth0_id else auth0_id
            
            # Search by numeric ID
            student = db[cls.collection_name].find_one({'auth0_id': {'$regex': f'.*{numeric_id}$'}})
            
            if student:
                student['_id'] = str(student['_id'])  # Convert ObjectId to string
            return student
            
        except Exception as e:
            logger.error(f"Error getting user by auth0_id: {str(e)}")
            raise

    @classmethod
    def get_by_auth0_id(cls, auth0_id: str):
        """Get user by auth0_id"""
        try:
            logger.info(f"Getting student by auth0_id: {auth0_id}")
            db = get_db()
            
            # Extract numeric ID - everything after the last '|'
            numeric_id = auth0_id.split('|')[-1] if '|' in auth0_id else auth0_id
            logger.info(f"Searching with numeric_id: {numeric_id}")
            
            # Search by numeric ID
            student = db[cls.collection_name].find_one({'auth0_id': {'$regex': f'.*{numeric_id}$'}})
            
            if student:
                student['_id'] = str(student['_id'])  # Convert ObjectId to string
                logger.info(f"Found student: {student}")
            else:
                logger.warning(f"No student found with auth0_id: {auth0_id}")
            
            return student
            
        except Exception as e:
            logger.error(f"Error getting user by auth0_id: {str(e)}")
            raise

    def to_dict(self):
        """Convert the student instance to a dictionary, handling ObjectId and datetime conversions"""
        data = dict(self)
        
        # Convert ObjectId to string
        if '_id' in data:
            data['_id'] = str(data['_id'])
        
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'updated_at', 'last_login']:
            if key in data and data[key] is not None:
                if isinstance(data[key], datetime):
                    data[key] = data[key].isoformat()
        
        # Handle subscription datetime fields
        if 'subscription' in data:
            for key in ['current_period_start', 'current_period_end', 'last_payment_date', 'created_at', 'updated_at', 'trial_end']:
                if key in data['subscription'] and data['subscription'][key] is not None:
                    if isinstance(data['subscription'][key], datetime):
                        data['subscription'][key] = data['subscription'][key].isoformat()
        
        return data

    @classmethod
    def add_target_college(cls, auth0_id: str, college_data: dict) -> bool:
        """Add a college to student's target colleges list"""
        try:
            db = get_db()
            
            # First check if student exists and initialize target_colleges if needed
            student = db[cls.collection_name].find_one({'auth0_id': auth0_id})
            if not student:
                logger.error(f"Student not found with auth0_id: {auth0_id}")
                return False
                
            # Initialize target_colleges if it doesn't exist or isn't a list
            if 'target_colleges' not in student or not isinstance(student['target_colleges'], list):
                db[cls.collection_name].update_one(
                    {'auth0_id': auth0_id},
                    {'$set': {'target_colleges': []}}
                )
                logger.info(f"Initialized target_colleges for student {auth0_id}")
            
            # Format the college data according to new schema
            formatted_college = {
                'name': college_data['name'],
                'type': college_data.get('type', ''),  # Get type directly from college_data
                'added_at': datetime.utcnow()
            }

            # Check if college already exists in target list
            existing_college = db[cls.collection_name].find_one({
                'auth0_id': auth0_id,
                'target_colleges.name': formatted_college['name']
            })

            if existing_college:
                logger.info(f"College {formatted_college['name']} already exists in target list")
                return True

            # Update the student document with schema validation bypass
            result = db[cls.collection_name].update_one(
                {'auth0_id': auth0_id},
                {
                    '$push': {'target_colleges': formatted_college},
                    '$set': {'updated_at': datetime.utcnow()}
                },
                bypass_document_validation=True  # Bypass schema validation temporarily
            )

            success = result.modified_count > 0
            if not success:
                logger.error(f"Failed to add college to target list for student {auth0_id}")
                # Log current state of target_colleges
                current_student = db[cls.collection_name].find_one({'auth0_id': auth0_id})
                if current_student:
                    logger.error(f"Current target_colleges: {current_student.get('target_colleges')}")
            else:
                logger.info(f"Successfully added college {college_data['name']} to target list for student {auth0_id}")

            return success

        except Exception as e:
            logger.error(f"Error adding college to target list: {str(e)}")
            return False

    @classmethod
    def get_paginated_target_colleges(cls, auth0_id: str, page: int = 1, per_page: int = 10) -> dict:
        """Get paginated target colleges for a student"""
        try:
            db = get_db()
            
            # Get the student document
            student = db[cls.collection_name].find_one(
                {'auth0_id': auth0_id},
                {'target_colleges': 1}
            )

            if not student or 'target_colleges' not in student:
                return {
                    'colleges': [],
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }

            # Calculate pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            total_colleges = len(student['target_colleges'])
            total_pages = (total_colleges + per_page - 1) // per_page

            # Get the slice of colleges for the current page
            raw_colleges = student['target_colleges'][start_idx:end_idx]
            
            # Format colleges according to new schema
            formatted_colleges = []
            for college in raw_colleges:
                formatted_college = {
                    'name': college.get('name', ''),
                    'type': college.get('type', ''),  # Get type directly from college object
                    'added_at': college.get('added_at', datetime.utcnow()).isoformat()
                }
                formatted_colleges.append(formatted_college)

            return {
                'colleges': formatted_colleges,
                'total': total_colleges,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            }

        except Exception as e:
            logger.error(f"Error getting paginated target colleges: {str(e)}")
            return {
                'colleges': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            }

    @classmethod
    def migrate_target_colleges_structure(cls):
        """Migrate any existing students with incorrect target_colleges structure"""
        try:
            db = get_db()
            # Find all students
            students = db[cls.collection_name].find({})
            
            for student in students:
                target_colleges = student.get('target_colleges', [])
                
                # Check if any college in target_colleges doesn't match the schema
                needs_update = False
                for college in target_colleges:
                    if not isinstance(college, dict) or 'type' not in college or 'added_at' not in college:
                        needs_update = True
                        break
                
                if needs_update:
                    # Update with proper structure
                    formatted_colleges = []
                    for college in target_colleges:
                        if isinstance(college, str):
                            # Convert old string format to new structure
                            formatted_colleges.append({
                                'name': college,
                                'type': '',  # Default empty type
                                'added_at': datetime.utcnow()
                            })
                        elif isinstance(college, dict):
                            # Extract type from stats if it exists
                            college_type = ''
                            if 'stats' in college and isinstance(college['stats'], dict):
                                college_type = college['stats'].get('type', '')
                            elif 'type' in college:
                                college_type = college['type']
                            
                            # Ensure dict has proper structure
                            formatted_college = {
                                'name': college.get('name', ''),
                                'type': college_type,
                                'added_at': college.get('added_at', datetime.utcnow())
                            }
                            formatted_colleges.append(formatted_college)
                    
                    # Update the student document with bypass_document_validation
                    db[cls.collection_name].update_one(
                        {'_id': student['_id']},
                        {
                            '$set': {
                                'target_colleges': formatted_colleges,
                                'updated_at': datetime.utcnow()
                            }
                        },
                        bypass_document_validation=True
                    )
                    logger.info(f"Migrated target_colleges structure for student {student.get('auth0_id')}")
            
            logger.info("Completed target_colleges structure migration")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating target_colleges structure: {str(e)}")
            return False

    @classmethod
    def remove_target_college(cls, auth0_id: str, college_name: str) -> bool:
        """Remove a college from student's target colleges list"""
        try:
            db = get_db()
            
            # First check if student exists
            student = db[cls.collection_name].find_one({'auth0_id': auth0_id})
            if not student:
                logger.error(f"Student not found with auth0_id: {auth0_id}")
                return False
            
            # Remove the college using $pull operator
            result = db[cls.collection_name].update_one(
                {'auth0_id': auth0_id},
                {
                    '$pull': {
                        'target_colleges': {'name': college_name}
                    },
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Successfully removed college {college_name} from target list for student {auth0_id}")
            else:
                logger.error(f"Failed to remove college {college_name} from target list for student {auth0_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing college from target list: {str(e)}")
            return False

    @classmethod
    def add_target_activity(cls, auth0_id: str, activity_data: dict) -> bool:
        """Add an activity to student's target activities"""
        try:
            collection = cls.get_collection()
            
            # Ensure activity has required fields
            if not all(key in activity_data for key in ['name', 'description']):
                logger.error("Activity data missing required fields")
                return False
                
            # Add timestamp if not present
            if 'added_at' not in activity_data:
                activity_data['added_at'] = datetime.utcnow()

            # Set default values for optional fields
            formatted_activity = {
                'name': activity_data['name'],
                'description': activity_data['description'],
                'hours_per_week': activity_data.get('hours_per_week', 0),
                'activity_type': activity_data.get('activity_type', 'Other'),
                'position': activity_data.get('position', ''),
                'added_at': activity_data.get('added_at', datetime.utcnow())
            }
                
            # Check for duplicates
            existing = collection.find_one({
                'auth0_id': auth0_id,
                'target_activities.name': formatted_activity['name']
            })
            
            if existing:
                logger.warning(f"Activity {formatted_activity['name']} already exists in target list")
                return False
                
            # Add to target activities
            result = collection.update_one(
                {'auth0_id': auth0_id},
                {
                    '$push': {
                        'target_activities': formatted_activity
                    },
                    '$set': {
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Added activity {formatted_activity['name']} to target list")
            else:
                logger.error(f"Failed to add activity {formatted_activity['name']} to target list")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error adding target activity: {str(e)}")
            return False

    @classmethod
    def remove_target_activity(cls, auth0_id: str, activity_name: str) -> bool:
        """Remove an activity from student's target activities"""
        try:
            collection = cls.get_collection()
            
            result = collection.update_one(
                {'auth0_id': auth0_id},
                {
                    '$pull': {
                        'target_activities': {'name': activity_name}
                    },
                    '$set': {
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Removed activity {activity_name} from target list")
            else:
                logger.error(f"Failed to remove activity {activity_name} from target list")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error removing target activity: {str(e)}")
            return False
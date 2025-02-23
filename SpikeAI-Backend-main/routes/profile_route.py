from flask import Blueprint, request, jsonify, g
from middleware.google_auth import verify_google_token
from middleware.theme_generator import analyze_profile_theme
from config.db import get_db
import logging
from bson import ObjectId
from datetime import datetime
import stripe
from routes.payment_route import get_plan_features
from controllers.profile_controller import update_user_profile
import os
from models.student_model import Student
from services.subscription_service import SubscriptionService
from services.crew_suggestions_service import CrewSuggestionsService
import asyncio
import json

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/sync-user', methods=['POST'])
@verify_google_token
def sync_user():
    logger.info("==== STARTING PROFILE SYNC ====")
    logger.info(f"User info in context: {g.user_info if hasattr(g, 'user_info') else 'No user info'}")
    
    try:
        user_email = g.user_email
        user_info = g.user_info
        auth0_id = user_info.get('sub')  # Get the Google OAuth sub as auth0_id
        logger.debug(f"Syncing user: {user_email} with auth0_id: {auth0_id}")

        if not auth0_id:
            logger.error("No auth0_id in token")
            return jsonify({
                'success': False,
                'error': 'User ID not found'
            }), 401

        db = get_db()
        
        # Check if student exists by auth0_id first, then by email as fallback
        existing_student = db.students.find_one({'auth0_id': auth0_id}) or db.students.find_one({'email': user_email})
        
        if existing_student:
            # Update existing student while preserving all other fields
            update_data = {
                'auth0_id': auth0_id,  # Ensure auth0_id is set
                'email': user_email,
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'updated_at': datetime.utcnow()
            }
            
            db.students.update_one(
                {'_id': existing_student['_id']},
                {'$set': update_data}
            )
            
            logger.info(f"Updated existing student: {auth0_id}")
            return jsonify({
                'success': True,
                'message': 'Student updated'
            }), 200
        else:
            # Create new student with all required fields
            new_student = {
                'auth0_id': auth0_id,
                'email': user_email,
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'major': '',  # Empty string instead of None
                'extracurriculars': [],  # Will be array of objects
                'awards': [],
                'hooks': [],
                'target_colleges': [],
                'personality_type': '',  # Empty string instead of None
                'student_context': {
                    'country': '',  # Empty string instead of None
                    'estimated_contribution': 0,
                    'financial_aid_required': False,
                    'first_generation': False,
                    'ethnicity': '',  # Empty string instead of None
                    'gender': '',  # Empty string instead of None
                    'international_student': False
                },
                'student_statistics': {
                    'class_rank': 0,
                    'unweight_gpa': 0.0,
                    'weight_gpa': 0.0,
                    'sat_score': 0
                },
                'student_preferences': {
                    'campus_sizes': [],
                    'college_types': [],
                    'preferred_regions': [],
                    'preferred_states': []
                },
                'student_theme': '',  # Empty string instead of None
                'subscription': {
                    'is_subscribed': False,
                    'plan': '',  # Empty string instead of None
                    'status': 'inactive',
                    'trial_used': False,
                    'features': []
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            logger.info(f"Creating new student with data: {new_student}")
            result = db.students.insert_one(new_student)
            logger.info(f"Created new student: {auth0_id} with _id: {result.inserted_id}")
            return jsonify({
                'success': True,
                'message': 'Student created'
            }), 201

    except Exception as e:
        logger.error(f"Error in sync_user: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/', methods=['GET'])
@verify_google_token
def get_profile():
    try:
        user_email = g.user_email
        auth0_id = g.user_info.get('sub')  # Get the Google OAuth sub as auth0_id
        logger.info(f"Fetching profile for user: {auth0_id} ({user_email})")
        
        if not auth0_id:
            logger.error("No auth0_id in token")
            return jsonify({
                'success': False,
                'error': 'User ID not found'
            }), 401

        db = get_db()
        logger.debug(f"Connected to database, searching for profile with auth0_id: {auth0_id}")
        
        # Find student profile by auth0_id
        student = db.students.find_one({'auth0_id': auth0_id})
        
        if not student:
            logger.info(f"Creating new profile for auth0_id: {auth0_id}")
            # Create new student with all required fields
            student = {
                'auth0_id': auth0_id,  # Store the Google OAuth sub as auth0_id
                'email': user_email,
                'name': g.user_info.get('name'),
                'picture': g.user_info.get('picture'),
                'major': '',
                'extracurriculars': [],
                'awards': [],
                'hooks': [],
                'target_colleges': [],
                'personality_type': '',
                'student_context': {
                    'country': '',
                    'estimated_contribution': 0,
                    'financial_aid_required': False,
                    'first_generation': False,
                    'ethnicity': '',
                    'gender': '',
                    'international_student': False
                },
                'student_statistics': {
                    'class_rank': 0,
                    'unweight_gpa': 0.0,
                    'weight_gpa': 0.0,
                    'sat_score': 0
                },
                'student_preferences': {
                    'campus_sizes': [],
                    'college_types': [],
                    'preferred_regions': [],
                    'preferred_states': []
                },
                'student_theme': '',
                'subscription': {
                    'is_subscribed': False,
                    'status': 'inactive',
                    'stripe_customer_id': None,
                    'stripe_subscription_id': None,
                    'plan_type': None,
                    'current_period_start': None,
                    'current_period_end': None,
                    'cancel_at_period_end': False,
                    'payment_status': None,
                    'last_payment_date': None,
                    'features': []
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'last_login': datetime.utcnow()
            }
            
            try:
                result = db.students.insert_one(student)
                student['_id'] = result.inserted_id
                logger.info(f"Created new profile for auth0_id: {auth0_id}")
            except Exception as e:
                logger.error(f"Error creating new profile: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to create profile'
                }), 500
        else:
            logger.info(f"Found existing profile for auth0_id: {auth0_id}")
            
            # Update last login time and ensure auth0_id exists
            update_data = {
                'last_login': datetime.utcnow(),
                'auth0_id': auth0_id  # Ensure auth0_id is set
            }
            
            # Update email and name if they've changed
            if student.get('email') != user_email:
                update_data['email'] = user_email
            if student.get('name') != g.user_info.get('name'):
                update_data['name'] = g.user_info.get('name')
            if student.get('picture') != g.user_info.get('picture'):
                update_data['picture'] = g.user_info.get('picture')
            
            # Check Stripe subscription status if customer ID exists
            if student.get('subscription', {}).get('stripe_customer_id'):
                try:
                    subscription_id = student['subscription']['stripe_subscription_id']
                    if subscription_id:
                        stripe_sub = stripe.Subscription.retrieve(subscription_id)
                        logger.debug(f"Retrieved Stripe subscription: {stripe_sub}")
                        
                        # Update subscription data
                        update_data['subscription'] = {
                            'is_subscribed': stripe_sub.status == 'active',
                            'status': stripe_sub.status,
                            'stripe_customer_id': stripe_sub.customer,
                            'stripe_subscription_id': stripe_sub.id,
                            'plan_type': 'monthly' if 'month' in stripe_sub.plan.interval else 'yearly',
                            'current_period_start': datetime.fromtimestamp(stripe_sub.current_period_start),
                            'current_period_end': datetime.fromtimestamp(stripe_sub.current_period_end),
                            'cancel_at_period_end': stripe_sub.cancel_at_period_end,
                            'payment_status': 'paid',
                            'last_payment_date': datetime.utcnow(),
                            'features': get_plan_features()
                        }
                        logger.info(f"Updated subscription status from Stripe: {update_data['subscription']}")
                except stripe.error.InvalidRequestError as e:
                    logger.error(f"Invalid Stripe subscription: {str(e)}")
                    # Clear invalid subscription data
                    update_data['subscription'] = {
                        'is_subscribed': False,
                        'status': 'inactive',
                        'stripe_customer_id': None,
                        'stripe_subscription_id': None,
                        'features': []
                    }
                except Exception as e:
                    logger.error(f"Error fetching Stripe subscription: {str(e)}")
            
            try:
                db.students.update_one(
                    {'_id': student['_id']},
                    {'$set': update_data}
                )
                # Update the student object with the new data
                student.update(update_data)
                logger.info("Updated profile with latest information")
            except Exception as e:
                logger.error(f"Error updating profile: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to update profile'
                }), 500

        # Create a copy for JSON serialization
        response_data = dict(student)
        
        # Convert ObjectId to string
        if '_id' in response_data:
            response_data['_id'] = str(response_data['_id'])
        
        # Convert datetime objects to strings for JSON serialization
        for key in ['created_at', 'updated_at', 'last_login']:
            if key in response_data and response_data[key] is not None:
                if isinstance(response_data[key], datetime):
                    response_data[key] = response_data[key].isoformat()
                elif isinstance(response_data[key], str):
                    try:
                        # Try to parse the string as a datetime
                        dt = datetime.fromisoformat(response_data[key].replace('Z', '+00:00'))
                        response_data[key] = dt.isoformat()
                    except (ValueError, AttributeError):
                        # If parsing fails, leave it as is
                        pass
        
        # Convert subscription datetime objects
        if 'subscription' in response_data:
            for key in ['current_period_start', 'current_period_end', 'last_payment_date']:
                if key in response_data['subscription'] and response_data['subscription'][key] is not None:
                    if isinstance(response_data['subscription'][key], datetime):
                        response_data['subscription'][key] = response_data['subscription'][key].isoformat()
                    elif isinstance(response_data['subscription'][key], str):
                        try:
                            # Try to parse the string as a datetime
                            dt = datetime.fromisoformat(response_data['subscription'][key].replace('Z', '+00:00'))
                            response_data['subscription'][key] = dt.isoformat()
                        except (ValueError, AttributeError):
                            # If parsing fails, leave it as is
                            pass

        logger.info("Profile fetched successfully")
        return jsonify({
            'success': True,
            'profile': response_data
        }), 200

    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch profile: {str(e)}'
        }), 500

@profile_bp.route('/', methods=['PUT'])
@verify_google_token
@analyze_profile_theme
def update_profile():
    logger.info("==== STARTING PROFILE UPDATE ====")
    try:
        # Get user info from verified token
        user_email = g.user_email
        auth0_id = g.user_info.get('sub')  # Get the Google OAuth sub as auth0_id
        logger.info(f"Updating profile for user: {auth0_id} ({user_email})")
        
        if not auth0_id:
            logger.error("❌ No auth0_id in token")
            return jsonify({
                'success': False,
                'error': 'User ID not found'
            }), 401

        # Get update data from request
        data = request.get_json()
        logger.info(f"Received update data: {json.dumps(data, default=str)}")
        
        if not data:
            logger.error("❌ No update data provided")
            return jsonify({
                'success': False,
                'error': 'No update data provided'
            }), 400

        db = get_db()
        existing_student = db.students.find_one({'auth0_id': auth0_id})
        
        if not existing_student:
            logger.error(f"❌ No student found with auth0_id: {auth0_id}")
            return jsonify({
                'success': False,
                'error': 'Student not found'
            }), 404

        logger.info(f"Current hooks in database: {existing_student.get('hooks', [])}")
        
        # Handle array fields - ensure they are lists and handle duplicates appropriately
        array_fields = ['hooks', 'target_colleges']  # Remove awards from array_fields since it's now an object array
        for field in array_fields:
            if field in data:
                logger.info(f"Processing {field} field. Current value: {data[field]}")
                if field == 'target_colleges':
                    # For target_colleges, keep as is since they contain dictionaries
                    colleges = data[field] if data[field] else existing_student.get(field, [])
                    # Convert added_at strings to datetime objects
                    for college in colleges:
                        if 'added_at' in college and isinstance(college['added_at'], str):
                            try:
                                # Try parsing the date string
                                college['added_at'] = datetime.strptime(
                                    college['added_at'].replace(' GMT', ''),
                                    '%a, %d %b %Y %H:%M:%S'
                                )
                            except ValueError:
                                # If parsing fails, use current time
                                college['added_at'] = datetime.utcnow()
                    data[field] = colleges
                else:
                    # For other arrays that contain simple values, remove duplicates and handle empty values
                    if data[field] is None:
                        data[field] = existing_student.get(field, [])
                    elif not isinstance(data[field], list):
                        logger.warning(f"❌ {field} is not a list, received: {type(data[field])}. Using empty list.")
                        data[field] = []
                    else:
                        # Filter out empty strings and whitespace-only strings
                        filtered_values = [str(item).strip() for item in data[field] if item and str(item).strip()]
                        data[field] = list(set(filtered_values))
                    logger.info(f"Final {field} value after processing: {data[field]}")

        # Handle awards separately since it's now an array of objects
        if 'awards' in data:
            logger.info(f"Processing awards. Current value: {data['awards']}")
            if not isinstance(data['awards'], list):
                logger.warning("❌ awards is not a list. Using empty list.")
                data['awards'] = []
            else:
                # Validate and format each award
                formatted_awards = []
                for award in data['awards']:
                    if isinstance(award, dict):
                        formatted_award = {
                            'title': award.get('title', '').strip(),
                            'grade_levels': [str(grade).strip() for grade in award.get('grade_levels', []) if str(grade).strip()],
                            'recognition_levels': [str(level).strip() for level in award.get('recognition_levels', []) if str(level).strip()],
                            'added_at': award.get('added_at', datetime.utcnow().isoformat())
                        }
                        # Only add if title is provided
                        if formatted_award['title']:
                            formatted_awards.append(formatted_award)
                data['awards'] = formatted_awards[:10]  # Limit to 10 awards
            logger.info(f"Final awards value after processing: {data['awards']}")

        # Handle extracurriculars separately since it's now an array of objects
        if 'extracurriculars' in data:
            logger.info(f"Processing extracurriculars. Current value: {data['extracurriculars']}")
            if not isinstance(data['extracurriculars'], list):
                logger.warning("❌ extracurriculars is not a list. Using empty list.")
                data['extracurriculars'] = []
            else:
                # Validate and format each extracurricular activity
                formatted_activities = []
                for activity in data['extracurriculars']:
                    if isinstance(activity, dict):
                        formatted_activity = {
                            'name': activity.get('name', ''),
                            'activity_type': activity.get('activity_type', ''),
                            'position_leadership': activity.get('position_leadership', '').strip(),
                            'organization_description': activity.get('organization_description', '').strip(),
                            'activity_description': activity.get('activity_description', '').strip(),
                            'added_at': activity.get('added_at', datetime.utcnow())
                        }
                        formatted_activities.append(formatted_activity)
                data['extracurriculars'] = formatted_activities[:10]  # Limit to 10 activities
            logger.info(f"Final extracurriculars value after processing: {data['extracurriculars']}")

        # Handle nested objects - merge with existing data
        nested_objects = ['student_preferences', 'student_context', 'student_statistics']
        for obj in nested_objects:
            if obj in data:
                existing_data = existing_student.get(obj, {})
                if isinstance(data[obj], dict):
                    existing_data.update(data[obj])
                    data[obj] = existing_data

        # Preserve subscription data
        if 'subscription' in existing_student:
            data['subscription'] = existing_student['subscription']

        # Handle datetime fields
        current_time = datetime.utcnow()
        data['updated_at'] = current_time
        data['last_login'] = current_time
        
        # Ensure created_at is preserved or set if missing
        if 'created_at' in existing_student:
            data['created_at'] = existing_student['created_at']
        else:
            data['created_at'] = current_time

        # Convert any string datetime fields in subscription to datetime objects
        if 'subscription' in data:
            for key in ['current_period_start', 'current_period_end', 'last_payment_date']:
                if key in data['subscription'] and isinstance(data['subscription'][key], str):
                    try:
                        data['subscription'][key] = datetime.fromisoformat(data['subscription'][key].replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        data['subscription'][key] = None

        # Update profile while preserving existing fields
        try:
            update_result = db.students.update_one(
                {'auth0_id': auth0_id},
                {'$set': data}
            )
            
            if update_result.modified_count == 0:
                logger.warning(f"No changes made to profile for auth0_id: {auth0_id}")
            
            # Get updated profile
            updated_student = db.students.find_one({'auth0_id': auth0_id})
            
            # Create a copy for JSON serialization
            response_data = dict(updated_student)
            
            # Convert ObjectId to string
            if '_id' in response_data:
                response_data['_id'] = str(response_data['_id'])
            
            # Convert datetime objects to strings for JSON response
            for key in ['created_at', 'updated_at', 'last_login']:
                if key in response_data and response_data[key] is not None:
                    if isinstance(response_data[key], datetime):
                        response_data[key] = response_data[key].isoformat()
            
            # Convert subscription datetime fields
            if 'subscription' in response_data:
                for key in ['current_period_start', 'current_period_end', 'last_payment_date']:
                    if key in response_data['subscription'] and response_data['subscription'][key] is not None:
                        if isinstance(response_data['subscription'][key], datetime):
                            response_data['subscription'][key] = response_data['subscription'][key].isoformat()
            
            logger.info(f"Successfully updated profile for auth0_id: {auth0_id}")
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': response_data
            })

        except Exception as e:
            logger.error(f"Error updating profile in database: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Database update failed: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"Error in update_profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@profile_bp.route('/', methods=['DELETE'])
@verify_google_token
def delete_profile():
    try:
        auth0_id = g.user_info.get('sub')
        user_email = g.user_email
        logger.info(f"Deleting profile for user {user_email} with auth0_id {auth0_id}")
        
        if not auth0_id:
            return jsonify({
                'success': False,
                'error': 'No auth0_id found in token'
            }), 401
        
        # Delete from MongoDB
        db = get_db()
        student = Student.get_by_auth0_id(auth0_id)
        if student:
            # Cancel subscription if exists
            subscription = student.get('subscription', {})
            if subscription and subscription.get('stripe_subscription_id'):
                try:
                    subscription_service = SubscriptionService()
                    subscription_service.cancel_subscription(auth0_id)
                    logger.info(f"✅ Cancelled subscription for user {user_email}")
                except Exception as e:
                    logger.error(f"❌ Error cancelling subscription: {str(e)}")
                    # Continue with deletion even if subscription cancellation fails
            
            # Delete student profile
            result = db.students.delete_one({'auth0_id': auth0_id})
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted student profile from MongoDB for {auth0_id}")
            else:
                logger.warning(f"No student profile found to delete in MongoDB for {auth0_id}")
        else:
            logger.warning(f"No student profile found in MongoDB for {auth0_id}")
            
        # Delete from CrewSuggestions and CrewSuggestionsTemp
        crew_service = CrewSuggestionsService()
        crew_success = crew_service.delete_user_suggestions(auth0_id)
        if crew_success:
            logger.info(f"✅ Deleted crew suggestions for {auth0_id}")
        else:
            logger.error(f"❌ Failed to delete crew suggestions for {auth0_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in delete_profile: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
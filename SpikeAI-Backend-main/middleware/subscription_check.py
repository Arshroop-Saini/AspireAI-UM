from functools import wraps
from flask import jsonify, g
from config.db import get_db
import logging
import os
import stripe

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def requires_subscription(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get user email from the verified token info stored in g
            user_email = g.user_email
            auth0_id = g.user_info.get('sub')
            
            if not user_email or not auth0_id:
                logger.error("No user email or auth0_id found in context")
                return jsonify({
                    'success': False,
                    'error': 'User not authenticated'
                }), 401

            logger.debug(f"Checking subscription for user: {user_email}")
            
            # Get student from database
            db = get_db()
            student = db.students.find_one({'auth0_id': auth0_id})
            
            if not student:
                logger.error(f"No student found for auth0_id: {auth0_id}")
                return jsonify({
                    'success': False,
                    'error': 'Student not found'
                }), 404
            
            # Check if student has subscription info
            subscription = student.get('subscription', {})
            stripe_subscription_id = subscription.get('stripe_subscription_id')
            
            if stripe_subscription_id:
                try:
                    # Verify subscription with Stripe
                    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                    logger.debug(f"Stripe subscription status: {stripe_sub.status}")
                    
                    if stripe_sub.status not in ['active', 'trialing']:
                        return jsonify({
                            'success': False,
                            'error': 'No active subscription',
                            'subscription_status': stripe_sub.status
                        }), 403
                except stripe.error.InvalidRequestError:
                    logger.error(f"Invalid Stripe subscription ID: {stripe_subscription_id}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid subscription'
                    }), 403
                except Exception as e:
                    logger.error(f"Error checking Stripe subscription: {str(e)}")
                    # Fall back to local subscription check
                    pass
            
            # Check local subscription status if Stripe check fails or no Stripe ID
            if not subscription.get('is_subscribed'):
                logger.error(f"No active subscription found for user: {user_email}")
                return jsonify({
                    'success': False,
                    'error': 'No active subscription'
                }), 403

            logger.debug(f"Subscription check passed for user: {user_email}")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in subscription check: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to verify subscription',
                'details': str(e)
            }), 500
            
    return decorated_function
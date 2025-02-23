import stripe
from os import environ as env
from datetime import datetime
from models.student_model import Student
import logging
from pymongo import MongoClient

stripe.api_key = env.get('STRIPE_SECRET_KEY')
logger = logging.getLogger(__name__)

class SubscriptionService:
    @staticmethod
    def create_checkout_session(student, subscription_type):
        """Create a Stripe checkout session for subscription"""
        try:
            price_id = env.get('STRIPE_MONTHLY_PRICE_ID') if subscription_type == 'monthly' else env.get('STRIPE_YEARLY_PRICE_ID')
            
            session = stripe.checkout.Session.create(
                customer_email=student.email,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{env.get('CORS_ORIGIN')}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{env.get('CORS_ORIGIN')}/subscription",
                metadata={
                    'student_id': student.auth0_id,
                    'subscription_type': subscription_type
                }
            )
            return session
        except Exception as e:
            raise Exception(f"Error creating checkout session: {str(e)}")

    @staticmethod
    def get_subscription_status(student_id):
        """Get subscription status for a student"""
        try:
            student = Student.get_by_auth0_id(student_id)
            if not student:
                raise Exception("Student not found")

            return {
                'is_subscribed': student.is_subscribed,
                'subscription_id': student.subscription_id,
                'subscription_status': student.subscription_status,
                'subscription_end_date': student.subscription_end_date.isoformat() if student.subscription_end_date else None
            }
        except Exception as e:
            raise Exception(f"Error getting subscription status: {str(e)}")

    @staticmethod
    def cancel_subscription(student_id):
        """Cancel a student's subscription"""
        try:
            student = Student.get_by_auth0_id(student_id)
            if not student:
                raise Exception("Student not found")

            if not student.subscription_id:
                raise Exception("No active subscription found")

            # Cancel at period end
            subscription = stripe.Subscription.modify(
                student.subscription_id,
                cancel_at_period_end=True
            )

            # Update student record
            student.update_subscription(
                subscription_status='canceling',
                subscription_end_date=datetime.fromtimestamp(subscription.current_period_end)
            )

            return {
                'message': 'Subscription will be cancelled at the end of the billing period',
                'end_date': datetime.fromtimestamp(subscription.current_period_end).isoformat()
            }
        except Exception as e:
            raise Exception(f"Error canceling subscription: {str(e)}")

    @staticmethod
    def handle_webhook_event(event):
        """Handle Stripe webhook events"""
        try:
            logger.info(f"Processing webhook event: {event.type}")
            logger.info(f"Event data: {event.data}")
            
            if event.type == 'checkout.session.completed':
                session = event.data.object
                auth0_id = session.metadata.get('auth0_id')
                user_email = session.metadata.get('user_email')
                
                logger.info(f"Processing checkout completion for {user_email} (auth0_id: {auth0_id})")
                
                # Try to find student by auth0_id first, then by email
                db = get_db()
                query = {'$or': [{'auth0_id': auth0_id}, {'email': user_email}]} if auth0_id else {'email': user_email}
                student = db.students.find_one(query)
                
                if student:
                    subscription = stripe.Subscription.retrieve(session.subscription)
                    plan_type = session.metadata.get('plan_type', 'monthly' if 'month' in subscription.plan.interval else 'yearly')
                    
                    subscription_data = {
                        'is_subscribed': subscription.status == 'active',
                        'stripe_customer_id': session.customer,
                        'stripe_subscription_id': subscription.id,
                        'plan_type': plan_type,
                        'status': subscription.status,
                        'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                        'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'payment_status': 'paid',
                        'updated_at': datetime.utcnow(),
                        'last_payment_date': datetime.utcnow()
                    }
                    
                    # Update student profile
                    result = db.students.update_one(
                        query,
                        {'$set': {'subscription': subscription_data}}
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"Successfully updated subscription for {user_email}")
                    else:
                        logger.warning(f"No subscription update needed for {user_email}")
                    
            elif event.type == 'customer.subscription.deleted':
                subscription = event.data.object
                # Try to find student by customer ID
                db = get_db()
                student = db.students.find_one({'subscription.stripe_customer_id': subscription.customer})
                
                if student:
                    subscription_data = {
                        'is_subscribed': False,
                        'status': 'cancelled',
                        'cancel_at_period_end': True,
                        'updated_at': datetime.utcnow(),
                        'current_period_end': datetime.fromtimestamp(subscription.current_period_end)
                    }
                    
                    result = db.students.update_one(
                        {'_id': student['_id']},
                        {'$set': {'subscription': subscription_data}}
                    )
                    
                    logger.info(f"Subscription cancelled for user: {student.get('email')}")
                    
            elif event.type == 'customer.subscription.updated':
                subscription = event.data.object
                # Try to find student by customer ID
                db = get_db()
                student = db.students.find_one({'subscription.stripe_customer_id': subscription.customer})
                
                if student:
                    subscription_data = {
                        'is_subscribed': subscription.status == 'active',
                        'status': subscription.status,
                        'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'updated_at': datetime.utcnow()
                    }
                    
                    result = db.students.update_one(
                        {'_id': student['_id']},
                        {'$set': {'subscription': subscription_data}}
                    )
                    
                    logger.info(f"Subscription updated for user: {student.get('email')}")
                
        except Exception as e:
            logger.error(f"Error handling webhook event: {str(e)}")
            raise Exception(f"Error handling webhook event: {str(e)}")

    @staticmethod
    def check_and_update_expired_subscriptions():
        """Check and update expired subscriptions"""
        try:
            db = get_db()
            current_time = datetime.utcnow()
            
            # Find all active subscriptions that have passed their end date
            expired_subscriptions = db.students.find({
                'subscription.is_subscribed': True,
                'subscription.status': 'active',
                'subscription.current_period_end': {'$lt': current_time}
            })
            
            for student in expired_subscriptions:
                try:
                    subscription_data = student.get('subscription', {})
                    stripe_subscription_id = subscription_data.get('stripe_subscription_id')
                    
                    if stripe_subscription_id:
                        # Verify with Stripe
                        try:
                            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                            if stripe_sub.status != 'active':
                                # Update subscription data
                                subscription_data.update({
                                    'is_subscribed': False,
                                    'status': 'expired',
                                    'updated_at': current_time,
                                    'features': []
                                })
                                
                                # Update in database
                                db.students.update_one(
                                    {'_id': student['_id']},
                                    {'$set': {'subscription': subscription_data}}
                                )
                                logger.info(f"Updated expired subscription for user: {student.get('email')}")
                        except stripe.error.InvalidRequestError:
                            # Invalid or expired subscription
                            subscription_data.update({
                                'is_subscribed': False,
                                'status': 'expired',
                                'stripe_subscription_id': None,
                                'updated_at': current_time,
                                'features': []
                            })
                            
                            # Update in database
                            db.students.update_one(
                                {'_id': student['_id']},
                                {'$set': {'subscription': subscription_data}}
                            )
                            logger.info(f"Cleared invalid subscription for user: {student.get('email')}")
                    else:
                        # No Stripe subscription ID, just update local status
                        subscription_data.update({
                            'is_subscribed': False,
                            'status': 'expired',
                            'updated_at': current_time,
                            'features': []
                        })
                        
                        # Update in database
                        db.students.update_one(
                            {'_id': student['_id']},
                            {'$set': {'subscription': subscription_data}}
                        )
                        logger.info(f"Updated local expired subscription for user: {student.get('email')}")
                        
                except Exception as e:
                    logger.error(f"Error updating expired subscription for user {student.get('email')}: {str(e)}")
                    continue
            
            return True
        except Exception as e:
            logger.error(f"Error checking expired subscriptions: {str(e)}")
            return False

def get_db():
    client = MongoClient(env.get('MONGO_URI'))
    return client.get_database() 
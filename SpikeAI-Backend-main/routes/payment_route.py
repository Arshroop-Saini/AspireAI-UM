from flask import Blueprint, request, jsonify, g
from middleware.google_auth import verify_google_token
from config.db import get_db
from models.student_model import Student
from config.stripe_config import get_price_id, STRIPE_PRODUCTS
from services.subscription_service import SubscriptionService
import logging
from datetime import datetime
import stripe
from os import environ as env
import os
import time
import traceback

logger = logging.getLogger(__name__)
payment_bp = Blueprint('payment', __name__)

# Initialize Stripe with secret key
stripe.api_key = env.get('STRIPE_SECRET_KEY')

@payment_bp.route('/create-checkout-session', methods=['POST'])
@verify_google_token
def create_checkout_session():
    """Create a new checkout session for subscription"""
    try:
        user_email = g.user_email
        auth0_id = g.user_info.get('sub')
        data = request.get_json()
        plan_type = data.get('plan_type', 'monthly')
        
        if plan_type not in ['monthly', 'yearly']:
            return jsonify({'error': 'Invalid plan type'}), 400
            
        price_id = env.get('STRIPE_MONTHLY_PRICE_ID') if plan_type == 'monthly' else env.get('STRIPE_YEARLY_PRICE_ID')
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            success_url=f"{env.get('FRONTEND_URL')}/subscription?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{env.get('FRONTEND_URL')}/subscription",
            mode='subscription',
            billing_address_collection='auto',
            customer_email=user_email,
            allow_promotion_codes=True,
            metadata={
                'user_email': user_email,
                'auth0_id': auth0_id,
                'plan_type': plan_type
            },
            line_items=[
                {"price": price_id, "quantity": 1}
            ],
            subscription_data={
                'metadata': {
                    'user_email': user_email,
                    'auth0_id': auth0_id,
                    'plan_type': plan_type
                }
            }
        )

        # Store session ID for verification
        db = get_db()
        db.checkout_sessions.update_one(
            {'user_email': user_email},
            {
                '$set': {
                    'session_id': session.id,
                    'auth0_id': auth0_id,
                    'plan_type': plan_type,
                    'created_at': datetime.utcnow()
                }
            },
            upsert=True
        )
        
        logger.info(f"Created checkout session {session.id} for {user_email} with plan {plan_type}")
        
        return jsonify({
            'url': session.url,
            'sessionId': session.id
        })
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/create-portal-session', methods=['POST'])
@verify_google_token
def create_portal_session():
    try:
        user_email = g.user_email
        auth0_id = g.user_info.get('sub')
        
        if not user_email or not auth0_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        # Get student from database
        db = get_db()
        student = db.students.find_one({'auth0_id': auth0_id})
        
        if not student or not student.get('subscription', {}).get('stripe_customer_id'):
            return jsonify({
                'success': False,
                'error': 'No active subscription found'
            }), 404

        # Create portal session using dashboard configuration
        session = stripe.billing_portal.Session.create(
            customer=student['subscription']['stripe_customer_id'],
            return_url=f"{os.environ.get('FRONTEND_URL')}/dashboard"
        )

        return jsonify({
            'success': True,
            'url': session.url
        })

    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        logger.error("Webhook secret not configured")
        return jsonify({'error': 'Webhook secret not configured'}), 500

    try:
        # Log incoming webhook with more details
        logger.info(f"Received webhook - Headers: {dict(request.headers)}")
        logger.info(f"Webhook secret first 10 chars: {webhook_secret[:10]}...")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return jsonify({'error': 'Invalid signature'}), 400

        # Log the event type and data
        logger.info(f"Processing webhook event: {event.type}")
        logger.info(f"Event data: {event.data.object}")
        logger.info(f"Event metadata: {event.data.object.get('metadata', {})}")
        
        event_object = event.data.object

        if event.type == 'checkout.session.completed':
            logger.info(f"Processing completed checkout session: {event_object.id}")
            
            try:
                # Get subscription and customer details
                subscription = stripe.Subscription.retrieve(
                    event_object.subscription,
                    expand=['plan']
                )
                customer = stripe.Customer.retrieve(event_object.customer)
                
                # Get user info from metadata or customer
                user_email = event_object.metadata.get('user_email') or customer.email
                auth0_id = event_object.metadata.get('auth0_id')
                plan_type = event_object.metadata.get('plan_type', 'monthly' if 'month' in subscription.plan.interval else 'yearly')
                
                logger.info(f"Subscription details - ID: {subscription.id}, Status: {subscription.status}")
                logger.info(f"Customer details - ID: {customer.id}, Email: {user_email}")
                
                # Format subscription data
                subscription_data = {
                    'subscription': {
                        'is_subscribed': True,
                        'plan': plan_type,
                        'status': 'active',
                        'stripe_customer_id': customer.id,
                        'stripe_subscription_id': subscription.id,
                        'plan_type': plan_type,
                        'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                        'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'payment_status': 'succeeded',
                        'last_payment_date': datetime.utcnow(),
                        'features': get_plan_features(),
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
                
                # Update student profile
                db = get_db()
                query = {'$or': [{'email': user_email}]}
                if auth0_id:
                    query['$or'].append({'auth0_id': auth0_id})
                
                # Log the query and update data
                logger.info(f"Database query: {query}")
                logger.info(f"Update data: {subscription_data}")
                
                update_result = db.students.update_one(
                    query,
                    {
                        '$set': subscription_data,
                        '$setOnInsert': {
                            'email': user_email,
                            'auth0_id': auth0_id,
                            'created_at': datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                
                logger.info(f"Profile update result - Modified: {update_result.modified_count}, Matched: {update_result.matched_count}, Upserted: {update_result.upserted_id}")
                
                # Verify the update
                updated_student = db.students.find_one(query)
                if not updated_student:
                    logger.error(f"Failed to find student after update for {user_email}")
                    return jsonify({'error': 'Failed to verify subscription update'}), 500
                
                logger.info(f"Updated student subscription status: {updated_student.get('subscription', {}).get('is_subscribed')}")
                
                if not updated_student.get('subscription', {}).get('is_subscribed'):
                    logger.error(f"Subscription not properly set for {user_email}")
                    return jsonify({'error': 'Failed to verify subscription status'}), 500
                
                logger.info(f"Successfully updated and verified subscription for {user_email}")
                
            except Exception as e:
                logger.error(f"Error in checkout.session.completed: {str(e)}")
                logger.error(f"Error traceback: {traceback.format_exc()}")
                return jsonify({'error': str(e)}), 500
            
        elif event.type == 'customer.subscription.updated':
            # Handle subscription updates
            subscription = event_object
            customer = stripe.Customer.retrieve(subscription.customer)
            user_email = customer.email
            
            logger.info(f"Processing subscription update for {user_email}")
            
            try:
                db = get_db()
                update_result = db.students.update_one(
                    {'subscription.stripe_customer_id': customer.id},
                    {
                        '$set': {
                            'subscription.status': subscription.status,
                            'subscription.is_subscribed': subscription.status == 'active',
                            'subscription.current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                            'subscription.cancel_at_period_end': subscription.cancel_at_period_end,
                            'subscription.payment_status': subscription.status,
                            'subscription.updated_at': datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"Subscription update result - modified: {update_result.modified_count}")
                
                if update_result.modified_count == 0:
                    logger.warning(f"No subscription updated for customer {customer.id}")
                
            except Exception as e:
                logger.error(f"Error updating subscription: {str(e)}")
                logger.error(f"Error traceback: {traceback.format_exc()}")
                return jsonify({'error': 'Failed to update subscription'}), 500
                
        elif event.type == 'customer.subscription.deleted':
            # Handle subscription deletion
            subscription = event_object
            customer = stripe.Customer.retrieve(subscription.customer)
            user_email = customer.email
            
            logger.info(f"Processing subscription deletion for {user_email}")
            
            try:
                db = get_db()
                update_result = db.students.update_one(
                    {'subscription.stripe_customer_id': customer.id},
                    {
                        '$set': {
                            'subscription.status': 'cancelled',
                            'subscription.is_subscribed': False,
                            'subscription.cancel_at_period_end': True,
                            'subscription.updated_at': datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"Subscription deletion result - modified: {update_result.modified_count}")
                
                if update_result.modified_count == 0:
                    logger.warning(f"No subscription found to cancel for customer {customer.id}")
                
            except Exception as e:
                logger.error(f"Error cancelling subscription: {str(e)}")
                logger.error(f"Error traceback: {traceback.format_exc()}")
                return jsonify({'error': 'Failed to cancel subscription'}), 500

        # Log successful processing
        logger.info(f"Successfully processed webhook event: {event.type}")
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 400

def handle_successful_checkout(session):
    """Handle successful checkout completion"""
    try:
        # Get subscription and customer details
        subscription = stripe.Subscription.retrieve(session.subscription)
        customer = stripe.Customer.retrieve(session.customer)
        user_email = session.metadata.get('user_email') or customer.email
        auth0_id = session.metadata.get('auth0_id')
        
        logger.info(f"Processing successful checkout for {user_email} (auth0_id: {auth0_id})")
        logger.info(f"Subscription details: {subscription}")
        logger.info(f"Customer details: {customer}")

        # Get plan details
        plan = subscription.plan
        plan_type = session.metadata.get('plan_type', 'monthly' if 'month' in plan.interval else 'yearly')

        # Format subscription data
        subscription_data = {
            'is_subscribed': True,  # Force to True on successful checkout
            'stripe_customer_id': customer.id,
            'stripe_subscription_id': subscription.id,
            'plan_type': plan_type,
            'status': subscription.status,
            'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'payment_status': 'paid',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'last_payment_date': datetime.utcnow(),
            'features': get_plan_features(),
            'price_id': plan.id,
            'amount': plan.amount / 100,  # Convert from cents to dollars
            'currency': plan.currency,
            'interval': plan.interval
        }

        # Update student profile with retries
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                logger.info(f"Attempt {retry_count + 1} to update student profile with subscription data")
                
                db = get_db()
                
                # Try to find student by auth0_id first, then by email
                query = {'$or': [{'email': user_email}]}
                if auth0_id:
                    query['$or'].append({'auth0_id': auth0_id})
                
                # Use upsert to ensure the student document exists
                update_result = db.students.update_one(
                    query,
                    {
                        '$set': {
                            'subscription': subscription_data,
                            'updated_at': datetime.utcnow(),
                            'email': user_email,  # Ensure email is set
                        },
                        '$setOnInsert': {
                            'created_at': datetime.utcnow(),
                            'auth0_id': auth0_id,  # Only set auth0_id if document is new
                            'name': customer.name if hasattr(customer, 'name') else '',
                            'picture': '',
                            'target_colleges': [],
                            'student_preferences': {},
                            'student_statistics': {},
                            'student_context': {}
                        }
                    },
                    upsert=True
                )
                
                logger.info(f"Update result: {update_result.modified_count} documents modified, {update_result.upserted_id if hasattr(update_result, 'upserted_id') else 'no'} document upserted")
                
                # Verify the update
                updated_student = db.students.find_one(query)
                if updated_student:
                    updated_subscription = updated_student.get('subscription', {})
                    if (updated_subscription.get('stripe_subscription_id') == subscription.id and 
                        updated_subscription.get('is_subscribed') == True):
                        logger.info(f"Successfully verified subscription update for {user_email}")
                        logger.info(f"Updated subscription data: {updated_subscription}")
                        success = True
                        break
                    else:
                        logger.warning(f"Update verification failed - subscription data mismatch for {user_email}")
                else:
                    logger.warning(f"Update verification failed - could not find student document for {user_email}")
                
                retry_count += 1
                if not success and retry_count < max_retries:
                    time.sleep(1)  # Wait before retrying
                    
            except Exception as e:
                logger.error(f"Error updating subscription on attempt {retry_count + 1}: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)  # Wait before retrying
        
        if not success:
            logger.error(f"Failed to update subscription after {max_retries} attempts for {user_email}")
            raise Exception("Failed to update subscription after maximum retries")

    except Exception as e:
        logger.error(f"Error handling checkout: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        raise

def handle_successful_payment(invoice):
    """Handle successful payment"""
    try:
        # Get subscription and customer from invoice
        subscription = stripe.Subscription.retrieve(invoice.subscription)
        customer = stripe.Customer.retrieve(invoice.customer)
        user_email = customer.email
        
        logger.info(f"Processing successful payment for {user_email}")
        
        subscription_data = {
            'is_subscribed': True,
            'stripe_customer_id': customer.id,
            'stripe_subscription_id': subscription.id,
            'plan_type': 'monthly' if 'month' in subscription.plan.interval else 'yearly',
            'status': subscription.status,
            'current_period_start': subscription.current_period_start,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'payment_status': 'paid',
            'last_payment_date': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'features': get_plan_features()
        }

        # Update student profile
        Student.update_subscription(user_email, subscription_data)
        logger.info(f"Successfully processed payment for {user_email}")

    except Exception as e:
        logger.error(f"Error handling payment: {str(e)}")
        raise

def send_welcome_email(email: str, subscription_data: dict):
    """Send welcome email to new subscribers"""
    try:
        # You can implement email sending here using your preferred email service
        # For example, using SendGrid, Mailgun, or AWS SES
        plan_type = subscription_data['plan_type']
        end_date = datetime.fromtimestamp(subscription_data['current_period_end'])
        
        # Example email content
        subject = "Welcome to SpikeAI Premium!"
        content = f"""
        Thank you for subscribing to SpikeAI Premium!
        
        Subscription Details:
        - Plan: {plan_type.capitalize()}
        - Valid until: {end_date.strftime('%B %d, %Y')}
        - Status: Active
        
        You now have access to all premium features.
        """
        
        # Send email using your email service
        # send_email(email, subject, content)
        
        logger.info(f"Welcome email sent to {email}")
        
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        # Don't raise the error as this is not critical

def handle_subscription_created(subscription):
    """Handle new subscription creation"""
    try:
        customer = stripe.Customer.retrieve(subscription.customer)
        user_email = customer.email
        
        # Get subscription details
        subscription_data = {
            'is_subscribed': True,
            'stripe_customer_id': subscription.customer,
            'stripe_subscription_id': subscription.id,
            'plan_type': 'monthly' if 'month' in subscription.plan.interval else 'yearly',
            'status': subscription.status,
            'current_period_start': subscription.current_period_start,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'trial_end': subscription.trial_end,
            'price_id': subscription.plan.id,
            'payment_status': subscription.latest_invoice.payment_intent.status if subscription.latest_invoice else 'no_payment_required',
            'features': get_plan_features()
        }

        # Update student profile
        Student.update_subscription(user_email, subscription_data)
        logger.info(f"Successfully updated subscription for user: {user_email}")

    except Exception as e:
        logger.error(f"Error handling subscription creation: {str(e)}")
        raise

def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    try:
        customer = stripe.Customer.retrieve(subscription.customer)
        user_email = customer.email
        
        subscription_data = {
            'status': subscription.status,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'updated_at': datetime.utcnow(),
            'is_subscribed': subscription.status == 'active'
        }

        Student.update_subscription(user_email, subscription_data)
        logger.info(f"Successfully updated subscription for {user_email}")

    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")
        raise

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        customer = stripe.Customer.retrieve(subscription.customer)
        user_email = customer.email
        
        logger.info(f"Processing subscription cancellation for {user_email}")
        logger.info(f"Subscription details: {subscription}")
        
        subscription_data = {
            'is_subscribed': False,
            'status': 'cancelled',
            'cancel_at_period_end': True,
            'updated_at': datetime.utcnow(),
            'features': []
        }

        Student.update_subscription(user_email, subscription_data)
        
        # Verify the update
        updated_student = Student.get_by_email(user_email)
        logger.info(f"Updated subscription status: {updated_student.get('subscription', {})}")
        
        logger.info(f"Successfully cancelled subscription for user: {user_email}")

    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {str(e)}")
        raise

@payment_bp.route('/create-checkout', methods=['POST'])
@verify_google_token
def create_checkout():
    try:
        data = request.get_json()
        plan_type = data.get('plan_type')  # 'monthly' or 'yearly'
        user_email = g.user_email

        # Validate plan type
        if plan_type not in ['monthly', 'yearly']:
            return jsonify({'error': 'Invalid plan type'}), 400

        price_id = get_price_id(plan_type)
        if not price_id:
            return jsonify({'error': 'Price configuration not found'}), 500

        # Check if user already has an active subscription
        student = Student.get_by_email(user_email)
        if student and student.get('subscription', {}).get('status') == 'active':
            return jsonify({'error': 'User already has an active subscription'}), 400

        # Create or retrieve Stripe customer
        customer = None
        if student and student.get('subscription', {}).get('stripe_customer_id'):
            customer = stripe.Customer.retrieve(student['subscription']['stripe_customer_id'])
        else:
            customer = stripe.Customer.create(
                email=user_email,
                metadata={'user_email': user_email}
            )

        # Create checkout session with only the selected plan
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{env.get('FRONTEND_URL')}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{env.get('FRONTEND_URL')}/subscription?canceled=true",
            metadata={
                'user_email': user_email,
                'plan_type': plan_type
            },
            subscription_data={
                'metadata': {
                    'user_email': user_email,
                    'plan_type': plan_type
                }
            },
            allow_promotion_codes=True,
            billing_address_collection='auto'
        )

        return jsonify({
            'sessionId': session.id,
            'url': session.url
        })

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/subscription-status', methods=['GET'])
@verify_google_token
def get_subscription_status():
    try:
        user_email = g.user_email
        db = get_db()
        student = db.students.find_one({'email': user_email})
        
        if not student or 'subscription' not in student:
            return jsonify({
                'success': True,
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
                }
            })

        subscription = student.get('subscription', {})
        
        # Convert datetime objects to strings for JSON serialization
        for key in ['current_period_start', 'current_period_end', 'last_payment_date', 'created_at', 'updated_at']:
            if key in subscription and subscription[key] is not None:
                if isinstance(subscription[key], datetime):
                    subscription[key] = subscription[key].isoformat()
        
        # Ensure all required fields are present
        subscription.setdefault('is_subscribed', False)
        subscription.setdefault('status', 'inactive')
        subscription.setdefault('stripe_customer_id', None)
        subscription.setdefault('stripe_subscription_id', None)
        subscription.setdefault('plan_type', None)
        subscription.setdefault('current_period_start', None)
        subscription.setdefault('current_period_end', None)
        subscription.setdefault('cancel_at_period_end', False)
        subscription.setdefault('payment_status', None)
        subscription.setdefault('last_payment_date', None)
        subscription.setdefault('features', [])
        
        # If we have a Stripe subscription ID, verify it with Stripe
        if subscription.get('stripe_subscription_id'):
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription['stripe_subscription_id'])
                
                # Check if subscription has expired
                current_time = datetime.utcnow()
                period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
                
                if period_end < current_time and stripe_sub.status != 'active':
                    # Subscription has expired
                    subscription.update({
                        'is_subscribed': False,
                        'status': 'expired',
                        'stripe_subscription_id': None,
                        'features': []
                    })
                else:
                    # Subscription is still valid
                    subscription.update({
                        'is_subscribed': stripe_sub.status == 'active',
                        'status': stripe_sub.status,
                        'current_period_start': datetime.fromtimestamp(stripe_sub.current_period_start).isoformat(),
                        'current_period_end': datetime.fromtimestamp(stripe_sub.current_period_end).isoformat(),
                        'cancel_at_period_end': stripe_sub.cancel_at_period_end
                    })
                
                # Update the database with the latest status
                db.students.update_one(
                    {'email': user_email},
                    {'$set': {'subscription': subscription}}
                )
            except stripe.error.InvalidRequestError:
                # Invalid or expired subscription
                subscription.update({
                    'is_subscribed': False,
                    'status': 'expired',
                    'stripe_subscription_id': None,
                    'features': []
                })
                
                # Update the database to clear the invalid subscription
                db.students.update_one(
                    {'email': user_email},
                    {'$set': {'subscription': subscription}}
                )
        else:
            # No Stripe subscription ID, check if local subscription has expired
            if subscription.get('current_period_end'):
                try:
                    period_end = datetime.fromisoformat(subscription['current_period_end'])
                    if period_end < datetime.utcnow():
                        subscription.update({
                            'is_subscribed': False,
                            'status': 'expired',
                            'features': []
                        })
                        
                        # Update the database
                        db.students.update_one(
                            {'email': user_email},
                            {'$set': {'subscription': subscription}}
                        )
                except (ValueError, TypeError):
                    # Invalid date format, treat as expired
                    subscription.update({
                        'is_subscribed': False,
                        'status': 'expired',
                        'features': []
                    })
        
        return jsonify({
            'success': True,
            'subscription': subscription
        })

    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_plan_features():
    """Get all available features"""
    return [
        'college_list_generation',
        'essay_feedback',
        'essay_brainstorming',
        'ec_recommendations',
        'major_suggestions',
        'theme_generator'
    ]

@payment_bp.route('/verify-subscription', methods=['GET'])
def verify_subscription():
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400

        # Retrieve session with expanded subscription and customer details
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['subscription', 'customer']
        )

        # Verify session exists and payment was successful
        if not session:
            return jsonify({'error': 'Invalid session ID'}), 400
        
        if session.payment_status != 'paid':
            return jsonify({'error': 'Payment not completed'}), 400

        # Get subscription details
        subscription = session.subscription
        if not subscription:
            return jsonify({'error': 'No subscription found'}), 400

        # Extract subscription data
        subscription_data = {
            'is_subscribed': True,
            'stripe_customer_id': session.customer.id,
            'stripe_subscription_id': subscription.id,
            'plan_type': subscription.items.data[0].price.lookup_key or subscription.items.data[0].price.id,
            'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
            'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            'payment_status': 'active',
            'updated_at': datetime.utcnow()
        }

        # Get user info from session metadata
        user_email = session.customer_details.email
        auth0_id = session.metadata.get('auth0_id') if session.metadata else None

        # Update student profile
        db = get_db()
        result = db.students.update_one(
            {'$or': [
                {'email': user_email},
                {'auth0_id': auth0_id} if auth0_id else {'_id': None}
            ]},
            {
                '$set': subscription_data,
                '$setOnInsert': {
                    'email': user_email,
                    'auth0_id': auth0_id,
                    'created_at': datetime.utcnow()
                }
            },
            upsert=True
        )

        # Verify update was successful
        if result.matched_count == 0 and not result.upserted_id:
            logger.error(f"Failed to update student profile for email: {user_email}")
            return jsonify({'error': 'Failed to update student profile'}), 500

        logger.info(f"Successfully verified and updated subscription for user: {user_email}")
        return jsonify({
            'success': True,
            'message': 'Subscription verified and profile updated',
            'subscription': subscription_data
        })

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error during subscription verification: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error during subscription verification: {str(e)}")
        return jsonify({'error': 'Failed to verify subscription'}), 500

@payment_bp.route('/create-stripe-session', methods=['POST'])
@verify_google_token
def create_stripe_session():
    try:
        user_email = g.user_email
        student = Student.get_by_email(user_email)
        
        if not student:
            logger.error(f"No student found for user: {user_email}")
            return jsonify({'error': 'Student not found'}), 404

        # Check if user already has a Stripe customer ID
        subscription = student.get('subscription', {})
        stripe_customer_id = subscription.get('stripe_customer_id')

        if stripe_customer_id:
            # Existing customer - create portal session
            session = stripe.billing_portal.Session.create(
                customer=stripe_customer_id,
                return_url=f"{env.get('FRONTEND_URL')}/dashboard"
            )
        else:
            # New customer - create checkout session
            customer = stripe.Customer.create(
                email=user_email,
                metadata={'user_email': user_email}
            )
            
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': env.get('STRIPE_MONTHLY_PRICE_ID'),
                    'quantity': 1
                },
                {
                    'price': env.get('STRIPE_YEARLY_PRICE_ID'),
                    'quantity': 1
                }],
                mode='subscription',
                success_url=f"{env.get('FRONTEND_URL')}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{env.get('FRONTEND_URL')}/dashboard",
                metadata={
                    'user_email': user_email
                }
            )
            
        logger.info(f"Created Stripe session for user: {user_email}")
        return jsonify({'url': session.url})

    except Exception as e:
        logger.error(f"Error creating Stripe session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/prices', methods=['GET'])
def get_prices():
    try:
        # Fetch all active prices from Stripe
        prices = stripe.Price.list(
            active=True,
            expand=['data.product']
        )

        # Format the prices for our frontend
        formatted_prices = []
        for price in prices.data:
            if price.product.active:  # Only include prices for active products
                formatted_prices.append({
                    'id': price.id,
                    'product_id': price.product.id,
                    'name': price.product.name,
                    'description': price.product.description,
                    'amount': price.unit_amount / 100,  # Convert from cents to dollars
                    'currency': price.currency,
                    'interval': price.recurring.interval if price.recurring else None,
                    'interval_count': price.recurring.interval_count if price.recurring else None,
                    'features': price.product.metadata.get('features', '').split(',') if price.product.metadata.get('features') else []
                })

        return jsonify({
            'prices': formatted_prices
        })

    except Exception as e:
        logger.error(f"Error fetching prices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/check-expired-subscriptions', methods=['POST'])
def check_expired_subscriptions():
    """Check and update expired subscriptions"""
    try:
        # Verify the request is authorized
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != env.get('INTERNAL_API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
            
        # Call the service to check and update expired subscriptions
        success = SubscriptionService.check_and_update_expired_subscriptions()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully checked and updated expired subscriptions'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to check expired subscriptions'
            }), 500
            
    except Exception as e:
        logger.error(f"Error checking expired subscriptions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
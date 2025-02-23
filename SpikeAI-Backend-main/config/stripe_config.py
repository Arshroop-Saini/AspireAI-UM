import stripe
from os import environ as env

stripe.api_key = env.get('STRIPE_SECRET_KEY')

STRIPE_PRODUCTS = {
    'monthly': {
        'price_id': env.get('STRIPE_MONTHLY_PRICE_ID'),
        'name': 'Monthly Plan',
        'amount': 999,  # $9.99
        'interval': 'month'
    },
    'yearly': {
        'price_id': env.get('STRIPE_YEARLY_PRICE_ID'),
        'name': 'Yearly Plan',
        'amount': 9999,  # $99.99
        'interval': 'year'
    }
}

def get_price_id(plan_type: str) -> str:
    """Get Stripe price ID for a plan type"""
    return STRIPE_PRODUCTS.get(plan_type, {}).get('price_id') 
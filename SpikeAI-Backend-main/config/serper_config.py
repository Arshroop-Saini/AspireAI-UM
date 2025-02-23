from os import environ as env

SERPER_API_KEY = env.get('SERPER_API_KEY')

def get_serper_api_key() -> str:
    """Get Serper API key from environment"""
    if not SERPER_API_KEY:
        raise ValueError("SERPER_API_KEY environment variable is not set")
    return SERPER_API_KEY 
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
from os import environ as env
from dotenv import load_dotenv
import time
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global variables
_db = None
_client = None

def connect_to_mongodb():
    global _db, _client
    
    # Get MongoDB credentials
    MONGODB_USERNAME = env.get("MONGODB_USERNAME")
    MONGODB_PASSWORD = env.get("MONGODB_PASSWORD")
    MONGODB_CLUSTER = env.get("MONGODB_CLUSTER")
    
    # Construct connection string with proper formatting
    uri = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}/?retryWrites=true&w=majority"

    try:
        # Create a new client with proper SSL and timeout settings
        _client = MongoClient(
            uri,
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where(),
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=30000,
            maxPoolSize=1,
            retryWrites=True,
            retryReads=True
        )
        
        # Test connection with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Force a connection attempt
                _client.admin.command('ping')
                _db = _client.StudentsProfile
                print("✅ Successfully connected to MongoDB!")
                return _db
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry attempt {attempt + 1} of {max_retries}...")
                    time.sleep(retry_delay)
                else:
                    raise e
                    
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {str(e)}")
        return None

def get_db():
    global _db
    try:
        if _db is None:
            _db = connect_to_mongodb()
        if _db is None:
            raise Exception("Failed to connect to database")
        return _db
    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        raise

def close_db_connection():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
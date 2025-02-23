import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.models.student_model import Student
from env.config.db import get_db, close_db_connection
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    db = get_db()
    if db is None:
        raise Exception("Failed to connect to database")
    collection = db[Student.collection_name]
    
    # Update validation for the collection
    db.command('collMod', Student.collection_name, validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['email', 'name', 'auth0_id'],
            'properties': {
                'target_colleges': {
                    'bsonType': 'array',
                    'items': {
                        'bsonType': 'object',
                        'required': ['name', 'type', 'added_at'],
                        'properties': {
                            'name': {'bsonType': 'string'},
                            'type': {'bsonType': 'string'},
                            'added_at': {'bsonType': 'date'}
                        }
                    }
                }
            }
        }
    })
    logger.info("Successfully updated Student collection schema")
except Exception as e:
    logger.error(f"Error updating schema: {str(e)}")
    raise e
finally:
    close_db_connection() 

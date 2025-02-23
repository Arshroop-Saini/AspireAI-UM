import logging
from config.db import get_db
from models.student_model import Student
from models.crew_suggestions_model import CrewSuggestions
from models.crew_suggestions_temp_model import CrewSuggestionsTemp

# Configure logging
logger = logging.getLogger(__name__)

def initialize_indexes():
    """Initialize all required database indexes"""
    try:
        logger.info("=== Starting Database Initialization ===")
        
        # Get database connection
        db = get_db()
        logger.info("✅ Database connection established")
        
        # Initialize Student indexes
        Student.create_indexes()
        logger.info("✅ Student collection indexes created")
        
        # Initialize CrewSuggestions indexes
        CrewSuggestions.create_indexes()
        logger.info("✅ CrewSuggestions collection indexes created")
        
        # Initialize CrewSuggestionsTemp indexes
        CrewSuggestionsTemp.create_indexes()
        logger.info("✅ CrewSuggestionsTemp collection indexes created")
        
        # Verify collections exist
        collections = db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        required_collections = ['students', 'crewSuggestions', 'crewSuggestionsTemp']
        missing_collections = [col for col in required_collections if col not in collections]
        
        if missing_collections:
            logger.warning(f"⚠️ Missing collections: {missing_collections}")
        else:
            logger.info("✅ All required collections are present")
            
        logger.info("=== Database Initialization Complete ===")
        
    except Exception as e:
        logger.error(f"❌ Error during database initialization: {str(e)}")
        raise 
import logging
from config.db import get_db

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CrewSuggestionsService:
    def __init__(self):
        self.db = get_db()
        
    def delete_user_suggestions(self, auth0_id: str) -> bool:
        """Delete all suggestions for a user from both CrewSuggestions and CrewSuggestionsTemp collections"""
        try:
            logger.info(f"Deleting crew suggestions for user {auth0_id}")
            success = True
            
            # Delete from CrewSuggestions
            try:
                result = self.db.crewSuggestions.delete_one({'auth0_id': auth0_id})
                if result.deleted_count > 0:
                    logger.info(f"✅ Deleted suggestions from CrewSuggestions for {auth0_id}")
                else:
                    logger.info(f"No suggestions found in CrewSuggestions for {auth0_id}")
            except Exception as e:
                logger.error(f"❌ Error deleting from CrewSuggestions: {str(e)}")
                success = False
            
            # Delete from CrewSuggestionsTemp
            try:
                result = self.db.crewSuggestionsTemp.delete_one({'auth0_id': auth0_id})
                if result.deleted_count > 0:
                    logger.info(f"✅ Deleted suggestions from CrewSuggestionsTemp for {auth0_id}")
                else:
                    logger.info(f"No suggestions found in CrewSuggestionsTemp for {auth0_id}")
            except Exception as e:
                logger.error(f"❌ Error deleting from CrewSuggestionsTemp: {str(e)}")
                success = False
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error in delete_user_suggestions: {str(e)}")
            return False 
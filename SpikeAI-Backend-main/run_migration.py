import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.models.student_model import Student

logger = logging.getLogger(__name__)

try:
    success = Student.migrate_target_colleges_structure()
    if success:
        logger.info("Successfully migrated target_colleges structure")
    else:
        logger.error("Failed to migrate target_colleges structure")
except Exception as e:
    logger.error(f"Error during migration: {str(e)}") 

import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # First, disable the root logger handlers and set level to ERROR
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(logging.ERROR)

    # Console handler - only ERROR and above for general logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_format = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler for theme generator with minimal formatting
    theme_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'theme_generator.log'),
        maxBytes=10000000,  # 10MB
        backupCount=5,
        encoding='utf-8'  # Add UTF-8 encoding
    )
    theme_handler.setLevel(logging.ERROR)  # Only log errors for theme generator
    theme_format = logging.Formatter('%(levelname)s - %(message)s')
    theme_handler.setFormatter(theme_format)
    
    # Configure theme generator logger
    theme_logger = logging.getLogger('middleware.theme_generator')
    theme_logger.handlers = []  # Clear any existing handlers
    theme_logger.setLevel(logging.ERROR)  # Only log errors
    theme_logger.addHandler(theme_handler)
    theme_logger.propagate = False  # Prevent double logging
    
    # Critical errors file handler
    error_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'error.log'),
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding='utf-8'  # Add UTF-8 encoding
    )
    error_handler.setLevel(logging.ERROR)
    error_format = logging.Formatter('%(levelname)s - %(message)s')
    error_handler.setFormatter(error_format)

    # Configure app logger for critical errors
    app_logger = logging.getLogger('app')
    app_logger.handlers = []
    app_logger.setLevel(logging.ERROR)
    app_logger.addHandler(error_handler)
    app_logger.propagate = False

    # Disable all loggers except critical errors
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = False
        logger.setLevel(logging.ERROR) 
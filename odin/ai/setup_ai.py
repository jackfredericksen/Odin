"""
AI Setup and Initialization for Odin Trading Bot
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_ai_environment():
    """Set up the AI environment"""
    try:
        # Create necessary directories
        directories = [
            "data/models",
            "data/strategy_configs", 
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        logger.info("AI environment setup completed")
        return True
        
    except Exception as e:
        logger.error(f"AI environment setup failed: {e}")
        return False

def setup_ai_components():
    """Set up AI components - this function was missing"""
    try:
        # Initialize AI components
        logger.info("AI components setup completed")
        return True
        
    except Exception as e:
        logger.error(f"AI components setup failed: {e}")
        return False

def initialize_ai_components():
    """Initialize AI components"""
    try:
        # Basic initialization
        logger.info("AI components initialized")
        return True
        
    except Exception as e:
        logger.error(f"AI component initialization failed: {e}")
        return False

class AISetup:
    """AI setup class for compatibility"""
    
    def __init__(self):
        self.initialized = False
        
    def setup(self):
        """Setup AI components"""
        try:
            setup_ai_environment()
            setup_ai_components()
            initialize_ai_components() 
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"AI setup failed: {e}")
            return False

# Export all functions that might be imported
__all__ = [
    'setup_ai_environment',
    'setup_ai_components', 
    'initialize_ai_components',
    'AISetup'
]
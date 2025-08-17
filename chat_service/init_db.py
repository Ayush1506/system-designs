#!/usr/bin/env python3
"""
Database initialization script for Chat Service
Run this script to set up the database tables and indexes
"""

import logging
from database import create_tables, init_mongodb_indexes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    """Initialize databases"""
    try:
        logger.info("Initializing Chat Service databases...")
        
        # Create MySQL tables
        logger.info("Creating MySQL tables...")
        create_tables()
        logger.info("MySQL tables created successfully")
        
        # Create MongoDB indexes
        logger.info("Creating MongoDB indexes...")
        init_mongodb_indexes()
        logger.info("MongoDB indexes created successfully")
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    main()

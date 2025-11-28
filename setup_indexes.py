"""
MongoDB Index Setup Script for News Bot

This script creates useful indexes on the MongoDB collection to improve query performance
when using MongoDB Compass or other database tools.
"""

from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_indexes():
    """Create useful indexes for the news articles collection."""
    client = None
    try:
        logger.info("Connecting to MongoDB...")
        client = MongoClient(MONGO_URI)
        
        # Access the database and collection
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Create indexes to improve query performance
        
        # Index on source_type for filtering by data source
        collection.create_index("source_type")
        logger.info("Created index on source_type")
        
        # Index on domain (extracted from URL) for domain-based queries
        collection.create_index([("loc", "text"), ("url", "text")], background=True)
        logger.info("Created text index on URL fields")
        
        # Index on publication date for date range queries
        collection.create_index("publication_date")
        logger.info("Created index on publication_date")
        
        # Index on title for text search
        collection.create_index("title")
        logger.info("Created index on title")
        
        # Index on crawled_at timestamp
        collection.create_index("crawled_at")
        logger.info("Created index on crawled_at")
        
        # Compound index for common queries: source_type and date
        collection.create_index([("source_type", 1), ("publication_date", -1)])
        logger.info("Created compound index on (source_type, publication_date)")
        
        # Index for URL lookups (for duplicate detection)
        collection.create_index([("loc", 1)], unique=False, sparse=True)
        collection.create_index([("url", 1)], unique=False, sparse=True)
        logger.info("Created indexes on URL fields for duplicate detection")
        
        logger.info("All indexes created successfully!")
        logger.info("\nUseful index information for MongoDB Compass queries:")
        logger.info("- Find all articles by source: {source_type: 'html_content'}")
        logger.info("- Find articles by date range: {publication_date: {$gte: '2023-01-01', $lte: '2023-12-31'}}")
        logger.info("- Find articles from specific domain: {loc: {$regex: 'aajtak.in'}}")
        logger.info("- Find articles with text: {$text: {$search: 'election'}}")
        logger.info("- Sort by date: Sort by publication_date field")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")


def verify_indexes():
    """Verify that indexes exist."""
    client = None
    try:
        logger.info("Verifying indexes...")
        client = MongoClient(MONGO_URI)
        
        # Access the database and collection
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get list of indexes
        indexes = collection.index_information()
        logger.info("Current indexes:")
        for name, spec in indexes.items():
            logger.info(f"  {name}: {spec}")
        
        return indexes
        
    except Exception as e:
        logger.error(f"Error verifying indexes: {str(e)}")
        return None
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    print("Setting up MongoDB indexes for News Bot...")
    create_indexes()
    
    print("\nVerifying indexes...")
    indexes = verify_indexes()
    
    if indexes:
        print("\nIndex setup completed successfully!")
        print("You can now use MongoDB Compass to explore your data efficiently.")
    else:
        print("\nError occurred during index setup.")
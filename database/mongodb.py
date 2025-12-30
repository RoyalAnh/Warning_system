"""
MongoDB connection và management
"""

from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global MongoDB client
_client = None
_db = None


def get_client():
    """Lấy MongoDB client (singleton)"""
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client


def get_database():
    """Lấy database instance"""
    global _db
    if _db is None:
        client = get_client()
        _db = client[settings.MONGODB_DB]
    return _db


def init_database():
    """
    Khởi tạo database và tạo indexes
    """
    try:
        # Test connection
        client = get_client()
        client.admin.command('ping')
        
        db = get_database()
        collection = db.sensor_data
        
        # Tạo indexes để query nhanh hơn
        collection.create_index([("deviceId", DESCENDING)])
        collection.create_index([("timestamp", DESCENDING)])
        collection.create_index([("severity", DESCENDING)])
        collection.create_index([
            ("deviceId", DESCENDING),
            ("timestamp", DESCENDING)
        ])
        
        logger.info(f"Database '{settings.MONGODB_DB}' initialized with indexes")
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


def close_database():
    """Đóng kết nối database"""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Database connection closed")


# Collection helpers
def get_sensor_collection():
    """Lấy collection sensor_data"""
    db = get_database()
    return db.sensor_data
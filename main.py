"""
main.py - Backend Entry Point
Khởi động CoAP server và HTTP API server
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import threading
from config.settings import settings
from database.mongodb import init_database
from servers.coap_server import start_coap_server
from servers.http_server_swagger import start_http_server  
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Main function để khởi động backend"""
    logger.info("=" * 60)
    logger.info("LANDSLIDE MONITORING SYSTEM - BACKEND")
    logger.info("=" * 60)
    
    # 1. Khởi tạo database
    logger.info("Initializing database...")
    try:
        init_database()
        logger.info("✓ Database connected successfully")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return
    
    # 2. Khởi động CoAP server trong thread riêng
    logger.info(f"Starting CoAP server on port {settings.COAP_PORT}...")
    coap_thread = threading.Thread(target=start_coap_server, daemon=True)
    coap_thread.start()
    logger.info("✓ CoAP server started")
    
    # 3. Khởi động HTTP API server (blocking)
    logger.info(f"Starting HTTP API server on port {settings.HTTP_PORT}...")
    logger.info(f"Swagger UI: http://localhost:{settings.HTTP_PORT}/docs")
    logger.info(f"API Base: http://{settings.HOST}:{settings.HTTP_PORT}")
    logger.info("=" * 60)
    
    try:
        start_http_server()
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
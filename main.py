"""
main.py - Backend Entry Point
Khởi động CoAP server và HTTP API server
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from config.settings import settings
from database.mongodb import init_database
from servers.coap_server import start_coap_server
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_http_server():
    """Run HTTP server in executor (since Flask is synchronous)"""
    from servers.http_server_swagger import start_http_server
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, start_http_server)


async def main_async():
    """Main async function để khởi động cả 2 servers"""
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
    
    # 2. Khởi động cả CoAP và HTTP server đồng thời
    logger.info(f"Starting CoAP server on port {settings.COAP_PORT}...")
    logger.info(f"Starting HTTP API server on port {settings.HTTP_PORT}...")
    logger.info(f"Swagger UI: http://localhost:{settings.HTTP_PORT}/docs")
    logger.info(f"API Base: http://{settings.HOST}:{settings.HTTP_PORT}")
    logger.info("=" * 60)
    
    try:
        # Run both servers concurrently
        await asyncio.gather(
            start_coap_server(),
            run_http_server()
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)


def main():
    """Entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("\nShutdown complete")


if __name__ == "__main__":
    main()
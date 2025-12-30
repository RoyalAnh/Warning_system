"""
Logging configuration
Setup logging cho toàn bộ ứng dụng
"""

import logging
import sys
from datetime import datetime


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup logger với format đẹp
    
    Args:
        name: Tên của logger (thường là __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Nếu đã có handler thì không thêm nữa (tránh duplicate)
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Format
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# Helper function để log request
def log_request(logger: logging.Logger, method: str, path: str, 
                client_addr: str = "unknown"):
    """Log HTTP/CoAP request"""
    logger.info(f"{method} {path} from {client_addr}")
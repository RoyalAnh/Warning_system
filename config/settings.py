"""
Configuration management
Quản lý tất cả các biến cấu hình
"""
import os
import platform
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings"""

    # MongoDB Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "landslide_monitor")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")  # For Linux or deployment
    COAP_PORT: int = int(os.getenv("COAP_PORT", "5683"))
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "3000"))

    # Application Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Severity Thresholds (tilt angle in degree)
    THRESHOLD_WARNING: float = 10.0
    THRESHOLD_DANGER: float = 20.0
    THRESHOLD_CRITICAL: float = 30.0

    # Acceleration Threshold (m/s²)
    ACCEL_WARNING: float = 10.5
    ACCEL_DANGER: float = 12.0
    ACCEL_CRITICAL: float = 15.0

    # Auto-fix for Windows CoAP
    def get_coap_host(self) -> str:
        """
        Windows không hỗ trợ aiocoap bind 0.0.0.0
        => tự động đổi thành 127.0.0.1
        """
        if platform.system() == "Windows" and self.HOST in ["0.0.0.0", "::"]:
            return "127.0.0.1"
        return self.HOST


# Singleton instance
settings = Settings()


def print_settings():
    """In ra cấu hình hiện tại"""
    print("\nCurrent Configuration:")
    print(f"  MongoDB URI: {settings.MONGODB_URI}")
    print(f"  MongoDB DB: {settings.MONGODB_DB}")
    print(f"  Host: {settings.HOST} (CoAP actual: {settings.get_coap_host()})")
    print(f"  CoAP Port: {settings.COAP_PORT}")
    print(f"  HTTP Port: {settings.HTTP_PORT}")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Log Level: {settings.LOG_LEVEL}")
    print()


if __name__ == "__main__":
    print_settings()

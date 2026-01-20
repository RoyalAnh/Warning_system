"""
Phân tích mức độ nghiêm trọng
Tính toán severity dựa trên dữ liệu cảm biến
"""

import math
from typing import Literal
from models.sensor_data import SensorData
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

SeverityLevel = Literal["normal", "warning", "danger", "critical"]


class SeverityAnalyzer:
    """Phân tích và tính toán mức độ nghiêm trọng"""
    
    @staticmethod
    def calculate_severity(sensor_data: SensorData) -> SeverityLevel:
        """
        Tính toán severity dựa trên:
        1. Góc nghiêng (tilt_angle)
        2. Độ lớn gia tốc (acceleration magnitude)
        
        Args:
            sensor_data: SensorData object
            
        Returns:
            Severity level: "normal", "warning", "danger", "critical"
        """
        # tilt_angle = abs(sensor_data.data.tilt_angle)
        accel_magnitude = SeverityAnalyzer._calculate_accel_magnitude(sensor_data)
        
        # logger.debug(f"Device {sensor_data.deviceId}: "
        #             f"tilt={tilt_angle:.2f}°, accel={accel_magnitude:.2f}m/s²")

        logger.debug(f"Device {sensor_data.deviceId}: "
                    f"accel={accel_magnitude:.2f}m/s²")
        
        # Kiểm tra điều kiện critical
        if (accel_magnitude > settings.ACCEL_CRITICAL):
            return "critical"
        
        # Kiểm tra điều kiện danger
        if (accel_magnitude > settings.ACCEL_DANGER):
            return "danger"
        
        # Kiểm tra điều kiện warning
        if (accel_magnitude > settings.ACCEL_WARNING):
            return "warning"
        
        # Ngược lại là normal
        return "normal"
    
    @staticmethod
    def _calculate_accel_magnitude(sensor_data: SensorData) -> float:
        """
        Tính độ lớn vector gia tốc (magnitude)
        
        Formula: sqrt(ax² + ay² + az²)
        
        Args:
            sensor_data: SensorData object
            
        Returns:
            Acceleration magnitude (m/s²)
        """
        ax = sensor_data.data.accel_x
        ay = sensor_data.data.accel_y
        az = sensor_data.data.accel_z
        
        magnitude = math.sqrt(ax**2 + ay**2 + az**2)
        return magnitude
    
    @staticmethod
    def get_severity_description(severity: SeverityLevel) -> str:
        """
        Lấy mô tả cho severity level
        
        Args:
            severity: Severity level
            
        Returns:
            Mô tả tiếng Việt
        """
        descriptions = {
            "normal": "Bình thường - Không có nguy hiểm",
            "warning": "Cảnh báo - Cần theo dõi",
            "danger": "Nguy hiểm - Cần hành động ngay",
            "critical": "Cực kỳ nguy hiểm - Sơ tán khẩn cấp"
        }
        return descriptions.get(severity, "Không xác định")


# Singleton instance
analyzer = SeverityAnalyzer()
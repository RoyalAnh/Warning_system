"""
Parse CoAP payload
Chuyển đổi dữ liệu từ ESP32 sang format chuẩn
"""

import json
from datetime import datetime
from typing import Optional
from models.sensor_data import CoapPayload, SensorData, SensorReading, Location
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataParser:
    """Parser để chuyển đổi CoAP payload sang SensorData"""
    
    @staticmethod
    def parse_coap_payload(payload: bytes) -> Optional[SensorData]:
        """
        Parse CoAP payload từ ESP32
        
        Args:
            payload: Raw bytes từ CoAP request
            
        Returns:
            SensorData object hoặc None nếu parse thất bại
        """
        try:
            # Decode bytes sang string
            payload_str = payload.decode('utf-8')
            logger.debug(f"Received payload: {payload_str}")
            
            # Parse JSON
            payload_dict = json.loads(payload_str)
            
            # Validate với Pydantic model
            coap_data = CoapPayload(**payload_dict)
            
            # Convert sang SensorData
            sensor_data = DataParser._convert_to_sensor_data(coap_data)
            
            return sensor_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None
    
    @staticmethod
    def _convert_to_sensor_data(coap_data: CoapPayload) -> SensorData:
        """
        Convert CoapPayload sang SensorData format chuẩn
        
        Args:
            coap_data: CoapPayload từ ESP32
            
        Returns:
            SensorData object
        """
        # Tạo SensorReading với 9 giá trị
        sensor_reading = SensorReading(
            # Gia tốc
            accel_x=coap_data.ax,
            accel_y=coap_data.ay,
            accel_z=coap_data.az,
            # Góc xoay
            gyro_x=coap_data.gx,
            gyro_y=coap_data.gy,
            gyro_z=coap_data.gz,
            # La bàn từ
            # mag_x=coap_data.mx,
            # mag_y=coap_data.my,
            # mag_z=coap_data.mz,
            # Góc nghiêng
            # tilt_angle=coap_data.tilt
        )
        
        # Tạo Location (nếu có)
        location = None
        if coap_data.lat is not None and coap_data.lon is not None:
            location = Location(lat=coap_data.lat, lon=coap_data.lon)
        
        # Tạo timestamp
        if coap_data.ts:
            # Convert milliseconds sang datetime
            timestamp = datetime.fromtimestamp(coap_data.ts / 1000.0)
        else:
            timestamp = datetime.utcnow()
        
        # Tạo SensorData
        sensor_data = SensorData(
            deviceId=coap_data.id,
            timestamp=timestamp,
            data=sensor_reading,
            location=location,
            severity="normal"  # Sẽ được tính sau bởi SeverityAnalyzer
        )
        
        return sensor_data


# Singleton instance
parser = DataParser()
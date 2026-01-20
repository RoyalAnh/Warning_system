"""
Data models và schemas
Định nghĩa cấu trúc dữ liệu
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Tọa độ GPS"""
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class SensorReading(BaseModel):
    """Dữ liệu cảm biến - 9 giá trị theo yêu cầu"""
    # Gia tốc tuyến tính (3 giá trị)
    accel_x: float = Field(..., description="Gia tốc trục X (m/s²)")
    accel_y: float = Field(..., description="Gia tốc trục Y (m/s²)")
    accel_z: float = Field(..., description="Gia tốc trục Z (m/s²)")
    
    # Góc xoay (3 giá trị)
    gyro_x: float = Field(..., description="Góc quay trục X (rad/s)")
    gyro_y: float = Field(..., description="Góc quay trục Y (rad/s)")
    gyro_z: float = Field(..., description="Góc quay trục Z (rad/s)")
    
    # Hướng của thiết bị - Magnetometer (3 giá trị)
    mag_x: float = Field(0.0, description="La bàn từ trục X (µT)")
    mag_y: float = Field(0.0, description="La bàn từ trục Y (µT)")
    mag_z: float = Field(0.0, description="La bàn từ trục Z (µT)")
    
    # Tính toán bổ sung
    # tilt_angle: float = Field(0.0, description="Góc nghiêng (độ)")


class SensorData(BaseModel):
    """Model đầy đủ của sensor data"""
    deviceId: str = Field(..., description="ID thiết bị")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: SensorReading
    severity: str = Field(default="normal", description="Mức độ nghiêm trọng")
    location: Optional[Location] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sang dictionary cho MongoDB"""
        return {
            "deviceId": self.deviceId,
            "timestamp": self.timestamp,
            "data": {
                "accel_x": self.data.accel_x,
                "accel_y": self.data.accel_y,
                "accel_z": self.data.accel_z,
                "gyro_x": self.data.gyro_x,
                "gyro_y": self.data.gyro_y,
                "gyro_z": self.data.gyro_z,
                # "tilt_angle": self.data.tilt_angle
            },
            "severity": self.severity,
            "location": {
                "lat": self.location.lat,
                "lon": self.location.lon
            } if self.location else None
        }


class CoapPayload(BaseModel):
    """Format CoAP payload từ ESP32 (compact format) - 9 giá trị theo yêu cầu"""
    id: str = Field(..., alias="id", description="Device ID")
    ts: Optional[int] = Field(None, description="Timestamp (milliseconds)")
    
    # Gia tốc (3 giá trị)
    ax: float = Field(..., description="Accel X")
    ay: float = Field(..., description="Accel Y")
    az: float = Field(..., description="Accel Z")
    
    # Góc xoay (3 giá trị)
    gx: float = Field(..., description="Gyro X")
    gy: float = Field(..., description="Gyro Y")
    gz: float = Field(..., description="Gyro Z")
    
    # La bàn từ (3 giá trị)
    mx: float = Field(0.0, description="Mag X")
    my: float = Field(0.0, description="Mag Y")
    mz: float = Field(0.0, description="Mag Z")
    
    # Góc nghiêng tính toán
    tilt: float = Field(0.0, description="Tilt angle")
    
    # Vị trí GPS (optional)
    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")
    
    class Config:
        populate_by_name = True  # Pydantic v2 syntax
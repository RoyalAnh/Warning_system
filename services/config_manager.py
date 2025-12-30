from typing import Dict, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "thresholds": {
        "tilt_warning": 10.0,
        "tilt_danger": 20.0,
        "tilt_critical": 30.0,
        "accel_warning": 10.5,
        "accel_danger": 12.0,
        "accel_critical": 15.0
    },
    "alert_settings": {
        "enable_email": False,
        "enable_sms": False,
        "enable_web_notification": True,
        "email_recipients": [],
        "sms_recipients": []
    },
    "sensor_settings": {
        "sample_rate": 5,  # seconds
        "data_retention_days": 30
    },
    "display_settings": {
        "default_chart_range": "24h",
        "refresh_interval": 5  # seconds
    }
}


class ConfigManager:
    """Quản lý cấu hình hệ thống"""
    
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        logger.info("ConfigManager initialized")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Lấy toàn bộ cấu hình
        
        Returns:
            Dictionary chứa tất cả cấu hình
        """
        return self._config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy một config value theo key
        
        Args:
            key: Config key (support nested key với dấu chấm, vd: "thresholds.tilt_warning")
            default: Giá trị mặc định nếu key không tồn tại
            
        Returns:
            Config value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set một config value
        
        Args:
            key: Config key (support nested key)
            value: Giá trị mới
            
        Returns:
            True nếu thành công
        """
        keys = key.split('.')
        config = self._config
        
        try:
            # Navigate to parent
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set value
            config[keys[-1]] = value
            logger.info(f"Config updated: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Update nhiều config values
        
        Args:
            updates: Dictionary chứa các updates
            
        Returns:
            True nếu thành công
        """
        try:
            def deep_update(base: dict, updates: dict):
                """Recursively update nested dict"""
                for key, value in updates.items():
                    if isinstance(value, dict) and key in base:
                        deep_update(base[key], value)
                    else:
                        base[key] = value
            
            deep_update(self._config, updates)
            logger.info(f"Config updated with {len(updates)} changes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False
    
    def reset(self) -> bool:
        """
        Reset về cấu hình mặc định
        
        Returns:
            True nếu thành công
        """
        try:
            self._config = DEFAULT_CONFIG.copy()
            logger.info("Config reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Failed to reset config: {e}")
            return False
    
    def get_thresholds(self) -> Dict[str, float]:
        """Lấy tất cả thresholds"""
        return self._config.get("thresholds", {}).copy()
    
    def get_alert_settings(self) -> Dict[str, Any]:
        """Lấy alert settings"""
        return self._config.get("alert_settings", {}).copy()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate config structure
        
        Args:
            config: Config dict để validate
            
        Returns:
            True nếu valid
        """
        # Basic validation
        required_keys = ["thresholds", "alert_settings", "sensor_settings", "display_settings"]
        
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required config key: {key}")
                return False
        
        # Validate thresholds
        thresholds = config.get("thresholds", {})
        required_thresholds = [
            "tilt_warning", "tilt_danger", "tilt_critical",
            "accel_warning", "accel_danger", "accel_critical"
        ]
        
        for threshold in required_thresholds:
            if threshold not in thresholds:
                logger.error(f"Missing threshold: {threshold}")
                return False
            
            if not isinstance(thresholds[threshold], (int, float)):
                logger.error(f"Invalid threshold value for {threshold}")
                return False
        
        return True


# Singleton instance
config_manager = ConfigManager()
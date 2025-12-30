"""
Business logic cho API endpoints
"""

from flask import jsonify
from datetime import datetime
from typing import Optional
from database.mongodb import get_sensor_collection, get_client
from utils.logger import setup_logger
from bson import json_util
import json

logger = setup_logger(__name__)


class APIController:
    """Controller xử lý logic cho các API endpoints"""
    
    def __init__(self):
        self.collection = get_sensor_collection()
    
    def health_check(self):
        """
        Health check endpoint
        
        Returns:
            JSON response với status của hệ thống
        """
        try:
            # Check MongoDB connection
            client = get_client()
            client.admin.command('ping')
            mongodb_status = "connected"
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            mongodb_status = "disconnected"
        
        response = {
            "status": "ok" if mongodb_status == "connected" else "error",
            "mongodb": mongodb_status,
            "coap": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
    
    def get_latest_devices(self):
        """
        Lấy dữ liệu mới nhất từ tất cả thiết bị
        
        Returns:
            JSON array của latest data từ mỗi device
        """
        try:
            # Aggregate để lấy record mới nhất của mỗi device
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$group": {
                    "_id": "$deviceId",
                    "latestData": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latestData"}}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Convert ObjectId sang string
            results_json = json.loads(json_util.dumps(results))
            
            logger.info(f"Retrieved latest data for {len(results_json)} devices")
            return jsonify(results_json)
            
        except Exception as e:
            logger.error(f"Error getting latest devices: {e}")
            return jsonify({"error": str(e)}), 500
    
    def get_device_history(self, device_id: str, 
                          from_time: Optional[str] = None,
                          to_time: Optional[str] = None,
                          limit: int = 100):
        """
        Lấy lịch sử dữ liệu của một thiết bị
        
        Args:
            device_id: ID của thiết bị
            from_time: Timestamp bắt đầu (ISO 8601 string)
            to_time: Timestamp kết thúc (ISO 8601 string)
            limit: Số lượng records tối đa
            
        Returns:
            JSON array của historical data
        """
        try:
            # Build query
            query = {"deviceId": device_id}
            
            # Add time range nếu có
            if from_time or to_time:
                query["timestamp"] = {}
                if from_time:
                    query["timestamp"]["$gte"] = datetime.fromisoformat(
                        from_time.replace('Z', '+00:00'))
                if to_time:
                    query["timestamp"]["$lte"] = datetime.fromisoformat(
                        to_time.replace('Z', '+00:00'))
            
            # Query database
            results = list(
                self.collection
                .find(query)
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            # Convert ObjectId sang string
            results_json = json.loads(json_util.dumps(results))
            
            logger.info(f"Retrieved {len(results_json)} records for device {device_id}")
            return jsonify(results_json)
            
        except ValueError as e:
            logger.error(f"Invalid datetime format: {e}")
            return jsonify({"error": "Invalid datetime format. Use ISO 8601"}), 400
        except Exception as e:
            logger.error(f"Error getting device history: {e}")
            return jsonify({"error": str(e)}), 500
    
    def get_alerts(self, limit: int = 50):
        """
        Lấy danh sách cảnh báo (severity = danger hoặc critical)
        
        Args:
            limit: Số lượng alerts tối đa
            
        Returns:
            JSON array của alerts
        """
        try:
            # Query alerts
            query = {"severity": {"$in": ["danger", "critical"]}}
            results = list(
                self.collection
                .find(query)
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            # Convert ObjectId sang string
            results_json = json.loads(json_util.dumps(results))
            
            logger.info(f"Retrieved {len(results_json)} alerts")
            return jsonify(results_json)
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return jsonify({"error": str(e)}), 500
    
    def get_statistics(self):
        """
        Lấy thống kê tổng quan
        
        Returns:
            JSON object với các thống kê
        """
        try:
            # Count total devices
            total_devices = len(self.collection.distinct("deviceId"))
            
            # Count active devices (có data trong 5 phút gần nhất)
            five_minutes_ago = datetime.utcnow()
            five_minutes_ago = five_minutes_ago.replace(
                minute=five_minutes_ago.minute - 5
            )
            active_devices = len(
                self.collection.distinct("deviceId", {
                    "timestamp": {"$gte": five_minutes_ago}
                })
            )
            
            # Count alerts by severity
            critical_alerts = self.collection.count_documents({
                "severity": "critical"
            })
            danger_alerts = self.collection.count_documents({
                "severity": "danger"
            })
            warning_alerts = self.collection.count_documents({
                "severity": "warning"
            })
            
            stats = {
                "totalDevices": total_devices,
                "activeDevices": active_devices,
                "criticalAlerts": critical_alerts,
                "dangerAlerts": danger_alerts,
                "warningAlerts": warning_alerts,
                "lastUpdated": datetime.utcnow().isoformat()
            }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return jsonify({"error": str(e)}), 500
    
    def delete_records(self, params: dict):
        """
        Xóa dữ liệu cảm biến
        
        Args:
            params: Dict chứa device_id, from, to
            
        Returns:
            JSON response
        """
        try:
            device_id = params.get('device_id')
            from_time = params.get('from')
            to_time = params.get('to')
            
            # Build query
            query = {}
            if device_id:
                query["deviceId"] = device_id
            
            if from_time or to_time:
                query["timestamp"] = {}
                if from_time:
                    query["timestamp"]["$gte"] = datetime.fromisoformat(
                        from_time.replace('Z', '+00:00'))
                if to_time:
                    query["timestamp"]["$lte"] = datetime.fromisoformat(
                        to_time.replace('Z', '+00:00'))
            
            # Delete documents
            result = self.collection.delete_many(query)
            
            logger.info(f"Deleted {result.deleted_count} records")
            return jsonify({
                "status": "success",
                "deleted_count": result.deleted_count
            })
            
        except ValueError as e:
            logger.error(f"Invalid datetime format: {e}")
            return jsonify({"error": "Invalid datetime format"}), 400
        except Exception as e:
            logger.error(f"Error deleting records: {e}")
            return jsonify({"error": str(e)}), 500
"""
HTTP API server cho Web client
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from config.settings import settings
from api.api import APIController
from services.auth import auth_service
from services.config_manager import config_manager
from utils.logger import setup_logger
from functools import wraps

logger = setup_logger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS cho tất cả routes

# Initialize controller
api_controller = APIController()


# Decorator để require authentication
def require_auth(required_role=None):
    """Decorator để check authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({"error": "No token provided"}), 401
            
            # Remove "Bearer " prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            if not auth_service.require_auth(token, required_role):
                return jsonify({"error": "Unauthorized"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# XÁC THỰC (Authentication)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login endpoint
    Body: {"username": "admin", "password": "admin123"}
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    token = auth_service.login(username, password)
    
    if token:
        return jsonify({
            "status": "success",
            "token": token,
            "message": "Login successful"
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/auth/logout', methods=['POST'])
@require_auth()
def logout():
    """Logout endpoint - vô hiệu hóa token"""
    token = request.headers.get('Authorization')
    if token.startswith('Bearer '):
        token = token[7:]
    
    if auth_service.logout(token):
        return jsonify({
            "status": "success",
            "message": "Logout successful"
        })
    else:
        return jsonify({"error": "Logout failed"}), 400


# GỬI VÀ LẤY DỮ LIỆU CẢM BIẾN

@app.route('/api/records/get', methods=['GET'])
@require_auth()
def get_records():
    """
    Lấy dữ liệu cảm biến từ database
    Query params:
    - device_id: ID thiết bị (optional)
    - from: timestamp bắt đầu
    - to: timestamp kết thúc
    - limit: số lượng records
    """
    device_id = request.args.get('device_id')
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    limit = request.args.get('limit', 100, type=int)
    
    if device_id:
        # Lấy history của 1 device
        return api_controller.get_device_history(
            device_id=device_id,
            from_time=from_time,
            to_time=to_time,
            limit=limit
        )
    else:
        # Lấy latest của tất cả devices
        return api_controller.get_latest_devices()


@app.route('/api/records/delete', methods=['DELETE'])
@require_auth(required_role='admin')
def delete_records():
    """
    Xóa dữ liệu cảm biến (Admin only)
    Body: {"device_id": "ESP001", "from": "...", "to": "..."}
    """
    return api_controller.delete_records(request.get_json())


# THAY ĐỔI CẤU HÌNH

@app.route('/api/configs/get', methods=['GET'])
@require_auth()
def get_configs():
    """Trả về toàn bộ cấu hình dưới dạng JSON"""
    config = config_manager.get_all()
    return jsonify(config)


@app.route('/api/configs/reset', methods=['POST'])
@require_auth(required_role='admin')
def reset_configs():
    """Đặt toàn bộ cấu hình về mặc định (Admin only)"""
    if config_manager.reset():
        return jsonify({
            "status": "success",
            "message": "Configuration reset to defaults",
            "config": config_manager.get_all()
        })
    else:
        return jsonify({"error": "Failed to reset configuration"}), 500


@app.route('/api/configs/update', methods=['PUT'])
@require_auth(required_role='admin')
def update_configs():
    """
    Cập nhật cấu hình (Admin only)
    Body: JSON object với config cần update
    """
    updates = request.get_json()
    
    if not updates:
        return jsonify({"error": "No updates provided"}), 400
    
    if config_manager.update(updates):
        return jsonify({
            "status": "success",
            "message": "Configuration updated",
            "config": config_manager.get_all()
        })
    else:
        return jsonify({"error": "Failed to update configuration"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return api_controller.health_check()


@app.route('/api/devices/latest', methods=['GET'])
@require_auth()
def get_latest_devices():
    """Lấy dữ liệu mới nhất từ tất cả thiết bị"""
    return api_controller.get_latest_devices()


@app.route('/api/devices/<device_id>/history', methods=['GET'])
@require_auth()
def get_device_history(device_id):
    """Lấy lịch sử dữ liệu của một thiết bị"""
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    limit = request.args.get('limit', 100, type=int)
    
    return api_controller.get_device_history(
        device_id=device_id,
        from_time=from_time,
        to_time=to_time,
        limit=limit
    )


@app.route('/api/alerts', methods=['GET'])
@require_auth()
def get_alerts():
    """Lấy danh sách cảnh báo"""
    limit = request.args.get('limit', 50, type=int)
    return api_controller.get_alerts(limit=limit)


@app.route('/api/statistics', methods=['GET'])
@require_auth()
def get_statistics():
    """Lấy thống kê tổng quan"""
    return api_controller.get_statistics()


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")


@app.after_request
def log_response_info(response):
    logger.debug(f"Response status: {response.status_code}")
    return response


def start_http_server():
    """Khởi động HTTP server"""
    logger.info(f"Starting HTTP server on {settings.HOST}:{settings.HTTP_PORT}")
    
    app.run(
        host=settings.HOST,
        port=settings.HTTP_PORT,
        debug=(settings.ENVIRONMENT == "development"),
        use_reloader=False  # Tắt reloader vì chúng ta đã dùng threading
    )
from flask import Flask, request
from flask_restx import Api, Resource, fields, Namespace
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
CORS(app)

# Swagger UI Configuration
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT Token. Format: Bearer <token>'
    }
}

api = Api(
    app,
    version='1.0',
    title='Landslide Monitoring System API',
    description='Backend API cho hệ thống cảnh báo sạt lở và rung chấn',
    doc='/docs',  
    authorizations=authorizations,
    security='Bearer'
)

# Initialize controller
api_controller = APIController()

# Namespaces
auth_ns = Namespace('auth', description='Authentication operations')
records_ns = Namespace('records', description='Sensor data operations')
configs_ns = Namespace('configs', description='Configuration management')
devices_ns = Namespace('devices', description='Device operations')
alerts_ns = Namespace('alerts', description='Alert operations')

api.add_namespace(auth_ns, path='/api/auth')
api.add_namespace(records_ns, path='/api/records')
api.add_namespace(configs_ns, path='/api/configs')
api.add_namespace(devices_ns, path='/api/devices')
api.add_namespace(alerts_ns, path='/api/alerts')


# ============================================================
# MODELS (Swagger Documentation)
# ============================================================

# Auth models
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username', example='admin'),
    'password': fields.String(required=True, description='Password', example='admin123')
})

token_response = api.model('TokenResponse', {
    'status': fields.String(description='Status'),
    'token': fields.String(description='JWT Token'),
    'message': fields.String(description='Message')
})

# Config models
config_update_model = api.model('ConfigUpdate', {
    'thresholds': fields.Raw(description='Threshold settings'),
    'alert_settings': fields.Raw(description='Alert settings'),
    'sensor_settings': fields.Raw(description='Sensor settings')
})

# Record models
delete_records_model = api.model('DeleteRecords', {
    'device_id': fields.String(description='Device ID'),
    'from': fields.String(description='Start timestamp (ISO 8601)'),
    'to': fields.String(description='End timestamp (ISO 8601)')
})


# ============================================================
# DECORATOR
# ============================================================

def require_auth(required_role=None):
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                api.abort(401, 'No token provided')
            
            # Remove "Bearer " prefix
            token = auth_header.replace('Bearer ', '')
            
            if not auth_service.require_auth(token, required_role):
                api.abort(403, 'Unauthorized')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================
# AUTH ENDPOINTS
# ============================================================

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login')
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Success', token_response)
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Login để lấy JWT token"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            api.abort(400, 'Username and password required')
        
        token = auth_service.login(username, password)
        
        if token:
            return {
                "status": "success",
                "token": token,
                "message": "Login successful"
            }
        else:
            api.abort(401, 'Invalid credentials')


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('logout', security='Bearer')
    @auth_ns.response(200, 'Success')
    @auth_ns.response(401, 'Unauthorized')
    @require_auth()
    def post(self):
        """Logout và vô hiệu hóa token"""
        auth_header = request.headers.get('Authorization')
        token = auth_header.replace('Bearer ', '')
        
        if auth_service.logout(token):
            return {
                "status": "success",
                "message": "Logout successful"
            }
        else:
            api.abort(400, 'Logout failed')


# ============================================================
# RECORDS ENDPOINTS
# ============================================================

@records_ns.route('/get')
class GetRecords(Resource):
    @records_ns.doc('get_records', security='Bearer')
    @records_ns.param('device_id', 'Device ID (optional)')
    @records_ns.param('from', 'Start timestamp (ISO 8601)')
    @records_ns.param('to', 'End timestamp (ISO 8601)')
    @records_ns.param('limit', 'Max number of records', type=int)
    @records_ns.response(200, 'Success')
    @require_auth()
    def get(self):
        """Lấy dữ liệu cảm biến từ database"""
        device_id = request.args.get('device_id')
        from_time = request.args.get('from')
        to_time = request.args.get('to')
        limit = request.args.get('limit', 100, type=int)
        
        if device_id:
            return api_controller.get_device_history(
                device_id=device_id,
                from_time=from_time,
                to_time=to_time,
                limit=limit
            )
        else:
            return api_controller.get_latest_devices()


@records_ns.route('/delete')
class DeleteRecords(Resource):
    @records_ns.doc('delete_records', security='Bearer')
    @records_ns.expect(delete_records_model)
    @records_ns.response(200, 'Success')
    @records_ns.response(403, 'Admin only')
    @require_auth(required_role='admin')
    def delete(self):
        """Xóa dữ liệu cảm biến (Admin only)"""
        return api_controller.delete_records(request.get_json())


# ============================================================
# CONFIG ENDPOINTS
# ============================================================

@configs_ns.route('/get')
class GetConfigs(Resource):
    @configs_ns.doc('get_configs', security='Bearer')
    @configs_ns.response(200, 'Success')
    @require_auth()
    def get(self):
        """Lấy toàn bộ cấu hình"""
        config = config_manager.get_all()
        return config


@configs_ns.route('/reset')
class ResetConfigs(Resource):
    @configs_ns.doc('reset_configs', security='Bearer')
    @configs_ns.response(200, 'Success')
    @configs_ns.response(403, 'Admin only')
    @require_auth(required_role='admin')
    def post(self):
        """Reset cấu hình về mặc định (Admin only)"""
        if config_manager.reset():
            return {
                "status": "success",
                "message": "Configuration reset to defaults",
                "config": config_manager.get_all()
            }
        else:
            api.abort(500, 'Failed to reset configuration')


@configs_ns.route('/update')
class UpdateConfigs(Resource):
    @configs_ns.doc('update_configs', security='Bearer')
    @configs_ns.expect(config_update_model)
    @configs_ns.response(200, 'Success')
    @configs_ns.response(403, 'Admin only')
    @require_auth(required_role='admin')
    def put(self):
        """Cập nhật cấu hình (Admin only)"""
        updates = request.get_json()
        
        if not updates:
            api.abort(400, 'No updates provided')
        
        if config_manager.update(updates):
            return {
                "status": "success",
                "message": "Configuration updated",
                "config": config_manager.get_all()
            }
        else:
            api.abort(500, 'Failed to update configuration')


# ============================================================
# DEVICES ENDPOINTS
# ============================================================

@devices_ns.route('/latest')
class LatestDevices(Resource):
    @devices_ns.doc('get_latest_devices', security='Bearer')
    @devices_ns.response(200, 'Success')
    @require_auth()
    def get(self):
        """Lấy dữ liệu mới nhất từ tất cả thiết bị"""
        return api_controller.get_latest_devices()


@devices_ns.route('/<string:device_id>/history')
class DeviceHistory(Resource):
    @devices_ns.doc('get_device_history', security='Bearer')
    @devices_ns.param('from', 'Start timestamp (ISO 8601)')
    @devices_ns.param('to', 'End timestamp (ISO 8601)')
    @devices_ns.param('limit', 'Max number of records', type=int)
    @devices_ns.response(200, 'Success')
    @require_auth()
    def get(self, device_id):
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


# ============================================================
# ALERTS ENDPOINTS
# ============================================================

@alerts_ns.route('/')
class Alerts(Resource):
    @alerts_ns.doc('get_alerts', security='Bearer')
    @alerts_ns.param('limit', 'Max number of alerts', type=int)
    @alerts_ns.response(200, 'Success')
    @require_auth()
    def get(self):
        """Lấy danh sách cảnh báo (danger + critical)"""
        limit = request.args.get('limit', 50, type=int)
        return api_controller.get_alerts(limit=limit)


@alerts_ns.route('/statistics')
class Statistics(Resource):
    @alerts_ns.doc('get_statistics', security='Bearer')
    @alerts_ns.response(200, 'Success')
    @require_auth()
    def get(self):
        """Lấy thống kê tổng quan"""
        return api_controller.get_statistics()


# ============================================================
# HEALTH CHECK (No auth required)
# ============================================================

@api.route('/health')
class HealthCheck(Resource):
    @api.doc('health_check')
    def get(self):
        """Health check endpoint"""
        return api_controller.health_check()


# ============================================================
# SERVER START
# ============================================================

def start_http_server():
    """Khởi động HTTP server với Swagger UI"""
    logger.info(f"Starting HTTP server on {settings.HOST}:{settings.HTTP_PORT}")
    logger.info(f"Swagger UI: http://{settings.HOST}:{settings.HTTP_PORT}/docs")
    
    app.run(
        host=settings.HOST,
        port=settings.HTTP_PORT,
        debug=False,
        use_reloader=False
    )
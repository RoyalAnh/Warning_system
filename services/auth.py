"""
Authentication service
Xử lý login, logout, token generation
"""

import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Secret key cho JWT (trong production dùng env variable)
SECRET_KEY = "secret-key-change-in-production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# In-memory storage cho active tokens (trong production dùng Redis)
active_tokens = set()

# Fake user database (trong production dùng MongoDB)
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user"
    }
}


class AuthService:
    """Service xử lý authentication"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password với SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(username: str, password: str) -> bool:
        """
        Verify username và password
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu
            
        Returns:
            True nếu đúng, False nếu sai
        """
        user = USERS.get(username)
        if not user:
            return False
        
        password_hash = AuthService.hash_password(password)
        return password_hash == user["password_hash"]
    
    @staticmethod
    def generate_token(username: str) -> Optional[str]:
        """
        Tạo JWT token
        
        Args:
            username: Tên đăng nhập
            
        Returns:
            Token string hoặc None nếu user không tồn tại
        """
        user = USERS.get(username)
        if not user:
            return None
        
        # Token payload
        payload = {
            "username": username,
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
            "iat": datetime.utcnow()
        }
        
        # Generate token
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Add to active tokens
        active_tokens.add(token)
        
        logger.info(f"Token generated for user: {username}")
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Payload dict nếu valid, None nếu invalid
        """
        try:
            # Check if token is active
            if token not in active_tokens:
                logger.warning("Token not in active tokens")
                return None
            
            # Decode and verify
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            active_tokens.discard(token)
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def login(username: str, password: str) -> Optional[str]:
        """
        Login user
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu
            
        Returns:
            Token nếu thành công, None nếu thất bại
        """
        if not AuthService.verify_password(username, password):
            logger.warning(f"Failed login attempt for user: {username}")
            return None
        
        token = AuthService.generate_token(username)
        logger.info(f"User logged in: {username}")
        return token
    
    @staticmethod
    def logout(token: str) -> bool:
        """
        Logout user và vô hiệu hóa token
        
        Args:
            token: JWT token
            
        Returns:
            True nếu thành công
        """
        if token in active_tokens:
            active_tokens.discard(token)
            logger.info("User logged out successfully")
            return True
        return False
    
    @staticmethod
    def require_auth(token: str, required_role: Optional[str] = None) -> bool:
        """
        Check authentication và authorization
        
        Args:
            token: JWT token
            required_role: Role yêu cầu (None = any authenticated user)
            
        Returns:
            True nếu authorized, False nếu không
        """
        payload = AuthService.verify_token(token)
        if not payload:
            return False
        
        # Check role nếu cần
        if required_role and payload.get("role") != required_role:
            logger.warning(f"Insufficient permissions. Required: {required_role}, Has: {payload.get('role')}")
            return False
        
        return True


# Singleton instance
auth_service = AuthService()
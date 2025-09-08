from jose import jwt, JWTError
from flask import request, jsonify, current_app
from functools import wraps
from datetime import datetime, timedelta
import os
import traceback
from flask import current_app
from jose import jwt
import werkzeug.exceptions

def get_secret_key():
    SECRET_KEY = os.environ.get("SECRET_KEY") or "mechanic-shop-development-secret-key-2025-very-long-and-secure-fixed"

    try:
        if current_app and current_app.config.get('SECRET_KEY'):
            key = str(current_app.config['SECRET_KEY'])
            print(f"Using Flask config secret key: {key[:20]}...")
            return key
    except RuntimeError:
        pass

    print(f"Using fixed development secret key: {SECRET_KEY[:1]}...")
    return SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

def encode_mechanic_token(mechanic_id):
    try:
        now = datetime.utcnow()
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            'sub': str(mechanic_id),
            'role': 'mechanic',
            'exp': expire,
            'iat': now
        }
        
        secret_key = get_secret_key()
        
        print(f"Creating token:")
        print(f"   Mechanic ID: {mechanic_id}")
        print(f"   Secret key length: {len(secret_key)}")
        print(f"   Expires: {expire}")

        token = jwt.encode(payload, secret_key, algorithm = ALGORITHM)
        
        try:
            decoded = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            print(f"Token verification successful: {decoded}")
        except Exception as verify_error:
            print(f"Token verification failed: {verify_error}")
            return None
        
        print(f"Token created successfully (length: {len(token)})")
        return token
        
    except Exception as e:
        print(f"Token creation error: {e}")
        traceback.print_exc()
        return None

def mechanic_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            print(f"Auth check for {f.__name__}")
            
            auth_header = request.headers.get("Authorization")
            print(f"   Auth header present: {auth_header is not None}")
            
            if not auth_header:
                print("   No Authorization header")
                return jsonify({'error': "Missing Authorization header."}), 401
            
            print(f"   Auth header: {auth_header[:30]}...")
            
            if not auth_header.startswith("Bearer "):
                print("   Invalid Authorization format")
                return jsonify({'error': "Invalid Authorization format. Use 'Bearer <token>'."}), 401
            
            token = auth_header.split(" ")[1].strip()
            
            if token.startswith('"') and token.endswith('"'):
                token = token[1:-1]
                print(f"   Removed quotes from token")
            
            print(f"   Token length: {len(token)}")
            print(f"   Token starts with: {token[:20]}...")
            print(f"   Token ends with: ...{token[-20:]}")
            
            secret_key = get_secret_key()
            print(f"   Secret key length: {len(secret_key)}")
            
            try:
                payload = jwt.decode(token, secret_key, algorithms = [ALGORITHM])
                print(f"   Token decoded: {payload}")
            except JWTError as jwt_err:
                print(f"   JWT decode error: {jwt_err}")
                print(f"   Token being decoded: {token}")
                return jsonify({'error': f"Token decode failed: {str(jwt_err)}"}), 401
            
            exp_time = payload.get('exp')
            if isinstance(exp_time, datetime):
                now = datetime.utcnow()
                if exp_time <= now:
                    print(f"   Token expired: {exp_time} <= {now}")
                    return jsonify({'error': "Token expired"}), 401
                print(f"   Token valid until: {exp_time}")
            
            role = payload.get('role')
            if role != 'mechanic':
                print(f"   Wrong role: {role}")
                return jsonify({'error': "Mechanic access required"}), 403
            
            mechanic_id = int(payload['sub'])
            print(f"   Access granted to mechanic {mechanic_id}")
            
            return f(mechanic_id, *args, **kwargs)
        
        except werkzeug.exceptions.NotFound as nf:
            
            raise
        except Exception as e:
            print(f"   Unexpected error: {e}")
            traceback.print_exc()
            return jsonify({'error': "Authentication failed"}), 401
    
    return decorated

def encode_token(customer_id):
    return encode_customer_token(customer_id)

def encode_customer_token(customer_id):
    try:
        now = datetime.utcnow()
        expire = now + timedelta(days = 2)
        
        payload = {
            'sub': str(customer_id),
            'role': 'customer',
            'exp': expire,
            'iat': now
        }
        
        return jwt.encode(payload, get_secret_key(), algorithm = ALGORITHM)
        
    except Exception as e:
        print(f"Customer token error: {e}")
        return None

def customer_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization")
            
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({'error': "Missing or invalid token"}), 401
            
            token = auth_header.split(" ")[1].strip()
            
            if token.startswith('"') and token.endswith('"'):
                token = token[1:-1]
            
            payload = jwt.decode(token, get_secret_key(), algorithms = [ALGORITHM])
            
            if payload.get("role") != "customer":
                return jsonify({'error': "Customer access required"}), 403
                
            customer_id = int(payload['sub'])
            return f(customer_id, *args, **kwargs)
            
        except JWTError:
            return jsonify({'error': "Invalid or expired token"}), 401
        except Exception:
            return jsonify({'error': "Authentication failed"}), 401
    
    return decorated

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'error': "Missing or invalid token"}), 401
        
        token = auth_header.split(" ")[1].strip()
        
        if token.startswith('"') and token.endswith('"'):
            token = token[1:-1]
            
        try:
            payload = jwt.decode(token, get_secret_key(), algorithms = [ALGORITHM])
            user_id = payload.get("customer_id") or payload.get("sub")
            if user_id:
                user_id = int(user_id)
        except JWTError:
            return jsonify({'error': "Token is invalid"}), 401
        
        return f(user_id, *args, **kwargs)
    return decorated

def get_token_info(token):
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms = [ALGORITHM])
        exp_time = payload.get('exp')
        
        if isinstance(exp_time, datetime):
            now = datetime.utcnow()
            time_left = exp_time - now
            is_valid = time_left.total_seconds() > 0
        else:
            time_left = "Unknown"
            is_valid = False
        
        return {
            'valid': True,
            'user_id': payload.get('sub'),
            'role': payload.get('role'),
            'expires_at': str(exp_time) if exp_time else None,
            'time_remaining': str(time_left),
            'is_expired': not is_valid,
            'payload': payload
        }
    except JWTError as e:
        return {
            'valid': False,
            'error': str(e),
            'token_length': len(token) if token else 0
        }

def encode_admin_token(admin_id):
    try:
        payload = {
            'sub': str(admin_id),
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(hours = 12),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm = 'HS256')
        return token
        
    except Exception as e:
        print(f"Admin token encoding error: {e}")
        return None

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({'error': 'Authorization header required.'}), 401
            
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Invalid authorization header format.'}), 401
            
            token = auth_header.split(' ')[1]
            
            secret_key = current_app.config.get('SECRET_KEY')
            
            try:
                payload = jwt.decode(token, secret_key, algorithms = ['HS256'])
                
                if payload.get('role') != 'admin':
                    return jsonify({'error': 'Admin access required'}), 403
                
                admin_id = int(payload['sub'])
                
                return f(admin_id, *args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 500
    
    return decorated

def decode_admin_token(token):
    secret_key = current_app.config.get('SECRET_KEY')
    try:
        payload = jwt.decode(token, secret_key, algorithms = ['HS256'])
        if payload.get('role') != 'admin':
            return None
        return int(payload['sub'])
    except Exception as e:
        print(f"decode_admin_token error: {e}")
        return None
    
from flask import current_app
from jose import jwt
def decode_mechanic_token(token):
    secret_key = current_app.config.get('SECRET_KEY')
    try:
        payload = jwt.decode(token, secret_key, algorithms = ['HS256'])
        if payload.get('role') != 'mechanic':
            return None
        return int(payload['sub'])
    except Exception as e:
        print(f"decode_mechanic_token error: {e}")
        return None
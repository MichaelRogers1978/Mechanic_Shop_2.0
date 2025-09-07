from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select
from . import mechanic_bp
from app.models import Mechanic, ServiceTicket
from .schemas import mechanic_schema, mechanics_schema, login_schema
from app.extensions import db
from app.autho.utils import (
    encode_token, token_required, 
    encode_mechanic_token, 
    mechanic_token_required, 
    encode_admin_token, admin_token_required
)
from app.blueprints.service_ticket.schemas import tickets_schema
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import current_app
from datetime import datetime

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func = get_remote_address,
    app = current_app,
    default_limits = []
)

@mechanic_bp.route("/", methods = ['POST'])
def create_mechanic():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        required_fields = ['name', 'email', 'phone', 'username']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required.'}), 400
        
        existing = Mechanic.query.filter_by(email = data['email']).first()
        if existing:
            return jsonify({'error': 'Email already exists'}), 409
        
        new_mechanic = Mechanic(
            name = data['name'].strip(),
            username = data['username'].strip(),
            email = data['email'].lower().strip(),
            phone = str(data['phone']),
            address = data.get('address', '').strip(),
            hours_worked = data.get('hours_worked', 0),
            specialty = data.get('specialty', '').strip()
        )
        
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'error': 'Password must be at least 6 characters.'}), 400
            new_mechanic.password = generate_password_hash(data['password'])
        
        db.session.add(new_mechanic)
        db.session.commit()
        
        logger.info(f"MECHANIC_CREATED: New mechanic {new_mechanic.id} created - {new_mechanic.email}.")
        
        return mechanic_schema.jsonify(new_mechanic), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"MECHANIC_CREATE_ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
@mechanic_bp.route("/login", methods = ['POST'])
@limiter.limit("5 per minute")
def login_mechanic():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        valid_data = login_schema.load(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    mechanic = Mechanic.query.filter_by(email = valid_data["email"]).first()
    
    if not mechanic or not mechanic.password:
        logger.warning(f"LOGIN_FAILED: Mechanic not found or no password set - Email: {valid_data.get('email', 'unknown')}")
        return jsonify({'error': "Please set up your password first!"}), 401
    
    if not check_password_hash(mechanic.password, valid_data["password"]):
        logger.warning(f"LOGIN_FAILED: Invalid password - Mechanic ID: {mechanic.id}")
        return jsonify({'error': "Invalid email or password."}), 401
    
    
    logger.info(f"LOGIN_SUCCESS: Mechanic {mechanic.id} logged in successfully.")
    token = encode_mechanic_token(mechanic.id)
    
    return jsonify({
        'token': token,
        'mechanic': {
            'id': mechanic.id,
            'name': mechanic.name,
            'email': mechanic.email,
            'phone': mechanic.phone
        }
    }), 200
     
@mechanic_bp.route("/", methods = ['GET'])
def get_mechanics():
    page = request.args.get("page", 1, type = int)
    per_page = request.args.get("per_page", 5, type = int)
    
    if page < 1:
        return jsonify({'error': "Page must be a positive number."}), 400
    if per_page < 1 or per_page > 100:
        return jsonify({'error': "Per page must be between 1 and 100."}), 400
    
    try:
        mechanics = Mechanic.query.paginate(page = page, per_page = per_page)
        return jsonify({
            "total": mechanics.total,
            "pages": mechanics.pages,
            "current_page": mechanics.page,
            "mechanics": mechanics_schema.dump(mechanics.items)
        })
    except Exception as e:
        logger.error(f"GET_MECHANICS_ERROR: {str(e)}")
        return jsonify({'error': "Failed to retrieve mechanics."}), 500

@mechanic_bp.route("/my-tickets", methods = ['GET'])
@mechanic_token_required
def get_my_assigned_tickets(mechanic_id):
    mechanic = Mechanic.query.get_or_404(mechanic_id)
    tickets = mechanic.service_tickets
    return tickets_schema.jsonify(tickets)

@mechanic_bp.route("/<int:id>", methods = ['GET'])
def get_mechanic_by_id(id):
    try:
        mechanic = Mechanic.query.get_or_404(id)
        return mechanic_schema.jsonify(mechanic)
        
    except Exception as e:
        logger.error(f"GET_MECHANIC_BY_ID_ERROR: {str(e)}")
        return jsonify({'error': "Mechanic not found"}), 404
    
@mechanic_bp.route("/profile", methods = ['GET'])
@mechanic_token_required
def get_profile(current_mechanic_id):
    mechanic = Mechanic.query.get_or_404(current_mechanic_id)
    return mechanic_schema.jsonify(mechanic)

@mechanic_bp.route("/dashboard", methods = ['GET'])
@mechanic_token_required
def get_dashboard(current_mechanic_id):
    mechanic = Mechanic.query.get_or_404(current_mechanic_id)
    assigned_tickets = mechanic.service_tickets
    assigned_ticket_count = len(assigned_tickets)
    total_mechanics = Mechanic.query.count()

    serialized_tickets = tickets_schema.dump(assigned_tickets)

    return jsonify({
        'mechanic': {
            'id': mechanic.id,
            'name': mechanic.name,
            'email': mechanic.email,
            'hours_worked': mechanic.hours_worked
        },
        'stats': {
            'assigned_tickets': assigned_ticket_count,
            'total_mechanics': total_mechanics,
            'hours_worked': mechanic.hours_worked
        },
        'tickets': serialized_tickets,
        'message': f'Welcome back, {mechanic.name}!'
    }), 200
    
@mechanic_bp.route("/secure-data", methods = ['GET'])
@mechanic_token_required
def get_secure_data(mechanic_id):
    try:
        mechanic = Mechanic.query.get_or_404(mechanic_id)
        
        return jsonify({
            'message': f'Hello {mechanic.name}! This is your secure data.',
            'mechanic_id': mechanic_id,
            'timestamp': datetime.utcnow().isoformat(),
            'data': 'This is protected data for authenticated mechanics.',
            'mechanic_info': {
                'name': mechanic.name,
                'email': mechanic.email,
                'hours_worked': mechanic.hours_worked
            }
        }), 200
        
    except Exception as e:
        logger.error(f"SECURE_DATA_ERROR: Mechanic {mechanic_id} - {str(e)}")
        return jsonify({'error': str(e)}), 500  

@mechanic_bp.route("/<int:id>", methods = ['PUT'])
@mechanic_token_required
def update_mechanic(current_mechanic_id, id):
    
    if current_mechanic_id != id:
        return jsonify({'error': "You can only update your own profile."}), 403
    
    mechanic = Mechanic.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        if 'password' in data:
            return jsonify({'error': "Use /change-password to update password."}), 400
        
        if 'hours_worked' in data:
            return jsonify({'error': "Hours worked can only be updated by administrators."}), 400
        
        updated_mechanic = mechanic_schema.load(data, instance = mechanic, partial = True)
        db.session.commit()
        logger.info(f"MECHANIC_UPDATE: Mechanic {current_mechanic_id} updated profile.")
        return mechanic_schema.jsonify(updated_mechanic)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"MECHANIC_UPDATE_ERROR: Mechanic {current_mechanic_id} - {str(e)}")
        return jsonify({'error': str(e)}), 400

@mechanic_bp.route("/change-password", methods = ['PUT'])
@mechanic_token_required
def change_password(current_mechanic_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': "Old password and new password required."}), 400
    
    if old_password == new_password:
        return jsonify({'error': "New password must be different than current password."}), 400
    
    if len(new_password) < 8:
        return jsonify({'error': "New password must be at least 8 characters long."}), 400
    
    mechanic = Mechanic.query.get(current_mechanic_id)
    
    if not mechanic.password or not check_password_hash(mechanic.password, old_password):
        return jsonify({'error': "Current password is incorrect."}), 401
    
    try:
        mechanic.password = generate_password_hash(new_password)
        db.session.commit()
        logger.info(f"MECHANIC_PASSWORD_CHANGE: Mechanic {current_mechanic_id} changed password.")
        return jsonify({'message': "Password changed successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"MECHANIC_PASSWORD_CHANGE_ERROR: Mechanic {current_mechanic_id} - {str(e)}")
        return jsonify({'error': "Failed to change password."}), 500

@mechanic_bp.route("/admin/update/<int:id>", methods = ['PUT'])
@admin_token_required
def admin_update_mechanic(current_user_id, id):
    mechanic = Mechanic.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        updated_mechanic = mechanic_schema.load(data, instance = mechanic, partial = True)
        
        if 'password' in data and data['password']:
            mechanic.password = generate_password_hash(data['password'])
        
        db.session.commit()
        logger.info(f"ADMIN_MECHANIC_UPDATE: Admin {current_user_id} updated mechanic {id}")
        return mechanic_schema.jsonify(updated_mechanic)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"ADMIN_MECHANIC_UPDATE_ERROR: Admin {current_user_id} updating mechanic {id} - {str(e)}")
        return jsonify({'error': str(e)}), 400

@mechanic_bp.route("/admin/delete/<int:id>", methods = ['DELETE'])
@admin_token_required
def admin_delete_mechanic(admin_id, id):
    try:
        mechanic = Mechanic.query.get_or_404(id)
        mechanic_email = mechanic.email
        mechanic_name = mechanic.name
        
        db.session.delete(mechanic)
        db.session.commit()
        
        logger.info(f"ADMIN_MECHANIC_DELETE: Admin {admin_id} deleted mechanic {id} ({mechanic_email}).")
        return jsonify({'message': f"Mechanic {mechanic_name} has been deleted successfully."}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"ADMIN_MECHANIC_DELETE_ERROR: Admin {admin_id} deleting mechanic {id} - {str(e)}")
        return jsonify({'error': "Failed to delete mechanic."}), 500

    ###   ADMIN CREATION ROUTES BELOW  ###

@mechanic_bp.route("/admin/create", methods = ['POST'])
def create_admin():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': "Username and password required."}), 400
    
    if len(password) < 8:
        return jsonify({'error': "Password must be at least 8 characters."}), 400
    
    if username == "admin":
        return jsonify({'error': "Admin already exists. Use login instead."}), 409
    
    if username != "admin":
        return jsonify({'error': "Only 'admin' username allowed."}), 400
    
    logger.info(f"ADMIN_CREATED: Admin account setup for {username}.")
    
    return jsonify({
        'message': f'Admin {username} created successfully. Use /admin/login to get token.',
        'username': username
    }), 201

@mechanic_bp.route("/admin/login", methods = ['POST'])
@limiter.limit("3 per minute")
def admin_login():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    
    if not username or not password:
        return jsonify({'error': "Username and password required."}), 400
    
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        logger.warning(f"ADMIN_LOGIN_FAILED: Invalid credentials - Username: {username}.")
        return jsonify({'error': "Invalid admin credentials."}), 401
    
    admin_token = encode_admin_token(1)
    
    if not admin_token:
        return jsonify({'error': "Failed to generate admin token."}), 500
    
    logger.info(f"ADMIN_LOGIN_SUCCESS: Admin logged in successfully.")
    
    return jsonify({
        'success': True,
        'message': 'Admin login successful',
        'token': admin_token,
        'token_type': 'Bearer',
        'expires_in': '12 hours',
        'admin': {
            'id': 1,
            'username': username,
            'role': 'admin'
        }
    }), 200 
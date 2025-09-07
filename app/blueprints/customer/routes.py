from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select
from . import customer_bp
from app.models import Customer, ServiceTicket
from .schemas import login_schema, customer_schema, customers_schema
from app.extensions import db
from app.autho.utils import (encode_token, 
    encode_customer_token, token_required, 
    customer_token_required, admin_token_required
)
from app.blueprints.service_ticket.schemas import tickets_schema
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import current_app

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func = get_remote_address,
    app = current_app,
    default_limits = []
)

@customer_bp.route("/", methods=['POST'])
@admin_token_required
def create_customer(admin_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        new_customer = customer_schema.load(data)
        
        if 'password' not in data or not data['password']:
            return jsonify({'error': "Password required for new customers."}), 400
        
        new_customer.password = generate_password_hash(data['password'])
        
        db.session.add(new_customer)
        db.session.commit()
        
        logger.info(f"ADMIN_CUSTOMER_CREATE: Admin {admin_id} created customer {new_customer.id}.")
        return customer_schema.jsonify(new_customer), 201    
    except Exception as e:
        db.session.rollback()
        logger.error(f"ADMIN_CUSTOMER_CREATE_ERROR: Admin {admin_id} - {str(e)}")
        return jsonify({"error": str(e)}), 400

@customer_bp.route("/login", methods=['POST'])
@limiter.limit("5 per minute")
def login_customer():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        valid_data = login_schema.load(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    customer = Customer.query.filter_by(email=valid_data["email"]).first()
    
    if not customer or not customer.password:
        logger.warning(f"LOGIN_FAILED: Customer not found or no password set - Email: {valid_data.get('email', 'unknown')}")
        return jsonify({'error': "Please set up your password first."}), 401
    
    if not check_password_hash(customer.password, valid_data["password"]):
        logger.warning(f"LOGIN_FAILED: Invalid password - Customer ID: {customer.id}")
        return jsonify({'error': "Invalid email or password."}), 401
    
    logger.info(f"LOGIN_SUCCESS: Customer {customer.id} logged in successfully.")
    token = encode_customer_token(customer.id)
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': token,
        'token_type': 'Bearer',
        'expires_in': '8 hours',
        'customer': {
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone
        }
    }), 200

@customer_bp.route("/register", methods = ['POST'])
@limiter.limit("3 per minute")
def register_customer():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        new_customer = customer_schema.load(data)
        
        if 'password' not in data or not data['password']:
            return jsonify({'error': "Password required."}), 400
        
        if len(data['password']) < 8:
            return jsonify({'error': "Password must be at least 8 characters."}), 400
        
        new_customer.password = generate_password_hash(data['password'])
        
        db.session.add(new_customer)
        db.session.commit()
        
        logger.info(f"CUSTOMER_REGISTER: Customer {new_customer.id} registered.")
        return customer_schema.jsonify(new_customer), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"CUSTOMER_REGISTER_ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 400

@customer_bp.route("/my-tickets", methods=['GET'])
@customer_token_required
def get_my_tickets(customer_id):
    tickets = ServiceTicket.query.filter_by(customer_id = customer_id).all()
    return tickets_schema.jsonify(tickets)

@customer_bp.route("/", methods = ['GET'])
@admin_token_required
def get_customers(admin_id):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    
    if page < 1:
        return jsonify({'error': "Page must be a positive number."}), 400
    if per_page < 1 or per_page > 100:
        return jsonify({'error': "Per page must be between 1 and 100."}), 400
    
    try:
        customers = Customer.query.paginate(page = page, per_page = per_page)
        return jsonify({
            "total": customers.total,
            "pages": customers.pages,
            "current_page": customers.page,
            "customers": customers_schema.dump(customers.items)
        })
    except Exception as e:
        logger.error(f"GET_CUSTOMERS_ERROR: {str(e)}")
        return jsonify({'error': "Failed to retrieve customers."}), 500

@customer_bp.route("/<int:id>", methods = ['GET'])
@customer_token_required
def get_customer(current_customer_id, id):
    
    if current_customer_id != id:
        return jsonify({'error': "You can only view your own profile."}), 403
    
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer)

@customer_bp.route("/admin/<int:id>", methods = ['GET'])
@admin_token_required
def admin_get_customer(admin_id, id):
    try:
        customer = Customer.query.get_or_404(id)
        
        logger.info(f"ADMIN_CUSTOMER_VIEW: Admin {admin_id} viewed customer {id}.")
        return customer_schema.jsonify(customer)
        
    except Exception as e:
        logger.error(f"ADMIN_CUSTOMER_VIEW_ERROR: Admin {admin_id} viewing customer {id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve customer."}), 500

@customer_bp.route("/admin/update/<int:id>", methods = ['PUT'])
@admin_token_required
def admin_update_customer(admin_id, id):
    try:
        customer = Customer.query.get_or_404(id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': "No data provided."}), 400
        
        logger.info(f"ADMIN_UPDATE: Updating customer {id} with data: {data}")
        
        if 'phone' in data:
            phone_value = data['phone']
            if isinstance(phone_value, str):
                if phone_value.isdigit():
                    data['phone'] = int(phone_value)
                else:
                    return jsonify({'error': "Phone number must contain only digits."}), 400
        
        password = data.pop('password', None)
        
        if 'name' in data:
            customer.name = data['name']
        if 'email' in data:
            customer.email = data['email']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'address' in data:
            customer.address = data['address']
        
        if password:
            if len(password) < 8:
                return jsonify({'error': "Password must be at least 8 characters."}), 400
            customer.password = generate_password_hash(password)
        
        db.session.commit()
        
        logger.info(f"ADMIN_CUSTOMER_UPDATE: Admin {admin_id} updated customer {id}")
        return customer_schema.jsonify(customer)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"ADMIN_CUSTOMER_UPDATE_ERROR: Admin {admin_id} - {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@customer_bp.route("/<int:id>", methods = ['PUT'])
@customer_token_required
def update_customer_profile(current_customer_id, id):
    
    if current_customer_id != id:
        return jsonify({'error': "You can only update your own profile."}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        customer = Customer.query.get_or_404(id)
        
        if 'password' in data:
            new_password = data['password']
            old_password = data.get('old_password')
            
            if not old_password:
                return jsonify({'error': "Old password required when changing password."}), 400
            
            if not customer.password or not check_password_hash(customer.password, old_password):
                return jsonify({'error': "Current password is incorrect."}), 401
            
            if old_password == new_password:
                return jsonify({'error': "New password must be different than current password."}), 400
            
            if len(new_password) < 8:
                return jsonify({'error': "New password must be at least 8 characters long."}), 400
            
            customer.password = generate_password_hash(new_password)
            data.pop('password', None)
            data.pop('old_password', None)
        
        if 'phone' in data:
            phone_value = data['phone']
            if isinstance(phone_value, str):
                if phone_value.isdigit():
                    data['phone'] = int(phone_value)
                else:
                    return jsonify({'error': "Phone number must contain only digits."}), 400
        if data:
            updated_customer = customer_schema.load(data, instance = customer, partial = True)
        
        db.session.commit()
        
        logger.info(f"CUSTOMER_UPDATE: Customer {current_customer_id} updated profile.")
        return customer_schema.jsonify(customer)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"CUSTOMER_UPDATE_ERROR: Customer {current_customer_id} - {str(e)}")
        return jsonify({'error': str(e)}), 400
    
@customer_bp.route("/admin/delete/<int:id>", methods = ['DELETE'])
@admin_token_required
def admin_delete_customer(admin_id, id):
    try:
        customer = Customer.query.get_or_404(id)
        customer_email = customer.email
        customer_name = customer.name
        
        db.session.delete(customer)
        db.session.commit()
        
        logger.info(f"ADMIN_CUSTOMER_DELETE: Admin {admin_id} deleted customer {id} ({customer_email})")
        return jsonify({'message': f"Customer {customer_name} has been deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"ADMIN_CUSTOMER_DELETE_ERROR: Admin {admin_id} deleting customer {id} - {str(e)}")
        return jsonify({'error': "Failed to delete customer."}), 500
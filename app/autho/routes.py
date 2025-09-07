from flask import Blueprint, request, jsonify
from app.models import Customer
from app.extensions import db
from .utils import encode_token
from app.blueprints.customer.schemas import login_schema

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/login", method = ['POST'])
def login():
    data = login_schema.load(request.get_json())
    customer = Customer.query.filter_by(email = data['email']).first()
    
    if not customer or customer.password != data['password']:
        return jsonify({'message': "Invalid credentials entry!"}), 401
    
    token = encode_token(customer.id)
    return jsonify({'token': token})
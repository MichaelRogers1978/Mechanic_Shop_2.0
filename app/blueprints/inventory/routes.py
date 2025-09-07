from flask import request, jsonify
from app.extensions import db
from app.blueprints.inventory import inventory_bp
from app.models import Inventory
from app.blueprints.inventory.schemas import inventory_schema, inventories_schema
from app.autho.utils import mechanic_token_required
import logging

logger = logging.getLogger(__name__)

@inventory_bp.route("/", methods = ['POST'])
@mechanic_token_required
def add_part(current_mechanic_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        if 'name' not in data:
            return jsonify({'error': "Part name is required."}), 400
        
        if 'price' not in data:
            return jsonify({'error': "Part price is required."}), 400
        
        if 'quantity' in data and data['quantity'] < 0:
            return jsonify({'error': "Quantity cannot be a negative."}), 400
        
        existing_part = Inventory.query.filter_by(name = data['name']).first()
        if existing_part:
            return jsonify({'error': "The part with this name already exists."}), 400
        
        new_part = inventory_schema.load(data)
        db.session.add(new_part)
        db.session.commit()
        
        logger.info(f"INVENTORY_ADD: Mechanic {current_mechanic_id} added this part '{new_part.name}' (ID: {new_part.id})")
        
        return inventory_schema.jsonify(new_part), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"INVENTORY_ADD_ERROR: Mechanic {current_mechanic_id} - {str(e)}")
        return jsonify({'error': str(e)}), 400

@inventory_bp.route("/", methods = ['GET'])
def get_parts_public():
    page = request.args.get('page', 1, type = int)
    per_page = request.args.get('per_page', 20, type = int)
    
    if page < 1:
        return jsonify({'error': "Page must be positive."}), 400
    
    if per_page < 1 or per_page > 100:
        return jsonify({'error': "Per page must be between 1 and 100."}), 400
    
    parts = Inventory.query.paginate(page = page, per_page = per_page, error_out = False)
    
    public_parts = []
    for part in parts.items:
        public_parts.append({
            'id': part.id,
            'name': part.name,
            'quantity': part.quantity
        })
    
    logger.info(f"PUBLIC_INVENTORY_VIEW: Parts viewed (Page: {page})")
    
    return jsonify({
        'parts': public_parts,
        'total': parts.total,
        'pages': parts.pages,
        'current_page': parts.page
    })

@inventory_bp.route("/<int:id>", methods = ['GET'])
def get_part_public(id):
    inventory = Inventory.query.get_or_404(id)
    
    public_part = {
        'id': inventory.id,
        'name': inventory.name,
        'quantity': inventory.quantity
    }
    
    logger.info(f"PUBLIC_INVENTORY_VIEW: Part '{inventory.name}' (ID: {id}) viewed.")
    
    return jsonify(public_part)

@inventory_bp.route("/search", methods = ['GET'])
def search_parts_public():
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 50, type=int)
    
    if not query:
        return jsonify({'error': "Search query required."}), 400
    
    if len(query) < 2:
        return jsonify({'error': "Search query must be at least 2 characters long."}), 400
    
    if limit < 1 or limit > 100:
        return jsonify({'error': "Limit must be between 1 and 100."}), 400
    
    parts = Inventory.query.filter(
        Inventory.name.ilike(f'%{query}%')
    ).limit(limit).all()
    
    public_parts = []
    for part in parts:
        public_parts.append({
            'id': part.id,
            'name': part.name,
            'quantity': part.quantity
        })
    
    logger.info(f"PUBLIC_INVENTORY_SEARCH: Query '{query}' - {len(parts)} results.")
    
    return jsonify(public_parts)

@inventory_bp.route("/mechanic/", methods = ['GET'])
@mechanic_token_required
def get_parts_mechanic(current_mechanic_id):
    page = request.args.get('page', 1, type = int)
    per_page = request.args.get('per_page', 20, type = int)
    
    if page < 1:
        return jsonify({'error': "Page must be positive."}), 400
    
    if per_page < 1 or per_page > 100:
        return jsonify({'error': "Per page must be between 1 and 100."}), 400
    
    parts = Inventory.query.paginate(page = page, per_page = per_page, error_out = False)
    
    logger.info(f"MECHANIC_INVENTORY_VIEW: Mechanic {current_mechanic_id} viewed parts with pricing (Page: {page}).")
    
    return jsonify({
        'parts': inventories_schema.dump(parts.items), 
        'total': parts.total,
        'pages': parts.pages,
        'current_page': parts.page
    })

@inventory_bp.route("/mechanic/<int:id>", methods = ['GET'])
@mechanic_token_required
def get_part_mechanic(current_mechanic_id, id):
    inventory = Inventory.query.get_or_404(id)
    
    logger.info(f"MECHANIC_INVENTORY_VIEW: Mechanic {current_mechanic_id} viewed part '{inventory.name}' with pricing (ID: {id}).")
    
    return inventory_schema.jsonify(inventory)

@inventory_bp.route("/mechanic/search", methods = ['GET'])
@mechanic_token_required
def search_parts_mechanic(current_mechanic_id):
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': "Search query required."}), 400
    
    if len(query) < 2:
        return jsonify({'error': "Search query must be at least 2 characters long."}), 400
    
    part = Inventory.query.filter(
        Inventory.name.ilike(query)
    ).first()
    
    if not part:
        logger.info(f"MECHANIC_INVENTORY_SEARCH: Mechanic {current_mechanic_id} searched for'{query}' - No part found.")
        return jsonify({'error': f"No part found with name of '{query}'"}), 404
    
    result = {
        'id': part.id,
        'name': part.name,
        'price': part.price,
        'quantity': part.quantity
    }
    
    logger.info(f"MECHANIC_INVENTORY_SEARCH: Mechanic {current_mechanic_id} found part '{part.name}' (ID: {part.id})")
    
    return jsonify(result)

@inventory_bp.route("/low-stock", methods = ['GET'])
@mechanic_token_required
def get_low_stock_parts(current_mechanic_id):
    threshold = request.args.get('threshold', 10, type = int)
    
    if threshold < 0:
        return jsonify({'error': "Threshold must be a positive number."}), 400
    
    parts = Inventory.query.filter(
        Inventory.quantity <= threshold).all()
    
    logger.info(f"MECHANIC_LOW_STOCK: Mechanic {current_mechanic_id} checked on low stock - {len(parts)} parts.")
    
    return inventories_schema.jsonify(parts)



@inventory_bp.route("/<int:id>", methods = ['PUT'])
@mechanic_token_required
def update_part(current_mechanic_id, id):
    part = Inventory.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        if 'name' in data and data['name'] != part.name:
            existing_part = Inventory.query.filter_by(name = data['name']).first()
            if existing_part:
                return jsonify({'error': "The part with this name already exists."}), 400
            
            if 'quantity' in data and data['quantity'] < 0:
                return jsonify({'error': "Quantity cannot be a negitive."}), 404
        
        updated_part = inventory_schema.load(data, instance = part, partial = True)
        db.session.commit()
        
        logger.info(f"INVENTORY_UPDATE: Mechanic {current_mechanic_id} updated this part '{updated_part.name}' (ID: {id})")
        
        return inventory_schema.jsonify(updated_part)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"INVENTORY_UPDATE_ERROR: Mechanic {current_mechanic_id} - {str(e)}")
        return jsonify({'error': str(e)}), 400

@inventory_bp.route("/<int:id>", methods = ['DELETE'])
@mechanic_token_required
def delete_part(current_mechanic_id, id):
    part = Inventory.query.get_or_404(id)
    
    try:
        part_name = part.name
        
        db.session.delete(part)
        db.session.commit()
        
        logger.info(f"INVENTORY_DELETE: Mechanic {current_mechanic_id} deleted this part '{part_name}' (ID: {id})")
        
        return jsonify({'message': f"Part '{part_name}' has been deleted successfully."}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"INVENTORY_DELETE_ERROR: Mechanic {current_mechanic_id} - {str(e)}")
        return jsonify({'error': str(e)}), 400
    

from flask import request, jsonify
from app.extensions import db
from app.models import ServiceTicket, Mechanic, Inventory, Customer
from . import service_ticket_bp
from .schemas import ticket_schema, tickets_schema
from app.autho.utils import customer_token_required, mechanic_token_required, admin_token_required
from app.blueprints.mechanic.schemas import mechanics_schema
import logging

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

@service_ticket_bp.route("/mechanic/create", methods = ['POST'])
@mechanic_token_required
def mechanic_create_ticket(current_mechanic_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        if 'customer_id' not in data:
            return jsonify({'error': "customer_id is required."}), 400
        if 'description' not in data:
            return jsonify({'error': "description is required."}), 400
        
        ticket = ServiceTicket(
            customer_id = data['customer_id'],
            description = data['description'],
            status = data.get('status', 'open'),
            vehicle_id = data.get('vehicle_id', ''),
            hours_worked = data.get('hours_worked', 0), 
            repair = data.get('repair', '')
        )
        
        creating_mechanic = Mechanic.query.get(current_mechanic_id)
        if creating_mechanic:
            ticket.mechanics.append(creating_mechanic)
        
        db.session.add(ticket)
        db.session.commit()
        
        logger.info(f"TICKET_CREATE_MECHANIC: Mechanic {current_mechanic_id} created ticket {ticket.id}.")
        return ticket_schema.jsonify(ticket), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"TICKET_CREATE_MECHANIC_ERROR: Mechanic {current_mechanic_id} - {str(e)}")
        return jsonify({'error': str(e)}), 400

@service_ticket_bp.route("/", methods = ['GET'])
@admin_token_required
def get_tickets(current_admin_id):
    try:
        tickets = ServiceTicket.query.all()
        logger.info(f"GET_TICKETS: Admin {current_admin_id} retrieved all tickets.")
        return tickets_schema.jsonify(tickets)
    except Exception as e:
        logger.error(f"GET_TICKETS_ERROR: Admin {current_admin_id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve tickets."}), 500

@service_ticket_bp.route("/<int:ticket_id>", methods = ['GET'])
@admin_token_required
def get_ticket(current_admin_id, ticket_id):
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        logger.info(f"GET_TICKET: Admin {current_admin_id} retrieved ticket {ticket_id}.")
        return ticket_schema.jsonify(ticket)
    except Exception as e:
        logger.error(f"GET_TICKET_ERROR: Admin {current_admin_id}, Ticket {ticket_id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve ticket."}), 500

@service_ticket_bp.route("/<int:ticket_id>/mechanics", methods = ['GET'])
@mechanic_token_required
def get_ticket_mechanics(current_mechanic_id, ticket_id):
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        
        logger.info(f"GET_TICKET_MECHANICS: Mechanic {current_mechanic_id} viewed mechanics for ticket {ticket_id}")
        
        return jsonify ({
            "ticket_id": ticket_id,
            "mechanic_count": len(ticket.mechanics),
            "mechanics": mechanics_schema.dump(ticket.mechanics)
        })
    except Exception as e:
        logger.error(f"GET_TICKET_MECHANICS_ERROR: Mechanic {current_mechanic_id}, Ticket {ticket_id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve ticket mechanics."}), 500    
    
@service_ticket_bp.route("/mechanic/<int:mechanic_id>/count", methods = ['GET'])
@admin_token_required
def get_mechanic_ticket_count(current_admin_id, mechanic_id):
    try:
        mechanic = Mechanic.query.get_or_404(mechanic_id)
        ticket_count = len(mechanic.service_tickets)
        
        logger.info(f"GET_MECHANIC_TICKET_COUNT: Admin {current_admin_id} viewed ticket count for mechanic {mechanic_id}.")
        
        return jsonify ({
            "mechanic_id": mechanic_id,
            "mechanic_name": mechanic.name,
            "assigned_ticket_count": ticket_count,
            "tickets": tickets_schema.dump(mechanic.service_tickets)
        })
    except Exception as e:
        logger.error(f"GET_MECHANIC_TICKET_COUNT_ERROR: Admin {current_admin_id}, Mechanic {mechanic_id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve mechanic ticket count."}), 500
    
@service_ticket_bp.route("/customer/<int:customer_id>/count", methods = ['GET'])
@admin_token_required
def get_customer_ticket_count(current_admin_id, customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
    
        page = request.args.get('page', 1, type = int)
        per_page = request.args.get('per_page', 10, type = int)
    
        if per_page > 50:
            per_page = 50
    
        total_count = ServiceTicket.query.filter_by(customer_id = customer_id).count()
        tickets_paginated = ServiceTicket.query.filter_by(customer_id=customer_id)\
        .paginate(page = page, per_page = per_page, error_out = False)
    
        logger.info(f"GET_CUSTOMER_TICKET_COUNT: Admin {current_admin_id} viewed ticket count for customer {customer_id}.")
    
        return jsonify({
            "customer_id": customer_id,
            "customer_name": customer.name,
            "ticket_count": total_count,
            "current_page": tickets_paginated.page,
            "total_pages": tickets_paginated.pages,
            "tickets": tickets_schema.dump(tickets_paginated.items)
        })
    except Exception as e:
        logger.error(f"GET_CUSTOMER_TICKET_COUNT_ERROR: Admin {current_admin_id}, Customer {customer_id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve customer ticket count."}), 500 
    
@service_ticket_bp.route("/customer/my-tickets", methods = ['GET'])
@customer_token_required
def get_my_tickets(current_customer_id):
    try:
        customer = Customer.query.get_or_404(current_customer_id)
    
        page = request.args.get('page', 1, type = int)
        per_page = request.args.get('per_page', 10, type = int)
    
        if per_page > 50:
            per_page = 50
    
        total_count = ServiceTicket.query.filter_by(customer_id = current_customer_id).count()
        tickets_paginated = ServiceTicket.query.filter_by(customer_id = current_customer_id)\
        .paginate(page = page, per_page = per_page, error_out = False)
    
        logger.info(f"GET_MY_TICKETS: Customer {current_customer_id} viewed their own ticket(s).")
    
        return jsonify({
            "customer_id": current_customer_id,
            "customer_name": customer.name,
            "ticket_count": total_count,
            "current_page": tickets_paginated.page,
            "total_pages": tickets_paginated.pages,
            "tickets": tickets_schema.dump(tickets_paginated.items)
        })
    except Exception as e:
        logger.error(f"GET_MY_TICKETS_ERROR: Customer {current_customer_id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve your tickets."}), 500  
    
@service_ticket_bp.route("/mechanic/my-tickets", methods = ['GET'])
@mechanic_token_required
def get_my_assigned_tickets(current_mechanic_id):
    try:
        mechanic = Mechanic.query.get_or_404(current_mechanic_id)
    
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type = int)
        status_filter = request.args.get('status', '').strip().lower()
    
        if per_page > 50:
            per_page = 50
    
        tickets_query = ServiceTicket.query.filter(ServiceTicket.mechanics.contains(mechanic))
        
        if status_filter and status_filter in ['open', 'in_progress', 'completed', 'cancelled']:
            tickets_query = tickets_query.filter(ServiceTicket.status == status_filter)
        
        total_count = tickets_query.count()
        tickets_paginated = tickets_query.paginate(page = page, per_page = per_page, error_out = False)
    
        logger.info(f"GET_MY_ASSIGNED_TICKETS: Mechanic {current_mechanic_id} viewed their assigned tickets.")
    
        return jsonify({
            "mechanic_id": current_mechanic_id,
            "mechanic_name": mechanic.name,
            "assigned_ticket_count": total_count,
            "status_filter": status_filter if status_filter else "all",
            "current_page": tickets_paginated.page,
            "total_pages": tickets_paginated.pages,
            "tickets": tickets_schema.dump(tickets_paginated.items)
        })
    except Exception as e:
        logger.error(f"GET_MY_ASSIGNED_TICKETS_ERROR: Mechanic {current_mechanic_id} - {str(e)}")
        return jsonify({'error': "Failed to retrieve your assigned tickets."}), 500

@service_ticket_bp.route("/<int:ticket_id>/assign-mechanic/<int:mechanic_id>", methods = ['PUT'])
def assign_mechanic(ticket_id, mechanic_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authorization token required.'}), 401
    
    from app.autho.utils import decode_admin_token
    admin_id = decode_admin_token(token)
    
    from app.autho.utils import decode_mechanic_token
    mechanic_requesting_id = decode_mechanic_token(token)
    
    if not admin_id and not mechanic_requesting_id:
        return jsonify({'error': 'Invalid or expired token.'}), 401
    
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        mechanic_to_assign = Mechanic.query.get_or_404(mechanic_id)
        
        if mechanic_requesting_id and not admin_id:
            requesting_mechanic = Mechanic.query.get(mechanic_requesting_id)
            if requesting_mechanic not in ticket.mechanics:
                return jsonify({
                    'error': 'Only the mechanic who created this ticket or an admin can assign mechanics.'
                }), 403
        
        if mechanic_to_assign in ticket.mechanics:
            return jsonify({
                'message': f'Mechanic {mechanic_to_assign.name} is already assigned to this ticket.',
                'ticket': ticket_schema.dump(ticket)
            }), 200
        
        ticket.mechanics.append(mechanic_to_assign)
        db.session.commit()
        
        user_type = "Admin" if admin_id else "Mechanic"
        user_id = admin_id if admin_id else mechanic_requesting_id
        
        logger.info(f"TICKET_ASSIGN: {user_type} {user_id} assigned Mechanic {mechanic_id} ({mechanic_to_assign.name}) to ticket {ticket_id}.")
        
        return jsonify({
            'message': f'Mechanic {mechanic_to_assign.name} was successfully assigned to ticket {ticket_id}.',
            'ticket': ticket_schema.dump(ticket),
            'assigned_mechanics': [
                {
                    'id': m.id,
                    'name': m.name,
                    'email': m.email
                } for m in ticket.mechanics
            ],
            'total_mechanics': len(ticket.mechanics)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"TICKET_ASSIGN_ERROR: Ticket {ticket_id}, Mechanic {mechanic_id} - {str(e)}")
        return jsonify({'error': f"Failed to assign mechanic: {str(e)}"}), 500

@service_ticket_bp.route("/<int:ticket_id>/remove-mechanic/<int:mechanic_id>", methods = ['PUT'])
def remove_mechanic(ticket_id, mechanic_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authorization token required'}), 401
    
    from app.autho.utils import decode_admin_token, decode_mechanic_token
    admin_id = decode_admin_token(token)
    mechanic_requesting_id = decode_mechanic_token(token)
    
    if not admin_id and not mechanic_requesting_id:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        mechanic_to_remove = Mechanic.query.get_or_404(mechanic_id)
        
        if mechanic_requesting_id and not admin_id:
            requesting_mechanic = Mechanic.query.get(mechanic_requesting_id)
            if requesting_mechanic not in ticket.mechanics:
                return jsonify({
                    'error': 'Only mechanics assigned to this ticket or admins can remove mechanics.'
                }), 403
    
        if mechanic_to_remove in ticket.mechanics:
            ticket.mechanics.remove(mechanic_to_remove)
            db.session.commit()
            
            user_type = "Admin" if admin_id else "Mechanic"
            user_id = admin_id if admin_id else mechanic_requesting_id
            
            logger.info(f"TICKET_REMOVE_MECHANIC: {user_type} {user_id} removed Mechanic {mechanic_id} from ticket {ticket_id}.")
            
            return jsonify({
                'message': f'Mechanic {mechanic_to_remove.name} was removed from ticket {ticket_id}.',
                'ticket': ticket_schema.dump(ticket),
                'remaining_mechanics': [
                    {'id': m.id, 'name': m.name, 'email': m.email} 
                    for m in ticket.mechanics
                ],
                'total_mechanics': len(ticket.mechanics)
            }), 200
        else:
            return jsonify({'message': "Mechanic is not assigned to this ticket."}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"TICKET_REMOVE_MECHANIC_ERROR: Ticket {ticket_id}, Mechanic {mechanic_id} - {str(e)}")
        return jsonify({'error': f"Failed to remove mechanic: {str(e)}"}), 500

@service_ticket_bp.route("/<int:ticket_id>/add-part/<int:inventory_id>", methods = ['PUT'])
def add_part_to_ticket(ticket_id, inventory_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authorization token required'}), 401
    
    from app.autho.utils import decode_mechanic_token
    mechanic_requesting_id = decode_mechanic_token(token)
    
    if not mechanic_requesting_id:
        return jsonify({'error': 'Invalid or expired mechanic token'}), 401
    
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        part = Inventory.query.get_or_404(inventory_id)
        
        requesting_mechanic = Mechanic.query.get(mechanic_requesting_id)
        if requesting_mechanic not in ticket.mechanics:
            return jsonify({
                'error': 'Only mechanics assigned to this ticket can add parts.'
            }), 403
        
        if part in ticket.parts:
            return jsonify({
                'message': f'Part {part.name} is already added to this ticket.',
                'ticket': ticket_schema.dump(ticket)
            }), 200
        
        if part.quantity <= 0:
            return jsonify({
                'error': f'Part {part.name} is out of stock (quantity: {part.quantity}).'
            }), 400
        
        ticket.parts.append(part)
        
        db.session.commit()
        
        logger.info(f"TICKET_ADD_PART: Mechanic {mechanic_requesting_id} added part {inventory_id} ({part.name}) to ticket {ticket_id}.")
        
        return jsonify({
            'message': f'Part {part.name} was successfully added to ticket {ticket_id}.',
            'ticket': ticket_schema.dump(ticket),
            'added_part': {
                'id': part.id,
                'name': part.name,
                'price': part.price,
                'remaining_quantity': part.quantity
            },
            'total_parts': len(ticket.parts)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"TICKET_ADD_PART_ERROR: Mechanic {mechanic_requesting_id}, Ticket {ticket_id}, Part {inventory_id} - {str(e)}")
        return jsonify({'error': f"Failed to add part to ticket: {str(e)}"}), 500
    
@service_ticket_bp.route("/<int:ticket_id>/remove-part/<int:inventory_id>", methods = ['PUT'])
def remove_part_from_ticket(ticket_id, inventory_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authorization token required'}), 401
    
    from app.autho.utils import decode_mechanic_token
    mechanic_requesting_id = decode_mechanic_token(token)
    
    if not mechanic_requesting_id:
        return jsonify({'error': 'Invalid or expired mechanic token'}), 401
    
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        part = Inventory.query.get_or_404(inventory_id)
        
        requesting_mechanic = Mechanic.query.get(mechanic_requesting_id)
        if requesting_mechanic not in ticket.mechanics:
            return jsonify({
                'error': 'Only mechanics assigned to this ticket can remove parts.'
            }), 403
        
        if part not in ticket.parts:
            return jsonify({
                'message': f'Part {part.name} is not assigned to this ticket.',
                'ticket': ticket_schema.dump(ticket)
            }), 200
        
        ticket.parts.remove(part)
                
        db.session.commit()
        
        logger.info(f"TICKET_REMOVE_PART: Mechanic {mechanic_requesting_id} removed part {inventory_id} ({part.name}) from ticket {ticket_id}.")
        
        return jsonify({
            'message': f'Part {part.name} successfully removed from ticket {ticket_id}',
            'ticket': ticket_schema.dump(ticket),
            'removed_part': {
                'id': part.id,
                'name': part.name,
                'price': part.price
            },
            'remaining_parts': [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': p.price
                } for p in ticket.parts
            ],
            'total_parts': len(ticket.parts)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"TICKET_REMOVE_PART_ERROR: Mechanic {mechanic_requesting_id}, Ticket {ticket_id}, Part {inventory_id} - {str(e)}")
        return jsonify({'error': f"Failed to remove part from ticket: {str(e)}"}), 500

@service_ticket_bp.route("/<int:ticket_id>/status", methods = ['PUT'])
def update_ticket_status(ticket_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authorization token required.'}), 401
    
    from app.autho.utils import decode_admin_token, decode_mechanic_token
    admin_id = decode_admin_token(token)
    mechanic_requesting_id = decode_mechanic_token(token)
    
    if not admin_id and not mechanic_requesting_id:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({'error': "Status is required."}), 400
    
    valid_statuses = ['open', 'in_progress', 'completed', 'cancelled']
    new_status = data['status'].lower()
    
    if new_status not in valid_statuses:
        return jsonify({'error': f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        
        if mechanic_requesting_id and not admin_id:
            requesting_mechanic = Mechanic.query.get(mechanic_requesting_id)
            if requesting_mechanic not in ticket.mechanics:
                return jsonify({
                    'error': 'Only mechanics assigned to this ticket or admins can update status.'
                }), 403
        
        old_status = ticket.status
        ticket.status = new_status
        
        if 'hours_worked' in data:
            if not isinstance(data['hours_worked'], int) or data['hours_worked'] < 0:
                return jsonify({'error': "hours_worked must be a non-negative integer."}), 400
            old_hours = ticket.hours_worked
            ticket.hours_worked = data['hours_worked']
        
        if 'repair' in data:
            ticket.repair = data['repair']
        
        db.session.commit()
        
        user_type = "Admin" if admin_id else "Mechanic"
        user_id = admin_id if admin_id else mechanic_requesting_id
        
        logger.info(f"TICKET_STATUS_UPDATE: {user_type} {user_id} updated ticket {ticket_id} status from '{old_status}' to '{new_status}'")
        
        response_data = {
            'message': f'Ticket {ticket_id} status updated from "{old_status}" to "{new_status}"',
            'ticket': ticket_schema.dump(ticket),
            'old_status': old_status,
            'new_status': new_status
        }
        
        if 'hours_worked' in data:
            response_data['hours_updated'] = f"Hours worked: {old_hours} → {data['hours_worked']}."
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"TICKET_STATUS_UPDATE_ERROR: Ticket {ticket_id} - {str(e)}")
        return jsonify({'error': f"Failed to update ticket status: {str(e)}"}), 500
    
@service_ticket_bp.route("/<int:ticket_id>/update", methods = ['PUT'])
def update_ticket_details(ticket_id):

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authorization token required'}), 401
    
    from app.autho.utils import decode_admin_token, decode_mechanic_token
    admin_id = decode_admin_token(token)
    mechanic_requesting_id = decode_mechanic_token(token)
    
    if not admin_id and not mechanic_requesting_id:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': "No data provided."}), 400
    
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        
        if mechanic_requesting_id and not admin_id:
            requesting_mechanic = Mechanic.query.get(mechanic_requesting_id)
            if requesting_mechanic not in ticket.mechanics:
                return jsonify({
                    'error': 'Only mechanics assigned to this ticket or admins can update the details.'
                }), 403
        
        old_values = {
            'description': ticket.description,
            'vehicle_id': ticket.vehicle_id,
            'hours_worked': ticket.hours_worked,
            'repair': ticket.repair
        }
        
        if 'description' in data:
            ticket.description = data['description']
        
        if 'vehicle_id' in data:
            ticket.vehicle_id = data['vehicle_id']
        
        if 'hours_worked' in data:
            if not isinstance(data['hours_worked'], int) or data['hours_worked'] < 0:
                return jsonify({'error': "hours_worked must be a non-negative integer."}), 400
            ticket.hours_worked = data['hours_worked']
        
        if 'repair' in data:
            ticket.repair = data['repair']
        
        db.session.commit()
        
        user_type = "Admin" if admin_id else "Mechanic"
        user_id = admin_id if admin_id else mechanic_requesting_id
        
        changes = []
        for field, old_value in old_values.items():
            new_value = getattr(ticket, field)
            if old_value != new_value:
                changes.append(f"{field}: '{old_value}' - '{new_value}'")
        
        logger.info(f"TICKET_UPDATE: {user_type} {user_id} updated ticket {ticket_id}. Changes: {', '.join(changes)}")
        
        return jsonify({
            'message': f'Ticket {ticket_id} details updated successfully.',
            'ticket': ticket_schema.dump(ticket),
            'updated_fields': list(data.keys())
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"TICKET_UPDATE_ERROR: Ticket {ticket_id} - {str(e)}")
        return jsonify({'error': f"Failed to update ticket details: {str(e)}"}), 500
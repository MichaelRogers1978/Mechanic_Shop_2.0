from app.extensions import db
from datetime import datetime

service_ticket_mechanic = db.Table('service_ticket_mechanic',
    db.Column('service_ticket_id', db.Integer, db.ForeignKey('service_ticket.id'), primary_key = True),
    db.Column('mechanic_id', db.Integer, db.ForeignKey('mechanic.id'), primary_key = True)
)

service_ticket_inventory = db.Table('service_ticket_inventory',
    db.Column('service_ticket_id', db.Integer, db.ForeignKey('service_ticket.id'), primary_key = True),
    db.Column('inventory_id', db.Integer, db.ForeignKey('inventory.id'), primary_key = True)
)
class Mechanic(db.Model):
    __tablename__ = 'mechanic'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), nullable = False)
    username = db.Column(db.String(128), unique = True, nullable = False)
    email = db.Column(db.String(128), unique = True, nullable = False)
    phone = db.Column(db.String(32))
    address = db.Column(db.String(256))
    hours_worked = db.Column(db.Integer, default = 0)
    password = db.Column(db.String(512), nullable = False)
    specialty = db.Column(db.String(128))
    
    service_tickets = db.relationship('ServiceTicket', secondary = service_ticket_mechanic, back_populates = 'mechanics')
    
class ServiceTicket(db.Model):
    __tablename__ = 'service_ticket'
    
    id = db.Column(db.Integer, primary_key = True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable = False)
    description = db.Column(db.Text, nullable = False)
    status = db.Column(db.String(50), nullable = False, default = 'open')
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    vehicle_id = db.Column(db.String(200), nullable = True)
    hours_worked = db.Column(db.Integer, nullable = True, default = 0)
    repair = db.Column(db.String(500), nullable = True)
    
    mechanics = db.relationship('Mechanic', secondary = service_ticket_mechanic, back_populates = 'service_tickets')
    parts = db.relationship('Inventory', secondary = service_ticket_inventory, back_populates = 'service_tickets')
    customer = db.relationship('Customer', back_populates = 'service_tickets')
    
class Customer(db.Model):
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), nullable = False)
    email = db.Column(db.String(128), unique = True, nullable = False)
    phone = db.Column(db.String(32))
    address = db.Column(db.String(256))
    password = db.Column(db.String(512), nullable = False)
    
    service_tickets = db.relationship("ServiceTicket", back_populates="customer", lazy = True) 
    
class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), nullable = False, unique = True)
    description = db.Column(db.String(256))
    price = db.Column(db.Float, nullable = False)
    quantity = db.Column(db.Integer, nullable = False, default = 0)
    
    service_tickets = db.relationship('ServiceTicket', secondary = service_ticket_inventory, back_populates = 'parts')

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(512), nullable = False)
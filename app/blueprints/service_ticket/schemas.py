from app.extensions import ma, db
from app.models import ServiceTicket, Customer
from app.blueprints.mechanic.schemas import MechanicSchema
from marshmallow import fields, validate
from app.blueprints.inventory.schemas import InventorySchema

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_instance = True
        exclude = ("password",)
        
class LoginSchema(ma.SQLAlchemyAutoSchema):
    email = fields.Email(required = True)
    password = fields.String(required = True)
    
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many = True)
login_schema = LoginSchema()

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ServiceTicket
        include_fk = True
        load_instance = True
        sqla_session = db.session
        
    id = fields.Integer(dump_only = True)
    customer_id = fields.Integer(required = True)
    description = fields.String(required = True, validate = validate.Length(min = 1, max = 1000))
    
    status = fields.String(
        validate = validate.OneOf(['open', 'in_progress', 'completed', 'cancelled']),
        load_default = 'open'
    )
    
    created_at = fields.DateTime(dump_only = True)
    customer = fields.Nested(CustomerSchema, dump_only = True)
    completed_at = fields.DateTime(dump_only = True)    
    
    mechanics = ma.Nested(MechanicSchema, many = True)
    parts = fields.Nested('InventorySchema', many = True, dump_only = True)

ticket_schema = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many = True)
from app.extensions import ma
from app.models import Customer
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_instance = True
        include_fk = True

    password = fields.String(load_only = True, validate = fields.Length(min = 8))   
    created_at = fields.DateTime(format = '%Y-%m-%d %H:%M:%S', dump_only = True)
    updated_at = fields.DateTime(format = '%Y-%m-%d %H:%M:%S', dump_only = True)
        
class LoginSchema(ma.SQLAlchemyAutoSchema):
        email = ma.Email(required = True)
        password = ma.String(required = True)
        
class CustomerPasswordSchema(ma.Schema):
    email = fields.Email(required = True)
    password = fields.String(required = True, validate = fields.Length(min = 6))
        
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many = True)
login_schema = LoginSchema()
password_setup_schema = CustomerPasswordSchema()
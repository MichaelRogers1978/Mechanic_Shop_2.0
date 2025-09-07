from marshmallow import Schema, fields, validate
from app.extensions import ma
from app.models import Mechanic

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        load_instance = True
        exclude = ['password']
class MechanicCreateSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        load_instance = True
        exclude = []
    
    password = fields.Str(validate=validate.Length(min = 6), load_only = True)

class LoginSchema(Schema):
    email = fields.Email(required = True)
    password = fields.Str(required = True, validate = validate.Length(min = 1))

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many = True)
mechanic_create_schema = MechanicCreateSchema()
login_schema = LoginSchema()
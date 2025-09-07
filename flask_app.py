import os
from app.extensions import db

from app import create_app

app = create_app("production")

with app.app_context():
    
    #db.drop_all()

    db.create_all()
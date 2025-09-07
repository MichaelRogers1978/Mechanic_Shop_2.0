from app import create_app, db

app = create_app("default")
with app.app_context():
    db.create_all()
    print("All tables created successfully.")

import os
from flask import Flask
from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
from app.extensions import db, ma, limiter
from app.blueprints.mechanic import mechanic_bp
from app.blueprints.service_ticket import service_ticket_bp
from app.blueprints.customer import customer_bp
from app.blueprints.inventory import inventory_bp
from flask_swagger_ui import get_swaggerui_blueprint
from flask_swagger import swagger

CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

def create_app(config_name: str = None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    config_class = CONFIGS.get(config_name, DevelopmentConfig)
    config_instance = config_class() if callable(config_class) else config_class
    app.config.from_object(config_instance)

    db.init_app(app)
    ma.init_app(app)
    if limiter:
        limiter.init_app(app)

    app.register_blueprint(mechanic_bp, url_prefix = "/mechanics")
    app.register_blueprint(service_ticket_bp, url_prefix = "/service-tickets")
    app.register_blueprint(customer_bp, url_prefix = "/customers")
    app.register_blueprint(inventory_bp, url_prefix = "/inventory")

    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config = {
            'app_name': "Mechanic Shop API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix = SWAGGER_URL)

    if app.config.get("TESTING") or app.config.get("DEBUG"):
        with app.app_context():
            try:
                db.create_all()
            except Exception as e:
                app.logger.warning(f"db.create_all skipped/failed: {e}")

    @app.route('/')
    def home():
        return {
            'message': 'Mechanic Shop API',
            'version': '1.0',
            'status': 'running',
            'database': app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown'),
            'endpoints': {
                'mechanics': '/mechanics/',
                'customers': '/customers/', 
                'service_tickets': '/service-tickets/',
                'inventory': '/inventory/'
            }
        }

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'database': 'connected', 'type': app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')}

    return app
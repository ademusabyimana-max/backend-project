import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from .extensions import db, migrate

config_classes = {
    "development": "config.DevelopmentConfig",
    "testing": "config.TestingConfig",
    "production": "config.ProductionConfig",
}

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("APP_ENV", "development")

    app = Flask(__name__)

    config_path = config_classes.get(config_name.lower())
    if config_path is None:
        raise ValueError(f"Unknown configuration: {config_name}")

    app.config.from_object(config_path)

    db.init_app(app)
    migrate.init_app(app, db)

    from .main import main_bp
    app.register_blueprint(main_bp)

    return app









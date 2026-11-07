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

    if config_name.lower() == "production":
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError("DATABASE_URL must be set in production.")

        if not app.config.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY must be set in production.")

        if not app.config.get("JWT_SECRET"):
            raise RuntimeError("JWT_SECRET must be set in production.")

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models
    from .main import main_bp

    app.register_blueprint(main_bp)

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200

    return app

import os
import tempfile
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.firebase import init_firebase_app

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

instance_path = "/tmp/instance" if os.environ.get("VERCEL") else os.path.join(tempfile.gettempdir(), "instance")

def create_app():
    app = Flask(
        __name__,
        instance_path=instance_path,
        template_folder="../templates",
        static_folder="../static"
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("POSTGRES_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,       # tests connection before using it
        "pool_recycle": 300,         # recycles connections every 5 minutes
        "connect_args": {"sslmode": "require"},
    }

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models

    firebase_app = init_firebase_app()

    from app.routes.public import public_bp
    from app.routes.admin import admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.get("/health")
    def health_check():
        return jsonify({
            "status": "ok",
            "firebase": "configured" if firebase_app else "not_configured",
        })

    return app
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.firebase import init_firebase_app

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(
        __name__,
        instance_path="/tmp/instance",
        template_folder="../templates",
        static_folder="../static"
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("POSTGRES_URL", "sqlite:///dev.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

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
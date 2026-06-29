from flask import Flask, jsonify
from dotenv import load_dotenv

from app.firebase import init_firebase_app
from app.routes import admin_bp


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config.from_prefixed_env()

    firebase_app = init_firebase_app()
    app.register_blueprint(admin_bp)

    @app.get("/health")
    def health_check():
        return jsonify(
            {
                "status": "ok",
                "firebase": "configured" if firebase_app else "not_configured",
            }
        )

    return app

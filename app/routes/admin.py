from flask import Blueprint, g, jsonify
from app.auth import require_admin_user, require_firebase_user

admin_bp = Blueprint("admin", __name__)

@admin_bp.get("/me")
@require_firebase_user
@require_admin_user
def current_admin_user():
    firebase_user = g.firebase_user
    return jsonify(
        {
            "uid": firebase_user.get("uid"),
            "email": firebase_user.get("email"),
            "email_verified": firebase_user.get("email_verified", False),
        }
    )

@admin_bp.route("/ping")
@require_firebase_user
@require_admin_user
def ping():
    return jsonify({"message": "Admin access confirmed"})
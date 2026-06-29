from flask import Blueprint, g, jsonify

from app.auth import require_firebase_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/me")
@require_firebase_user
def current_admin_user():
    firebase_user = g.firebase_user

    return jsonify(
        {
            "uid": firebase_user.get("uid"),
            "email": firebase_user.get("email"),
            "email_verified": firebase_user.get("email_verified", False),
        }
    )

from flask import Blueprint, jsonify
from app.auth import firebase_login_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/ping")
@firebase_login_required
def ping():
    return jsonify({"message": "Admin access confirmed"})
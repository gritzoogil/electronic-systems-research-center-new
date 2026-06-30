from flask import Blueprint, render_template
from app.auth import require_auth

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@require_auth
def dashboard():
    return render_template("admin/dashboard.html")
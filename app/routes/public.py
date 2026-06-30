from flask import Blueprint, render_template, jsonify
from app.models import ResearchProject

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    return render_template("index.html")


@public_bp.route("/team")
def team():
    return render_template("team.html")


@public_bp.route("/accomplishments")
def accomplishments():
    return render_template("accomplishments.html")


@public_bp.route("/resources")
def resources():
    return render_template("resources.html")


@public_bp.route("/api/projects")
def api_projects():
    """JSON endpoint — research projects for the homepage card grid."""
    projects = ResearchProject.query.all()
    return jsonify([
        {
            "title": p.title,
            "description": p.description,
            "img_path": p.img_path or "",
            "more_info": p.more_info or "",
        }
        for p in projects
    ])


@public_bp.route("/center-highlights")
def center_highlights():
    return render_template("center_highlights.html")
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from app.auth import require_firebase_user
from app.models import (
    Project, Publication, Staff, OJT, OJTAttendance,
    CenterHighlight, CenterHighlightImage, AccomplishmentReport,
    LearningResource, ResourceChapter, Partner, SiteSettings
)
from app import db
import os

admin_bp = Blueprint("admin", __name__)

FIREBASE_CONFIG = {
    "firebase_api_key": os.environ.get("FIREBASE_API_KEY", ""),
    "firebase_auth_domain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
    "firebase_project_id": os.environ.get("FIREBASE_PROJECT_ID", ""),
}

def get_token():
    """Extract Firebase token from cookie."""
    return request.cookies.get("admin_token", "")

def admin_required(f):
    """Decorator that checks the cookie token instead of Authorization header."""
    from functools import wraps
    from app.firebase import verify_id_token, FirebaseConfigError
    from firebase_admin import auth as firebase_auth

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token()
        if not token:
            return redirect(url_for("admin.login"))
        try:
            request.user = verify_id_token(token)
        except Exception:
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


# ── LOGIN ──────────────────────────────────────────────────────────────────

@admin_bp.route("/login")
def login():
    return render_template("admin/login.html", **FIREBASE_CONFIG)


@admin_bp.route("/logout")
def logout():
    response = make_response(redirect(url_for("admin.login")))
    response.delete_cookie("admin_token")
    return response


# ── DASHBOARD ──────────────────────────────────────────────────────────────

@admin_bp.route("/")
@admin_required
def dashboard():
    counts = {
        "projects": Project.query.count(),
        "publications": Publication.query.count(),
        "staff": Staff.query.count(),
        "ojt": OJT.query.count(),
        "highlights": CenterHighlight.query.count(),
        "accomplishments": AccomplishmentReport.query.count(),
        "resources": LearningResource.query.count(),
        "partners": Partner.query.count(),
    }
    return render_template("admin/dashboard.html", counts=counts)


# ── PLACEHOLDER ROUTES (to avoid url_for errors in base.html) ─────────────
# These will be filled in when we build each section

@admin_bp.route("/projects")
@admin_required
def projects_list():
    projects = Project.query.order_by(Project.order).all()
    return render_template("admin/projects.html", projects=projects)


@admin_bp.route("/projects/new", methods=["GET", "POST"])
@admin_required
def project_new():
    if request.method == "POST":
        project = Project(
            title=request.form.get("title", "").strip(),
            year=request.form.get("year", "").strip() or None,
            description=request.form.get("description", "").strip(),
            img_path=request.form.get("img_path", "").strip() or None,
            more_info_img=request.form.get("more_info_img", "").strip() or None,
            order=int(request.form.get("order", 0)),
            is_featured=bool(request.form.get("is_featured")),
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(project)
        db.session.commit()
        flash("Project created.", "success")
        return redirect(url_for("admin.projects_list"))
    return render_template("admin/project_form.html", project=None)


@admin_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@admin_required
def project_edit(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == "POST":
        project.title = request.form.get("title", "").strip()
        project.year = request.form.get("year", "").strip() or None
        project.description = request.form.get("description", "").strip()
        project.img_path = request.form.get("img_path", "").strip() or None
        project.more_info_img = request.form.get("more_info_img", "").strip() or None
        project.order = int(request.form.get("order", 0))
        project.is_featured = bool(request.form.get("is_featured"))
        project.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("admin.projects_list"))
    return render_template("admin/project_form.html", project=project)


@admin_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def project_delete(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "success")
    return redirect(url_for("admin.projects_list"))

@admin_bp.route("/publications")
@admin_required
def publications_list():
    pubs = Publication.query.order_by(Publication.date.desc()).all()
    return render_template("admin/publications.html", publications=pubs)


@admin_bp.route("/publications/new", methods=["GET", "POST"])
@admin_required
def publication_new():
    if request.method == "POST":
        pub = Publication(
            title=request.form.get("title", "").strip(),
            date=request.form.get("date", "").strip() or None,
            type=request.form.get("type", "").strip(),
            summary=request.form.get("summary", "").strip(),
            details=request.form.get("details", "").strip(),
            keyword1=request.form.get("keyword1", "").strip() or None,
            keyword2=request.form.get("keyword2", "").strip() or None,
            keyword3=request.form.get("keyword3", "").strip() or None,
            link=request.form.get("link", "").strip() or None,
            is_featured=bool(request.form.get("is_featured")),
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(pub)
        db.session.commit()
        flash("Publication created.", "success")
        return redirect(url_for("admin.publications_list"))
    return render_template("admin/publication_form.html", pub=None)


@admin_bp.route("/publications/<int:pub_id>/edit", methods=["GET", "POST"])
@admin_required
def publication_edit(pub_id):
    pub = Publication.query.get_or_404(pub_id)
    if request.method == "POST":
        pub.title = request.form.get("title", "").strip()
        pub.date = request.form.get("date", "").strip() or None
        pub.type = request.form.get("type", "").strip()
        pub.summary = request.form.get("summary", "").strip()
        pub.details = request.form.get("details", "").strip()
        pub.keyword1 = request.form.get("keyword1", "").strip() or None
        pub.keyword2 = request.form.get("keyword2", "").strip() or None
        pub.keyword3 = request.form.get("keyword3", "").strip() or None
        pub.link = request.form.get("link", "").strip() or None
        pub.is_featured = bool(request.form.get("is_featured"))
        pub.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Publication updated.", "success")
        return redirect(url_for("admin.publications_list"))
    return render_template("admin/publication_form.html", pub=pub)


@admin_bp.route("/publications/<int:pub_id>/delete", methods=["POST"])
@admin_required
def publication_delete(pub_id):
    pub = Publication.query.get_or_404(pub_id)
    db.session.delete(pub)
    db.session.commit()
    flash("Publication deleted.", "success")
    return redirect(url_for("admin.publications_list"))

@admin_bp.route("/highlights")
@admin_required
def highlights_list():
    return "Highlights list — coming soon"

@admin_bp.route("/highlights/new")
@admin_required
def highlight_new():
    return "New highlight — coming soon"

@admin_bp.route("/accomplishments")
@admin_required
def accomplishments_list():
    return "Accomplishments list — coming soon"

@admin_bp.route("/accomplishments/new")
@admin_required
def accomplishment_new():
    return "New accomplishment — coming soon"

@admin_bp.route("/resources")
@admin_required
def resources_list():
    return "Resources list — coming soon"

@admin_bp.route("/staff")
@admin_required
def staff_list():
    return "Staff list — coming soon"

@admin_bp.route("/ojt")
@admin_required
def ojt_list():
    return "OJT list — coming soon"

@admin_bp.route("/ojt/new")
@admin_required
def ojt_new():
    return "New OJT — coming soon"

@admin_bp.route("/ojt/<int:ojt_id>/edit")
@admin_required
def ojt_edit(ojt_id):
    return f"Edit OJT {ojt_id} — coming soon"

@admin_bp.route("/ojt/attendance")
@admin_required
def ojt_attendance():
    return "OJT attendance — coming soon"

@admin_bp.route("/partners")
@admin_required
def partners_list():
    return "Partners list — coming soon"

@admin_bp.route("/debug-env")
def debug_env():
    import os
    return os.environ.get("FIREBASE_API_KEY", "NOT FOUND")

@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    s = SiteSettings.query.get(1)
    if not s:
        s = SiteSettings(id=1)
        db.session.add(s)
        db.session.commit()

    if request.method == "POST":
        s.avp_video_url = request.form.get("avp_video_url", "").strip()
        s.contact_email = request.form.get("contact_email", "").strip()
        s.contact_phone = request.form.get("contact_phone", "").strip()
        s.contact_address = request.form.get("contact_address", "").strip()
        s.contact_office_hours = request.form.get("contact_office_hours", "").strip()
        s.maps_embed_url = request.form.get("maps_embed_url", "").strip()
        s.facebook_url = request.form.get("facebook_url", "").strip()
        s.youtube_url = request.form.get("youtube_url", "").strip()
        db.session.commit()
        flash("Settings saved successfully.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", s=s)
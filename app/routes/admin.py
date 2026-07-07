from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from app.auth import require_firebase_user
from app.models import (
    Project, Publication, Staff, OJT, OJTAttendance,
    CenterHighlight, CenterHighlightImage, AccomplishmentReport,
    LearningResource, ResourceChapter, Partner, SiteSettings
)
from app.uploads import upload_image_to_blob, UploadError
from app.attendance import get_sheets_service, get_available_dates, get_attendance_for_date
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


MAX_FEATURED_PROJECTS = 6
MAX_FEATURED_PUBLICATIONS = 3

def _featured_count_ok(model, exclude_id=None, limit=None):
    """Check whether adding one more featured item would exceed the cap."""
    q = model.query.filter_by(is_featured=True)
    if exclude_id is not None:
        q = q.filter(model.id != exclude_id)
    return q.count() < limit

from app.uploads import upload_image_to_blob, UploadError

@admin_bp.route("/projects/new", methods=["GET", "POST"])
@admin_required
def project_new():
    if request.method == "POST":
        img_path = None
        try:
            img_path = upload_image_to_blob(request.files.get("image_file"), folder="projects")
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/project_form.html", project=None)

        project = Project(
            title=request.form.get("title", "").strip(),
            year=request.form.get("year", "").strip() or None,
            description=request.form.get("description", "").strip(),
            img_path=img_path,
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
        try:
            new_url = upload_image_to_blob(request.files.get("image_file"), folder="projects")
            if new_url:
                project.img_path = new_url
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/project_form.html", project=project)

        project.title = request.form.get("title", "").strip()
        project.year = request.form.get("year", "").strip() or None
        project.description = request.form.get("description", "").strip()
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
        wants_featured = bool(request.form.get("is_featured"))
        if wants_featured and not _featured_count_ok(Publication, limit=MAX_FEATURED_PUBLICATIONS):
            flash(f"Only {MAX_FEATURED_PUBLICATIONS} publications can be featured at once. "
                  f"Un-feature another publication first.", "error")
            return render_template("admin/publication_form.html", pub=None)

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
            is_featured=wants_featured,
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
        wants_featured = bool(request.form.get("is_featured"))
        if wants_featured and not _featured_count_ok(Publication, exclude_id=pub.id, limit=MAX_FEATURED_PUBLICATIONS):
            flash(f"Only {MAX_FEATURED_PUBLICATIONS} publications can be featured at once. "
                  f"Un-feature another publication first.", "error")
            return render_template("admin/publication_form.html", pub=pub)

        pub.title = request.form.get("title", "").strip()
        pub.date = request.form.get("date", "").strip() or None
        pub.type = request.form.get("type", "").strip()
        pub.summary = request.form.get("summary", "").strip()
        pub.details = request.form.get("details", "").strip()
        pub.keyword1 = request.form.get("keyword1", "").strip() or None
        pub.keyword2 = request.form.get("keyword2", "").strip() or None
        pub.keyword3 = request.form.get("keyword3", "").strip() or None
        pub.link = request.form.get("link", "").strip() or None
        pub.is_featured = wants_featured
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
    highlights = CenterHighlight.query.order_by(CenterHighlight.date.desc()).all()
    return render_template("admin/highlights.html", highlights=highlights)


@admin_bp.route("/highlights/new", methods=["GET", "POST"])
@admin_required
def highlight_new():
    if request.method == "POST":
        highlight = CenterHighlight(
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            date=request.form.get("date", "").strip() or None,
            alt_text=request.form.get("alt_text", "").strip() or None,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(highlight)
        db.session.flush()  # flush to get the ID before adding images

        # Handle image uploads
        image_files = request.files.getlist("image_files")
        order = 0
        for image_file in image_files:
            if image_file and image_file.filename:
                try:
                    image_url = upload_image_to_blob(image_file, folder="highlights")
                    highlight_image = CenterHighlightImage(
                        highlight_id=highlight.id,
                        image_url=image_url,
                        order=order
                    )
                    db.session.add(highlight_image)
                    order += 1
                except UploadError as e:
                    db.session.rollback()
                    flash(str(e), "error")
                    return render_template("admin/highlight_form.html", highlight=None)

        db.session.commit()
        flash("Highlight created.", "success")
        return redirect(url_for("admin.highlights_list"))
    return render_template("admin/highlight_form.html", highlight=None)


@admin_bp.route("/highlights/<int:highlight_id>/edit", methods=["GET", "POST"])
@admin_required
def highlight_edit(highlight_id):
    highlight = CenterHighlight.query.get_or_404(highlight_id)
    
    if request.method == "POST":
        highlight.title = request.form.get("title", "").strip()
        highlight.description = request.form.get("description", "").strip()
        highlight.date = request.form.get("date", "").strip() or None
        highlight.alt_text = request.form.get("alt_text", "").strip() or None
        highlight.is_published = bool(request.form.get("is_published"))

        # Handle new image uploads
        image_files = request.files.getlist("image_files")
        if image_files and image_files[0].filename:
            order = highlight.images[-1].order + 1 if highlight.images else 0
            for image_file in image_files:
                if image_file and image_file.filename:
                    try:
                        image_url = upload_image_to_blob(image_file, folder="highlights")
                        highlight_image = CenterHighlightImage(
                            highlight_id=highlight.id,
                            image_url=image_url,
                            order=order
                        )
                        db.session.add(highlight_image)
                        order += 1
                    except UploadError as e:
                        db.session.rollback()
                        flash(str(e), "error")
                        return render_template("admin/highlight_form.html", highlight=highlight)

        # Handle image deletion (if passed image IDs to delete)
        images_to_delete = request.form.get("images_to_delete", "").split(",")
        for img_id_str in images_to_delete:
            if img_id_str.strip():
                try:
                    img_id = int(img_id_str.strip())
                    img = CenterHighlightImage.query.get(img_id)
                    if img and img.highlight_id == highlight.id:
                        db.session.delete(img)
                except (ValueError, TypeError):
                    pass

        db.session.commit()
        flash("Highlight updated.", "success")
        return redirect(url_for("admin.highlights_list"))
    
    return render_template("admin/highlight_form.html", highlight=highlight)


@admin_bp.route("/highlights/<int:highlight_id>/delete", methods=["POST"])
@admin_required
def highlight_delete(highlight_id):
    highlight = CenterHighlight.query.get_or_404(highlight_id)
    db.session.delete(highlight)
    db.session.commit()
    flash("Highlight deleted.", "success")
    return redirect(url_for("admin.highlights_list"))

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

# ── STAFF ──────────────────────────────────────────────────────────────────

@admin_bp.route("/staff")
@admin_required
def staff_list():
    staff = Staff.query.order_by(Staff.order).all()
    return render_template("admin/staff.html", staff=staff)


@admin_bp.route("/staff/new", methods=["GET", "POST"])
@admin_required
def staff_new():
    if request.method == "POST":
        try:
            photo_url = upload_image_to_blob(request.files.get("photo_file"), folder="staff")
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/staff_form.html", member=None)

        member = Staff(
            name=request.form.get("name", "").strip(),
            role=request.form.get("role", "").strip() or None,
            bio=request.form.get("bio", "").strip() or None,
            photo_url=photo_url,
            order=int(request.form.get("order", 0)),
            image_position=request.form.get("image_position", "center").strip(),
            is_core_staff=bool(request.form.get("is_core_staff")),
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(member)
        db.session.commit()
        flash("Staff member created.", "success")
        return redirect(url_for("admin.staff_list"))
    return render_template("admin/staff_form.html", member=None)


@admin_bp.route("/staff/<int:staff_id>/edit", methods=["GET", "POST"])
@admin_required
def staff_edit(staff_id):
    member = Staff.query.get_or_404(staff_id)
    if request.method == "POST":
        try:
            new_photo = upload_image_to_blob(request.files.get("photo_file"), folder="staff")
            if new_photo:
                member.photo_url = new_photo
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/staff_form.html", member=member)

        member.name = request.form.get("name", "").strip()
        member.role = request.form.get("role", "").strip() or None
        member.bio = request.form.get("bio", "").strip() or None
        member.order = int(request.form.get("order", 0))
        member.image_position = request.form.get("image_position", "center").strip()
        member.is_core_staff = bool(request.form.get("is_core_staff"))
        member.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Staff member updated.", "success")
        return redirect(url_for("admin.staff_list"))
    return render_template("admin/staff_form.html", member=member)


@admin_bp.route("/staff/<int:staff_id>/delete", methods=["POST"])
@admin_required
def staff_delete(staff_id):
    member = Staff.query.get_or_404(staff_id)
    db.session.delete(member)
    db.session.commit()
    flash("Staff member deleted.", "success")
    return redirect(url_for("admin.staff_list"))


# ── OJT INTERNS ────────────────────────────────────────────────────────────

@admin_bp.route("/ojt")
@admin_required
def ojt_list():
    interns = OJT.query.order_by(OJT.batch_label, OJT.order).all()
    return render_template("admin/ojt.html", interns=interns)


@admin_bp.route("/ojt/new", methods=["GET", "POST"])
@admin_required
def ojt_new():
    if request.method == "POST":
        try:
            photo_url = upload_image_to_blob(request.files.get("photo_file"), folder="ojt")
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/ojt_form.html", intern=None)

        intern = OJT(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip() or None,
            course=request.form.get("course", "").strip() or None,
            batch_label=request.form.get("batch_label", "").strip() or None,
            photo_url=photo_url,
            order=int(request.form.get("order", 0)),
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(intern)
        db.session.commit()
        flash("Intern added.", "success")
        return redirect(url_for("admin.ojt_list"))
    return render_template("admin/ojt_form.html", intern=None)


@admin_bp.route("/ojt/<int:ojt_id>/edit", methods=["GET", "POST"])
@admin_required
def ojt_edit(ojt_id):
    intern = OJT.query.get_or_404(ojt_id)
    if request.method == "POST":
        try:
            new_photo = upload_image_to_blob(request.files.get("photo_file"), folder="ojt")
            if new_photo:
                intern.photo_url = new_photo
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/ojt_form.html", intern=intern)

        intern.name = request.form.get("name", "").strip()
        intern.email = request.form.get("email", "").strip() or None
        intern.course = request.form.get("course", "").strip() or None
        intern.batch_label = request.form.get("batch_label", "").strip() or None
        intern.order = int(request.form.get("order", 0))
        intern.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Intern updated.", "success")
        return redirect(url_for("admin.ojt_list"))
    return render_template("admin/ojt_form.html", intern=intern)


@admin_bp.route("/ojt/<int:ojt_id>/delete", methods=["POST"])
@admin_required
def ojt_delete(ojt_id):
    intern = OJT.query.get_or_404(ojt_id)
    db.session.delete(intern)
    db.session.commit()
    flash("Intern deleted.", "success")
    return redirect(url_for("admin.ojt_list"))


# ── OJT ATTENDANCE (view-only) ──────────────────────────────────────────────

@admin_bp.route("/ojt/attendance")
@admin_required
def ojt_attendance():
    error = None
    records = []
    dates = []
    selected_date = request.args.get("date", "")

    try:
        service = get_sheets_service()
        dates = get_available_dates(service)

        if not selected_date and dates:
            selected_date = dates[0]  # default to most recent

        if selected_date:
            records, error = get_attendance_for_date(service, selected_date)

    except Exception as e:
        error = str(e)

    return render_template("admin/ojt_attendance.html",
                           records=records,
                           dates=dates,
                           selected_date=selected_date,
                           error=error)

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
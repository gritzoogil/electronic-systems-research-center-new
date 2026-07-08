from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from app.auth import require_firebase_user
from app.models import (
    Project, Publication, Staff, OJT, OJTAttendance,
    CenterHighlight, CenterHighlightImage, AccomplishmentReport,
    LearningResource, ResourcePage, Partner, SiteSettings
)
from app.uploads import upload_image_to_blob, UploadError
from app.attendance import get_sheets_service, get_available_dates, get_attendance_for_date
from app import db
from app.ordering import reorder_on_create, reorder_on_update, reorder_on_delete
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

def _resolve_project_order(requested_order, exclude_id=None):
    """Clamp the requested order into a valid position, then shift any
    projects at or after that position down by one to make room."""
    existing = Project.query
    if exclude_id is not None:
        existing = existing.filter(Project.id != exclude_id)
    count = existing.count()

    # If requested order is beyond the current list, just append as next
    order = max(0, min(requested_order, count))

    # Shift everything at/after this position down by one
    to_shift = existing.filter(Project.order >= order).order_by(Project.order)
    for p in to_shift:
        p.order += 1

    return order


def _resequence_projects():
    """After a delete, compact order values so there are no gaps (0..n-1)."""
    projects = Project.query.order_by(Project.order, Project.id).all()
    for i, p in enumerate(projects):
        p.order = i

from app.ordering import reorder_on_create, reorder_on_update, reorder_on_delete

@admin_bp.route("/projects/new", methods=["GET", "POST"])
@admin_required
def project_new():
    if request.method == "POST":
        wants_featured = bool(request.form.get("is_featured"))
        if wants_featured and not _featured_count_ok(Project, limit=MAX_FEATURED_PROJECTS):
            flash(f"Only {MAX_FEATURED_PROJECTS} projects can be featured at once. "
                  f"Un-feature another project first.", "error")
            return render_template("admin/project_form.html", project=None)

        img_path = None
        try:
            img_path = upload_image_to_blob(request.files.get("image_file"), folder="projects")
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/project_form.html", project=None)

        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(Project, requested_order)

        project = Project(
            title=request.form.get("title", "").strip(),
            year=request.form.get("year", "").strip() or None,
            description=request.form.get("description", "").strip(),
            img_path=img_path,
            more_info_img=request.form.get("more_info_img", "").strip() or None,
            order=safe_order,
            is_featured=wants_featured,
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
        wants_featured = bool(request.form.get("is_featured"))
        if wants_featured and not _featured_count_ok(Project, exclude_id=project.id, limit=MAX_FEATURED_PROJECTS):
            flash(f"Only {MAX_FEATURED_PROJECTS} projects can be featured at once. "
                  f"Un-feature another project first.", "error")
            return render_template("admin/project_form.html", project=project)

        try:
            new_url = upload_image_to_blob(request.files.get("image_file"), folder="projects")
            if new_url:
                project.img_path = new_url
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/project_form.html", project=project)

        old_order = project.order
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_update(Project, project.id, old_order, requested_order)

        project.title = request.form.get("title", "").strip()
        project.year = request.form.get("year", "").strip() or None
        project.description = request.form.get("description", "").strip()
        project.more_info_img = request.form.get("more_info_img", "").strip() or None
        project.order = safe_order
        project.is_featured = wants_featured
        project.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("admin.projects_list"))
    return render_template("admin/project_form.html", project=project)


@admin_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def project_delete(project_id):
    project = Project.query.get_or_404(project_id)
    deleted_order = project.order
    db.session.delete(project)
    db.session.commit()
    reorder_on_delete(Project, deleted_order)
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

# ── ACCOMPLISHMENTS ────────────────────────────────────────────────────────

@admin_bp.route("/accomplishments")
@admin_required
def accomplishments_list():
    reports = AccomplishmentReport.query.order_by(
        AccomplishmentReport.year.desc(),
        AccomplishmentReport.quarter.desc()
    ).all()
    return render_template("admin/accomplishments.html", reports=reports)


@admin_bp.route("/accomplishments/new", methods=["GET", "POST"])
@admin_required
def accomplishment_new():
    if request.method == "POST":
        try:
            thumbnail_url = upload_image_to_blob(request.files.get("thumbnail_file"), folder="accomplishments")
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/accomplishment_form.html", report=None)

        report = AccomplishmentReport(
            title=request.form.get("title", "").strip(),
            year=int(request.form.get("year", 0)),
            quarter=int(request.form.get("quarter", 1)),
            description=request.form.get("description", "").strip(),
            thumbnail_url=thumbnail_url,
            flipbook_link=request.form.get("flipbook_link", "").strip() or None,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(report)
        db.session.commit()
        flash("Accomplishment report created.", "success")
        return redirect(url_for("admin.accomplishments_list"))
    return render_template("admin/accomplishment_form.html", report=None)


@admin_bp.route("/accomplishments/<int:report_id>/edit", methods=["GET", "POST"])
@admin_required
def accomplishment_edit(report_id):
    report = AccomplishmentReport.query.get_or_404(report_id)
    if request.method == "POST":
        try:
            new_thumb = upload_image_to_blob(request.files.get("thumbnail_file"), folder="accomplishments")
            if new_thumb:
                report.thumbnail_url = new_thumb
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/accomplishment_form.html", report=report)

        report.title = request.form.get("title", "").strip()
        report.year = int(request.form.get("year", 0))
        report.quarter = int(request.form.get("quarter", 1))
        report.description = request.form.get("description", "").strip()
        report.flipbook_link = request.form.get("flipbook_link", "").strip() or None
        report.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Accomplishment report updated.", "success")
        return redirect(url_for("admin.accomplishments_list"))
    return render_template("admin/accomplishment_form.html", report=report)


@admin_bp.route("/accomplishments/<int:report_id>/delete", methods=["POST"])
@admin_required
def accomplishment_delete(report_id):
    report = AccomplishmentReport.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash("Accomplishment report deleted.", "success")
    return redirect(url_for("admin.accomplishments_list"))


# ── RESOURCES ──────────────────────────────────────────────────────────────

@admin_bp.route("/resources")
@admin_required
def resources_list():
    resources = LearningResource.query.order_by(LearningResource.order).all()
    return render_template("admin/resources.html", resources=resources)


@admin_bp.route("/resources/new", methods=["GET", "POST"])
@admin_required
def resource_new():
    if request.method == "POST":
        try:
            thumbnail_url = upload_image_to_blob(request.files.get("thumbnail_file"), folder="resources")
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/resource_form.html", resource=None)

        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(LearningResource, requested_order)

        resource = LearningResource(
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            thumbnail_url=thumbnail_url,
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(resource)
        db.session.flush()

        titles = request.form.getlist("chapter_title[]")
        urls = request.form.getlist("chapter_url[]")
        for i, (title, url) in enumerate(zip(titles, urls)):
            if title.strip():
                db.session.add(ResourcePage(
                    resource_id=resource.id,
                    title=title.strip(),
                    embed_url=url.strip() or None,
                    order=i,
                ))

        db.session.commit()
        flash("Resource created.", "success")
        return redirect(url_for("admin.resources_list"))
    return render_template("admin/resource_form.html", resource=None)


@admin_bp.route("/resources/<int:resource_id>/edit", methods=["GET", "POST"])
@admin_required
def resource_edit(resource_id):
    resource = LearningResource.query.get_or_404(resource_id)
    if request.method == "POST":
        try:
            new_thumb = upload_image_to_blob(request.files.get("thumbnail_file"), folder="resources")
            if new_thumb:
                resource.thumbnail_url = new_thumb
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/resource_form.html", resource=resource)

        old_order = resource.order
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_update(LearningResource, resource.id, old_order, requested_order)

        resource.title = request.form.get("title", "").strip()
        resource.description = request.form.get("description", "").strip()
        resource.order = safe_order
        resource.is_published = bool(request.form.get("is_published"))

        # Replace all chapters
        ResourcePage.query.filter_by(resource_id=resource.id).delete()
        titles = request.form.getlist("chapter_title[]")
        urls = request.form.getlist("chapter_url[]")
        for i, (title, url) in enumerate(zip(titles, urls)):
            if title.strip():
                db.session.add(ResourcePage(
                    resource_id=resource.id,
                    title=title.strip(),
                    embed_url=url.strip() or None,  # fixed: was 'flipbook_url', which doesn't exist on the model
                    order=i,
                ))

        db.session.commit()
        flash("Resource updated.", "success")
        return redirect(url_for("admin.resources_list"))
    return render_template("admin/resource_form.html", resource=resource)


@admin_bp.route("/resources/<int:resource_id>/delete", methods=["POST"])
@admin_required
def resource_delete(resource_id):
    resource = LearningResource.query.get_or_404(resource_id)
    deleted_order = resource.order
    db.session.delete(resource)
    db.session.commit()
    reorder_on_delete(LearningResource, deleted_order)
    db.session.commit()
    flash("Resource deleted.", "success")
    return redirect(url_for("admin.resources_list"))

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

        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(Staff, requested_order)

        member = Staff(
            name=request.form.get("name", "").strip(),
            role=request.form.get("role", "").strip() or None,
            bio=request.form.get("bio", "").strip() or None,
            photo_url=photo_url,
            order=safe_order,
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

        old_order = member.order
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_update(Staff, member.id, old_order, requested_order)

        member.name = request.form.get("name", "").strip()
        member.role = request.form.get("role", "").strip() or None
        member.bio = request.form.get("bio", "").strip() or None
        member.order = safe_order
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
    deleted_order = member.order
    db.session.delete(member)
    db.session.commit()
    reorder_on_delete(Staff, deleted_order)
    db.session.commit()
    flash("Staff member deleted.", "success")
    return redirect(url_for("admin.staff_list"))


# ── OJT INTERNS ────────────────────────────────────────────────────────────

def _get_ojt_batches():
    """Distinct, non-empty batch labels currently in use, for the dropdown."""
    rows = db.session.query(OJT.batch_label).filter(OJT.batch_label.isnot(None)).distinct().all()
    return sorted(set(r[0] for r in rows if r[0]))

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
            return render_template("admin/ojt_form.html", intern=None, existing_batches=_get_ojt_batches())

        batch_label = request.form.get("batch_label", "").strip()
        if batch_label == "__new__":
            batch_label = request.form.get("new_batch_label", "").strip()

        if not batch_label:
            flash("Batch is required. Choose an existing batch or add a new one.", "error")
            return render_template("admin/ojt_form.html", intern=None, existing_batches=_get_ojt_batches())

        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(OJT, requested_order, filters={"batch_label": batch_label})

        intern = OJT(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip() or None,
            course=request.form.get("course", "").strip() or None,
            batch_label=batch_label,
            photo_url=photo_url,
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(intern)
        db.session.commit()
        flash("Intern added.", "success")
        return redirect(url_for("admin.ojt_list"))
    return render_template("admin/ojt_form.html", intern=None, existing_batches=_get_ojt_batches())


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
            return render_template("admin/ojt_form.html", intern=intern, existing_batches=_get_ojt_batches())

        new_batch_label = request.form.get("batch_label", "").strip()
        if new_batch_label == "__new__":
            new_batch_label = request.form.get("new_batch_label", "").strip()

        if not new_batch_label:
            flash("Batch is required. Choose an existing batch or add a new one.", "error")
            return render_template("admin/ojt_form.html", intern=intern, existing_batches=_get_ojt_batches())

        old_order = intern.order
        requested_order = int(request.form.get("order", 0))

        if new_batch_label != intern.batch_label:
            reorder_on_delete(OJT, old_order, filters={"batch_label": intern.batch_label})
            safe_order = reorder_on_create(OJT, requested_order, filters={"batch_label": new_batch_label})
        else:
            safe_order = reorder_on_update(OJT, intern.id, old_order, requested_order,
                                            filters={"batch_label": intern.batch_label})

        intern.name = request.form.get("name", "").strip()
        intern.email = request.form.get("email", "").strip() or None
        intern.course = request.form.get("course", "").strip() or None
        intern.batch_label = new_batch_label
        intern.order = safe_order
        intern.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Intern updated.", "success")
        return redirect(url_for("admin.ojt_list"))
    return render_template("admin/ojt_form.html", intern=intern, existing_batches=_get_ojt_batches())


@admin_bp.route("/ojt/<int:ojt_id>/delete", methods=["POST"])
@admin_required
def ojt_delete(ojt_id):
    intern = OJT.query.get_or_404(ojt_id)
    deleted_order = intern.order
    batch_label = intern.batch_label
    db.session.delete(intern)
    db.session.commit()
    reorder_on_delete(OJT, deleted_order, filters={"batch_label": batch_label})
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

# ── PARTNERS ───────────────────────────────────────────────────────────────

@admin_bp.route("/partners")
@admin_required
def partners_list():
    partners = Partner.query.order_by(Partner.order).all()
    return render_template("admin/partners.html", partners=partners)


from app.ordering import reorder_on_create, reorder_on_update, reorder_on_delete

@admin_bp.route("/partners/new", methods=["GET", "POST"])
@admin_required
def partner_new():
    if request.method == "POST":
        try:
            logo_url = upload_image_to_blob(request.files.get("logo_file"), folder="partners")
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/partner_form.html", partner=None)

        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(Partner, requested_order)

        partner = Partner(
            name=request.form.get("name", "").strip(),
            logo_url=logo_url,
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(partner)
        db.session.commit()
        flash("Partner added.", "success")
        return redirect(url_for("admin.partners_list"))
    return render_template("admin/partner_form.html", partner=None)


@admin_bp.route("/partners/<int:partner_id>/edit", methods=["GET", "POST"])
@admin_required
def partner_edit(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    if request.method == "POST":
        try:
            new_logo = upload_image_to_blob(request.files.get("logo_file"), folder="partners")
            if new_logo:
                partner.logo_url = new_logo
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/partner_form.html", partner=partner)

        old_order = partner.order
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_update(Partner, partner.id, old_order, requested_order)

        partner.name = request.form.get("name", "").strip()
        partner.order = safe_order
        partner.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Partner updated.", "success")
        return redirect(url_for("admin.partners_list"))
    return render_template("admin/partner_form.html", partner=partner)


@admin_bp.route("/partners/<int:partner_id>/delete", methods=["POST"])
@admin_required
def partner_delete(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    deleted_order = partner.order
    db.session.delete(partner)
    db.session.commit()
    reorder_on_delete(Partner, deleted_order)
    db.session.commit()
    flash("Partner deleted.", "success")
    return redirect(url_for("admin.partners_list"))

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
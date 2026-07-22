from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from app.auth import require_firebase_user
from app.models import (
    Project, Publication, Staff, OJT, OJTAttendance,
    CenterHighlight, CenterHighlightImage, AccomplishmentReport,
    LearningResource, ResourcePage, Partner, SiteSettings,
    ResearchArea, ServiceOffered, EquipmentItem, CoreValue
)
from app.uploads import upload_image_to_blob, UploadError
from app.attendance import get_sheets_service, get_available_dates, get_attendance_for_date
from app import db
from app.ordering import reorder_on_create, reorder_on_update, reorder_on_delete
import os
import resend
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import timedelta

import logging
logger = logging.getLogger(__name__)

def _send_email(to_address, subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "ESRC Appointments <esrc.batstateutneu@gmail.com>"
    msg["To"] = to_address
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("esrc.batstateutneu@gmail.com", os.environ.get("GMAIL_APP_PASSWORD"))
        server.sendmail("esrc.batstateutneu@gmail.com", to_address, msg.as_string())

def send_status_email(appt, new_status):
    from app.scheduling import format_time_for_display
    resend.api_key = os.environ.get("RESEND_API_KEY")

    if new_status == "Approved":
        date_display = appt.appointment_date.strftime("%B %d, %Y")
        time_display = format_time_for_display(appt.appointment_time)
        service_name = appt.service.name
        duration = appt.service.duration_minutes
        admin_notes_row = f'<div class="ticket-row"><span class="ticket-label">Admin Notes</span><span class="ticket-value">{appt.admin_notes}</span></div>' if appt.admin_notes else ''

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; background: #f4f7fb; margin: 0; padding: 24px; }}
  .container {{ max-width: 560px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #0f2942, #0f4c81); color: white;
             border-radius: 12px 12px 0 0; padding: 32px 28px; text-align: center; }}
  .header h1 {{ margin: 0 0 4px; font-size: 22px; }}
  .header p {{ margin: 0; font-size: 13px; opacity: .8; }}
  .ticket {{ background: white; border: 1px solid #e2e8f0; padding: 28px; position: relative; }}
  .ticket::before {{ content: 'CONFIRMED'; position: absolute; top: 16px; right: 16px;
    background: #dcfce7; color: #166534; font-size: 10px; font-weight: 800;
    letter-spacing: .1em; padding: 3px 8px; border-radius: 4px; }}
  .ticket-row {{ display: table; width: 100%; padding: 10px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
    padding: 10px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
  .ticket-row:last-child {{ border-bottom: none; }}
  .ticket-label {{ display: table-cell; color: #64748b; font-weight: 600; width: 40%; }}
  .ticket-value {{ display: table-cell; color: #0f2942; font-weight: 700; width: 60%; }}
  .divider {{ border: none; border-top: 2px dashed #e2e8f0; margin: 20px 0; }}
  .ref-box {{ background: #f0f7ff; border: 1px solid #bfdbfe; border-radius: 8px;
    text-align: center; padding: 14px; margin: 16px 0; }}
  .ref-box p {{ margin: 0 0 4px; font-size: 11px; color: #64748b; font-weight: 600;
    text-transform: uppercase; letter-spacing: .05em; }}
  .ref-box span {{ font-size: 22px; font-weight: 900; color: #0f4c81; letter-spacing: .15em; }}
  .instructions {{ background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
    padding: 14px 16px; margin: 16px 0 0; font-size: 13px; color: #78350f; }}
  .instructions ul {{ margin: 6px 0 0 0; padding-left: 18px; }}
  .instructions li {{ margin-bottom: 4px; }}
  .footer {{ background: #f8fafc; border: 1px solid #e2e8f0; border-top: none;
    border-radius: 0 0 12px 12px; padding: 20px 28px; text-align: center;
    font-size: 12px; color: #94a3b8; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Appointment Confirmed ✓</h1>
    <p>Electronic Systems Research Center · BatStateU</p>
  </div>
  <div class="ticket">
    <p style="font-size:14px;color:#475569;margin:0 0 16px;">
      Hi <strong>{appt.full_name}</strong>, your appointment has been
      <strong style="color:#166534;">approved</strong>. Please present this email
      (printed or on your phone) when you arrive at the ESRC office.
    </p>
    <div class="ref-box">
      <p>Appointment Reference</p>
      <span>ESRC-{appt.id:05d}</span>
    </div>
    <div class="ticket-row">
      <span class="ticket-label">Service:</span>
      <span class="ticket-value">{service_name}</span>
    </div>
    <div class="ticket-row">
      <span class="ticket-label">Date:</span>
      <span class="ticket-value">{date_display}</span>
    </div>
    <div class="ticket-row">
      <span class="ticket-label">Time:</span>
      <span class="ticket-value">{time_display}</span>
    </div>
    <div class="ticket-row">
      <span class="ticket-label">Duration:</span>
      <span class="ticket-value">{duration} minutes</span>
    </div>
    <div class="ticket-row">
      <span class="ticket-label">Name:</span>
      <span class="ticket-value">{appt.full_name}</span>
    </div>
    <div class="ticket-row">
      <span class="ticket-label">Purpose:</span>
      <span class="ticket-value">{appt.purpose}</span>
    </div>
    {admin_notes_row}
    <hr class="divider">
    <div class="instructions">
      <strong>📍 What to bring on the day:</strong>
      <ul>
        <li>This email (printed or on your phone)</li>
        <li>Your valid school / company ID</li>
        <li>Any materials relevant to your appointment</li>
      </ul>
    </div>
    <p style="font-size:12px;color:#94a3b8;margin:16px 0 0;text-align:center;">
      Location: 2nd Floor, STEER Hub Building, BatStateU Alangilan Campus<br>
      Office Hours: Monday – Thursday, 7:00 AM – 8:00 PM
    </p>
  </div>
  <div class="footer">
    To cancel or reschedule, contact
    <a href="mailto:esrc.batstateutneu@gmail.com" style="color:#0f4c81;">esrc.batstateutneu@gmail.com</a><br>
    Reference: ESRC-{appt.id:05d} · {service_name} · {date_display}
  </div>
</div>
</body>
</html>"""

        subject = f"✓ Appointment Confirmed — {service_name} on {date_display} | ESRC-{appt.id:05d}"

    else:  # Rejected
        html = f"""
            <p>Hi {appt.full_name},</p>
            <p>Your appointment request for <strong>{appt.service.name}</strong> on
            {appt.appointment_date.strftime('%B %d, %Y')} at
            {format_time_for_display(appt.appointment_time)} has been
            <strong>rejected</strong>.</p>
            <p>If you have questions, feel free to reach out to us at
            <a href="mailto:esrc.batstateutneu@gmail.com">esrc.batstateutneu@gmail.com</a>.</p>
        """
        subject = f"Your ESRC Appointment Request was {new_status}"

    try:
        _send_email(appt.email, subject, html)
        return True
    except Exception as e:
        logger.error(f"Status notification email to {appt.email} failed: {e}")
        flash(f"Email error: {e}", "error")
        return False


def send_reschedule_email(appt, old_date, old_time):
    from app.scheduling import format_time_for_display
    try:
        _send_email(
            appt.email,
            "Your ESRC Appointment Has Been Rescheduled",
            f"""
                <p>Hi {appt.full_name},</p>
                <p>Your appointment for <strong>{appt.service.name}</strong> has been rescheduled.</p>
                <p><strong>Previous:</strong> {old_date.strftime('%B %d, %Y')} at {format_time_for_display(old_time)}</p>
                <p><strong>New:</strong> {appt.appointment_date.strftime('%B %d, %Y')} at {format_time_for_display(appt.appointment_time)}</p>
                <p>Please let us know if this new time doesn't work for you.</p>
            """
        )
        return True
    except Exception as e:
        logger.error(f"Reschedule notification email to {appt.email} failed: {e}")
        return False
    
resend.api_key = os.environ.get("RESEND_API_KEY")

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

@admin_bp.route("/change-password")
@admin_required
def change_password():
    return render_template("admin/change_password.html", **FIREBASE_CONFIG)

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
            sr_code=request.form.get("sr_code", "").strip() or None,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(intern)
        db.session.commit()
        if intern.sr_code:
            try:
                add_student_to_sheet(intern.sr_code, intern.name, intern.course or "")
            except Exception as e:
                flash(f"Intern saved, but Sheet sync failed: {e}", "error")
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
        intern.sr_code = request.form.get("sr_code", "").strip() or None
        intern.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        if intern.sr_code:
            try:
                update_student_in_sheet(intern.sr_code, intern.name, intern.course or "")
            except Exception as e:
                flash(f"Intern updated, but Sheet sync failed: {e}", "error")

        flash("Intern updated.", "success")
        return redirect(url_for("admin.ojt_list"))
    return render_template("admin/ojt_form.html", intern=intern, existing_batches=_get_ojt_batches())


@admin_bp.route("/ojt/<int:ojt_id>/delete", methods=["POST"])
@admin_required
def ojt_delete(ojt_id):
    intern = OJT.query.get_or_404(ojt_id)
    deleted_order = intern.order
    batch_label = intern.batch_label
    if intern.sr_code:
        try:
            delete_student_from_sheet(intern.sr_code, intern.name)
        except Exception as e:
            flash(f"Sheet sync failed: {e}", "error")
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
from app.attendance import (
    get_sheets_service, get_available_dates, get_attendance_for_date,
    update_task_accomplishment, add_student_to_sheet, update_student_in_sheet,
    delete_student_from_sheet, upload_signature,
)

@admin_bp.route("/ojt/attendance/update", methods=["POST"])
@admin_required
def ojt_attendance_update():
    sr_code = request.form.get("sr_code", "").strip()
    name = request.form.get("name", "").strip()
    course = request.form.get("course", "").strip()
    task = request.form.get("task", "").strip()
    accomplishment = request.form.get("accomplishment", "").strip()
    date_str = request.form.get("date", "").strip()

    try:
        update_task_accomplishment(sr_code, name, course, task, accomplishment, date_str)
        flash("Task/Accomplishment updated.", "success")
    except Exception as e:
        flash(f"Failed to update sheet: {e}", "error")

    return redirect(url_for("admin.ojt_attendance", date=date_str))


@admin_bp.route("/ojt/attendance/signature", methods=["POST"])
@admin_required
def ojt_attendance_signature():
    sr_code = request.form.get("sr_code", "").strip()
    name = request.form.get("name", "").strip()
    date_str = request.form.get("date", "").strip()
    signature_data = request.form.get("signature_data", "")  # base64 PNG from canvas or file

    try:
        result = upload_signature(sr_code, name, date_str, signature_data)
        flash("Signature saved.", "success")
    except Exception as e:
        flash(f"Failed to save signature: {e}", "error")

    return redirect(url_for("admin.ojt_attendance", date=date_str))

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
        try:
            new_hero_image = upload_image_to_blob(request.files.get("hero_image_file"), folder="site")
            if new_hero_image:
                s.hero_image_url = new_hero_image
        except UploadError as e:
            flash(str(e), "error")
            return render_template("admin/settings.html", s=s)

        s.avp_video_url = request.form.get("avp_video_url", "").strip()
        s.contact_email = request.form.get("contact_email", "").strip()
        s.contact_phone = request.form.get("contact_phone", "").strip()
        s.contact_address = request.form.get("contact_address", "").strip()
        s.contact_office_hours = request.form.get("contact_office_hours", "").strip()
        s.maps_embed_url = request.form.get("maps_embed_url", "").strip()
        s.facebook_url = request.form.get("facebook_url", "").strip()
        s.youtube_url = request.form.get("youtube_url", "").strip()

        s.hero_eyebrow = request.form.get("hero_eyebrow", "").strip()
        s.hero_heading = request.form.get("hero_heading", "").strip()
        s.hero_paragraph = request.form.get("hero_paragraph", "").strip()
        s.about_paragraph = request.form.get("about_paragraph", "").strip()
        s.vision = request.form.get("vision", "").strip() or None
        s.mission = request.form.get("mission", "").strip() or None
        s.quality_policy = request.form.get("quality_policy", "").strip() or None

        db.session.commit()
        flash("Settings saved successfully.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", s=s)

from app.models import Service, Appointment, BlockedDate, ScheduleConfig
from app.scheduling import get_schedule_config, DAY_ABBR
from datetime import datetime

# ── SERVICES ───────────────────────────────────────────────────────────────

@admin_bp.route("/services")
@admin_required
def services_list():
    services = Service.query.order_by(Service.order).all()
    return render_template("admin/services.html", services=services)


@admin_bp.route("/services/new", methods=["GET", "POST"])
@admin_required
def service_new():
    if request.method == "POST":
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(Service, requested_order)
        service = Service(
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip() or None,
            duration_minutes=int(request.form.get("duration_minutes", 60)),
            max_appointments_per_slot=int(request.form.get("max_appointments_per_slot", 1)),
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(service)
        db.session.commit()
        flash("Service created.", "success")
        return redirect(url_for("admin.services_list"))
    return render_template("admin/service_form.html", service=None)


@admin_bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@admin_required
def service_edit(service_id):
    service = Service.query.get_or_404(service_id)
    if request.method == "POST":
        old_order = service.order
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_update(Service, service.id, old_order, requested_order)

        service.name = request.form.get("name", "").strip()
        service.description = request.form.get("description", "").strip() or None
        service.duration_minutes = int(request.form.get("duration_minutes", 60))
        service.max_appointments_per_slot = int(request.form.get("max_appointments_per_slot", 1))
        service.order = safe_order
        service.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Service updated.", "success")
        return redirect(url_for("admin.services_list"))
    return render_template("admin/service_form.html", service=service)


@admin_bp.route("/services/<int:service_id>/delete", methods=["POST"])
@admin_required
def service_delete(service_id):
    service = Service.query.get_or_404(service_id)
    deleted_order = service.order
    db.session.delete(service)
    db.session.commit()
    reorder_on_delete(Service, deleted_order)
    db.session.commit()
    flash("Service deleted.", "success")
    return redirect(url_for("admin.services_list"))


# ── APPOINTMENTS ───────────────────────────────────────────────────────────

@admin_bp.route("/appointments")
@admin_required
def appointments_list():
    # Auto-cancel pending appointments whose date+time has passed
    from datetime import datetime, date, time as dtime
    import datetime as dt
    now = datetime.now()
    stale = Appointment.query.filter_by(status="Pending").all()
    for a in stale:
        appt_dt = datetime.combine(a.appointment_date, a.appointment_time)
        if appt_dt < now:
            a.status = "Cancelled"
    db.session.commit()

    view = request.args.get("view", "table")  # table | calendar
    status_filter = request.args.get("status", "all")

    query = Appointment.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    appointments = query.order_by(Appointment.appointment_date.desc(),
                                   Appointment.appointment_time.desc()).all()

    if view == "calendar":
        return render_template("admin/appointments_calendar.html", appointments=appointments)
    return render_template("admin/appointments.html", appointments=appointments,
                            active_status=status_filter)


@admin_bp.route("/appointments/<int:appt_id>")
@admin_required
def appointment_detail(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    return render_template("admin/appointment_detail.html", appt=appt,
                            statuses=Appointment.STATUSES, timedelta=timedelta)

from app.scheduling import get_schedule_config, DAY_ABBR, parse_time_from_input, format_time_for_display

@admin_bp.route("/appointments/<int:appt_id>/reschedule", methods=["POST"])
@admin_required
def appointment_reschedule(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    try:
        old_date = appt.appointment_date
        old_time = appt.appointment_time

        appt.appointment_date = datetime.strptime(
            request.form.get("appointment_date", ""), "%Y-%m-%d"
        ).date()
        appt.appointment_time = parse_time_from_input(request.form.get("appointment_time", ""))
        appt.status = "Approved"
        db.session.commit()

        email_sent = send_reschedule_email(appt, old_date, old_time)
        if email_sent:
            flash("Appointment rescheduled and visitor notified by email.", "success")
        else:
            flash("Appointment rescheduled, but the notification email could not be sent. "
                  "Contact the visitor directly if needed.", "error")
    except ValueError:
        flash("Invalid date or time.", "error")
    return redirect(url_for("admin.appointment_detail", appt_id=appt.id))

@admin_bp.route("/appointments/<int:appt_id>/delete", methods=["POST"])
@admin_required
def appointment_delete(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    flash("Appointment deleted.", "success")
    return redirect(url_for("admin.appointments_list"))


# ── SCHEDULE MANAGEMENT ────────────────────────────────────────────────────

@admin_bp.route("/schedule", methods=["GET", "POST"])
@admin_required
def schedule():
    cfg = get_schedule_config()
    if request.method == "POST":
        selected_days = request.form.getlist("working_days")
        cfg.working_days = ",".join(selected_days) if selected_days else cfg.working_days
        cfg.day_start_time = datetime.strptime(request.form.get("day_start_time", "09:00"), "%H:%M").time()
        cfg.day_end_time = datetime.strptime(request.form.get("day_end_time", "17:00"), "%H:%M").time()
        cfg.slot_duration_minutes = int(request.form.get("slot_duration_minutes", 60))
        cfg.max_appointments_per_day = int(request.form.get("max_appointments_per_day", 8))
        db.session.commit()
        flash("Schedule settings saved.", "success")
        return redirect(url_for("admin.schedule"))

    blocked_dates = BlockedDate.query.order_by(BlockedDate.date).all()
    return render_template("admin/schedule.html", cfg=cfg, blocked_dates=blocked_dates,
                            day_abbr=DAY_ABBR)


@admin_bp.route("/schedule/block", methods=["POST"])
@admin_required
def schedule_block_date():
    is_full_day = bool(request.form.get("is_full_day"))
    block = BlockedDate(
        date=datetime.strptime(request.form.get("date", ""), "%Y-%m-%d").date(),
        reason=request.form.get("reason", "").strip() or None,
        is_full_day=is_full_day,
        start_time=None if is_full_day else datetime.strptime(request.form.get("start_time", "09:00"), "%H:%M").time(),
        end_time=None if is_full_day else datetime.strptime(request.form.get("end_time", "17:00"), "%H:%M").time(),
    )
    db.session.add(block)
    db.session.commit()
    flash("Date/time blocked.", "success")
    return redirect(url_for("admin.schedule"))


@admin_bp.route("/schedule/block/<int:block_id>/delete", methods=["POST"])
@admin_required
def schedule_unblock_date(block_id):
    block = BlockedDate.query.get_or_404(block_id)
    db.session.delete(block)
    db.session.commit()
    flash("Block removed.", "success")
    return redirect(url_for("admin.schedule"))

@admin_bp.route("/appointments/<int:appt_id>/status", methods=["POST"])
@admin_required
def appointment_update_status(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    new_status = request.form.get("status")
    if new_status not in Appointment.STATUSES:
        flash("Invalid status.", "error")
        return redirect(url_for("admin.appointment_detail", appt_id=appt.id))

    old_status = appt.status
    appt.status = new_status
    appt.admin_notes = request.form.get("admin_notes", "").strip() or appt.admin_notes
    db.session.commit()

    if new_status != old_status and new_status in ("Approved", "Rejected"):
        if send_status_email(appt, new_status):
            flash(f"Appointment marked as {new_status} and visitor notified by email.", "success")
        else:
            flash(f"Appointment marked as {new_status}, but the notification email could not be sent. "
                  f"Contact the visitor directly if needed.", "error")
    else:
        flash(f"Appointment marked as {new_status}.", "success")

    return redirect(url_for("admin.appointment_detail", appt_id=appt.id))

# ── RESEARCH AREAS ─────────────────────────────────────────────────────────

@admin_bp.route("/research-areas")
@admin_required
def research_areas_list():
    areas = ResearchArea.query.order_by(ResearchArea.order).all()
    return render_template("admin/research_areas.html", areas=areas)


@admin_bp.route("/research-areas/new", methods=["GET", "POST"])
@admin_required
def research_area_new():
    if request.method == "POST":
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(ResearchArea, requested_order)
        area = ResearchArea(
            icon_key=request.form.get("icon_key", "embedded").strip(),
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(area)
        db.session.commit()
        flash("Research area created.", "success")
        return redirect(url_for("admin.research_areas_list"))
    return render_template("admin/research_area_form.html", area=None)


@admin_bp.route("/research-areas/<int:area_id>/edit", methods=["GET", "POST"])
@admin_required
def research_area_edit(area_id):
    area = ResearchArea.query.get_or_404(area_id)
    if request.method == "POST":
        old_order = area.order
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_update(ResearchArea, area.id, old_order, requested_order)

        area.icon_key = request.form.get("icon_key", "embedded").strip()
        area.title = request.form.get("title", "").strip()
        area.description = request.form.get("description", "").strip()
        area.order = safe_order
        area.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Research area updated.", "success")
        return redirect(url_for("admin.research_areas_list"))
    return render_template("admin/research_area_form.html", area=area)


@admin_bp.route("/research-areas/<int:area_id>/delete", methods=["POST"])
@admin_required
def research_area_delete(area_id):
    area = ResearchArea.query.get_or_404(area_id)
    deleted_order = area.order
    db.session.delete(area)
    db.session.commit()
    reorder_on_delete(ResearchArea, deleted_order)
    db.session.commit()
    flash("Research area deleted.", "success")
    return redirect(url_for("admin.research_areas_list"))


# ── SERVICES OFFERED (simple list) ─────────────────────────────────────────

@admin_bp.route("/services-offered")
@admin_required
def services_offered_list():
    items = ServiceOffered.query.order_by(ServiceOffered.order).all()
    return render_template("admin/simple_list.html",
                           items=items, kind="services_offered",
                           title="Services Offered",
                           list_url="admin.services_offered_list",
                           new_url="admin.service_offered_new",
                           edit_url="admin.service_offered_edit",
                           delete_url="admin.service_offered_delete")


@admin_bp.route("/services-offered/new", methods=["GET", "POST"])
@admin_required
def service_offered_new():
    if request.method == "POST":
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(ServiceOffered, requested_order)
        item = ServiceOffered(
            text=request.form.get("text", "").strip(),
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(item)
        db.session.commit()
        flash("Item added.", "success")
        return redirect(url_for("admin.services_offered_list"))
    return render_template("admin/simple_list_form.html", item=None,
                           title="Service Offered",
                           list_url="admin.services_offered_list",
                           save_url="admin.service_offered_new")


@admin_bp.route("/services-offered/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def service_offered_edit(item_id):
    item = ServiceOffered.query.get_or_404(item_id)
    if request.method == "POST":
        old_order = item.order
        requested_order = int(request.form.get("order", 0))
        item.order = reorder_on_update(ServiceOffered, item.id, old_order, requested_order)
        item.text = request.form.get("text", "").strip()
        item.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Item updated.", "success")
        return redirect(url_for("admin.services_offered_list"))
    return render_template("admin/simple_list_form.html", item=item,
                           title="Service Offered",
                           list_url="admin.services_offered_list",
                           save_url="admin.service_offered_edit")


@admin_bp.route("/services-offered/<int:item_id>/delete", methods=["POST"])
@admin_required
def service_offered_delete(item_id):
    item = ServiceOffered.query.get_or_404(item_id)
    deleted_order = item.order
    db.session.delete(item)
    db.session.commit()
    reorder_on_delete(ServiceOffered, deleted_order)
    db.session.commit()
    flash("Item deleted.", "success")
    return redirect(url_for("admin.services_offered_list"))


# ── EQUIPMENT ITEMS (simple list) ──────────────────────────────────────────

@admin_bp.route("/equipment-items")
@admin_required
def equipment_items_list():
    items = EquipmentItem.query.order_by(EquipmentItem.order).all()
    return render_template("admin/simple_list.html",
                           items=items, kind="equipment_items",
                           title="Equipment Available",
                           list_url="admin.equipment_items_list",
                           new_url="admin.equipment_item_new",
                           edit_url="admin.equipment_item_edit",
                           delete_url="admin.equipment_item_delete")


@admin_bp.route("/equipment-items/new", methods=["GET", "POST"])
@admin_required
def equipment_item_new():
    if request.method == "POST":
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(EquipmentItem, requested_order)
        item = EquipmentItem(
            text=request.form.get("text", "").strip(),
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(item)
        db.session.commit()
        flash("Item added.", "success")
        return redirect(url_for("admin.equipment_items_list"))
    return render_template("admin/simple_list_form.html", item=None,
                           title="Equipment Item",
                           list_url="admin.equipment_items_list",
                           save_url="admin.equipment_item_new")


@admin_bp.route("/equipment-items/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def equipment_item_edit(item_id):
    item = EquipmentItem.query.get_or_404(item_id)
    if request.method == "POST":
        old_order = item.order
        requested_order = int(request.form.get("order", 0))
        item.order = reorder_on_update(EquipmentItem, item.id, old_order, requested_order)
        item.text = request.form.get("text", "").strip()
        item.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Item updated.", "success")
        return redirect(url_for("admin.equipment_items_list"))
    return render_template("admin/simple_list_form.html", item=item,
                           title="Equipment Item",
                           list_url="admin.equipment_items_list",
                           save_url="admin.equipment_item_edit")


@admin_bp.route("/equipment-items/<int:item_id>/delete", methods=["POST"])
@admin_required
def equipment_item_delete(item_id):
    item = EquipmentItem.query.get_or_404(item_id)
    deleted_order = item.order
    db.session.delete(item)
    db.session.commit()
    reorder_on_delete(EquipmentItem, deleted_order)
    db.session.commit()
    flash("Item deleted.", "success")
    return redirect(url_for("admin.equipment_items_list"))


# ── CORE VALUES ─────────────────────────────────────────────────────────────

@admin_bp.route("/core-values")
@admin_required
def core_values_list():
    values = CoreValue.query.order_by(CoreValue.order).all()
    return render_template("admin/core_values.html", values=values)


@admin_bp.route("/core-values/new", methods=["GET", "POST"])
@admin_required
def core_value_new():
    if request.method == "POST":
        requested_order = int(request.form.get("order", 0))
        safe_order = reorder_on_create(CoreValue, requested_order)
        value = CoreValue(
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            order=safe_order,
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(value)
        db.session.commit()
        flash("Core value created.", "success")
        return redirect(url_for("admin.core_values_list"))
    return render_template("admin/core_value_form.html", value=None)


@admin_bp.route("/core-values/<int:value_id>/edit", methods=["GET", "POST"])
@admin_required
def core_value_edit(value_id):
    value = CoreValue.query.get_or_404(value_id)
    if request.method == "POST":
        old_order = value.order
        requested_order = int(request.form.get("order", 0))
        value.order = reorder_on_update(CoreValue, value.id, old_order, requested_order)
        value.title = request.form.get("title", "").strip()
        value.description = request.form.get("description", "").strip()
        value.is_published = bool(request.form.get("is_published"))
        db.session.commit()
        flash("Core value updated.", "success")
        return redirect(url_for("admin.core_values_list"))
    return render_template("admin/core_value_form.html", value=value)


@admin_bp.route("/core-values/<int:value_id>/delete", methods=["POST"])
@admin_required
def core_value_delete(value_id):
    value = CoreValue.query.get_or_404(value_id)
    deleted_order = value.order
    db.session.delete(value)
    db.session.commit()
    reorder_on_delete(CoreValue, deleted_order)
    db.session.commit()
    flash("Core value deleted.", "success")
    return redirect(url_for("admin.core_values_list"))
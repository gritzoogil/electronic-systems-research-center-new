from flask import Blueprint, render_template
import resend
import os
from collections import defaultdict
from app.models import (
    Staff, OJT, Project, Publication,
    AccomplishmentReport, CenterHighlight, LearningResource, db
)

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    projects = Project.query.filter_by(is_published=True).order_by(Project.order).all()
    staff = Staff.query.filter_by(is_published=True).order_by(Staff.order).all()
    publications = Publication.query.filter_by(is_published=True).order_by(Publication.date.desc()).all()

    stats = {
        "projects": Project.query.filter_by(is_published=True).count(),
        "publications": Publication.query.filter_by(is_published=True).count(),
        "staff": Staff.query.filter_by(is_published=True).count(),
    }
    return render_template("index.html", projects=projects, staff=staff, publications=publications, stats=stats)


@public_bp.route("/team")
def team():
    staff = Staff.query.filter_by(is_published=True).order_by(Staff.order).all()
    ojt_list = OJT.query.filter_by(is_published=True).order_by(OJT.batch_label, OJT.order).all()

    # Group OJT by batch_label in Python — Jinja2 groupby only groups consecutive items
    ojt_batches = defaultdict(list)
    for intern in ojt_list:
        label = intern.batch_label or "Interns"
        ojt_batches[label].append(intern)

    return render_template("team.html", staff=staff, ojt_batches=dict(ojt_batches))


@public_bp.route("/publications")
def publications():
    pubs = Publication.query.filter_by(is_published=True).order_by(Publication.date.desc()).all()
    return render_template("publications.html", publications=pubs)


@public_bp.route("/accomplishments")
def accomplishments():
    reports = (
        AccomplishmentReport.query
        .filter_by(is_published=True)
        .order_by(AccomplishmentReport.year.desc(), AccomplishmentReport.quarter.desc())
        .all()
    )
    return render_template("accomplishments.html", reports=reports)


@public_bp.route("/center-highlights")
def center_highlights():
    highlights = (
        CenterHighlight.query
        .filter_by(is_published=True)
        .order_by(CenterHighlight.date.desc())
        .all()
    )
    return render_template("center_highlights.html", highlights=highlights)


@public_bp.route("/resources")
def resources():
    items = (
        LearningResource.query
        .filter_by(is_published=True)
        .order_by(LearningResource.order)
        .all()
    )
    return render_template("resources.html", resources=items)

@public_bp.route("/projects")
def projects():
    all_projects = Project.query.filter_by(is_published=True).order_by(Project.order).all()
    return render_template("projects.html", projects=all_projects)


@public_bp.route("/projects/<int:project_id>")
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template("project_detail.html", project=project)


@public_bp.route("/publications/<int:pub_id>")
def publication_detail(pub_id):
    pub = Publication.query.get_or_404(pub_id)
    return render_template("publication_detail.html", publication=pub)


from flask import request, redirect, url_for, flash
from app.models import ContactMessage

resend.api_key = os.environ.get("RESEND_API_KEY")

@public_bp.route("/contact", methods=["POST"])
def contact_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "").strip()
    org = request.form.get("org", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("public.home") + "#contact")

    new_msg = ContactMessage(name=name, email=email, subject=subject, organization=org, message=message)
    db.session.add(new_msg)
    db.session.commit()

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",  # swap once domain is verified
            "to": ["esrc.batstateutneu@gmail.com"],
            "subject": f"New Contact Form Submission: {subject or 'No subject'}",
            "html": f"""
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Organization:</strong> {org or 'N/A'}</p>
                <p><strong>Subject:</strong> {subject or 'N/A'}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
            """,
        })
    except Exception as e:
        print(f"Email send failed: {e}")  # don't block the form submission if email fails

    flash("Message sent! We'll get back to you within 1-2 business days.", "success")
    return redirect(url_for("public.home") + "#contact")

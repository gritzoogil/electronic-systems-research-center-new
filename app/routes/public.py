from flask import Blueprint, render_template
from collections import defaultdict
from app.models import (
    Staff, OJT, Project, Publication,
    AccomplishmentReport, CenterHighlight, LearningResource
)

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    projects = Project.query.filter_by(is_published=True).order_by(Project.order).all()
    return render_template("index.html", projects=projects)


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
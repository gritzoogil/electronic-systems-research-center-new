from flask import Blueprint, render_template, request
import resend
import os
from datetime import datetime
from collections import defaultdict
from app.models import (
    Staff, OJT, Project, Publication,
    AccomplishmentReport, CenterHighlight, LearningResource,
    SiteSettings, Partner
)

public_bp = Blueprint("public", __name__)

def _parse_pub_date(date_str):
    """Publication.date is a free-text string like 'May 07, 2025'.
    Parse it into a real datetime so sorting is chronological, not alphabetical.
    Unparseable/empty values sort to the very end."""
    if not date_str:
        return datetime.min
    formats = ["%B %d, %Y", "%B %Y", "%Y-%m-%d", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.min

@public_bp.route("/")
def home():
    projects = (
        Project.query
        .filter_by(is_published=True, is_featured=True)
        .order_by(Project.order)
        .limit(6)
        .all()
    )
    staff = Staff.query.filter_by(is_published=True).order_by(Staff.order).all()
    publications = (
        Publication.query
        .filter_by(is_published=True, is_featured=True)
        .order_by(Publication.date.desc())
        .limit(3)
        .all()
    )
    partners = Partner.query.filter_by(is_published=True).order_by(Partner.order).all()
    settings = SiteSettings.query.get(1)
    stats = {
        "projects": Project.query.filter_by(is_published=True).count(),
        "publications": Publication.query.filter_by(is_published=True).count(),
        "staff": Staff.query.filter_by(is_published=True).count(),
    }
    return render_template("index.html", projects=projects, staff=staff,
                           publications=publications, partners=partners,
                           settings=settings, stats=stats)


@public_bp.route("/team")
def team():
    staff = Staff.query.filter_by(is_published=True, is_core_staff=True).order_by(Staff.order).all()
    ojt_list = OJT.query.filter_by(is_published=True).order_by(OJT.batch_label, OJT.order).all()

    # Group OJT by batch_label in Python — Jinja2 groupby only groups consecutive items
    ojt_batches = defaultdict(list)
    for intern in ojt_list:
        label = intern.batch_label or "Interns"
        ojt_batches[label].append(intern)

    return render_template("team.html", staff=staff, ojt_batches=dict(ojt_batches))


@public_bp.route("/publications")
def publications():
    page = request.args.get("page", 1, type=int)
    type_filter = request.args.get("type", "all")
    query_text = request.args.get("q", "").strip()
    per_page = 5
    is_ajax = request.headers.get("X-Requested-With") == "fetch"

    all_pubs = Publication.query.filter_by(is_published=True).all()

    if type_filter != "all":
        all_pubs = [
            p for p in all_pubs
            if type_filter in (p.type or "other").lower().replace(" ", "")
        ]

    if query_text:
        q_lower = query_text.lower()
        def matches(p):
            haystack = " ".join(filter(None, [
                _strip_markup(p.title), _strip_markup(p.summary), _strip_markup(p.details),
                p.keyword1, p.keyword2, p.keyword3
            ])).lower()
            return q_lower in haystack
        all_pubs = [p for p in all_pubs if matches(p)]

    all_pubs.sort(key=lambda p: _parse_pub_date(p.date), reverse=True)

    total = len(all_pubs)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = all_pubs[start:end]

    class SimplePagination:
        def __init__(self, page, per_page, total, items):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.items = items
            self.pages = max(1, (total + per_page - 1) // per_page)
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

        def iter_pages(self, left_edge=1, right_edge=1, left_current=1, right_current=2):
            last = 0
            for num in range(1, self.pages + 1):
                if (num <= left_edge
                        or (num > self.page - left_current - 1 and num < self.page + right_current)
                        or num > self.pages - right_edge):
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    pagination = SimplePagination(page, per_page, total, page_items)

    context = dict(
        publications=pagination.items,
        pagination=pagination,
        active_type=type_filter,
        active_q=query_text,
    )

    if is_ajax:
        return render_template("partials/publications_results.html", **context)

    return render_template("publications.html", **context)


@public_bp.route("/accomplishments")
def accomplishments():
    reports = (
        AccomplishmentReport.query
        .filter_by(is_published=True)
        .order_by(AccomplishmentReport.year.desc(), AccomplishmentReport.quarter.desc())
        .all()
    )
    return render_template("accomplishments.html", reports=reports)

@public_bp.route("/accomplishments/<int:report_id>")
def accomplishment_detail(report_id):
    report = AccomplishmentReport.query.get_or_404(report_id)
    return render_template("accomplishment_detail.html", report=report)


import re
import unicodedata

def _strip_markup(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)   # 𝐂𝐚𝐫𝐥𝐨𝐬 → Carlos
    text = re.sub(r"<[^>]+>", "", text)          # strip HTML tags, just in case
    text = re.sub(r"[*_`]+", "", text)           # strip markdown emphasis markers
    text = re.sub(r"\s+", " ", text).strip()
    return text


@public_bp.route("/center-highlights")
def center_highlights():
    page = request.args.get("page", 1, type=int)
    query_text = request.args.get("q", "").strip()
    year_filter = request.args.get("year", "all")
    per_page = 6
    is_ajax = request.headers.get("X-Requested-With") == "fetch"

    base_query = CenterHighlight.query.filter_by(is_published=True)

    if year_filter != "all":
        try:
            year_int = int(year_filter)
            base_query = base_query.filter(db.extract("year", CenterHighlight.date) == year_int)
        except ValueError:
            pass

    all_highlights = base_query.order_by(CenterHighlight.date.desc()).all()

    # Text search happens in Python against stripped (plain-text) versions
    # of title/description, so bold/markup spans don't break substring matching.
    if query_text:
        q_lower = _strip_markup(query_text).lower()  # normalize the search term too, in case someone pastes fancy text into the search box itself
        def matches(h):
            haystack = _strip_markup(h.title) + " " + _strip_markup(h.description or "")
            return q_lower in haystack.lower()
        all_highlights = [h for h in all_highlights if matches(h)]

    total = len(all_highlights)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = all_highlights[start:end]

    class SimplePagination:
        def __init__(self, page, per_page, total, items):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.items = items
            self.pages = max(1, (total + per_page - 1) // per_page)
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

        def iter_pages(self, left_edge=1, right_edge=1, left_current=1, right_current=2):
            last = 0
            for num in range(1, self.pages + 1):
                if (num <= left_edge
                        or (num > self.page - left_current - 1 and num < self.page + right_current)
                        or num > self.pages - right_edge):
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    pagination = SimplePagination(page, per_page, total, page_items)

    context = dict(
        highlights=pagination.items,
        pagination=pagination,
        active_q=query_text,
        active_year=year_filter,
    )

    if is_ajax:
        return render_template("partials/highlights_results.html", **context)

    all_dates = [
        h.date for h in
        CenterHighlight.query.filter_by(is_published=True).with_entities(CenterHighlight.date).all()
        if h.date
    ]
    available_years = sorted({d.year for d in all_dates}, reverse=True)

    return render_template("center-highlights.html", available_years=available_years, **context)


@public_bp.route("/resources")
def resources():
    items = (
        LearningResource.query
        .filter_by(is_published=True)
        .order_by(LearningResource.order)
        .all()
    )
    return render_template("resources.html", resources=items)

@public_bp.route("/resources/<int:resource_id>")
def resource_detail(resource_id):
    resource = LearningResource.query.get_or_404(resource_id)
    return render_template("resource_detail.html", resource=resource)

@public_bp.route("/resources/<int:resource_id>/page/<int:page_id>")
def resource_page(resource_id, page_id):
    page = ResourcePage.query.get_or_404(page_id)
    return render_template("resource_page.html", page=page)

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


from flask import redirect, url_for, flash
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

from flask import Blueprint, g, jsonify, render_template, request
import os
import requests
from werkzeug.utils import secure_filename

from app.auth import require_firebase_user, require_admin_role
from app.models import (
    Staff,
    OJT,
    Project,
    Publication,
    AccomplishmentReport,
    CenterHighlight,
    CenterHighlightImage,
    LearningResource,
    ResourcePage,
    db,
)


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/")
def admin_dashboard():

    team_items = Staff.query.order_by(Staff.order).all()
    resource_items = LearningResource.query.order_by(LearningResource.order).all()
    project_items = Project.query.order_by(Project.order).all()
    publication_items = Publication.query.all()
    highlight_items = CenterHighlight.query.all()

    stats = {
        "team": sum(1 for item in team_items if item.is_published),
        "resources": sum(1 for item in resource_items if item.is_published),
        "projects": sum(1 for item in project_items if item.is_published),
        "publications": len(publication_items),
        "highlights": len(highlight_items),
    }

    team_data = [
        {
            "name": item.name,
            "role": item.role,
            "is_published": item.is_published,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in team_items
    ]
    resources_data = [
        {
            "title": item.title,
            "description": item.description,
            "is_published": item.is_published,
            "order": item.order,
        }
        for item in resource_items
    ]
    projects_data = [
        {
            "title": item.title,
            "type": "Project",
            "is_published": item.is_published,
            "updated": item.created_at.strftime("%b %d, %Y") if item.created_at else "—",
        }
        for item in project_items
    ]

    firebase_config = {
        "apiKey": os.environ.get("FIREBASE_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    }

    return render_template(
        "admin.html",
        stats=stats,
        team_data=team_data,
        resources_data=resources_data,
        projects_data=projects_data,
        firebase_config=firebase_config,
    )



@admin_bp.get("/dashboard")
def admin_dashboard_alias():
    return admin_dashboard()


@admin_bp.get("/me")
@require_firebase_user
def current_admin_user():

    firebase_user = g.firebase_user
    return jsonify(
        {
            "uid": firebase_user.get("uid"),
            "email": firebase_user.get("email"),
            "email_verified": firebase_user.get("email_verified", False),
        }
    )


@admin_bp.route("/ping")
@require_firebase_user
def ping():
    return jsonify({"message": "Admin access confirmed"})


def _parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _require_editor():
    # Backwards-compatible no-op placeholder if roles are not yet configured.
    # Actual enforcement is handled by require_admin_role.
    return


# =============================
# ========== STAFF ============
# =============================


@admin_bp.get("/api/staff")
@require_admin_role
def list_staff():
    published = _parse_bool(request.args.get("published"), default=True)
    q = Staff.query
    q = q.filter_by(is_published=published)
    items = q.order_by(Staff.order, Staff.id).all()
    return jsonify(
        [
            {
                "id": i.id,
                "name": i.name,
                "role": i.role,
                "bio": i.bio,
                "photo_url": i.photo_url,
                "image_position": i.image_position,
                "image_scale": i.image_scale,
                "order": i.order,
                "is_published": i.is_published,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    )


@admin_bp.post("/api/staff")
@require_admin_role
def create_staff():
    data = request.get_json(force=True)
    i = Staff(
        name=(data.get("name") or "").strip(),
        role=(data.get("role") or "").strip() or None,
        bio=data.get("bio"),
        photo_url=(data.get("photo_url") or "").strip() or None,
        image_position=data.get("image_position") or "center",
        image_scale=data.get("image_scale") or 1.0,
        order=data.get("order") or 0,
        is_published=bool(data.get("is_published", True)),
    )
    db.session.add(i)
    db.session.commit()
    return jsonify({"id": i.id}), 201


@admin_bp.put("/api/staff/<int:staff_id>")
@require_admin_role
def update_staff(staff_id: int):
    i = Staff.query.get_or_404(staff_id)
    data = request.get_json(force=True)

    i.name = (data.get("name") or "").strip()
    i.role = (data.get("role") or "").strip() or None
    i.bio = data.get("bio")
    i.photo_url = (data.get("photo_url") or "").strip() or None
    i.image_position = data.get("image_position") or i.image_position
    if "image_scale" in data:
        i.image_scale = data.get("image_scale")
    if "order" in data:
        i.order = data.get("order")
    if "is_published" in data:
        i.is_published = bool(data.get("is_published"))

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/api/staff/<int:staff_id>")
@require_admin_role
def delete_staff(staff_id: int):
    i = Staff.query.get_or_404(staff_id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({"ok": True})


# =============================
# ============ OJT ============
# =============================


@admin_bp.get("/api/ojt")
@require_admin_role
def list_ojt():
    published = _parse_bool(request.args.get("published"), default=True)
    q = OJT.query.filter_by(is_published=published)
    items = q.order_by(OJT.batch_label, OJT.order, OJT.id).all()
    return jsonify(
        [
            {
                "id": i.id,
                "name": i.name,
                "email": i.email,
                "course": i.course,
                "photo_url": i.photo_url,
                "batch_label": i.batch_label,
                "order": i.order,
                "is_published": i.is_published,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    )


@admin_bp.post("/api/ojt")
@require_admin_role
def create_ojt():
    data = request.get_json(force=True)
    i = OJT(
        name=(data.get("name") or "").strip(),
        email=(data.get("email") or "").strip() or None,
        course=(data.get("course") or "").strip() or None,
        photo_url=(data.get("photo_url") or "").strip() or None,
        batch_label=(data.get("batch_label") or "").strip() or None,
        order=data.get("order") or 0,
        is_published=bool(data.get("is_published", True)),
    )
    db.session.add(i)
    db.session.commit()
    return jsonify({"id": i.id}), 201


@admin_bp.put("/api/ojt/<int:ojt_id>")
@require_admin_role
def update_ojt(ojt_id: int):
    i = OJT.query.get_or_404(ojt_id)
    data = request.get_json(force=True)

    i.name = (data.get("name") or "").strip()
    i.email = (data.get("email") or "").strip() or None
    i.course = (data.get("course") or "").strip() or None
    i.photo_url = (data.get("photo_url") or "").strip() or None
    i.batch_label = (data.get("batch_label") or "").strip() or None
    if "order" in data:
        i.order = data.get("order")
    if "is_published" in data:
        i.is_published = bool(data.get("is_published"))

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/api/ojt/<int:ojt_id>")
@require_admin_role
def delete_ojt(ojt_id: int):
    i = OJT.query.get_or_404(ojt_id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({"ok": True})


# =============================
# ========== PROJECTS =========
# =============================


@admin_bp.get("/api/projects")
@require_admin_role
def list_projects():
    published = _parse_bool(request.args.get("published"), default=True)
    items = Project.query.filter_by(is_published=published).order_by(Project.order, Project.id).all()
    return jsonify(
        [
            {
                "id": i.id,
                "title": i.title,
                "year": i.year,
                "description": i.description,
                "img_path": i.img_path,
                "alt_text": i.alt_text,
                "more_info_img": i.more_info_img,
                "image_position": "center",  # maintained in templates; model doesn't have it.
                "order": i.order,
                "is_published": i.is_published,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    )


@admin_bp.post("/api/projects")
@require_admin_role
def create_project():
    data = request.get_json(force=True)
    i = Project(
        title=(data.get("title") or "").strip(),
        year=(data.get("year") or "").strip() or None,
        description=data.get("description"),
        img_path=(data.get("img_path") or "").strip() or None,
        alt_text=(data.get("alt_text") or "").strip() or None,
        more_info_img=(data.get("more_info_img") or "").strip() or None,
        order=data.get("order") or 0,
        is_published=bool(data.get("is_published", True)),
    )
    db.session.add(i)
    db.session.commit()
    return jsonify({"id": i.id}), 201


@admin_bp.put("/api/projects/<int:project_id>")
@require_admin_role
def update_project(project_id: int):
    i = Project.query.get_or_404(project_id)
    data = request.get_json(force=True)

    if "title" in data:
        i.title = (data.get("title") or "").strip()
    if "year" in data:
        i.year = (data.get("year") or "").strip() or None
    if "description" in data:
        i.description = data.get("description")
    if "img_path" in data:
        i.img_path = (data.get("img_path") or "").strip() or None
    if "alt_text" in data:
        i.alt_text = (data.get("alt_text") or "").strip() or None
    if "more_info_img" in data:
        i.more_info_img = (data.get("more_info_img") or "").strip() or None
    if "order" in data:
        i.order = data.get("order")
    if "is_published" in data:
        i.is_published = bool(data.get("is_published"))

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/api/projects/<int:project_id>")
@require_admin_role
def delete_project(project_id: int):
    i = Project.query.get_or_404(project_id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({"ok": True})


# =============================
# ======= LEARNING RES =======
# =============================


@admin_bp.get("/api/resources")
@require_admin_role
def list_resources():
    published = _parse_bool(request.args.get("published"), default=True)
    items = LearningResource.query.filter_by(is_published=published).order_by(LearningResource.order, LearningResource.id).all()
    return jsonify(
        [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "thumbnail_url": i.thumbnail_url,
                "order": i.order,
                "is_published": i.is_published,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "pages": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "page_type": p.page_type,
                        "embed_url": p.embed_url,
                        "order": p.order,
                    }
                    for p in i.pages
                ],
            }
            for i in items
        ]
    )


@admin_bp.post("/api/resources")
@require_admin_role
def create_resource():
    data = request.get_json(force=True)
    i = LearningResource(
        title=(data.get("title") or "").strip(),
        description=data.get("description"),
        thumbnail_url=(data.get("thumbnail_url") or "").strip() or None,
        order=data.get("order") or 0,
        is_published=bool(data.get("is_published", True)),
    )
    db.session.add(i)
    db.session.flush()

    # optional pages bulk create
    pages = data.get("pages") or []
    for p_idx, p in enumerate(pages):
        db.session.add(
            ResourcePage(
                resource_id=i.id,
                title=(p.get("title") or "").strip(),
                page_type=p.get("page_type") or "flipbook",
                embed_url=p.get("embed_url"),
                order=p.get("order", p_idx),
            )
        )

    db.session.commit()
    return jsonify({"id": i.id}), 201


@admin_bp.put("/api/resources/<int:resource_id>")
@require_admin_role
def update_resource(resource_id: int):
    i = LearningResource.query.get_or_404(resource_id)
    data = request.get_json(force=True)

    if "title" in data:
        i.title = (data.get("title") or "").strip()
    if "description" in data:
        i.description = data.get("description")
    if "thumbnail_url" in data:
        i.thumbnail_url = (data.get("thumbnail_url") or "").strip() or None
    if "order" in data:
        i.order = data.get("order")
    if "is_published" in data:
        i.is_published = bool(data.get("is_published"))

    # Pages: simplest approach is replace all if pages provided.
    if "pages" in data:
        ResourcePage.query.filter_by(resource_id=i.id).delete()
        db.session.flush()
        pages = data.get("pages") or []
        for p_idx, p in enumerate(pages):
            db.session.add(
                ResourcePage(
                    resource_id=i.id,
                    title=(p.get("title") or "").strip(),
                    page_type=p.get("page_type") or "flipbook",
                    embed_url=p.get("embed_url"),
                    order=p.get("order", p_idx),
                )
            )

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/api/resources/<int:resource_id>")
@require_admin_role
def delete_resource(resource_id: int):
    i = LearningResource.query.get_or_404(resource_id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({"ok": True})


# =============================
# ======= PUBLICATIONS =======
# =============================


@admin_bp.get("/api/publications")
@require_admin_role
def list_publications():
    published = _parse_bool(request.args.get("published"), default=True)
    items = (
        Publication.query.filter_by(is_published=published)
        .order_by(Publication.created_at.desc(), Publication.id)
        .all()
    )
    return jsonify(
        [
            {
                "id": i.id,
                "title": i.title,
                "date": i.date,
                "type": i.type,
                "summary": i.summary,
                "details": i.details,
                "keyword1": i.keyword1,
                "keyword2": i.keyword2,
                "keyword3": i.keyword3,
                "link": i.link,
                "is_published": i.is_published,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    )


@admin_bp.post("/api/publications")
@require_admin_role
def create_publication():
    data = request.get_json(force=True)
    i = Publication(
        title=(data.get("title") or "").strip(),
        date=(data.get("date") or "").strip() or None,
        type=(data.get("type") or "").strip() or None,
        summary=data.get("summary"),
        details=data.get("details"),
        keyword1=(data.get("keyword1") or "").strip() or None,
        keyword2=(data.get("keyword2") or "").strip() or None,
        keyword3=(data.get("keyword3") or "").strip() or None,
        link=(data.get("link") or "").strip() or None,
        is_published=bool(data.get("is_published", True)),
    )
    db.session.add(i)
    db.session.commit()
    return jsonify({"id": i.id}), 201


@admin_bp.put("/api/publications/<int:pub_id>")
@require_admin_role
def update_publication(pub_id: int):
    i = Publication.query.get_or_404(pub_id)
    data = request.get_json(force=True)

    if "title" in data:
        i.title = (data.get("title") or "").strip()
    if "date" in data:
        i.date = (data.get("date") or "").strip() or None
    if "type" in data:
        i.type = (data.get("type") or "").strip() or None
    if "summary" in data:
        i.summary = data.get("summary")
    if "details" in data:
        i.details = data.get("details")
    if "keyword1" in data:
        i.keyword1 = (data.get("keyword1") or "").strip() or None
    if "keyword2" in data:
        i.keyword2 = (data.get("keyword2") or "").strip() or None
    if "keyword3" in data:
        i.keyword3 = (data.get("keyword3") or "").strip() or None
    if "link" in data:
        i.link = (data.get("link") or "").strip() or None
    if "is_published" in data:
        i.is_published = bool(data.get("is_published"))

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/api/publications/<int:pub_id>")
@require_admin_role
def delete_publication(pub_id: int):
    i = Publication.query.get_or_404(pub_id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({"ok": True})


# =============================
# ===== ACCOMPLISHMENTS ======
# =============================


@admin_bp.get("/api/accomplishments")
@require_admin_role
def list_accomplishments():
    published = _parse_bool(request.args.get("published"), default=True)
    items = (
        AccomplishmentReport.query.filter_by(is_published=published)
        .order_by(AccomplishmentReport.year.desc(), AccomplishmentReport.quarter.desc(), AccomplishmentReport.id)
        .all()
    )
    return jsonify(
        [
            {
                "id": i.id,
                "year": i.year,
                "quarter": i.quarter,
                "title": i.title,
                "description": i.description,
                "thumbnail_url": i.thumbnail_url,
                "flipbook_link": i.flipbook_link,
                "is_published": i.is_published,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    )


@admin_bp.post("/api/accomplishments")
@require_admin_role
def create_accomplishment():
    data = request.get_json(force=True)
    i = AccomplishmentReport(
        year=int(data.get("year")),
        quarter=int(data.get("quarter")),
        title=(data.get("title") or None),
        description=data.get("description"),
        thumbnail_url=(data.get("thumbnail_url") or "").strip() or None,
        flipbook_link=(data.get("flipbook_link") or "").strip() or None,
        is_published=bool(data.get("is_published", True)),
    )
    db.session.add(i)
    db.session.commit()
    return jsonify({"id": i.id}), 201


@admin_bp.put("/api/accomplishments/<int:acc_id>")
@require_admin_role
def update_accomplishment(acc_id: int):
    i = AccomplishmentReport.query.get_or_404(acc_id)
    data = request.get_json(force=True)

    if "year" in data:
        i.year = int(data.get("year"))
    if "quarter" in data:
        i.quarter = int(data.get("quarter"))
    if "title" in data:
        i.title = data.get("title")
    if "description" in data:
        i.description = data.get("description")
    if "thumbnail_url" in data:
        i.thumbnail_url = (data.get("thumbnail_url") or "").strip() or None
    if "flipbook_link" in data:
        i.flipbook_link = (data.get("flipbook_link") or "").strip() or None
    if "is_published" in data:
        i.is_published = bool(data.get("is_published"))

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/api/accomplishments/<int:acc_id>")
@require_admin_role
def delete_accomplishment(acc_id: int):
    i = AccomplishmentReport.query.get_or_404(acc_id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({"ok": True})


# =============================
# ======= CENTER HIGHLIGHTS ==
# =============================


@admin_bp.get("/api/highlights")
@require_admin_role
def list_highlights():
    published = _parse_bool(request.args.get("published"), default=True)
    items = (
        CenterHighlight.query.filter_by(is_published=published)
        .order_by(CenterHighlight.date.desc(), CenterHighlight.id)
        .all()
    )

    def img_list(h: CenterHighlight):
        return [
            {"id": im.id, "image_url": im.image_url, "order": im.order}
            for im in h.images
        ]

    return jsonify(
        [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "date": i.date.isoformat() if i.date else None,
                "alt_text": i.alt_text,
                "is_published": i.is_published,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "images": img_list(i),
            }
            for i in items
        ]
    )


@admin_bp.post("/api/highlights")
@require_admin_role
def create_highlight():
    data = request.get_json(force=True)
    i = CenterHighlight(
        title=(data.get("title") or "").strip(),
        description=data.get("description"),
        date=data.get("date"),
        alt_text=(data.get("alt_text") or "").strip() or None,
        is_published=bool(data.get("is_published", True)),
    )
    db.session.add(i)
    db.session.flush()

    images = data.get("images") or []
    for idx, im in enumerate(images):
        db.session.add(
            CenterHighlightImage(
                highlight_id=i.id,
                image_url=(im.get("image_url") or "").strip(),
                order=im.get("order", idx),
            )
        )

    db.session.commit()
    return jsonify({"id": i.id}), 201


@admin_bp.put("/api/highlights/<int:highlight_id>")
@require_admin_role
def update_highlight(highlight_id: int):
    i = CenterHighlight.query.get_or_404(highlight_id)
    data = request.get_json(force=True)

    if "title" in data:
        i.title = (data.get("title") or "").strip()
    if "description" in data:
        i.description = data.get("description")
    if "date" in data:
        i.date = data.get("date")
    if "alt_text" in data:
        i.alt_text = (data.get("alt_text") or "").strip() or None
    if "is_published" in data:
        i.is_published = bool(data.get("is_published"))

    # simplest: replace all images if provided
    if "images" in data:
        CenterHighlightImage.query.filter_by(highlight_id=i.id).delete()
        db.session.flush()
        images = data.get("images") or []
        for idx, im in enumerate(images):
            db.session.add(
                CenterHighlightImage(
                    highlight_id=i.id,
                    image_url=(im.get("image_url") or "").strip(),
                    order=im.get("order", idx),
                )
            )

    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/api/highlights/<int:highlight_id>")
@require_admin_role
def delete_highlight(highlight_id: int):
    i = CenterHighlight.query.get_or_404(highlight_id)
    db.session.delete(i)
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.put("/api/highlights/<int:highlight_id>/images/reorder")
@require_admin_role
def reorder_highlight_images(highlight_id: int):
    CenterHighlight.query.get_or_404(highlight_id)
    data = request.get_json(force=True)
    items = data.get("items") or []
    for it in items:
        img_id = it.get("id")
        new_order = it.get("order")
        if img_id is None or new_order is None:
            continue
        img = CenterHighlightImage.query.filter_by(id=int(img_id), highlight_id=highlight_id).one_or_none()
        if not img:
            continue
        img.order = int(new_order)
    db.session.commit()
    return jsonify({"ok": True})


# =============================
# ======= UPLOAD MEDIA =======
# =============================



def _get_blob_token() -> str:
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        # Keep error clear for admins.
        raise RuntimeError("Missing BLOB_READ_WRITE_TOKEN env var")
    return token.strip().strip('"')


def _blob_upload(blob_pathname: str, file_bytes: bytes, content_type: str) -> str:
    blob_token = _get_blob_token()

    # Vercel Blob accepts a PUT to /{pathname}.
    url = f"https://blob.vercel-storage.com/{blob_pathname}"
    resp = requests.put(
        url,
        data=file_bytes,
        headers={
            "authorization": f"Bearer {blob_token}",
            "x-content-type": content_type,
        },
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Blob upload failed: {resp.status_code} {resp.text}")

    payload = resp.json()
    return payload["url"]


def _allowed_image_mimetype(mimetype: str) -> bool:
    return mimetype.startswith("image/")


@admin_bp.post("/api/upload/image")
@require_admin_role
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "missing_file"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "missing_filename"}), 400

    mimetype = (f.mimetype or "").lower()
    if not _allowed_image_mimetype(mimetype):
        return jsonify({"error": "invalid_file_type"}), 400

    filename = secure_filename(f.filename)
    # basic safety: ensure an extension exists
    if "." not in filename:
        return jsonify({"error": "missing_extension"}), 400

    blob_pathname = f"images/{filename}"
    file_bytes = f.read()

    try:
        url = _blob_upload(blob_pathname, file_bytes, mimetype)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"url": url})


@admin_bp.post("/api/upload/pdf")
@require_admin_role
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "missing_file"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "missing_filename"}), 400

    mimetype = (f.mimetype or "").lower()
    if mimetype != "application/pdf":
        # Some browsers may send a generic mimetype; also allow by extension.
        if not f.filename.lower().endswith(".pdf"):
            return jsonify({"error": "invalid_file_type"}), 400

    filename = secure_filename(f.filename)
    if not filename.lower().endswith(".pdf"):
        # enforce .pdf
        filename = f"{filename}.pdf"

    blob_pathname = f"pdfs/{filename}"
    file_bytes = f.read()

    try:
        url = _blob_upload(blob_pathname, file_bytes, "application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"url": url})

    CenterHighlight.query.get_or_404(highlight_id)
    data = request.get_json(force=True)
    items = data.get("items") or []
    for it in items:
        img_id = it.get("id")
        new_order = it.get("order")
        if img_id is None or new_order is None:
            continue
        img = CenterHighlightImage.query.filter_by(id=int(img_id), highlight_id=highlight_id).one_or_none()
        if not img:
            continue
        img.order = int(new_order)
    db.session.commit()
    return jsonify({"ok": True})



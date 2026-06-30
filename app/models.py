from app import db
from datetime import datetime


class Staff(db.Model):
    """Center Head + Research Associates shown on team.html"""
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150))  # e.g. "Center Head, ESRC"
    bio = db.Column(db.Text)
    photo_url = db.Column(db.String(255))
    image_position = db.Column(db.String(30), default="center")
    image_scale = db.Column(db.Float, default=1.0)  
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OJT(db.Model):
    """Interns shown in team.html carousels"""
    __tablename__ = "ojt"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    course = db.Column(db.String(150))
    photo_url = db.Column(db.String(255))
    batch_label = db.Column(db.String(100))  # e.g. "2025-2026 Midterm Interns"
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Project(db.Model):
    """Research Projects shown on index.html (still admin-editable even if index.html itself is static elsewhere)"""
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(10))
    description = db.Column(db.Text)
    img_path = db.Column(db.String(255))
    alt_text = db.Column(db.String(255))
    more_info_img = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Publication(db.Model):
    __tablename__ = "publication"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)  # bumped from 255, just in case
    date = db.Column(db.String(50))
    type = db.Column(db.String(50))
    summary = db.Column(db.Text)
    details = db.Column(db.Text)
    keyword1 = db.Column(db.String(100))
    keyword2 = db.Column(db.String(100))
    keyword3 = db.Column(db.String(100))
    link = db.Column(db.Text)  # changed from String(255) — URLs can be very long
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AccomplishmentReport(db.Model):
    """accomplishment.html"""
    __tablename__ = "accomplishment_report"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)  # 1-4
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(255))
    flipbook_link = db.Column(db.String(255))  # link to the flipbook HTML/embed
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CenterHighlight(db.Model):
    """center-highlights.html — supports multiple images per article"""
    __tablename__ = "center_highlight"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    alt_text = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship("CenterHighlightImage", backref="highlight", cascade="all, delete-orphan", order_by="CenterHighlightImage.order")


class CenterHighlightImage(db.Model):
    __tablename__ = "center_highlight_image"

    id = db.Column(db.Integer, primary_key=True)
    highlight_id = db.Column(db.Integer, db.ForeignKey("center_highlight.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0)


class LearningResource(db.Model):
    """resources.html — books and course materials"""
    __tablename__ = "learning_resource"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(255))
    link = db.Column(db.String(255))  # links to the manager page with full content
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    __tablename__ = "contact_message"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255))
    organization = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
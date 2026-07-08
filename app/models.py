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
    is_core_staff = db.Column(db.Boolean, default=True)
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
    is_featured = db.Column(db.Boolean, default=False)


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
    is_featured = db.Column(db.Boolean, default=False)


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
    """A 'book'/course material, e.g. Design Principles and Logic Design"""
    __tablename__ = "learning_resource"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pages = db.relationship("ResourcePage", backref="resource", cascade="all, delete-orphan", order_by="ResourcePage.order")
    chapters = db.relationship("ResourceChapter", backref="resource",
                           cascade="all, delete-orphan",
                           order_by="ResourceChapter.order")


class ResourcePage(db.Model):
    __tablename__ = "resource_page"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("learning_resource.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    page_type = db.Column(db.String(20), default="flipbook")
    embed_url = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

class ContactMessage(db.Model):
    __tablename__ = "contact_message"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255))
    organization = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SiteSettings(db.Model):
    """Single-row table for sitewide config. Always use id=1."""
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    avp_video_url = db.Column(db.String(255), default="https://www.youtube.com/embed/Wa1IqM9Hn3c")
    contact_email = db.Column(db.String(150), default="esrc@g.batstate-u.edu.ph")
    contact_phone = db.Column(db.String(50), default="(043) 980-0385 local 2405")
    contact_address = db.Column(db.Text, default="2nd Flr. STEER Hub Building, Batangas State University Alangilan Campus, Batangas City 4200, Philippines")
    contact_office_hours = db.Column(db.String(150), default="Monday – Thursday, 7:00 AM – 8:00 PM")
    maps_embed_url = db.Column(db.Text)
    facebook_url = db.Column(db.String(255), default="https://www.facebook.com/ESRC.BatStateU")
    youtube_url = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Partner(db.Model):
    __tablename__ = "partner"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    logo_url = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ResourceChapter(db.Model):
    __tablename__ = "resource_chapter"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("learning_resource.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    flipbook_url = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)


class OJTAttendance(db.Model):
    __tablename__ = "ojt_attendance"

    id = db.Column(db.Integer, primary_key=True)
    ojt_id = db.Column(db.Integer, db.ForeignKey("ojt.id"), nullable=False)
    sr_code = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    time_in = db.Column(db.Time)
    time_out = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ojt = db.relationship("OJT", backref="attendances")

class Service(db.Model):
    """Bookable ESRC services shown on the public appointments page"""
    __tablename__ = "service"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=60, nullable=False)
    max_appointments_per_slot = db.Column(db.Integer, default=1, nullable=False)
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)  # availability toggle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Appointment(db.Model):
    """A visitor's appointment request"""
    __tablename__ = "appointment"

    STATUSES = ["Pending", "Approved", "Rejected", "Cancelled", "Completed", "No Show"]

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"), nullable=False)

    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    contact_number = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(200))
    purpose = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)

    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)

    status = db.Column(db.String(20), default="Pending", nullable=False)
    admin_notes = db.Column(db.Text)  # internal notes on approve/reject/reschedule

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service = db.relationship("Service", backref="appointments")


class BlockedDate(db.Model):
    """Admin-blocked dates/times — holidays, events, maintenance windows"""
    __tablename__ = "blocked_date"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255))
    is_full_day = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.Time)  # only used if not full_day
    end_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ScheduleConfig(db.Model):
    """Single-row table for booking-wide schedule rules. Always use id=1."""
    __tablename__ = "schedule_config"

    id = db.Column(db.Integer, primary_key=True)
    working_days = db.Column(db.String(50), default="Mon,Tue,Wed,Thu,Fri")  # comma-separated
    day_start_time = db.Column(db.Time, default=lambda: datetime.strptime("09:00", "%H:%M").time())
    day_end_time = db.Column(db.Time, default=lambda: datetime.strptime("17:00", "%H:%M").time())
    slot_duration_minutes = db.Column(db.Integer, default=60)
    max_appointments_per_day = db.Column(db.Integer, default=8)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
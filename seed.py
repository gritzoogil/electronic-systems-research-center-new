"""
Seeds the database from old static-site content.
Run AFTER upload_images.py has generated image_url_map.json.
Run with: uv run python seed.py
"""
import csv
import json
import os
import re
from datetime import datetime
from app import create_app, db
from app.models import AccomplishmentReport, Staff, OJT, Project, Publication, CenterHighlight, CenterHighlightImage

app = create_app()

image_map_path = "image_url_map.json"
if os.path.exists(image_map_path):
    with open(image_map_path, encoding="utf-8") as f:
        url_map = json.load(f)
else:
    url_map = {}
    print(f"{image_map_path} not found; continuing without resolved image URLs.")


def resolve_image(old_path):
    """Convert an old relative path like '../build/img/Staff/Dr.Sang.webp'
    into the new Firebase Storage URL using the map."""
    if not old_path:
        return None
    cleaned = old_path.replace("../build/img/", "").replace("/build/img/", "").strip()
    return url_map.get(cleaned, None)  # None if not found in map


with app.app_context():

    # --- STAFF ---
    staff_data = [
        ("Dr. Ralph Gerard B. Sangalang", "Center Head, ESRC",
         "Dr. Ralph Sangalang is an Associate Professor V at the Department of Electronics "
         "Engineering, College of Engineering, Batangas University - The National Engineering "
         "University, Alangilan, Batangas City. He also serves as the Center Head of the "
         "Electronic Research Center (ESRC), STEER Hub.",
         "Staff/Dr.Sang.webp", 1),
        ("Engr. Carlos Jhay A. Arroyo", "University Research Associate, ESRC",
         "Engr. Carlos Jhay A. Arroyo is a dedicated Instrumentation and Control Engineer "
         "from Balayan, Batangas. He currently serves as a University Research Associate and "
         "Project Technical Assistant at ESRC and DTC, STEERHub.",
         "Staff/engrcj.webp", 2),
        ("Engr. Ariel M. Rosales", "UNIRA, Project EIS",
         "Engr. Rosales earned a BS in Mechatronics Engineering from BatStateU TNEU, "
         "Alangilan Campus. His expertise lies in Industrial Automation, 3D Modeling, and Fabrication.",
         "Staff/engraries.webp", 3),
        ("Assoc. Prof Albertson D. Amante", "Director for STEERHUB, VPRDES BatStateU",
         "", "Staff/Engr.Amante.webp", 0),
    ]
    for name, role, bio, img_key, order in staff_data:
        db.session.add(Staff(
            name=name, role=role, bio=bio,
            photo_url=resolve_image(img_key), order=order,
        ))

    # --- OJT (kept from before, image keys updated to match map format) ---
    ojt_data = [
        ("Balmes, Genrique Sean Arkin D.", "23-06630@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/53.webp", "2025-2026 Midterm Interns"),
        ("Carranza, John Timothy S.", "23-05494@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/54.webp", "2025-2026 Midterm Interns"),
        ("De Castro, Ayelet D'arcy C.", "23-01387@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/55.webp", "2025-2026 Midterm Interns"),
        ("Guillermo, Gil Bryan O.", "23-09210@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/56.webp", "2025-2026 Midterm Interns"),
        ("Panganiban, Lenard Andrei V.", "23-02989@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/57.webp", "2025-2026 Midterm Interns"),
        ("Ramirez, Kent Iann V.", "23-00686@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/58.webp", "2025-2026 Midterm Interns"),
        # ... (rest of your OJT list from before — same data, just change photo_file to "OJT/<filename>")
    ]
    for idx, (name, email, course, img_key, batch) in enumerate(ojt_data):
        db.session.add(OJT(
            name=name, email=email, course=course,
            photo_url=resolve_image(img_key), batch_label=batch, order=idx,
        ))

    # --- PROJECTS (from research_projects.csv) ---
    with open("seed_data/research_projects.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            img_key = row["img_path"].replace("../build/img/", "").strip()
            more_info_key = row["more_info"].replace("../build/img/", "").strip() if row.get("more_info") else None
            db.session.add(Project(
                title=row["title"].strip(),
                year=row["year"].strip(),
                description=row["description"].strip(),
                img_path=resolve_image(img_key),
                more_info_img=resolve_image(more_info_key) if more_info_key else None,
                order=idx,
            ))

    # --- PUBLICATIONS (from dr_sang_publications.csv) ---
    with open("seed_data/dr_sang_publications.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.session.add(Publication(
                title=row["title"].strip(),
                date=row["date"].strip(),
                type=row["type"].strip(),
                summary=row["summary"].strip(),
                details=row["details"].strip(),
                keyword1=row.get("keyword1", "").strip(),
                keyword2=row.get("keyword2", "").strip(),
                keyword3=row.get("keyword3", "").strip(),
                link=row["link"].strip(),
            ))

    # --- CENTER HIGHLIGHTS (from research_center_highlights.csv) ---
    with open("seed_data/research_center_highlights.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date_obj = datetime.strptime(row["date"].strip(), "%m/%d/%Y").date()
            except ValueError:
                date_obj = None

            highlight = CenterHighlight(
                title=row["title"].strip(),
                description=row["description"].strip(),
                date=date_obj,
                alt_text=row.get("alt", "").strip(),
            )
            db.session.add(highlight)
            db.session.flush()  # get highlight.id before adding images

            for i, col in enumerate(["img1", "img2", "img3", "img4", "img5"], start=1):
                raw = row.get(col, "").strip()
                if raw:
                    img_key = raw.replace("../build/img/", "").strip()
                    resolved = resolve_image(img_key)
                    if resolved:
                        db.session.add(CenterHighlightImage(
                            highlight_id=highlight.id, image_url=resolved, order=i,
                        ))

    # --- ACCOMPLISHMENT REPORTS (skip duplicate 2026 report) ---
    db.session.query(AccomplishmentReport).delete()
    with open("seed_data/accomplishment_reports.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = row.get("year", "").strip()
            quarter = row.get("quarter", "").strip()
            if year == "2026":
                continue

            db.session.add(AccomplishmentReport(
                year=int(year),
                quarter=int(quarter),
                title=row.get("title", "").strip(),
                description=row.get("description", "").strip(),
                thumbnail_url=row.get("thumbnail_url", "").strip() or None,
                flipbook_link=row.get("flipbook_link", "").strip() or None,
                is_published=(row.get("is_published", "true").strip().lower() not in ["false", "0", "no"]),
            ))

    db.session.commit()
    print("Seeding complete.")
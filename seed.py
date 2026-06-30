"""
Seeds the database from old static-site content.
Run AFTER upload_images.py has generated image_url_map.json.
Run with: uv run python seed.py
"""
import csv
import json
import re
from datetime import datetime
from app import create_app, db
from app.models import Staff, OJT, Project, Publication, CenterHighlight, CenterHighlightImage

app = create_app()

with open("image_url_map.json", encoding="utf-8") as f:
    url_map = json.load(f)


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
        # 2025-2026 Midterm Interns
        ("Balmes, Genrique Sean Arkin D.", "23-06630@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/53.webp", "2025-2026 Midterm Interns"),
        ("Carranza, John Timothy S.", "23-05494@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/54.webp", "2025-2026 Midterm Interns"),
        ("De Castro, Ayelet D'arcy C.", "23-01387@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/55.webp", "2025-2026 Midterm Interns"),
        ("Guillermo, Gil Bryan O.", "23-09210@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/56.webp", "2025-2026 Midterm Interns"),
        ("Panganiban, Lenard Andrei V.", "23-02989@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/57.webp", "2025-2026 Midterm Interns"),
        ("Ramirez, Kent Iann V.", "23-00686@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/58.webp", "2025-2026 Midterm Interns"),

        # 2025-2026 2nd Semester Interns
        ("Carandang, Dave Andrei S.", "22-03603@g.batstate-u.edu.ph", "BS in Instrumentation and Control Engineering", "OJT/49.webp", "2025-2026 2nd Semester Interns"),
        ("Colambot, Kirsten Paulyn P.", "22-05058@g.batstate-u.edu.ph", "BS in Instrumentation and Control Engineering", "OJT/50.webp", "2025-2026 2nd Semester Interns"),
        ("Landicho, Juberson S.", "22-03534@g.batstate-u.edu.ph", "BIT Electronics Technology", "OJT/52.webp", "2025-2026 2nd Semester Interns"),
        ("Francisco, Vincent Jorge M.", "21-04599@g.batstate-u.edu.ph", "BIT Electronics Technology", "OJT/48.webp", "2025-2026 2nd Semester Interns"),
        ("Talban, John Lloyd J.", "21-01385@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/51.webp", "2025-2026 2nd Semester Interns"),

        # 2025-2026 1st Semester Interns
        ("Arago, Allan Jhasper P.", "21-06633@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/29.webp", "2025-2026 1st Semester Interns"),
        ("Capuno, Raphael Juno L.", "21-05238@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/30.webp", "2025-2026 1st Semester Interns"),
        ("Catayong, Russell A.", "22-02900@g.batstate-u.edu.ph", "BIT Electronics Technology", "OJT/31.webp", "2025-2026 1st Semester Interns"),
        ("De Castro, Rod Andrei N.", "21-03490@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/32.webp", "2025-2026 1st Semester Interns"),
        ("Datiles, Jiane Carl D.", "22-04980@g.batstate-u.edu.ph", "BIT - Electronics Technology", "OJT/33.webp", "2025-2026 1st Semester Interns"),
        ("Jambalos, Queian Kim F.", "21-03414@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/34.webp", "2025-2026 1st Semester Interns"),
        ("Libato, Jasper M.", "21-03740@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/35.webp", "2025-2026 1st Semester Interns"),
        ("Lintao, Christian", "22-05103@g.batstate-u.edu.ph", "BIT - Electronics Technology", "OJT/36.webp", "2025-2026 1st Semester Interns"),
        ("Marasigan, Jaezel Anne M.", "21-08841@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/37.webp", "2025-2026 1st Semester Interns"),
        ("Maristela, Mark Steven P.", "21-08278@g.batstate-u.edu.ph", "BIT - Electronics Technology", "OJT/38.webp", "2025-2026 1st Semester Interns"),
        ("Oliver, Ivy C.", "21-02272@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/39.webp", "2025-2026 1st Semester Interns"),
        ("Roxas, James Rodney G.", "22-09648@g.batstate-u.edu.ph", "BIT - Electronics Technology", "OJT/40.webp", "2025-2026 1st Semester Interns"),
        ("Sambile, Aezel F.", "21-01806@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/41.webp", "2025-2026 1st Semester Interns"),
        ("Pidoc, Jhoannes A.", "22-08765@g.batstate-u.edu.ph", "BIT - Electronics Technology", "OJT/42.webp", "2025-2026 1st Semester Interns"),
        ("Tenorio, Louis Angelo A.", "22-02240@g.batstate-u.edu.ph", "BIT - Electronics Technology", "OJT/43.webp", "2025-2026 1st Semester Interns"),

        # 2024-2025 Midterm Interns
        ("Marasigan, Xyzon Ezekiel R.", "22-00074@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/44.webp", "2024-2025 Midterm Interns"),
        ("Ramos, Mark Kevin I.", "22-04022@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/45.webp", "2024-2025 Midterm Interns"),
        ("Calalo, Homer M.", "22-05550@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/46.webp", "2024-2025 Midterm Interns"),
        ("Nuñez, Justin Mae T.", "22-02253@g.batstate-u.edu.ph", "BS in Computer Science", "OJT/47.webp", "2024-2025 Midterm Interns"),

        # 2024-2025 2nd Semester Interns
        ("Patrick James G. Verroya", "21-05720@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/1.webp", "2024-2025 2nd Semester Interns"),
        ("Brent Angelo M. Landicho", "21-00074@g.batstate-u.edu.ph", "BS Instrumentation and Control Engineering", "OJT/2.webp", "2024-2025 2nd Semester Interns"),
        ("Bryan E. Regana", "21-08516@g.batstate-u.edu.ph", "BS Instrumentation and Control Engineering", "OJT/3.webp", "2024-2025 2nd Semester Interns"),
        ("Billy M. Abante", "21-00453@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/4.webp", "2024-2025 2nd Semester Interns"),
        ("Jareck M. Mirano", "21-05304@g.batstate-u.edu.ph", "BS Instrumentation and Control Engineering", "OJT/5.webp", "2024-2025 2nd Semester Interns"),
        ("Gian Carl C. Tolentino", "21-01139@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/6.webp", "2024-2025 2nd Semester Interns"),
        ("Emmanuel B. Gumapac", "21-04067@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/7.webp", "2024-2025 2nd Semester Interns"),
        ("Dannielle Louis F. Abeleda", "21-04065@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/8.webp", "2024-2025 2nd Semester Interns"),
        ("Oliver M. Andal", "21-08145@g.batstate-u.edu.ph", "BS Instrumentation and Control Engineering", "OJT/9.webp", "2024-2025 2nd Semester Interns"),
        ("Lester John M. Umali", "21-05629@g.batstate-u.edu.ph", "BS Instrumentation and Control Engineering", "OJT/10.webp", "2024-2025 2nd Semester Interns"),
        ("Floriane A. Muñoz", "21-06029@g.batstate-u.edu.ph", "BS Mechatronics Engineering", "OJT/11.webp", "2024-2025 2nd Semester Interns"),
        ("Ashera Kathryn R. Aguilar", "21-32463@g.batstate-u.edu.ph", "BS Information Technology", "OJT/12.webp", "2024-2025 2nd Semester Interns"),
        ("Jhon Kyle P. Ilao", "21-36339@g.batstate-u.edu.ph", "BS Information Technology", "OJT/13.webp", "2024-2025 2nd Semester Interns"),

        # 2024-2025 1st Semester Interns
        ("John Romar A. Buenaflor", "20-04719@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/14.webp", "2024-2025 1st Semester Interns"),
        ("Earl John Aristeo O. Tupas", "21-04208@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/15.webp", "2024-2025 1st Semester Interns"),
        ("Lyka V. Solis", "21-09299@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/16.webp", "2024-2025 1st Semester Interns"),
        ("Gabriele Ely D. Castillo", "21-03287@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/17.webp", "2024-2025 1st Semester Interns"),
        ("Marvin I. Ariola", "19-07065@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/18.webp", "2024-2025 1st Semester Interns"),
        ("Ashley M. Bathan", "19-06617@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/19.webp", "2024-2025 1st Semester Interns"),
        ("Erica Michelle M. Aranda", "21-08420@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/20.webp", "2024-2025 1st Semester Interns"),
        ("Remuel John P. Arellano", "21-03001@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/21.webp", "2024-2025 1st Semester Interns"),
        ("Jhimuel C. Cadano", "21-06482@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/23.webp", "2024-2025 1st Semester Interns"),
        ("Marielle Ivy D. Taclob", "21-06329@g.batstate-u.edu.ph", "BS Electronics Engineering", "OJT/22.webp", "2024-2025 1st Semester Interns"),

        # 2023-2024 Midterm Interns
        ("Haron Lewer V. Muñoz", "21-09792@g.batstate-u.edu.ph", "BS Fine Arts & Design", "OJT/25.webp", "2023-2024 Midterm Interns"),
        ("Marian Joy A. Zara", "21-04192@g.batstate-u.edu.ph", "BS Fine Arts & Design", "OJT/26.webp", "2023-2024 Midterm Interns"),
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

    db.session.commit()
    print("Seeding complete.")
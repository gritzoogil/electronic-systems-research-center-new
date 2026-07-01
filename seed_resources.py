"""
Seeds Accomplishment Reports and Learning Resources from old static-site content.
Run AFTER seed.py has already populated image_url_map.json-based data.
Run with: uv run python seed_resources.py
"""
import json
from app import create_app, db
from app.models import AccomplishmentReport, LearningResource, ResourcePage

app = create_app()

with open("image_url_map.json", encoding="utf-8") as f:
    url_map = json.load(f)


def resolve_image(old_path):
    if not old_path:
        return None
    cleaned = old_path.replace("../build/img/", "").replace("/build/img/", "").strip()
    return url_map.get(cleaned, None)


with app.app_context():

    # --- ACCOMPLISHMENT REPORTS ---
    accomplishment_data = [
        (2025, 1, "1st Quarter Accomplishment Report 2025",
         "Highlights of the accomplishments in the first quarter of 2025.",
         "Accomplishments/Q1_2025.webp", "https://online.fliphtml5.com/pzzfx/xxdu/"),
        (2025, 2, "2nd Quarter Accomplishment Report 2025",
         "Highlights of the accomplishments in the second quarter of 2025.",
         "Accomplishments/Q2_2025.webp", "https://online.fliphtml5.com/pzzfx/lyty/"),
        (2025, 3, "3rd Quarter Accomplishment Report 2025",
         "Highlights of the accomplishments in the third quarter of 2025.",
         "Accomplishments/Q3_2025.webp", "https://online.fliphtml5.com/pzzfx/lqes/"),
        (2025, 4, "4th Quarter Accomplishment Report 2025",
         "Highlights of the accomplishments in the fourth quarter of 2025.",
         "Accomplishments/Q4_2025.webp", "https://online.fliphtml5.com/nnyxi/rgkf/"),
    ]

    for year, quarter, title, desc, img_key, flipbook_link in accomplishment_data:
        db.session.add(AccomplishmentReport(
            year=year, quarter=quarter, title=title, description=desc,
            thumbnail_url=resolve_image(img_key), flipbook_link=flipbook_link,
        ))

    # --- LEARNING RESOURCES ---
    resources_data = [
        {
            "title": "Design Principles and Logic Design",
            "description": "Introduction to Logic Circuits, Logic Gates, Clocks, Latches and Flip-flops",
            "thumbnail_key": "Book Thumbnail/Digital Principles and Logic.webp",
            "pages": [
                ("Exercises 1", "flipbook", "https://online.fliphtml5.com/pzzfx/yfay/"),
                ("Lab 1", "flipbook", "https://online.fliphtml5.com/pzzfx/ajix/"),
                ("Lesson 1", "flipbook", "https://online.fliphtml5.com/pzzfx/xaif/"),
                ("Lesson 2", "flipbook", "https://online.fliphtml5.com/pzzfx/cocx/"),
                ("Lesson 3", "flipbook", "https://online.fliphtml5.com/pzzfx/yeyb/"),
                ("Lesson 4", "flipbook", "https://online.fliphtml5.com/pzzfx/oawy/"),
                ("Lesson 5", "flipbook", "https://online.fliphtml5.com/pzzfx/tbii/"),
                ("Lesson 6", "flipbook", "https://online.fliphtml5.com/pzzfx/zoit/"),
                ("References", "flipbook", "https://online.fliphtml5.com/pzzfx/inku/"),
                ("Schematic", "flipbook", "https://online.fliphtml5.com/pzzfx/Schematic-f16I/"),
                ("Youtube List", "pdf", "https://docs.google.com/viewer?url=https://raw.githubusercontent.com/Electronic-Systems-Research-Center/Electronic-Systems-Research-Center.github.io/main/build/flipbook/Youtube%20List/Build%20an%208-bit%20computer%20from%20scratch.pdf&embedded=true"),
            ],
        },
        {
            "title": "Engineering Research",
            "description": "Introduction to research, citations, email etiquette, literature review, and methodology",
            "thumbnail_key": "Book Thumbnail/Engineering Research.webp",
            "pages": [
                ("Citation and Attribution", "flipbook", "https://online.fliphtml5.com/pzzfx/chei/"),
                ("Email Etiquette", "flipbook", "https://online.fliphtml5.com/pzzfx/dsbh/"),
                ("Engineering Reseach Methodology", "flipbook", "https://online.fliphtml5.com/pzzfx/sjfd/"),
                ("Intro to Research", "flipbook", "https://online.fliphtml5.com/pzzfx/moie/"),
                ("Literature Review", "flipbook", "https://online.fliphtml5.com/pzzfx/kxfi/"),
                ("Methodology", "flipbook", "https://online.fliphtml5.com/pzzfx/tjqq/"),
            ],
        },
    ]

    for res in resources_data:
        resource = LearningResource(
            title=res["title"],
            description=res["description"],
            thumbnail_url=resolve_image(res["thumbnail_key"]),
        )
        db.session.add(resource)
        db.session.flush()  # get resource.id before adding pages
        for idx, (page_title, page_type, link) in enumerate(res["pages"]):
            db.session.add(ResourcePage(
                resource_id=resource.id, title=page_title, page_type=page_type,
                embed_url=link, order=idx,
            ))

    db.session.commit()
    print(f"Seeded {len(accomplishment_data)} accomplishment reports and {len(resources_data)} learning resources.")
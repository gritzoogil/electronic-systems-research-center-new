"""
Targeted recovery script. Fixes:
- OJT (wiped, only 4 rows remain)
- Partner (wiped)
- AccomplishmentReport (wiped)
- LearningResource (wiped)
- CenterHighlightImage (only 1 row remains, needs full re-insert)

Does NOT touch: staff, project, publication, center_highlight, site_settings
Run with: uv run python scripts/reseed_missing.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import OJT, Partner, AccomplishmentReport, LearningResource, CenterHighlight, CenterHighlightImage
import json

with open("image_url_map.json", encoding="utf-8") as f:
    url_map = json.load(f)

def resolve(old_path):
    if not old_path:
        return None
    cleaned = old_path.replace("../build/img/", "").replace("/build/img/", "").strip()
    return url_map.get(cleaned)

app = create_app()

with app.app_context():

    # ── CLEAR WIPED TABLES ONLY ──────────────────────────────────────────
    OJT.query.delete()
    Partner.query.delete()
    AccomplishmentReport.query.delete()
    LearningResource.query.delete()
    CenterHighlightImage.query.delete()
    db.session.commit()
    print("Cleared wiped tables.")

    # ── OJT (full 55-person roster) ──────────────────────────────────────
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
            photo_url=resolve(img_key),
            batch_label=batch, order=idx,
        ))
    print(f"Added {len(ojt_data)} OJT interns.")

    # ── PARTNERS ─────────────────────────────────────────────────────────
    partner_names = [
        "BatStateU", "TESDA", "AboitizPower", "Don Bosco Technical College",
        "MSU General Santos", "Mindoro State University", "SPAMAST",
        "Rizal Technological University", "Tarlac State University",
        "National University Laguna", "OmniFab Inc.", "Collins Aerospace",
        "Phil Railways Institute - DOTr", "Thai Nguyen University of Technology",
        "Indian Maritime University",
    ]
    for i, name in enumerate(partner_names):
        db.session.add(Partner(name=name, order=i, is_published=True))
    print(f"Added {len(partner_names)} partners.")

    # ── ACCOMPLISHMENT REPORTS ───────────────────────────────────────────
    accomplishment_data = [
        (2026, 1, "1st Quarter Accomplishment Report 2026", "Highlights of ESRC accomplishments in Q1 2026.", "Accomplishments/Q1_2025.webp", "https://heyzine.com/flip-book/2d76101035.html"),
        (2025, 4, "4th Quarter Accomplishment Report 2025", "Highlights of ESRC accomplishments in Q4 2025.", "Accomplishments/Q4_2025.webp", None),
        (2025, 3, "3rd Quarter Accomplishment Report 2025", "Highlights of ESRC accomplishments in Q3 2025.", "Accomplishments/Q3_2025.webp", None),
        (2025, 2, "2nd Quarter Accomplishment Report 2025", "Highlights of ESRC accomplishments in Q2 2025.", "Accomplishments/Q2_2025.webp", None),
        (2025, 1, "1st Quarter Accomplishment Report 2025", "Highlights of ESRC accomplishments in Q1 2025.", "Accomplishments/Q1_2025.webp", None),
    ]
    for year, quarter, title, desc, thumb_key, flipbook in accomplishment_data:
        db.session.add(AccomplishmentReport(
            year=year, quarter=quarter, title=title, description=desc,
            thumbnail_url=resolve(thumb_key),
            flipbook_link=flipbook,
        ))
    print(f"Added {len(accomplishment_data)} accomplishment reports.")

    # ── LEARNING RESOURCES ───────────────────────────────────────────────
    resource_data = [
    ("Design Principles and Logic Design",
        "Introduction to Logic Circuits, Logic Gates, Clocks, Latches and Flip-flops",
        "Book Thumbnail/Digital Principles and Logic.webp", 0),
    ("Engineering Research",
        "Introduction to research, citations, email etiquette, literature review, and methodology",
        "Book Thumbnail/Engineering Research.webp", 1),
    ]

    for title, desc, thumb_key, order in resource_data:
        db.session.add(LearningResource(
            title=title, description=desc,
            thumbnail_url=resolve(thumb_key),
            order=order,
        ))
    print(f"Added {len(resource_data)} learning resources.")

    db.session.commit()
    print("Committed OJT, Partners, Accomplishments, Resources.")

    # ── CENTER HIGHLIGHT IMAGES ──────────────────────────────────────────
    # Map: highlight title fragment -> list of image keys in url_map
    highlight_image_map = {
        "LaTeX Training Program 2024": [
            "Research Center Highlights/The LaTeX Training/1.webp",
            "Research Center Highlights/The LaTeX Training/2.webp",
            "Research Center Highlights/The LaTeX Training/3.webp",
            "Research Center Highlights/The LaTeX Training/4.webp",
        ],
        "7th International Conference": [
            "Research Center Highlights/7th International Conference on Signal Processing and Information Communications/1.webp",
        ],
        "Tech Bits": [
            "Research Center Highlights/Tech Bits Become Innovative through Software Training/1.webp",
            "Research Center Highlights/Tech Bits Become Innovative through Software Training/2.webp",
            "Research Center Highlights/Tech Bits Become Innovative through Software Training/3.webp",
            "Research Center Highlights/Tech Bits Become Innovative through Software Training/4.webp",
            "Research Center Highlights/Tech Bits Become Innovative through Software Training/5.webp",
        ],
        "Mobile Phone Repair": [
            "Research Center Highlights/Mobile Phone Repair Training/1.webp",
            "Research Center Highlights/Mobile Phone Repair Training/2.webp",
            "Research Center Highlights/Mobile Phone Repair Training/3.webp",
            "Research Center Highlights/Mobile Phone Repair Training/4.webp",
            "Research Center Highlights/Mobile Phone Repair Training/5.webp",
        ],
        "Engineering Skills Series": [
            "Research Center Highlights/Engineering Skills Series/1.webp",
            "Research Center Highlights/Engineering Skills Series/2.webp",
            "Research Center Highlights/Engineering Skills Series/3.webp",
            "Research Center Highlights/Engineering Skills Series/4.webp",
            "Research Center Highlights/Engineering Skills Series/5.webp",
        ],
        "PCB 101": [
            "Research Center Highlights/PCB 101/1.webp",
            "Research Center Highlights/PCB 101/2.webp",
            "Research Center Highlights/PCB 101/3.webp",
            "Research Center Highlights/PCB 101/4.webp",
            "Research Center Highlights/PCB 101/5.webp",
        ],
        "PPDO at BatStateU": [
            "Research Center Highlights/PPDO at BatStateU TNEU/1.webp",
            "Research Center Highlights/PPDO at BatStateU TNEU/2.webp",
            "Research Center Highlights/PPDO at BatStateU TNEU/3.webp",
            "Research Center Highlights/PPDO at BatStateU TNEU/4.webp",
            "Research Center Highlights/PPDO at BatStateU TNEU/5.webp",
        ],
        "Empowering Innovation": [
            "Research Center Highlights/Empowering Innovation - Arduino Training in Biomed/1.webp",
            "Research Center Highlights/Empowering Innovation - Arduino Training in Biomed/2.webp",
            "Research Center Highlights/Empowering Innovation - Arduino Training in Biomed/3.webp",
            "Research Center Highlights/Empowering Innovation - Arduino Training in Biomed/4.webp",
            "Research Center Highlights/Empowering Innovation - Arduino Training in Biomed/5.webp",
        ],
        "PCB Designing and Fabrication": [
            "Research Center Highlights/PCB Design and Fabrication/1.jpg",
            "Research Center Highlights/PCB Design and Fabrication/2.jpg",
            "Research Center Highlights/PCB Design and Fabrication/3.jpg",
            "Research Center Highlights/PCB Design and Fabrication/4.jpg",
        ],
        "Drone Training": [
            "Research Center Highlights/Drone Training/1.jpg",
            "Research Center Highlights/Drone Training/2.jpg",
            "Research Center Highlights/Drone Training/3.jpg",
            "Research Center Highlights/Drone Training/4.jpg",
            "Research Center Highlights/Drone Training/5.jpg",
        ],
        "LaTeX Training Program for ESRC Interns": [
            "Research Center Highlights/LaTeX Training for Interns 2025/1.jpg",
            "Research Center Highlights/LaTeX Training for Interns 2025/2.jpg",
            "Research Center Highlights/LaTeX Training for Interns 2025/3.jpg",
            "Research Center Highlights/LaTeX Training for Interns 2025/4.jpg",
            "Research Center Highlights/LaTeX Training for Interns 2025/5.jpg",
        ],
        "World Engineering Day": [
            "Research Center Highlights/STEER Hub Open House/1.jpg",
            "Research Center Highlights/STEER Hub Open House/2.jpg",
            "Research Center Highlights/STEER Hub Open House/3.jpg",
            "Research Center Highlights/STEER Hub Open House/4.jpg",
            "Research Center Highlights/STEER Hub Open House/5.jpg",
        ],
        "STM32 Hackathon": [
            "Research Center Highlights/STM32 Hackathon/1.jpg",
            "Research Center Highlights/STM32 Hackathon/2.jpg",
            "Research Center Highlights/STM32 Hackathon/3.jpg",
            "Research Center Highlights/STM32 Hackathon/4.jpg",
            "Research Center Highlights/STM32 Hackathon/5.jpg",
        ],
        "MSU GenSan": [
            "Research Center Highlights/MSU/1.jpg",
            "Research Center Highlights/MSU/2.jpg",
            "Research Center Highlights/MSU/3.jpg",
            "Research Center Highlights/MSU/4.jpg",
            "Research Center Highlights/MSU/5.jpg",
        ],
        "Mindoro State University": [
            "Research Center Highlights/MinSu/1.jpg",
            "Research Center Highlights/MinSu/2.jpg",
            "Research Center Highlights/MinSu/3.jpg",
            "Research Center Highlights/MinSu/4.jpg",
            "Research Center Highlights/MinSu/5.jpg",
        ],
        "SPAMAST": [
            "Research Center Highlights/SPAMAST/1.jpg",
            "Research Center Highlights/SPAMAST/2.jpg",
            "Research Center Highlights/SPAMAST/3.jpg",
            "Research Center Highlights/SPAMAST/4.jpg",
            "Research Center Highlights/SPAMAST/5.jpg",
        ],
        "Lycan Motorcycle": [
            "Research Center Highlights/Lycan Motorcycle Inc/1.webp",
            "Research Center Highlights/Lycan Motorcycle Inc/2.webp",
            "Research Center Highlights/Lycan Motorcycle Inc/3.webp",
            "Research Center Highlights/Lycan Motorcycle Inc/4.webp",
            "Research Center Highlights/Lycan Motorcycle Inc/5.webp",
        ],
        "Secretary Kiko": [
            "Research Center Highlights/TESDA/1.webp",
            "Research Center Highlights/TESDA/2.webp",
            "Research Center Highlights/TESDA/3.webp",
            "Research Center Highlights/TESDA/4.webp",
            "Research Center Highlights/TESDA/5.webp",
        ],
        "Don Bosco Technical College": [
            "Research Center Highlights/Don Bosco Technical College/1.webp",
            "Research Center Highlights/Don Bosco Technical College/2.webp",
            "Research Center Highlights/Don Bosco Technical College/3.webp",
            "Research Center Highlights/Don Bosco Technical College/4.webp",
            "Research Center Highlights/Don Bosco Technical College/5.webp",
        ],
        "OmniFab": [
            "Research Center Highlights/OmniFab/1.png",
            "Research Center Highlights/OmniFab/2.png",
            "Research Center Highlights/OmniFab/3.png",
            "Research Center Highlights/OmniFab/4.png",
            "Research Center Highlights/OmniFab/5.png",
        ],
        "Phil Railways": [
            "Research Center Highlights/Phil Railways Institute of the Department of Transportation - Benchmarking/1.webp",
            "Research Center Highlights/Phil Railways Institute of the Department of Transportation - Benchmarking/2.webp",
        ],
        "On-the-Job Training Orientation": [
            "Research Center Highlights/On-the-Job Training Orientation/1 (1).webp",
            "Research Center Highlights/On-the-Job Training Orientation/1 (2).webp",
            "Research Center Highlights/On-the-Job Training Orientation/1 (3).webp",
            "Research Center Highlights/On-the-Job Training Orientation/1 (4).webp",
        ],
        "Thai Nguyen": [
            "Research Center Highlights/Thai Nguyen University of Technology visited ESRC/1 (1).webp",
            "Research Center Highlights/Thai Nguyen University of Technology visited ESRC/1 (2).webp",
        ],
        "National University Laguna": [
            "Research Center Highlights/National University Laguna visited ESRC/1 (1).webp",
            "Research Center Highlights/National University Laguna visited ESRC/1 (2).webp",
            "Research Center Highlights/National University Laguna visited ESRC/1 (3).webp",
        ],
        "Preparation for Innovation Month": [
            "Research Center Highlights/Preparation for Innovation Month/1 (1).webp",
            "Research Center Highlights/Preparation for Innovation Month/1 (2).webp",
            "Research Center Highlights/Preparation for Innovation Month/1 (3).webp",
        ],
        "BioMinded": [
            "Research Center Highlights/BioMinded 2025/1 (1).webp",
            "Research Center Highlights/BioMinded 2025/1 (2).webp",
            "Research Center Highlights/BioMinded 2025/1 (3).webp",
            "Research Center Highlights/BioMinded 2025/1 (4).webp",
        ],
        "Tarlac State University": [
            "Research Center Highlights/Tarlac State University visited ESRC/1 (1).webp",
            "Research Center Highlights/Tarlac State University visited ESRC/1 (2).webp",
            "Research Center Highlights/Tarlac State University visited ESRC/1 (3).webp",
        ],
        "MEXpansE": [
            "Research Center Highlights/MEXpansE 2.0 Charting New Frontiers in Mechatronics - Innovation Month 2025/1 (1).webp",
            "Research Center Highlights/MEXpansE 2.0 Charting New Frontiers in Mechatronics - Innovation Month 2025/1 (2).webp",
            "Research Center Highlights/MEXpansE 2.0 Charting New Frontiers in Mechatronics - Innovation Month 2025/1 (3).webp",
            "Research Center Highlights/MEXpansE 2.0 Charting New Frontiers in Mechatronics - Innovation Month 2025/1 (4).webp",
            "Research Center Highlights/MEXpansE 2.0 Charting New Frontiers in Mechatronics - Innovation Month 2025/1 (5).webp",
        ],
        "AboitizPower": [
            "Research Center Highlights/AboitizPower - Benchmarking/1 (1).webp",
            "Research Center Highlights/AboitizPower - Benchmarking/1 (2).webp",
            "Research Center Highlights/AboitizPower - Benchmarking/1 (3).webp",
        ],
        "Jitter Basics": [
            "Research Center Highlights/Jitter Basics and Signal Integrity Training for ESRC Interns/1 (1).webp",
            "Research Center Highlights/Jitter Basics and Signal Integrity Training for ESRC Interns/1 (2).webp",
            "Research Center Highlights/Jitter Basics and Signal Integrity Training for ESRC Interns/1 (3).webp",
        ],
        "Ignition SCADA": [
            "Research Center Highlights/Ignition SCADA Training for ESRC Interns/1 (1).webp",
            "Research Center Highlights/Ignition SCADA Training for ESRC Interns/1 (2).webp",
            "Research Center Highlights/Ignition SCADA Training for ESRC Interns/1 (3).webp",
        ],
        "PLC Training": [
            "Research Center Highlights/Plc Training/0.webp",
            "Research Center Highlights/Plc Training/1.webp",
            "Research Center Highlights/Plc Training/2.webp",
            "Research Center Highlights/Plc Training/3.webp",
            "Research Center Highlights/Plc Training/4.webp",
        ],
        "US Embassy": [
            "Research Center Highlights/US Embassy/4.webp",
            "Research Center Highlights/US Embassy/5.webp",
        ],
        "Indian Maritime": [
            "Research Center Highlights/IMU/2.webp",
            "Research Center Highlights/IMU/3.webp",
        ],
    }

    # Load all highlights from DB
    highlights = CenterHighlight.query.all()
    matched = 0
    unmatched = []

    for highlight in highlights:
        title = highlight.title
        img_keys = None
        for fragment, keys in highlight_image_map.items():
            if fragment.lower() in title.lower():
                img_keys = keys
                break

        if img_keys:
            for order, key in enumerate(img_keys, start=1):
                url = url_map.get(key)
                if url:
                    db.session.add(CenterHighlightImage(
                        highlight_id=highlight.id,
                        image_url=url,
                        order=order,
                    ))
            matched += 1
        else:
            unmatched.append(title)

    db.session.commit()
    print(f"\nHighlight images: {matched} highlights matched, {len(unmatched)} unmatched.")
    if unmatched:
        print("Unmatched highlights (no images assigned):")
        for t in unmatched:
            print(f"  - {t}")

    print("\nRecovery complete.")
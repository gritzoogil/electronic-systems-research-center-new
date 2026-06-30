from app import db


class ResearchProject(db.Model):
    __tablename__ = "research_projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    img_path = db.Column(db.String(512), nullable=True)
    more_info = db.Column(db.String(512), nullable=True)

    def __repr__(self):
        return f"<ResearchProject {self.title}>"
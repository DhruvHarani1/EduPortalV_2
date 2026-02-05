from app import create_app, db
from app.models import Subject, Syllabus

app = create_app()
with app.app_context():
    sub = Subject.query.first()
    print(f"Subject: {sub.name}")
    print(f"Syllabus via backref: {sub.syllabus}")

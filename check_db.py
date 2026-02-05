from app import create_app, db
from app.models import Subject, Syllabus

app = create_app()
with app.app_context():
    subjects = Subject.query.all()
    print(f"Total Subjects: {len(subjects)}")
    syllabi = Syllabus.query.all()
    print(f"Total Syllabi: {len(syllabi)}")
    
    for sub in subjects[:5]:
        syl = Syllabus.query.filter_by(subject_id=sub.id).first()
        print(f"Subject: {sub.name} (ID: {sub.id}), Syllabus: {'Found' if syl else 'Missing'}")

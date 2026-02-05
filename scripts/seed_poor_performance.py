import sys
import os
sys.path.append(os.getcwd()) # Ensure root is in path

from app import create_app, db
from app.models import StudentProfile, User, ExamEvent, ExamPaper, StudentResult, Subject
from datetime import date, timedelta, time
import random

app = create_app()

with app.app_context():
    print("--- Seeding Poor Performance Data ---")

    # 1. Create/Get a "Danger Zone" Student
    email = "danger_student@test.com"
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(email=email, role='student')
        u.set_password('password')
        db.session.add(u)
        db.session.flush()
        print(f"Created User: {email}")
        
    s = StudentProfile.query.filter_by(user_id=u.id).first()
    if not s:
        s = StudentProfile(
            user_id=u.id, 
            display_name="Danger Dan", 
            enrollment_number="LOW001",
            course_name="B.Tech",
            semester=1
        )
        db.session.add(s)
        db.session.flush()
        print(f"Created Profile: {s.display_name}")

    # 2. Get Recent Exam Papers
    # We'll attach results to any existing papers found in the DB
    papers = ExamPaper.query.limit(10).all()
    
    if not papers:
        print("No exam papers found! Creating dummy event & papers...")
        # Create Dummy Event
        evt = ExamEvent(name="Emergency Resit", academic_year="2025-26", course_name="B.Tech", semester=1, start_date=date.today(), end_date=date.today())
        db.session.add(evt)
        db.session.flush()
        
        # Create Dummy Subject
        sub = Subject.query.first()
        if not sub:
            sub = Subject(name="Hard Math", course_name="B.Tech", semester=1)
            db.session.add(sub)
            db.session.flush()
            
        paper = ExamPaper(
            exam_event_id=evt.id, 
            subject_id=sub.id, 
            date=date.today(), 
            start_time=time(9,0), 
            end_time=time(12,0)
        )
        db.session.add(paper)
        db.session.flush()
        papers = [paper]

    print(f"Assigning low marks for {len(papers)} papers...")
    
    # 3. Assign Low Marks (< 35)
    for p in papers:
        res = StudentResult.query.filter_by(student_id=s.id, exam_paper_id=p.id).first()
        if not res:
            res = StudentResult(
                student_id=s.id,
                exam_paper_id=p.id,
                marks_obtained=random.randint(10, 30), # Guaranteed < 40 average
                status='Present',
                is_fail=True
            )
            db.session.add(res)
        else:
            # Update existing to be low
            res.marks_obtained = random.randint(10, 30)
            res.is_fail = True
            
    db.session.commit()
    print("Seeding Complete. 'Danger Dan' should now appear in the Danger Zone table.")

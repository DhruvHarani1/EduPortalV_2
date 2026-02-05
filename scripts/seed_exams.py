from app import create_app,db
from app.models import ExamEvent, ExamPaper, Subject, StudentProfile, User
from datetime import date, timedelta, time

app = create_app()

with app.app_context():
    print("Seeding Dummy Exam Data...")

    # 1. Ensure we have a dummy course/sem
    course = "B.Tech"
    sem = 1
    
    # Check/Create Students
    if not StudentProfile.query.filter_by(course_name=course, semester=sem).first():
        print("Creating dummy students...")
        for i in range(1, 6):
            u = User(email=f'student{i}@test.com', role='student')
            u.set_password('password')
            db.session.add(u)
            db.session.flush()
            
            s = StudentProfile(
                user_id=u.id,
                display_name=f"Student {i}",
                enrollment_number=f"BT2024{i:03d}",
                course_name=course,
                semester=sem
            )
            db.session.add(s)
    
    # 2. Create a "Completed" Exam Event
    evt = ExamEvent.query.filter_by(name="Mid-Term 2024").first()
    if not evt:
        print("Creating Mid-Term 2024 Exam (Completed)...")
        evt = ExamEvent(
            name="Mid-Term 2024",
            course_name=course,
            semester=sem,
            academic_year="2024-2025",
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() - timedelta(days=15),
            is_published=True
        )
        db.session.add(evt)
        db.session.flush()
        
        # 3. Add Papers
        subjects = Subject.query.filter_by(course_name=course, semester=sem).all()
        for idx, sub in enumerate(subjects):
            paper = ExamPaper(
                exam_event_id=evt.id,
                subject_id=sub.id,
                date=evt.start_date + timedelta(days=idx),
                start_time=time(10, 0),
                end_time=time(13, 0),
                total_marks=50
            )
            db.session.add(paper)
            
    db.session.commit()
    
    # 4. Add Dummy Results (for Re-candidates testing)
    print("Seeding Dummy Results...")
    from app.models import StudentResult
    import random
    
    evt_papers = ExamPaper.query.filter_by(exam_event_id=evt.id).all()
    students = StudentProfile.query.filter_by(course_name=course, semester=sem).all()
    
    for student in students:
        for paper in evt_papers:
            # Randomly decide status
            rand = random.random()
            status = 'Present'
            marks = 0
            is_fail = False
            
            if rand < 0.1:
                status = 'Absent'
                is_fail = True
            elif rand < 0.3:
                # Fail
                marks = random.randint(0, 15) # Assuming 50 total, pass might be 20
                is_fail = True
            else:
                # Pass
                marks = random.randint(20, 50)
            
            # Check if result exists
            res = StudentResult.query.filter_by(exam_paper_id=paper.id, student_id=student.id).first()
            if not res:
                res = StudentResult(
                    exam_paper_id=paper.id,
                    student_id=student.id,
                    marks_obtained=marks,
                    status=status,
                    is_fail=is_fail
                )
                db.session.add(res)
    
    db.session.commit()
    print("Seeding Complete!")

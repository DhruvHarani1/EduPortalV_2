
import sys
import os
import random
import click
from datetime import datetime, date, timedelta, time
from flask.cli import FlaskGroup

sys.path.append(os.getcwd())

from app import create_app, db
from app.models import (
    User, StudentProfile, FacultyProfile, Subject, 
    Attendance, Notice, FeeRecord, StudentQuery, 
    QueryMessage, ExamEvent, ExamPaper, StudentResult, Timetable, ScheduleSettings, UniversityEvent
)

def get_image_bytes(filename):
    """Helper to read image bytes from artifacts specific path"""
    # Adjust path if needed or just use empty bytes if file not found
    path = os.path.join(r"C:\Users\TEST\.gemini\antigravity\brain\ea4b25ed-125c-45de-b3a1-50f6629eceb7", filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return b"" # Return empty bytes if file missing

def create_manage_app(*args, **kwargs):
    return create_app()

@click.group(cls=FlaskGroup, create_app=create_manage_app)
def cli():
    """Management script for EduPortal"""
    pass

@cli.command("seed")
def seed():
    """Seed the database with optimized standard data."""
    with create_app().app_context():
        print("--- Resetting Database for Universal Standard Data ---")
        db.drop_all()
        db.create_all()

        # 1. Admins
        print("Seeding Admins...")
        for i in [f"admin@edu.com", "admin2@edu.com"]:
            u = User(email=i, role='admin')
            u.set_password('123')
            db.session.add(u)
        
        # 2. Faculty
        print("Seeding Faculty...")
        faculty_objs = []
        for i in range(1, 11):
            u = User(email=f"faculty{i}@edu.com", role='faculty')
            u.set_password('123')
            db.session.add(u)
            db.session.flush()

            f = FacultyProfile(
                user_id=u.id, 
                display_name=f"Prof. {random.choice(['James', 'Mary', 'Robert', 'Patricia'])} {random.choice(['Smith', 'Johnson', 'Williams'])}",
                department=random.choice(["CS", "Electronics", "Math"]),
                designation="Asst. Professor"
            )
            db.session.add(f)
            faculty_objs.append(f)
        db.session.flush()

        # 3. Universal Structure (All courses/sems)
        courses = ["B.Tech", "BCA", "MCA"]
        for course in courses:
            for sem in range(1, 4):
                # Schedule
                settings = ScheduleSettings(
                    course_name=course, semester=sem,
                    start_time=time(9,0), end_time=time(17,0),
                    recess_duration=60, recess_after_slot=4
                )
                db.session.add(settings)
                
                # Subjects
                subs = []
                names = ["Data Structures and Algorithms", "Programming", "Logic", "Networks", "Databases"]
                for i, n in enumerate(names):
                    # Ensure faculty1 (id=1) gets at least one subject per sem
                    # faculty_objs[0] is faculty1
                    assigned_fac = faculty_objs[0] if i == 0 else random.choice(faculty_objs)
                    
                    s = Subject(
                        name=f"{n} {course}-{sem}", 
                        course_name=course, 
                        semester=sem, 
                        faculty_id=assigned_fac.id,
                        resource_link="https://drive.google.com/drive/u/0/folders/dummy_link" 
                    )
                    db.session.add(s)
                    subs.append(s)
                db.session.flush()

                # Timetable (4-Recess-3 pattern)
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                    for p in range(1, 8):
                        # Guarantee faculty1 has period 1 and 2 every day for testing
                        if p in [1, 2]:
                             fac_id = faculty_objs[0].id
                             sub_id = subs[0].id # Data Structures and Algorithms for faculty1
                        else:
                             fac_id = random.choice(faculty_objs).id
                             sub_id = random.choice(subs).id

                        slot = Timetable(
                            course_name=course, 
                            semester=sem, 
                            day_of_week=day, 
                            period_number=p, 
                            subject_id=sub_id, 
                            faculty_id=fac_id
                        )
                        db.session.add(slot)

        # 4. Students
        print("Seeding 40 Students and Mentorship...")
        for i in range(1, 41):
            u = User(email=f"student{i}@edu.com", role='student')
            u.set_password('123')
            db.session.add(u)
            db.session.flush()
            
            idx = (i-1) % 9
            c = courses[idx // 3]
            s = (idx % 3) + 1
            
            # Assign Mentor (faculty1 gets more mentees for testing)
            if i <= 10:
                mentor_id = faculty_objs[0].id # faculty1
            else:
                mentor_id = random.choice(faculty_objs).id

            # Randomly flag some students with 'Lost' ID card status
            id_status = 'Lost' if random.random() < 0.1 else 'Active'

            sp = StudentProfile(
                user_id=u.id, 
                display_name=f"Student {i}", 
                enrollment_number=f"EN{2024000+i:07d}", 
                course_name=c, 
                semester=s,
                mentor_id=mentor_id,
                phone_number=f"+91 {random.randint(7000, 9999)} {random.randint(1000, 9999)}",
                address=f"{random.randint(1, 999)}, Edu Lane, City {i}",
                id_card_status=id_status
            )
            db.session.add(sp)
        db.session.flush()

        # 5. Attendance
        print("Seeding Attendance Records...")
        students = StudentProfile.query.all()
        for stu in students:
            subjects = Subject.query.filter_by(course_name=stu.course_name, semester=stu.semester).all()
            if not subjects: continue
            
            # Seed last 30 days
            for day_offset in range(30):
                date_val = date.today() - timedelta(days=day_offset)
                if date_val.weekday() == 6: continue # Skip Sunday
                
                # Mark attendance for each subject
                for sub in subjects:
                    # 85% attendance rate
                    status = "Present" if random.random() < 0.85 else "Absent"
                    att = Attendance(
                        student_id=stu.id,
                        course_name=stu.course_name,
                        subject_id=sub.id,
                        faculty_id=sub.faculty_id,
                        date=date_val,
                        status=status
                    )
                    db.session.add(att)

        db.session.commit()
        
        # 6. Exams & Results
        print("Seeding Exams & Results...")
        for course in courses:
            for sem in range(1, 4):
                # Create an Exam Event
                ee = ExamEvent(
                    name=f"Mid-Term {course} Sem {sem}", 
                    academic_year="2024-2025", 
                    course_name=course, semester=sem,
                    start_date=date.today() - timedelta(days=20),
                    end_date=date.today() - timedelta(days=15),
                    is_published=True
                )
                db.session.add(ee)
                db.session.flush()

                # Get subjects for this course/sem
                relevant_subs = Subject.query.filter_by(course_name=course, semester=sem).all()
                
                # Create papers and results
                for idx, sub in enumerate(relevant_subs):
                    # Stagger dates (skip Sunday logic later if needed, for now just +idx)
                    paper_date = ee.start_date + timedelta(days=idx)
                    
                    paper = ExamPaper(
                        exam_event_id=ee.id, subject_id=sub.id,
                        date=paper_date, start_time=time(10,0), end_time=time(13,0),
                        total_marks=100
                    )
                    db.session.add(paper)
                    db.session.flush()
                    
                    # Add results for students in this course/sem
                    sem_students = [s for s in students if s.course_name == course and s.semester == sem]
                    for st in sem_students:
                        marks = random.gauss(75, 12) # Bell curve around 75
                        marks = round(max(0, min(100, marks)), 2) # Rounded to 2 digits
                        res = StudentResult(
                            exam_paper_id=paper.id, student_id=st.id,
                            marks_obtained=marks, status="Present",
                            is_fail=(marks < 40)
                        )
                        db.session.add(res)
        
        # 7. Fee Records
        print("Seeding Fee Records...")
        for st in students:
            # Sem 1 Paid
            f1 = FeeRecord(
                student_id=st.id, 
                semester=1, 
                academic_year="2024-2025", 
                amount_due=50000, 
                amount_paid=50000, 
                status="Paid", 
                due_date=date(2024, 8, 1),
                payment_date=datetime(2024, 7, 25),
                payment_mode="Online",
                transaction_reference=f"TXN{random.randint(10000,99999)}SEM1"
            )
            db.session.add(f1)
            # Current Sem
            if st.semester > 1:
                status = random.choice(["Paid", "Pending", "Partial"])
                paid = 50000 if status == "Paid" else (20000 if status == "Partial" else 0)
                
                payment_date = datetime(2025, 1, 10) if status in ["Paid", "Partial"] else None
                payment_mode = "Online" if status in ["Paid", "Partial"] else None
                txn_ref = f"TXN{random.randint(10000,99999)}SEM{st.semester}" if status in ["Paid", "Partial"] else None

                f2 = FeeRecord(
                    student_id=st.id, 
                    semester=st.semester, 
                    academic_year="2024-2025", 
                    amount_due=50000, 
                    amount_paid=paid, 
                    status=status, 
                    due_date=date(2025, 1, 15),
                    payment_date=payment_date,
                    payment_mode=payment_mode,
                    transaction_reference=txn_ref
                )
                db.session.add(f2)

        # 8. Notices
        print("Seeding Notices...")
        notices = [
            ("Exam Schedule Released", "exam", "The mid-term exam schedule is out."),
            ("Placement Drive 2025", "placement", "Google and Microsoft are visiting next week."),
            ("Holiday Notice", "general", "College remains closed on Friday."),
            ("Library Due Date", "admin", "Please return all books by end of month.")
        ]
        for t, c, b in notices:
            n = Notice(title=t, category=c, content=b, created_at=datetime.utcnow())
            db.session.add(n)

        # 9. Queries
        print("Seeding Queries...")
        topics = ["Hostel", "Library", "Exam", "Canteen"]
        all_faculty = FacultyProfile.query.all()
        for i in range(10):
            st = random.choice(students)
            fac = random.choice(all_faculty) 
            q = StudentQuery(
                student_id=st.id, 
                faculty_id=fac.id,  # Was missing
                title=f"Question about {random.choice(topics)}", 
                status=random.choice(["Pending", "Resolved"])
            )
            db.session.add(q)
            db.session.flush()
            m = QueryMessage(query_id=q.id, sender_type="student", content="Can you please help me with this issue?")
            db.session.add(m)

        db.session.commit()

        # 10. University Events
        print("Seeding University Events...")
        events = [
            {
                "title": "Annual Tech Symposium 2026",
                "desc": "A gathering of brilliant minds showcasing innovation.",
                "cat": "Tech",
                "img": "event_tech_symposium_1769855435285.png",
                "days_offset": 10
            },
            {
                "title": "Inter-University Sports Meet",
                "desc": "Join us for the grandest sports event of the year.",
                "cat": "Sports",
                "img": "event_sports_tournament_1769855453905.png",
                "days_offset": 25
            },
            {
                "title": "Cultural Night & Music Fest",
                "desc": "An evening of music, dance, and cultural celebration.",
                "cat": "Cultural",
                "img": "event_cultural_night_1769855474733.png",
                "days_offset": 45
            }
        ]
        
        for ev in events:
            img_data = get_image_bytes(ev['img'])
            event = UniversityEvent(
                title=ev['title'],
                description=ev['desc'],
                category=ev['cat'],
                date=date.today() + timedelta(days=ev['days_offset']),
                time=time(18, 00) if ev['cat'] == 'Cultural' else time(9, 30),
                location="Main Auditorium" if ev['cat'] != 'Sports' else "University Stadium",
                organizer="Student Council",
                is_upcoming=True,
                image_data=img_data if img_data else None,
                image_mimetype="image/png"
            )
            db.session.add(event)

        db.session.commit()

        # 11. Event Registrations
        print("Seeding Event Registrations...")
        all_events = UniversityEvent.query.all()
        all_students = StudentProfile.query.all()
        from app.models import EventRegistration
        for ev in all_events:
            # Register 15-25 random students per event
            reg_count = random.randint(15, 25)
            registered_students = random.sample(all_students, reg_count)
            for stu in registered_students:
                reg = EventRegistration(
                    event_id=ev.id,
                    student_id=stu.id,
                    registered_at=datetime.utcnow() - timedelta(days=random.randint(1, 5))
                )
                db.session.add(reg)
        db.session.commit()

        # 12. Syllabi
        print("Seeding Syllabi...")
        from app.models import Syllabus
        all_subjects = Subject.query.all()
        sample_pdf = b"%PDF-1.4\n1 0 obj\n<< /Title (Sample Syllabus) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        for sub in all_subjects:
            # Check if syllabus already exists (to avoid duplicates if re-seeding without reset)
            if not sub.syllabus:
                new_syl = Syllabus(
                    subject_id=sub.id,
                    filename=f"Syllabus_{sub.name.replace(' ', '_')}.pdf",
                    file_data=sample_pdf
                )
                db.session.add(new_syl)
        db.session.commit()

        print("--- Standard Seeding Complete ---")

if __name__ == "__main__":
    cli()

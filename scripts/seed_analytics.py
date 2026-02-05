from app import create_app, db
from app.models import StudentProfile, Attendance, StudentResult, ExamPaper, Subject, ExamEvent, User, FacultyProfile
from datetime import date, timedelta, time
import random
import statistics

app = create_app()

def seed_analytics_data():
    with app.app_context():
        print("--- Starting Massive Data Seeding (400 Students, 30 Faculty) ---")

        # 1. Setup Base Data (Course & Sem)
        course = "B.Tech"
        
        # --- Create Faculty (30) ---
        print("Creating Faculty...")
        faculties = FacultyProfile.query.all()
        if len(faculties) < 30:
            existing_count = len(faculties)
            for i in range(existing_count + 1, 31):
                email = f'faculty{i}_stats@test.com'
                if not User.query.filter_by(email=email).first():
                    u = User(email=email, role='faculty')
                    u.set_password('password')
                    db.session.add(u)
                    db.session.flush()
                    
                    f = FacultyProfile(
                        user_id=u.id,
                        display_name=f"Prof. {['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'][i % 8]} {i}",
                        department="Computer Science",
                        designation="Assistant Professor",
                        experience=random.randint(1, 20)
                    )
                    db.session.add(f)
            db.session.commit()
        
        faculties = FacultyProfile.query.all()
        print(f"Total Faculty: {len(faculties)}")

        # --- Create Students (400) ---
        # We will split them across sem 1, 2, 3? No, let's put them all in Sem 3 so we can generate history for 1 & 2
        semester = 3 
        
        students = StudentProfile.query.filter_by(course_name=course, semester=semester).all()
        target_students = 400
        
        if len(students) < target_students:
            print(f"Creating {target_students - len(students)} new students...")
            start_idx = len(students) + 1
            
            for i in range(start_idx, target_students + 1):
                email = f'student{i}_bigdata@test.com'
                if not User.query.filter_by(email=email).first():
                    u = User(email=email, role='student')
                    u.set_password('password')
                    db.session.add(u)
                    db.session.flush()
                    
                    s = StudentProfile(
                        user_id=u.id,
                        display_name=f"Student {i} (Batch 2024)",
                        enrollment_number=f"BT2024_X{i:04d}",
                        course_name=course,
                        semester=semester
                    )
                    db.session.add(s)
                
                if i % 50 == 0: 
                    db.session.commit() # batch commit
                    print(f"Created {i} students...")
            db.session.commit()
            
        students = StudentProfile.query.filter_by(course_name=course, semester=semester).all()
        print(f"Total Students: {len(students)}")

        # --- Personas ---
        # Persona: (Attendance Mean, Attendance Variance, Academic Mean, Academic Variance)
        personas = [
            (0.98, 0.02, 92, 3),   # Top 1%
            (0.90, 0.08, 80, 8),   # Good
            (0.75, 0.15, 60, 10),  # Average
            (0.50, 0.20, 45, 12),  # Below Average
            (0.30, 0.30, 25, 15)   # Critical
        ]
        # Weighted distribution: Most are average
        weights = [0.05, 0.20, 0.50, 0.20, 0.05]
        
        student_personas = {}
        for s in students:
            student_personas[s.id] = random.choices(personas, weights=weights, k=1)[0]

        # --- Loop Semesters 1, 2, 3 ---
        semesters = [1, 2, 3]
        
        for sem_iter in semesters:
            print(f"Generating Data for Semester {sem_iter}...")
            
            days_ago = (3 - sem_iter) * 180 + 60
            start_date = date.today() - timedelta(days=days_ago)

            # 1. Subjects & Faculty Mapping
            sem_subjects = Subject.query.filter_by(course_name=course, semester=sem_iter).all()
            if not sem_subjects:
                 subj_names = [f"Subject {sem_iter}-{chr(65+i)}" for i in range(5)]
                 for idx, name in enumerate(subj_names):
                     fact_idx = (sem_iter * 5 + idx) % len(faculties) # Distribute subjects among faculty
                     sub = Subject(
                         name=name, 
                         course_name=course, 
                         semester=sem_iter,
                         faculty_id=faculties[fact_idx].id 
                     )
                     db.session.add(sub)
                 db.session.commit()
                 sem_subjects = Subject.query.filter_by(course_name=course, semester=sem_iter).all()
            else:
                # Ensure existing subjects have faculty linked
                for idx, sub in enumerate(sem_subjects):
                    if not sub.faculty_id:
                        fact_idx = (sem_iter * 5 + idx) % len(faculties)
                        sub.faculty_id = faculties[fact_idx].id
                        db.session.add(sub)
                db.session.commit()

            # 2. Attendance (Only detailed for Sem 3, sparse for others is fine but user asked for "True Data" so let's generate)
            # Generating 60 days * 400 students = 24,000 records per sem. Total 72k records. 
            # SQLite handles this fine.
            print("  - Seeding Attendance...")
            
            # Batch inserts for speed
            attendance_buffer = []
            
            for day_offset in range(60): 
                current_date = start_date + timedelta(days=day_offset)
                if current_date.weekday() >= 5: continue

                day_fatigue = 0.0
                if current_date.weekday() == 0: day_fatigue = 0.15 
                if current_date.weekday() == 4: day_fatigue = 0.20 
                
                # Check if date already filled (re-run safety)
                if Attendance.query.filter_by(date=current_date).first():
                    continue

                for s in students:
                    att_mean, att_var, _, _ = student_personas[s.id]
                    prob = att_mean - day_fatigue + random.uniform(-att_var, att_var)
                    prob = max(0, min(1, prob))
                    status = 'Present' if random.random() < prob else 'Absent'
                    
                    attendance_buffer.append(Attendance(student_id=s.id, course_name=course, date=current_date, status=status))
            
            if attendance_buffer:
                db.session.add_all(attendance_buffer)
                db.session.commit()
                print(f"    Added {len(attendance_buffer)} attendance records.")

            # 3. Exams & Results
            print("  - Seeding Exams...")
            evt_name = f"End Sem {sem_iter} Exam (Big Data)"
            evt = ExamEvent.query.filter_by(name=evt_name).first()
            if not evt:
                evt = ExamEvent(
                    name=evt_name,
                    course_name=course,
                    semester=sem_iter,
                    academic_year=f"202{3+sem_iter}-202{4+sem_iter}",
                    start_date=start_date + timedelta(days=50),
                    end_date=start_date + timedelta(days=60),
                    is_published=True
                )
                db.session.add(evt)
                db.session.commit()
                
                for sub in sem_subjects:
                    paper = ExamPaper(
                        exam_event_id=evt.id,
                        subject_id=sub.id,
                        date=evt.start_date,
                        start_time=time(9,0),
                        end_time=time(12,0),
                        total_marks=100
                    )
                    db.session.add(paper)
                db.session.commit()

            evt_papers = ExamPaper.query.filter_by(exam_event_id=evt.id).all()
            
            # Result Buffer
            result_buffer = []
            
            # Difficulty Map per paper
            diff_map = {p.id: random.uniform(0, 15) for p in evt_papers}

            for p in evt_papers:
                penalty = diff_map[p.id]
                # Check exist
                if StudentResult.query.filter_by(exam_paper_id=p.id).count() > 0:
                    continue

                for s in students:
                    _, _, acad_mean, acad_var = student_personas[s.id]
                    
                    growth = 0
                    if acad_mean > 70: growth = (sem_iter - 1) * 2 
                    if acad_mean < 50: growth = (sem_iter - 1) * -3 
                    
                    score = acad_mean + growth - penalty + random.uniform(-acad_var, acad_var)
                    score = max(0, min(100, score))
                    
                    is_fail = score < 35
                    status = 'Present'
                    
                    result_buffer.append(StudentResult(
                        exam_paper_id=p.id,
                        student_id=s.id,
                        marks_obtained=round(score, 1),
                        status=status,
                        is_fail=is_fail
                    ))
            
            if result_buffer:
                db.session.add_all(result_buffer)
                db.session.commit()
                print(f"    Added {len(result_buffer)} exam results.")
        
        print("--- Massive Data Seeding Complete ---")

if __name__ == '__main__':
    seed_analytics_data()

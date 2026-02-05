import sys
import os
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import StudentProfile, User, Attendance, Subject, FacultyProfile
from datetime import date, timedelta
import random

app = create_app()

with app.app_context():
    print("--- Seeding Poor Attendance Data ---")

    # 1. Create/Get a "Truant" Student
    email = "truant_tom@test.com"
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
            display_name="Truant Tom", 
            enrollment_number="ABS001",
            course_name="B.Tech",
            semester=1
        )
        db.session.add(s)
        db.session.flush()
        print(f"Created Profile: {s.display_name}")

    # 2. Get Requirements (Subject, Faculty)
    sub = Subject.query.first()
    if not sub:
        print("Creating dummy subject...")
        sub = Subject(name="Bunking 101", course_name="B.Tech", semester=1)
        db.session.add(sub)
        db.session.flush()
        
    fac = FacultyProfile.query.first() # Optional, but good for completeness

    # 3. Add Attendance Records (Target: < 75%)
    # Let's add 20 days: 5 Present, 15 Absent = 25% Attendance
    
    # Clear existing for fresh calc
    Attendance.query.filter_by(student_id=s.id).delete()
    db.session.commit()
    
    start_date = date.today() - timedelta(days=30)
    
    print("Adding 20 days of data (mostly Absent)...")
    
    for i in range(20):
        current_day = start_date + timedelta(days=i)
        
        # Skip weekends
        if current_day.weekday() > 4: 
            continue
            
        status = 'Absent'
        if i % 4 == 0: # Every 4th day is present
            status = 'Present'
            
        att = Attendance(
            student_id=s.id,
            subject_id=sub.id,
            faculty_id=fac.id if fac else None,
            course_name=s.course_name,
            date=current_day,
            status=status
        )
        db.session.add(att)
            
    db.session.commit()
    
    # Verify
    total = Attendance.query.filter_by(student_id=s.id).count()
    present = Attendance.query.filter_by(student_id=s.id, status='Present').count()
    perc = (present/total)*100 if total > 0 else 0
    
    print(f"Seeding Complete.")
    print(f"Truant Tom Stats: {present}/{total} Present ({perc:.1f}%)")
    print("This should trigger the 'Truancy Risk' alert (< 75%).")

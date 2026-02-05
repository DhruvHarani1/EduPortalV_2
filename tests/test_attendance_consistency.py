
import sys
import os
from datetime import date, datetime

# Add app to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User, StudentProfile, FacultyProfile, Subject, Attendance, Timetable

app = create_app()

def test_attendance_consistency():
    with app.app_context():
        print("--- Starting Attendance Consistency Test ---")
        
        # 1. Setup Test Data
        # Create Dummy Student
        s_email = "test_student_cons@edu.com"
        s = StudentProfile.query.filter_by(enrollment_number="TEST999").first()
        if not s:
            u = User(email=s_email, role='student')
            u.set_password('123')
            db.session.add(u)
            db.session.commit()
            
            s = StudentProfile(
                user_id=u.id, 
                display_name="Test Student", 
                enrollment_number="TEST999",
                course_name="B.Tech",
                semester=1
            )
            db.session.add(s)
            db.session.commit()
            print("[✓] Created Test Student")
        else:
            print("[✓] Found Test Student")
            
        # Create Dummy Faculty
        f = FacultyProfile.query.filter_by(designation="TestProf").first()
        if not f:
            u_f = User(email="test_fac_cons@edu.com", role='faculty')
            u_f.set_password('123')
            db.session.add(u_f)
            db.session.commit()
            
            f = FacultyProfile(
                user_id=u_f.id,
                display_name="Test Faculty",
                designation="TestProf",
                department="TestDept",
                assigned_subject="Math, Physics"
            )
            db.session.add(f)
            db.session.commit()
            print("[✓] Created Test Faculty")
        else:
            print("[✓] Found Test Faculty")

        # Create Subjects
        sub1 = Subject.query.filter_by(name="TestMath").first()
        if not sub1:
            sub1 = Subject(name="TestMath", course_name="B.Tech", semester=1, faculty_id=f.id)
            db.session.add(sub1)
            db.session.commit()
        
        sub2 = Subject.query.filter_by(name="TestPhysics").first()
        if not sub2:
            sub2 = Subject(name="TestPhysics", course_name="B.Tech", semester=1, faculty_id=f.id)
            db.session.add(sub2)
            db.session.commit()
            
        print(f"[✓] Subjects Ready: {sub1.name} (ID: {sub1.id}), {sub2.name} (ID: {sub2.id})")
        
        # Create Timetable: Math on Mon P1, Physics on Mon P2
        # Ensure we test the 'Same Day' hypothesis
        Timetable.query.filter_by(room_number="TestRoom").delete()
        
        t1 = Timetable(
            course_name="B.Tech", semester=1, day_of_week="Monday", period_number=1,
            subject_id=sub1.id, faculty_id=f.id, room_number="TestRoom"
        )
        t2 = Timetable(
            course_name="B.Tech", semester=1, day_of_week="Monday", period_number=2,
            subject_id=sub2.id, faculty_id=f.id, room_number="TestRoom"
        )
        db.session.add(t1)
        db.session.add(t2)
        db.session.commit()
        print("[✓] Timetable Set: Math & Physics both on Monday")
        
        # 2. Simulate Marking Attendance for ONLY Math
        # Clear existing
        Attendance.query.filter_by(student_id=s.id).delete()
        db.session.commit()
        
        # Mark Math Present for a specific Monday (e.g., 2025-01-06 is a Monday)
        test_date = date(2025, 1, 6) 
        
        att1 = Attendance(
            student_id=s.id,
            subject_id=sub1.id,
            faculty_id=f.id,
            course_name="B.Tech",
            date=test_date,
            status="Present"
        )
        db.session.add(att1)
        db.session.commit()
        print(f"[✓] Marked Present for {sub1.name} (Math) on {test_date}")
        print(f"[ ] DID NOT mark anything for {sub2.name} (Physics)")
        
        # 3. Verify Database State
        math_att = Attendance.query.filter_by(student_id=s.id, subject_id=sub1.id).count()
        phys_att = Attendance.query.filter_by(student_id=s.id, subject_id=sub2.id).count()
        
        print(f"--- DB State ---")
        print(f"Math Records: {math_att} (Expected 1)")
        print(f"Physics Records: {phys_att} (Expected 0)")
        
        if phys_att > 0:
            print("CRITICAL ERROR: Physics record exists but wasn't marked!")
            
        # 4. Simulate Student View Logic (Reproducing app/student/routes.py logic)
        print("\n--- Simulating Student View Logic ---")
        
        # Replicating the logic from 'attendance' route
        # Map: DayName (0=Mon) -> [Subject_IDs]
        day_map = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        weekdays_str_map = {'Monday': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
        
        # Using the timetable we created
        timetable_entries = [t1, t2]
        for slot in timetable_entries:
            d_idx = weekdays_str_map.get(slot.day_of_week)
            if d_idx is not None:
                day_map[d_idx].append(slot.subject_id)
                
        # Subject Stats Init
        subject_stats = {
            sub1.id: {'name': sub1.name, 'total': 0, 'present': 0},
            sub2.id: {'name': sub2.name, 'total': 0, 'present': 0}
        }
        
        # Iterate Records
        records = Attendance.query.filter_by(student_id=s.id).all()
        
        for record in records:
            # Correct Logic: Use Subject ID
            if record.subject_id:
                if record.subject_id in subject_stats:
                    subject_stats[record.subject_id]['total'] += 1
                    if record.status == 'Present':
                        subject_stats[record.subject_id]['present'] += 1
            else:
                 # Legacy Fallback (keeping for reference in test)
                 day_idx = record.date.weekday() 
                 relevant_subjects = day_map.get(day_idx, [])
                 for sub_id in relevant_subjects:
                    if sub_id in subject_stats:
                        subject_stats[sub_id]['total'] += 1
                        if record.status == 'Present':
                            subject_stats[sub_id]['present'] += 1
                        
        # Report Results
        print("\n--- Student View Results ---")
        math_stats = subject_stats[sub1.id]
        phys_stats = subject_stats[sub2.id]
        
        print(f"Math (Calculated): {math_stats['present']}/{math_stats['total']}")
        print(f"Physics (Calculated): {phys_stats['present']}/{phys_stats['total']}")
        
        print("\n--- Analysis ---")
        if phys_stats['present'] > 0:
            print("❌ TEST FAILED: Physics shows as Present but only Math was marked!")
            print("   Reason: Student view logic assumes 'Present on Day X' = 'Present for ALL subjects on Day X'.")
            print("   This is an inconsistency because Attendance is marked per-subject.")
        else:
            print("✅ TEST PASSED: Physics correctly shows 0 attendance.")

if __name__ == "__main__":
    test_attendance_consistency()


import sys
import os
import pytest
from datetime import date, timedelta

# Add app to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User, StudentProfile, FacultyProfile, Subject, Attendance

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            # Cleanup
            db.create_all()
            yield client
            db.session.remove()
            # db.drop_all() # Optional: Keep data for debug if needed

def test_attendance_view_consistency(client):
    """
    Verify that Admin, Student, and Faculty views all see the exact same attendance %.
    """
    print("\n--- Starting View Consistency Test ---")
    
    # 0. Cleanup Old Data
    existing_u_stu = User.query.filter_by(email="view_test_stu@edu.com").first()
    if existing_u_stu:
        # Delete profile first if linked
        if existing_u_stu.student_profile:
             # Delete linked data
             Attendance.query.filter_by(student_id=existing_u_stu.student_profile.id).delete()
             db.session.delete(existing_u_stu.student_profile)
        db.session.delete(existing_u_stu)
        
    existing_u_fac = User.query.filter_by(email="view_test_fac@edu.com").first()
    if existing_u_fac:
        if existing_u_fac.faculty_profile:
             # Cleanup subjects
             Subject.query.filter_by(faculty_id=existing_u_fac.faculty_profile.id).delete()
             db.session.delete(existing_u_fac.faculty_profile)
        db.session.delete(existing_u_fac)
    
    db.session.commit()
    
    # 1. Setup Data
    # Student
    u_stu = User(email="view_test_stu@edu.com", role='student')
    u_stu.set_password('123')
    db.session.add(u_stu)
    db.session.flush()
    
    s = StudentProfile(
        user_id=u_stu.id, display_name="ViewTest Student", enrollment_number="VIEW001",
        course_name="B.Tech", semester=1
    )
    db.session.add(s)
    
    # Faculty
    u_fac = User(email="view_test_fac@edu.com", role='faculty')
    u_fac.set_password('123')
    db.session.add(u_fac)
    db.session.flush()
    
    f = FacultyProfile(
        user_id=u_fac.id, display_name="ViewTest Prof", designation="Prof", department="IT"
    )
    db.session.add(f)
    db.session.flush()
    
    # Subject
    sub = Subject(name="ViewSubject", course_name="B.Tech", semester=1, faculty_id=f.id)
    db.session.add(sub)
    db.session.commit()
    
    # 2. Mark Attendance (3 Present out of 4 Total = 75.0%)
    dates = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 4)]
    statuses = ['Present', 'Present', 'Absent', 'Present']
    
    for d, status in zip(dates, statuses):
        att = Attendance(
            student_id=s.id, subject_id=sub.id, faculty_id=f.id,
            course_name="B.Tech", date=d, status=status
        )
        db.session.add(att)
    db.session.commit()
    
    print("[✓] Data Setup: 4 days, 3 Present. Expected: 75.0%")

    # 3. Check Admin/Model View (The Source of Truth)
    # Admin uses student.get_overall_attendance() in the list view
    admin_view_val = s.get_overall_attendance()
    print(f"[Admin Panel] Calculated: {admin_view_val}%")
    assert admin_view_val == 75.0
    
    # 4. Check Student Dashboard View
    # Login as Student
    client.post('/auth/login', data={'email': 'view_test_stu@edu.com', 'password': '123', 'role': 'student'})
    
    # Fetch Dashboard
    resp = client.get('/student/dashboard')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    
    # Verify the value 75.0 is present in the rendered HTML
    # We look for "75.0%" or similar. The template uses {{ attendance_pct }}
    if "75.0" in html:
        print(f"[Student Panel] Dashboard HTML contains '75.0': MATCH")
    else:
        print("[Student Panel] FAILED: Could not find '75.0' in dashboard HTML!")
        # Debug: Print snippets
        # print(html[:1000])
        assert False, "Student Dashboard mismatch"
        
    # Check Student Attendance Route (Detailed View)
    resp_att = client.get('/student/attendance')
    html_att = resp_att.data.decode('utf-8')
    if "75.0" in html_att:
        print(f"[Student Panel] Detailed View HTML contains '75.0': MATCH")
    else:
        print("[Student Panel] FAILED: Could not find '75.0' in detailed view HTML!")
        assert False
        
    client.get('/auth/logout')
    
    # 5. Check Faculty View
    # Faculty sees it in 'student_detail'
    client.post('/auth/login', data={'email': 'view_test_fac@edu.com', 'password': '123', 'role': 'faculty'})
    resp_fac = client.get(f'/faculty/student/{s.id}')
    assert resp_fac.status_code == 200
    html_fac = resp_fac.data.decode('utf-8')
    
    if "75.0" in html_fac:
        print(f"[Faculty Panel] Student Detail HTML contains '75.0': MATCH")
    else:
        print("[Faculty Panel] FAILED: Could not find '75.0' in faculty view!")
        assert False
        
    print("\n✅ SUCCESS: All 3 panels show exactly 75.0%")

if __name__ == "__main__":
    import traceback
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    print("Running test_view_consistency as script...")
    
    try:
        with app.test_client() as c:
            with app.app_context():
                db.create_all()
                try:
                    test_attendance_view_consistency(c)
                finally:
                   pass
    except Exception:
        with open("traceback_internal.log", "w") as f:
            traceback.print_exc(file=f)
        print("CRITICAL ERROR: Exception captured to traceback_internal.log")

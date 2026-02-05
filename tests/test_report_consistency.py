
import pytest
from app import create_app, db
from app.models import User, StudentProfile, StudentResult, ExamEvent, ExamPaper, Subject
from datetime import date

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()

def test_student_performance_api_crash(client):
    """
    Regression Test: Ensure the API handles students with partial semester data without crashing.
    Bug: TypeError: '>' not supported between instances of 'list' and 'int'
    """
    # Create User & Valid Student
    u = User.query.filter_by(email="crash_test@edu.com").first()
    if not u:
        u = User(email="crash_test@edu.com", role='student')
        u.set_password('123')
        db.session.add(u)
        db.session.flush()

    if u.student_profile:
        s = u.student_profile
    else:
        s = StudentProfile(user_id=u.id, display_name="Crash Test Dummy", enrollment_number="CRASH001", course_name="B.Tech", semester=3)
        db.session.add(s)
        db.session.flush()

    # Create Subject & Event for Semester 1 (We will NOT add Semester 3 data to trigger the gap)
    # Create Subject & Event for Semester 1 (We will NOT add Semester 3 data to trigger the gap)
    sub = Subject(name="Maths", course_name="B.Tech", semester=1)
    db.session.add(sub)
    db.session.flush()

    from datetime import time
    event = ExamEvent(
        name="Sem 1 Finals", 
        academic_year="2025-2026",
        course_name="B.Tech",
        semester=1,
        start_date=date.today(),
        end_date=date.today()
    )
    db.session.add(event)
    db.session.flush()

    paper = ExamPaper(
        exam_event_id=event.id, 
        subject_id=sub.id, 
        date=date.today(),
        start_time=time(9,0),
        end_time=time(12,0)
    )
    db.session.add(paper)
    db.session.flush()

    # Add Result for Sem 1
    res = StudentResult(student_id=s.id, exam_paper_id=paper.id, marks_obtained=85.0)
    db.session.add(res)
    db.session.commit()

    # 2. Authenticate as Admin
    u_admin = User.query.filter_by(email="admin@edu.com").first()
    if not u_admin:
        u_admin = User(email="admin@edu.com", role='admin')
        db.session.add(u_admin)
    
    u_admin.set_password('admin')
    db.session.commit()
    
    client.post('/auth/login', data={'email': 'admin@edu.com', 'password': 'admin', 'role': 'admin'})

    # 3. Call The API
    # This should NOT crash with 500
    resp = client.get('/admin/api/reports/student-performance')
    
    # Debug output if validation fails
    if resp.status_code != 200:
        print(f"API Failed: {resp.status_code}")
        # print(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    json_data = resp.get_json()
    assert 'consistency' in json_data
    assert len(json_data['consistency']) > 0

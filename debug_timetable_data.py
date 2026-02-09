
from app import create_app, db
from app.models import StudentProfile, Course, Timetable

app = create_app()

with app.app_context():
    print("\n--- 1. ALL COURSES ---")
    courses = Course.query.all()
    for c in courses:
        print(f"ID: {c.id}, Name: '{c.name}', Code: '{c.code}'")

    print("\n--- 2. TARGET STUDENT (student1@edu.com) ---")
    # Find user first
    from app.models import User
    u = User.query.filter_by(email='student1@edu.com').first()
    if u:
        s = StudentProfile.query.filter_by(user_id=u.id).first()
        if s:
            print(f"Found Student: ID={s.id}, Name='{s.display_name}', Course='{s.course_name}', Sem={s.semester}")
            
            print("\n--- 3. TIMETABLE ENTRIES FOR THIS STUDENT ---")
            # 1. Direct Match
            direct_entries = Timetable.query.filter_by(course_name=s.course_name, semester=s.semester).all()
            print(f"Entries matching Course='{s.course_name}': {len(direct_entries)}")
            for t in direct_entries:
                print(f" - Day: {t.day_of_week}, Period: {t.period_number}, SubjectID: {t.subject_id}")
            
            # 2. Code/Name Mismatch Check
            c_def = Course.query.filter((Course.name == s.course_name) | (Course.code == s.course_name)).first()
            if c_def:
                print(f"Resolved Course Def -> Name: '{c_def.name}', Code: '{c_def.code}'")
                
                if c_def.code != s.course_name:
                    code_entries = Timetable.query.filter_by(course_name=c_def.code, semester=s.semester).all()
                    print(f"Entries matching CODE '{c_def.code}': {len(code_entries)}")
                    for t in code_entries:
                         print(f" - Day: {t.day_of_week}, Period: {t.period_number}, SubjectID: {t.subject_id}")

                if c_def.name != s.course_name:
                    name_entries = Timetable.query.filter_by(course_name=c_def.name, semester=s.semester).all()
                    print(f"Entries matching NAME '{c_def.name}': {len(name_entries)}")
            else:
                 print("CRITICAL: Course Definition NOT FOUND for this student's course_name!")
        else:
            print("StudentProfile not found for this user.")
    else:
        print("User 'student1@edu.com' not found.")

    print("\n--- 4. ALL TIMETABLE ENTRIES (Summary) ---")
    all_tt = Timetable.query.all()
    from collections import Counter
    summary = Counter([(t.course_name, t.semester) for t in all_tt])
    for (c, sm), count in summary.items():
        print(f"Course: '{c}', Sem: {sm} -> {count} slots")

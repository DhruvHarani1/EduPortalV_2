import sys
import os
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Timetable, Subject, FacultyProfile
import random

app = create_app()

def seed_timetable():
    with app.app_context():
        print("--- Seeding Timetable Data ---")
        
        # Clear existing
        num_deleted = Timetable.query.delete()
        db.session.commit()
        print(f"Cleared {num_deleted} existing timetable records.")

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        periods = [1, 2, 3, 4, 5, 6]
        
        # Target Semesters
        semesters = [1, 3] # Common ones we have data for
        course = "B.Tech"
        
        for sem in semesters:
            print(f"Generating Timetable for Sem {sem}...")
            subjects = Subject.query.filter_by(course_name=course, semester=sem).all()
            
            if not subjects:
                print(f"  No subjects found for Sem {sem}. Skipping.")
                continue
                
            for day in days:
                for p in periods:
                    # Pick random subject
                    sub = random.choice(subjects)
                    
                    # Ensure subject has faculty
                    if not sub.faculty_id:
                        # Try to find one or skip
                        fac = FacultyProfile.query.first()
                        if fac:
                            sub.faculty_id = fac.id
                            db.session.add(sub)
                            db.session.commit()
                        else:
                            continue
                            
                    # Create Slot
                    slot = Timetable(
                        course_name=course,
                        semester=sem,
                        day_of_week=day,
                        period_number=p,
                        subject_id=sub.id,
                        faculty_id=sub.faculty_id,
                        room_number=f"Room-{100+sem}"
                    )
                    db.session.add(slot)
            
            db.session.commit()
            print(f"  Created schedule for {day}...")
            
        print("--- Timetable Seeding Complete ---")

if __name__ == '__main__':
    seed_timetable()

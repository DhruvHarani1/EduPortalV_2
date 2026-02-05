import sys
from app import create_app, db
from app.models import User

app = create_app('development')

with app.app_context():
    # Helper to create user if not exists
    def create_user_if_not_exists(email, password, role):
        try:
            if not User.query.filter_by(email=email).first():
                user = User(email=email, role=role)
                user.set_password(password)
                db.session.add(user)
                print(f"Created {role} user: {email}")
            else:
                print(f"User {email} already exists")
        except Exception as e:
            print(f"Error creating user {email}: {e}")

    create_user_if_not_exists('admin@edu.com', 'password', 'admin')
    create_user_if_not_exists('faculty@edu.com', 'password', 'faculty')
    create_user_if_not_exists('student@edu.com', 'password', 'student')

    try:
        db.session.commit()
        print("Database seeded!")
    except Exception as e:
        db.session.rollback()
        print(f"Failed to commit changes: {e}")

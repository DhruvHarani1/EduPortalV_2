import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Club

def fix_duplicates():
    with app.app_context():
        # Find the duplicate "Saazroom" (ID 6 based on previous inspection)
        # We want to keep "Saaz Room" (ID 4)
        
        duplicate = Club.query.filter_by(name="Saazroom").first()
        if duplicate:
            print(f"Found duplicate club: {duplicate.name} (ID: {duplicate.id})")
            db.session.delete(duplicate)
            db.session.commit()
            print("Duplicate deleted successfully.")
        else:
            print("No club named 'Saazroom' found.")

if __name__ == "__main__":
    fix_duplicates()

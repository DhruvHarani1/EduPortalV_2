
from app import app, db
from models import Club

def update_clubs():
    with app.app_context():
        # 1. Delete Byte Club
        byte_club = Club.query.filter_by(name='Byte Club').first()
        if byte_club:
            db.session.delete(byte_club)
            print("Deleted Byte Club.")
        else:
            print("Byte Club not found.")

        # 2. Update Binary Brains
        bb_club = Club.query.filter_by(name='Binary Brains').first()
        if bb_club:
            bb_club.description = "The tech community -> Events , hackathons , meet and greets and your ultimate tech buddy"
            print("Updated Binary Brains description.")
        else:
            print("Binary Brains not found.")

        db.session.commit()
        print("Database updates committed.")

if __name__ == "__main__":
    update_clubs()

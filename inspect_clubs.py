from app import app, db
from models import Club

def inspect_clubs():
    with app.app_context():
        clubs = Club.query.all()
        print(f"{'ID':<5} {'Name':<30} {'Category':<20} {'Active':<10}")
        print("-" * 70)
        for club in clubs:
            print(f"{club.id:<5} {club.name:<30} {club.category:<20} {club.is_active:<10}")

if __name__ == "__main__":
    inspect_clubs()

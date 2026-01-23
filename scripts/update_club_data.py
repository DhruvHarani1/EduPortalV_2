
from app import app, db
from models import Club, Faculty

def update_club_data():
    with app.app_context():
        # helper to get or create club
        def update_or_create_club(name, category, interests, description=""):
            club = Club.query.filter_by(name=name).first()
            if not club:
                print(f"Creating new club: {name}")
                # Assign a default faculty if needed
                faculty = Faculty.query.first()
                club = Club(
                    name=name,
                    category=category,
                    faculty_coordinator=faculty.id if faculty else 1,
                    meeting_schedule="Weekly",
                    contact_email=f"{name.lower().replace(' ', '')}@college.edu"
                )
                db.session.add(club)
            
            # Update fields
            club.interests = interests
            club.category = category # Enforce category
            if description:
                club.description = description
            
            print(f"Updated {name} with interests: {interests}")

        # 1. Binary Brains
        update_or_create_club(
            "Binary Brains", 
            "technical", 
            "tech,coding,events,social_media",
            "The tech community -> Events , hackathons , meet and greets and your ultimate tech buddy"
        )

        # 2. LFA (assuming full name is LFA)
        update_or_create_club(
            "LFA", 
            "literary", 
            "marketing,content_writing,social_media,literature",
            "Literature, arts, and creative expression community."
        )

        # 3. Saaz Room
        update_or_create_club(
            "Saaz Room", 
            "cultural", 
            "music,songs,artist",
            "The ultimate music community for artists and enthusiasts."
        )

        # 4. LJSC
        update_or_create_club(
            "LJSC", 
            "social", 
            "social_media,events",
            "Leadership and Social Club - Events and social media handling."
        )

        db.session.commit()
        print("All clubs updated successfully!")

if __name__ == "__main__":
    update_club_data()

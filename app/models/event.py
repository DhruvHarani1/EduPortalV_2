from app.extensions import db
from datetime import datetime, timezone

class UniversityEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    organizer = db.Column(db.String(100), default="University Admin")
    category = db.Column(db.String(50), default="General") # Academic, Cultural, Sports, Tech
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mimetype = db.Column(db.String(50), nullable=True) # e.g. 'image/png'
    is_upcoming = db.Column(db.Boolean, default=True)
    
    # Relationships
    registrations = db.relationship('EventRegistration', backref='event', lazy=True)

    def __repr__(self):
        return f'<UniversityEvent {self.title}>'

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('university_event.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    student = db.relationship('StudentProfile', backref=db.backref('event_registrations', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<Registration {self.student_id} -> {self.event_id}>'

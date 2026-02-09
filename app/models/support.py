from datetime import datetime, timezone
from app.extensions import db

class StudentQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty_profile.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True) # Optional link to subject
    
    title = db.Column(db.String(200), nullable=False) # Context/Subject of the doubt
    status = db.Column(db.String(20), default='Pending') # Pending, Answered, Resolved
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    student = db.relationship('StudentProfile', backref=db.backref('queries', lazy=True, cascade="all, delete-orphan"))
    faculty = db.relationship('FacultyProfile', backref=db.backref('queries', lazy=True, cascade="all, delete-orphan"))
    subject = db.relationship('Subject', backref=db.backref('queries', lazy=True))
    messages = db.relationship('QueryMessage', backref='query', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Query {self.id} Status:{self.status}>'

class QueryMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('student_query.id'), nullable=False)
    
    sender_type = db.Column(db.String(20), nullable=False) # 'student' or 'faculty'
    content = db.Column(db.Text, nullable=True)
    
    # Image Support
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mimetype = db.Column(db.String(50), nullable=True)
    
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Msg {self.id} from {self.sender_type}>'

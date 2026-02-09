from datetime import datetime, timezone
from app.extensions import db

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='general') 
    
    # Targeting Logic
    target_type = db.Column(db.String(50), default='all') # all, class, mentees, individual, faculty
    
    # Specific Targets
    target_course = db.Column(db.String(100))
    target_semester = db.Column(db.Integer)
    target_student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'))
    target_faculty_id = db.Column(db.Integer, db.ForeignKey('faculty_profile.id')) # Added targeted faculty
    
    # Sender Info (If None, assumed Admin)
    sender_faculty_id = db.Column(db.Integer, db.ForeignKey('faculty_profile.id'))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sender = db.relationship('FacultyProfile', foreign_keys=[sender_faculty_id], backref='sent_notices')
    target_student = db.relationship('StudentProfile', foreign_keys=[target_student_id], backref='received_notices')
    target_faculty = db.relationship('FacultyProfile', foreign_keys=[target_faculty_id], backref='received_faculty_notices')

    def __repr__(self):
        return f'<Notice {self.title}>'

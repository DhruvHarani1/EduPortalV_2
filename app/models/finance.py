from datetime import datetime
from app.extensions import db

class FeeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(20), nullable=False) # e.g. "2025-2026"
    
    amount_due = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.Date, nullable=False)
    
    status = db.Column(db.String(20), default='Pending') # Pending, Paid, Partial, Overdue
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_mode = db.Column(db.String(50), nullable=True) # Online, Cash, Cheque
    transaction_reference = db.Column(db.String(100), nullable=True)
    
    # Relationship
    student = db.relationship('StudentProfile', backref=db.backref('fee_records', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<FeeRecord Stud:{self.student_id} Sem:{self.semester} Status:{self.status}>'

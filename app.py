from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduportal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, faculty, admin
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    enrollment_number = db.Column(db.String(20), unique=True, nullable=False)
    current_semester = db.Column(db.Integer, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    division = db.Column(db.String(5))  # e.g., 'A', 'B', 'C'
    batch = db.Column(db.String(10))  # e.g., 'C1', 'C2'
    admission_year = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float, default=0.0)
    photo_url = db.Column(db.String(500))
    annual_income = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(20))  # general, obc, sc, st, ews
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    emergency_contact = db.Column(db.String(15))
    address = db.Column(db.Text)
    
    user = db.relationship('User', backref=db.backref('student', uselist=False))

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    faculty_id = db.Column(db.String(20), unique=True, nullable=False)
    designation = db.Column(db.String(50), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    specialization = db.Column(db.String(100))
    
    user = db.relationship('User', backref=db.backref('faculty', uselist=False))

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(10), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    duration_years = db.Column(db.Integer, nullable=False)
    total_semesters = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(50), unique=True, nullable=False) # Increased length for user codes
    subject_name = db.Column(db.String(200), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    credits = db.Column(db.Integer, default=3)
    subject_type = db.Column(db.String(50)) # Theory/Lab from SQL
    
    course = db.relationship('Course', backref='subjects')

class SubjectAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    
    faculty = db.relationship('Faculty', backref='assignments')
    subject = db.relationship('Subject', backref='assignments')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # present, absent
    marked_by = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    
    student = db.relationship('Student', backref='attendances')
    subject = db.relationship('Subject', backref='attendances')
    faculty = db.relationship('Faculty', backref='marked_attendances')

class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    exam_type = db.Column(db.String(20), nullable=False)  # internal, external, assignment
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    exam_date = db.Column(db.Date)
    semester = db.Column(db.Integer, nullable=False)
    
    student = db.relationship('Student', backref='marks')
    subject = db.relationship('Subject', backref='marks')

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notice_type = db.Column(db.String(20), nullable=False)  # general, exam, holiday, event, urgent
    target_audience = db.Column(db.String(20), nullable=False)  # all, students, faculty, department
    department = db.Column(db.String(50))  # if target is department
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    creator = db.relationship('User', backref='notices')

class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    subject = db.relationship('Subject', backref='materials')
    faculty = db.relationship('Faculty', backref='materials')

class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    tuition_fee = db.Column(db.Float, nullable=False)
    lab_fee = db.Column(db.Float, default=0.0)
    library_fee = db.Column(db.Float, default=0.0)
    other_fees = db.Column(db.Float, default=0.0)
    total_fee = db.Column(db.Float, nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    
    course = db.relationship('Course', backref='fee_structures')

class FeePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structure.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default='completed')
    
    student = db.relationship('Student', backref='fee_payments')
    fee_structure = db.relationship('FeeStructure', backref='payments')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # technical, cultural, sports, workshop
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(200))
    organizer_name = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(15))
    contact_email = db.Column(db.String(100))
    registration_required = db.Column(db.Boolean, default=False)
    registration_deadline = db.Column(db.DateTime)
    max_participants = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    creator = db.relationship('User', backref='created_events')

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # technical, cultural, sports, social
    interests = db.Column(db.Text)  # comma-separated interests
    faculty_coordinator = db.Column(db.Integer, db.ForeignKey('faculty.id'))
    student_coordinator = db.Column(db.String(100))
    meeting_schedule = db.Column(db.String(200))
    contact_email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    
    coordinator = db.relationship('Faculty', backref='coordinated_clubs')

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    division = db.Column(db.String(5), nullable=True) # Modified: nullable. A, B, C or None for common
    batch = db.Column(db.String(10), nullable=True) # C1, C2, etc. or None
    day_of_week = db.Column(db.String(10), nullable=False)  # monday, tuesday, etc.
    time_slot = db.Column(db.String(20), nullable=False)  # 09:00-10:00
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    room_number = db.Column(db.String(20))
    academic_year = db.Column(db.String(10), nullable=False)
    
    course = db.relationship('Course', backref='timetables')
    subject = db.relationship('Subject', backref='timetable_entries')
    faculty = db.relationship('Faculty', backref='timetable_entries')

class StudentQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    query_title = db.Column(db.String(200), nullable=False)
    query_description = db.Column(db.Text, nullable=False)
    attachment_url = db.Column(db.String(500))  # for photo upload
    status = db.Column(db.String(20), default='pending')  # pending, answered, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)
    
    student = db.relationship('Student', backref='subject_queries')
    faculty = db.relationship('Faculty', backref='student_queries')
    subject = db.relationship('Subject', backref='student_queries')

class QueryResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('student_query.id'), nullable=False)
    response_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    query = db.relationship('StudentQuery', backref='responses')

class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # merit, need, minority, sports
    eligibility_criteria = db.Column(db.Text, nullable=False)
    min_cgpa = db.Column(db.Float, default=0.0)
    max_family_income = db.Column(db.Float, default=0.0)
    eligible_categories = db.Column(db.String(200))  # general,obc,sc,st,ews
    eligible_genders = db.Column(db.String(50))  # male,female,other,all
    amount = db.Column(db.Float, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    official_website = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScholarshipApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    documents_submitted = db.Column(db.Boolean, default=False)
    
    student = db.relationship('Student', backref='scholarship_applications')
    scholarship = db.relationship('Scholarship', backref='applications')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # notice, query, fee, scholarship, attendance
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')

class Mentorship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    faculty = db.relationship('Faculty', backref='mentees')
    student = db.relationship('Student', backref='mentors')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student-dashboard')
def student_dashboard():
    return render_template('student-dashboard.html')

@app.route('/faculty-dashboard')
def faculty_dashboard():
    return render_template('faculty-dashboard.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    user = User.query.filter_by(username=username, role=role).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['role'] = user.role
        
        # Get additional user data based on role
        user_data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'department': user.department
        }
        
        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                user_data.update({
                    'roll_number': student.roll_number,
                    'enrollment_number': student.enrollment_number,
                    'current_semester': student.current_semester,
                    'branch': student.branch,
                    'division': student.division,
                    'batch': student.batch,
                    'cgpa': student.cgpa
                })
        elif user.role == 'faculty':
            faculty = Faculty.query.filter_by(user_id=user.id).first()
            if faculty:
                user_data.update({
                    'faculty_id': faculty.faculty_id,
                    'designation': faculty.designation,
                    'experience_years': faculty.experience_years,
                    'specialization': faculty.specialization
                })
        
        return jsonify({'success': True, 'user': user_data})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/api/events')
def get_events():
    events = Event.query.filter(Event.is_active == True).order_by(Event.start_date.desc()).all()
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type,
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat(),
            'venue': event.venue,
            'organizer_name': event.organizer_name,
            'contact_person': event.contact_person,
            'contact_phone': event.contact_phone,
            'contact_email': event.contact_email,
            'registration_required': event.registration_required,
            'registration_deadline': event.registration_deadline.isoformat() if event.registration_deadline else None,
            'max_participants': event.max_participants
        })
    
    return jsonify(events_data)

@app.route('/api/student/fee-history/<int:student_id>')
def get_fee_history(student_id):
    payments = FeePayment.query.filter_by(student_id=student_id).order_by(FeePayment.payment_date.desc()).all()
    
    fee_history = []
    for payment in payments:
        fee_structure = payment.fee_structure
        fee_history.append({
            'id': payment.id,
            'semester': fee_structure.semester,
            'academic_year': fee_structure.academic_year,
            'amount_paid': payment.amount_paid,
            'payment_date': payment.payment_date.isoformat(),
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'tuition_fee': fee_structure.tuition_fee,
            'lab_fee': fee_structure.lab_fee,
            'library_fee': fee_structure.library_fee,
            'other_fees': fee_structure.other_fees,
            'total_fee': fee_structure.total_fee
        })
    
    return jsonify(fee_history)

@app.route('/api/student/queries', methods=['GET', 'POST'])
def handle_student_queries():
    if request.method == 'POST':
        data = request.get_json()
        
        query = StudentQuery(
            student_id=data.get('student_id'),
            faculty_id=data.get('faculty_id'),
            subject_id=data.get('subject_id'),
            query_title=data.get('query_title'),
            query_description=data.get('query_description'),
            attachment_url=data.get('attachment_url')
        )
        
        db.session.add(query)
        
        # Create notification for faculty
        faculty = Faculty.query.get(data.get('faculty_id'))
        if faculty:
            notification = Notification(
                user_id=faculty.user_id,
                title='New Student Query',
                message=f'New query: {data.get("query_title")}',
                notification_type='query'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Query submitted successfully'})
    
    else:
        student_id = request.args.get('student_id')
        queries = StudentQuery.query.filter_by(student_id=student_id).order_by(StudentQuery.created_at.desc()).all()
        
        queries_data = []
        for query in queries:
            queries_data.append({
                'id': query.id,
                'query_title': query.query_title,
                'query_description': query.query_description,
                'subject_name': query.subject.subject_name,
                'faculty_name': query.faculty.user.full_name,
                'status': query.status,
                'created_at': query.created_at.isoformat(),
                'answered_at': query.answered_at.isoformat() if query.answered_at else None,
                'responses': [
                    {
                        'response_text': resp.response_text,
                        'created_at': resp.created_at.isoformat()
                    } for resp in query.responses
                ]
            })
        
        return jsonify(queries_data)

@app.route('/api/student/id-card/<int:student_id>')
def get_student_id_card(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    id_card_data = {
        'full_name': student.user.full_name,
        'roll_number': student.roll_number,
        'enrollment_number': student.enrollment_number,
        'branch': student.branch,
        'semester': student.current_semester,
        'admission_year': student.admission_year,
        'photo_url': student.photo_url or 'https://via.placeholder.com/150x180',
        'blood_group': student.blood_group,
        'emergency_contact': student.emergency_contact,
        'address': student.address,
        'valid_until': f"{student.admission_year + 4}-12-31"
    }
    
    return jsonify(id_card_data)

@app.route('/api/clubs')
def get_clubs():
    clubs = Club.query.filter(Club.is_active == True).all()
    
    clubs_data = []
    for club in clubs:
        clubs_data.append({
            'id': club.id,
            'name': club.name,
            'description': club.description,
            'category': club.category,
            'interests': club.interests.split(',') if club.interests else [],
            'faculty_coordinator': club.coordinator.user.full_name if club.coordinator else None,
            'student_coordinator': club.student_coordinator,
            'meeting_schedule': club.meeting_schedule,
            'contact_email': club.contact_email
        })
    
    return jsonify(clubs_data)

@app.route('/api/student/club-recommendations', methods=['POST'])
def get_club_recommendations():
    data = request.get_json()
    student_interests = data.get('interests', [])
    
    # Get all clubs and calculate match score
    clubs = Club.query.filter(Club.is_active == True).all()
    recommendations = []
    
    for club in clubs:
        club_interests = club.interests.split(',') if club.interests else []
        match_score = len(set(student_interests) & set(club_interests))
        
        if match_score > 0:
            recommendations.append({
                'club': {
                    'id': club.id,
                    'name': club.name,
                    'description': club.description,
                    'category': club.category,
                    'faculty_coordinator': club.coordinator.user.full_name if club.coordinator else None,
                    'contact_email': club.contact_email
                },
                'match_score': match_score,
                'matching_interests': list(set(student_interests) & set(club_interests))
            })
    
    # Sort by match score
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify(recommendations)

@app.route('/api/student/timetable/<int:student_id>')
def get_student_timetable(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Get timetable for student's course, semester matches, AND (batch match OR null batch)
    if not student.division:
         # Fallback to general course/semester
        timetable_entries = Timetable.query.join(Course).filter(
            Course.course_name == student.branch,
            Timetable.semester == student.current_semester
        ).all()
    else:
        # Get entries for the student's DIVISION
        # AND ( entries with NO batch (Lectures) OR entries with MATCHING batch (Labs) )
        timetable_entries = Timetable.query.join(Course).filter(
            Course.course_name == student.branch,
            Timetable.semester == student.current_semester,
            Timetable.division == student.division,
            db.or_(Timetable.batch == None, Timetable.batch == student.batch)
        ).all()
    
    # Organize by day and time
    timetable = {}
    
    # Ensure all days are initialized for the frontend grid
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    for day in days:
        timetable[day] = {}
        # Pre-fill common slots (optional, but API usually just returns what it has)
    
    for entry in timetable_entries:
        day = entry.day_of_week.lower()
        time_slot = entry.time_slot
        
        timetable[day][time_slot] = {
            'subject_name': entry.subject.subject_name,
            'subject_code': entry.subject.subject_code,
            'faculty_name': entry.faculty.user.full_name,
            'room_number': entry.room_number
        }
    
    return jsonify(timetable)

@app.route('/api/scholarships/eligible', methods=['POST'])
def get_eligible_scholarships():
    data = request.get_json()
    student_cgpa = data.get('cgpa', 0.0)
    
    # Get inputs with fallback
    # The frontend sends these if the user fills them.
    family_income = data.get('family_income')
    category = data.get('category')
    gender = data.get('gender')
    
    # Filter scholarships based on strict eligibility
    scholarships = Scholarship.query.filter(Scholarship.is_active == True).all()
    eligible_scholarships = []
    
    for scholarship in scholarships:
        eligible = True
        reasons = []
        
        # 1. Check CGPA requirement (if student has one)
        if scholarship.min_cgpa > 0 and student_cgpa > 0 and student_cgpa < scholarship.min_cgpa:
            eligible = False
            reasons.append(f"Minimum CGPA required: {scholarship.min_cgpa}")
        
        # 2. Check income requirement (Strict)
        # If user provided income, check against max limit.
        if family_income is not None:
            try:
                income_val = float(family_income)
                if scholarship.max_family_income > 0 and income_val > scholarship.max_family_income:
                    eligible = False
                    reasons.append(f"Income exceeds limit of ₹{scholarship.max_family_income:,.0f}")
            except ValueError:
                pass # Invalid income input, ignore or handle? For now ignore.

        # 3. Check category eligibility (Strict)
        # If user provided category, it MUST be in the eligible list.
        if category:
            eligible_cats = [c.strip().lower() for c in scholarship.eligible_categories.split(',')]
            if 'all' not in eligible_cats and category.lower() not in eligible_cats:
                eligible = False
                reasons.append(f"Only for categories: {scholarship.eligible_categories}")
        
        # 4. Check gender eligibility (Strict)
        # If user provided gender, it MUST match.
        if gender:
            eligible_gens = [g.strip().lower() for g in scholarship.eligible_genders.split(',')]
            # 'all' means any gender is fine.
            if 'all' not in eligible_gens and gender.lower() not in eligible_gens:
                eligible = False
                reasons.append(f"Only for gender: {scholarship.eligible_genders}")
        
        # Only add if eligible (User asked to "match the details... and then show them the scholarship")
        # So we primarily want to show ELIGIBLE ones.
        if eligible:
            eligible_scholarships.append({
                'id': scholarship.id,
                'name': scholarship.name,
                'description': scholarship.description,
                'category': scholarship.category,
                'amount': scholarship.amount,
                'deadline': scholarship.deadline.isoformat(),
                'official_website': scholarship.official_website,
                'eligible': True,
                'eligibility_criteria': scholarship.eligibility_criteria
            })
    
    return jsonify(eligible_scholarships)

@app.route('/api/student/attendance/<int:student_id>')
def get_student_attendance(student_id):
    # Calculate attendance for each subject
    subjects = Subject.query.join(Course).filter(Course.department == 'Computer Science').all()
    attendance_data = []
    
    for subject in subjects:
        total_classes = Attendance.query.filter_by(
            student_id=student_id, 
            subject_id=subject.id
        ).count()
        
        present_classes = Attendance.query.filter_by(
            student_id=student_id, 
            subject_id=subject.id, 
            status='present'
        ).count()
        
        attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
        
        attendance_data.append({
            'subject_name': subject.subject_name,
            'attendance_percentage': round(attendance_percentage, 2),
            'present_classes': present_classes,
            'total_classes': total_classes
        })
    
    return jsonify(attendance_data)

@app.route('/api/student/marks/<int:student_id>')
def get_student_marks(student_id):
    marks = db.session.query(Marks, Subject).join(Subject).filter(
        Marks.student_id == student_id
    ).all()
    
    marks_data = []
    for mark, subject in marks:
        marks_data.append({
            'subject_name': subject.subject_name,
            'exam_type': mark.exam_type,
            'marks_obtained': mark.marks_obtained,
            'max_marks': mark.max_marks,
            'percentage': round((mark.marks_obtained / mark.max_marks) * 100, 2),
            'exam_date': mark.exam_date.isoformat() if mark.exam_date else None,
            'semester': mark.semester
        })
    
    return jsonify(marks_data)

@app.route('/api/notices')
def get_notices():
    role = request.args.get('role', 'all')
    department = request.args.get('department')
    
    query = Notice.query.filter(Notice.is_active == True)
    
    if role != 'all':
        query = query.filter(
            (Notice.target_audience == 'all') | 
            (Notice.target_audience == role)
        )
    
    if department:
        query = query.filter(
            (Notice.target_audience != 'department') |
            (Notice.department == department)
        )
    
    notices = query.order_by(Notice.created_at.desc()).all()
    
    notices_data = []
    for notice in notices:
        notices_data.append({
            'id': notice.id,
            'title': notice.title,
            'content': notice.content,
            'notice_type': notice.notice_type,
            'created_at': notice.created_at.isoformat(),
            'expires_at': notice.expires_at.isoformat() if notice.expires_at else None
        })
    
    return jsonify(notices_data)

@app.route('/api/faculty/classes/<int:faculty_id>')
def get_faculty_classes(faculty_id):
    assignments = db.session.query(SubjectAssignment, Subject, Course).join(
        Subject
    ).join(Course).filter(
        SubjectAssignment.faculty_id == faculty_id
    ).all()
    
    classes_data = []
    for assignment, subject, course in assignments:
        # Get student count for this subject
        student_count = db.session.query(Student).join(Course).filter(
            Course.id == course.id
        ).count()
        
        classes_data.append({
            'subject_name': subject.subject_name,
            'subject_code': subject.subject_code,
            'course_name': course.course_name,
            'semester': assignment.semester,
            'student_count': student_count,
            'credits': subject.credits
        })
    
    return jsonify(classes_data)

@app.route('/api/admin/stats')
def get_admin_stats():
    total_students = Student.query.count()
    total_faculty = Faculty.query.count()
    total_courses = Course.query.count()
    
    # Calculate total fee collection (mock data)
    total_fee_collection = db.session.query(db.func.sum(FeePayment.amount_paid)).scalar() or 0
    
    return jsonify({
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_courses': total_courses,
        'total_fee_collection': total_fee_collection
    })

# Initialize database
def init_db():
    with app.app_context():
        # Drop all tables to reset schema
        db.drop_all()
        db.create_all()
        
        # Create sample data if tables are empty
        if User.query.count() == 0:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@college.edu',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                full_name='System Administrator',
                department='Administration'
            )
            db.session.add(admin)
            
            # Create standard Faculty User (Placeholder for relations if needed)
            faculty_user = User(
                username='prof.smith',
                email='prof.smith@college.edu',
                password_hash=generate_password_hash('faculty123'),
                role='faculty',
                full_name='Prof. John Smith',
                department='Computer Science'
            )
            db.session.add(faculty_user)
            
            # Create sample student (Assigned to Semester 3, Division C, Batch C1)
            # Updated to match the SQL data context
            student_user = User(
                username='2023001',
                email='john.doe@student.college.edu',
                password_hash=generate_password_hash('student123'),
                role='student',
                full_name='John Doe',
                department='Computer Science'
            )
            db.session.add(student_user)
            
            db.session.commit()
            
            # Create Student Record
            student_record = Student(
                user_id=student_user.id,
                roll_number='2023001',
                enrollment_number='EN2023001',
                current_semester=3, # Updated to Semester 3
                branch='Computer Science Engineering',
                division='C', # Keeping consistent with user's previous preference
                batch='C1',
                admission_year=2023,
                cgpa=8.5,
                photo_url='https://via.placeholder.com/150x180',
                annual_income=300000,
                category='general',
                gender='male',
                blood_group='B+',
                emergency_contact='9876543210',
                address='123 Main Street, City, State - 123456'
            )
            db.session.add(student_record)
            
            # Create Course
            cse_course = Course(
                course_code='CSE',
                course_name='Computer Science Engineering',
                department='Computer Science',
                duration_years=4,
                total_semesters=8
            )
            db.session.add(cse_course)
            db.session.commit()

            # --- PARSING SQL DATA START ---
            
            # 1. Faculty
            faculty_codes = ['MCV', 'MVP', 'DVP', 'PSK', 'RKU', 'DKU', 'RHG', 'PHA', 'UMS', 'SSD', 'BNS', 'KMS', 'SPP', 'ZPB', 'AAP', 'AKS', 'BMS', 'KGR', 'MIN', 'JDP', 'SYD', 'POS', 'BAP', 'SOS', 'MMC', 'MHP', 'ZNP', 'FJO', 'PSP', 'DPS', 'HEJ', 'SHP', 'JVD', 'NAS', 'VBV', 'MSS', 'TAT', 'PRZ']
            
            faculty_map = {} # Code -> ID
            
            for code in faculty_codes:
                # Reuse the faculty_user for all for login simplicity, but separate Faculty records
                # Ideally create Users for each, but for this demo, we just need Faculty records.
                # However, Faculty model links to User. So we need Users or link to the same dummy user.
                # Linking to same dummy user is fine for display.
                
                f = Faculty(
                    user_id=faculty_user.id,
                    faculty_id=code,
                    designation='Assistant Professor',
                    experience_years=5,
                    specialization='Engineering'
                )
                db.session.add(f)
                db.session.flush() # Get ID
                faculty_map[code] = f.id

            # 2. Subjects (Semester 3)
            # Extracted from SQL INSERTs
            subjects_data = [
                ('PS(MCV)-301', 'Programming Skills - MCV', 'Theory'),
                ('FCSP-1(MVP)-406-7/Lab', 'FCSP-1 MVP Lab', 'Lab'),
                ('FSD-1(SPP)-410-B/Lab', 'FSD-1 SPP Lab', 'Lab'),
                ('PS(PSK)-302', 'Programming Skills - PSK', 'Theory'),
                ('FSD-1(PHA)-406-6/Lab', 'FSD-1 PHA Lab', 'Lab'),
                ('DE(RHG)-311', 'Digital Electronics - RHG', 'Theory'),
                ('DE(RHG)-302', 'Digital Electronics - RHG', 'Theory'), 
                ('DE(SSD)-301', 'Digital Electronics - SSD', 'Theory'),
                ('DE(SSD)-309-C', 'Digital Electronics - SSD', 'Theory'), # Using this one for Div C
                ('FCSP-1(KMS)-406-7/Lab', 'FCSP-1 KMS Lab', 'Lab')
            ]
            
            subject_map = {} # Code -> ID
            
            for code, name, type_ in subjects_data:
                # Check duplicate code existence (SQL has duplicates in the list but unique constraint on db)
                if not Subject.query.filter_by(subject_code=code).first():
                    s = Subject(
                        course_id=cse_course.id,
                        subject_code=code,
                        subject_name=name,
                        semester=3,
                        credits=4,
                        subject_type=type_
                    )
                    db.session.add(s)
                    db.session.flush()
                    subject_map[code] = s.id

            db.session.commit()

            # 3. Timetable (Monday - Semester 3)
            # Mapped to Division C where appropriate, or just generic 3
            
            # Slot Map
            # A1: 08:45-09:45
            # A2: 09:45-10:45
            # A3: 11:30-12:30
            # A4: 12:30-13:30
            # A6: 08:45-09:45 (Alternative batch/division) -> We will insert these as Division C for visibility
            # A7: 09:45-10:45
            # A8: 11:30-12:30 
            # A9: 12:30-13:30
            
            # I will select a cohesive set of subjects for Division C from the SQL data
            # Based on the "DE(SSD)-309-C" hint, I will follow the SSD/RHG/etc usage for C if possible.
            # actually, just inserting the User's exact INSERT sequence associated with "C" or similar.
            # The SQL INSERT has:
            # A1: PS(MCV)-301
            # A2: FCSP-1(MVP)-406-7/Lab
            # A3: FSD-1(SPP)-410-B/Lab
            # A4: PS(PSK)-302
            # A6: DE(RHG)-311
            # A7: FSD-1(PHA)-406-6/Lab
            # A8: DE(SSD)-301 
            # A9: DE(RHG)-310
            
            # Since the student is C1, I will assign the ones that look like "C" or Labs to them.
            # But to be safe and show data, I will assign the PRIMARY list (1-4) to Division C.
            # And I'll add the "DE(SSD)" one as well.
            
            timetable_entries = [
                # Monday
                ('monday', '08:45-09:45', 'PS(MCV)-301', '301', 'MCV', 'Theory'),
                ('monday', '09:45-10:45', 'FCSP-1(MVP)-406-7/Lab', '406-7', 'MVP', 'Lab'),
                ('monday', '11:30-12:30', 'FSD-1(SPP)-410-B/Lab', '410-B', 'SPP', 'Lab'),
                ('monday', '12:30-13:30', 'PS(PSK)-302', '302', 'PSK', 'Theory'),
                
                # Adding the "C" specific one explicitly
                ('monday', '08:45-09:45', 'DE(SSD)-309-C', '309-C', 'SSD', 'Theory') # Conflict with 8:45 slot? Grid handles it or shows both.
            ]
            
            for day, time, subj_code, room, fac_code, type_ in timetable_entries:
                # Lookups
                s_id = subject_map.get(subj_code)
                f_id = faculty_map.get(fac_code)
                
                # If valid
                if s_id and f_id:
                     t = Timetable(
                        course_id=cse_course.id,
                        semester=3,
                        division='C', # Assign to C
                        batch='C1',   # Assign to C1
                        day_of_week=day,
                        time_slot=time,
                        subject_id=s_id,
                        faculty_id=f_id,
                        room_number=room,
                        academic_year='2025-26'
                     )
                     db.session.add(t)

            # Scholarships (Re-add)
            scholarships_data = [
                 Scholarship(name='MYSY', description='Merit Scholarship', category='merit', eligibility_criteria='80%+', amount=50000.0, deadline=datetime(2025, 12, 31).date(), official_website='https://mysy.guj.nic.in/'),
                 Scholarship(name='Digital Gujarat', description='Post Matric', category='minority', eligibility_criteria='SEBC/SC/ST', amount=20000.0, deadline=datetime(2025, 11, 30).date(), official_website='https://www.digitalgujarat.gov.in/')
            ]
            for s in scholarships_data:
                db.session.add(s)

            db.session.commit()
            print("SQL Migration Complete using Semester 3 Data.")

if __name__ == '__main__':
    if not os.path.exists('eduportal.db'):
        init_db()
    else:
        init_db() 
        
    app.run(debug=True, port=5001)
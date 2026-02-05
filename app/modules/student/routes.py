from flask import render_template, send_file, Response
from flask_login import login_required, current_user
import io
from datetime import datetime
from . import student_bp
from app.models import StudentProfile, Attendance, Subject, Timetable, StudentResult, ExamPaper, ExamEvent, UniversityEvent, EventRegistration, Notice, FeeRecord, StudentQuery, QueryMessage, FacultyProfile, Syllabus
from app.extensions import db
from flask import render_template, request, redirect, url_for, flash, jsonify

@student_bp.route('/dashboard')
@login_required
def dashboard():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # 1. Attendance Stats
    attendance_pct = student.get_overall_attendance()
    
    # 2. Recent Notices
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(4).all()
    
    # 3. Upcoming Event
    from datetime import date
    next_event = UniversityEvent.query.filter(
        UniversityEvent.date >= date.today()
    ).order_by(UniversityEvent.date).first()
    
    # 4. Pending Fee Count
    pending_fees = FeeRecord.query.filter_by(student_id=student.id, status='Pending').count()

    # 5. Calculate Latest SGPA (SPI)
    # Fetch results for current semester (or latest available)
    results = StudentResult.query.filter_by(student_id=student.id).all()
    
    total_credits = 0
    total_points = 0
    
    # Filter for results belonging to the latest exam event
    if results:
        # Group by event to find latest
        events = {}
        for res in results:
            eid = res.paper.exam_event_id
            if eid not in events: events[eid] = []
            events[eid].append(res)
            
        # Sort events by date (desc)
        sorted_events = sorted(events.keys(), key=lambda eid: events[eid][0].paper.exam_event.start_date, reverse=True)
        latest_eid = sorted_events[0]
        latest_results = events[latest_eid]
        
        for res in latest_results:
            marks = res.marks_obtained or 0
            points = 0
            if marks >= 90: points = 10
            elif marks >= 80: points = 9
            elif marks >= 70: points = 8
            elif marks >= 60: points = 7
            elif marks >= 50: points = 6
            elif marks >= 40: points = 5
            else: points = 0
            
            credits = res.paper.subject.weekly_lectures or 3
            total_points += (points * credits)
            total_credits += credits

    latest_spi = round(total_points / total_credits, 2) if total_credits > 0 else 0.0

    return render_template('student_dashboard.html', 
                           student=student, 
                           attendance_pct=attendance_pct, 
                           notices=notices, 
                           next_event=next_event, 
                           pending_fees=pending_fees,
                           latest_spi=latest_spi)

# Placeholder Routes for Sidebar Navigation
@student_bp.route('/attendance')
@login_required
def attendance():
    from app.models import Attendance, Subject, Timetable, StudentProfile
    from sqlalchemy import func
    import math

    # 1. Get Student Context
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # 2. Get Overall Attendance (Daily)
    # Using standardized model method
    overall_percent = student.get_overall_attendance()
    overall_status = "Excellent" if overall_percent >= 85 else "Good" if overall_percent >= 75 else "Critical"

    # 3. Derive Subject-Wise Data via Timetable Heuristic
    # Logic: If present on Monday, present for all Monday subjects.
    subjects = Subject.query.filter_by(course_name=student.course_name, semester=student.semester).all()
    timetable = Timetable.query.filter_by(course_name=student.course_name, semester=student.semester).all()
    
    # Map: DayName (0=Mon) -> [Subject_IDs]
    day_map = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    weekdays_str_map = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
    
    for slot in timetable:
        d_idx = weekdays_str_map.get(slot.day_of_week)
        if d_idx is not None:
             day_map[d_idx].append(slot.subject_id)

    # Initialize Stats Container
    subject_stats = {} # {id: {name, total, present}}
    for sub in subjects:
        subject_stats[sub.id] = {'name': sub.name, 'total': 0, 'present': 0}

    # Iterate Attendance History
    records = Attendance.query.filter_by(student_id=student.id).all()
    
    for record in records:
        # Direct Subject Match (Preferred)
        if record.subject_id:
            if record.subject_id in subject_stats:
                subject_stats[record.subject_id]['total'] += 1
                if record.status == 'Present':
                    subject_stats[record.subject_id]['present'] += 1
        else:
            # Fallback for Legacy Data (Day-based Heuristic)
            day_idx = record.date.weekday() # 0=Mon
            relevant_subjects = day_map.get(day_idx, [])
            
            for sub_id in relevant_subjects:
                if sub_id in subject_stats:
                    subject_stats[sub_id]['total'] += 1
                    if record.status == 'Present':
                        subject_stats[sub_id]['present'] += 1

    # 4. Final Calculations (Percent + Recovery)
    processed_subjects = []
    for sub_id, data in subject_stats.items():
        total = data['total']
        present = data['present']
        pct = (present / total * 100) if total > 0 else 0
        
        # Remark
        remark = "Excellent"
        color = "green"
        if pct < 75:
            remark = "Warning"
            color = "amber"
        if pct < 60:
            remark = "Critical"
            color = "red"

        # Recovery Logic: How many consecutive presents needed to hit 75%?
        # Eq: (Present + X) / (Total + X) = 0.75
        # Present + X = 0.75*Total + 0.75*X
        # 0.25*X = 0.75*Total - Present
        # X = (0.75*Total - Present) / 0.25
        recovery_needed = 0
        if pct < 75:
            target = 0.75
            x = (target * total - present) / (1 - target)
            recovery_needed = math.ceil(x) if x > 0 else 0

        processed_subjects.append({
            'name': data['name'],
            'total': total,
            'present': present,
            'percent': round(pct, 1),
            'remark': remark,
            'color': color,
            'recovery_needed': int(recovery_needed)
        })

    return render_template('student/attendance.html', 
                         overall_percent=round(overall_percent, 1),
                         overall_status=overall_status,
                         subjects=processed_subjects)

@student_bp.route('/academics')
@login_required
def academics():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Fetch all results
    results = StudentResult.query.filter_by(student_id=student.id).all()
    
    # Group by Exam Event
    exams_data = {}
    
    for res in results:
        exam_event = res.paper.exam_event
        if exam_event.id not in exams_data:
            exams_data[exam_event.id] = {
                'event': exam_event,
                'results': [],
                'total_credits': 0,
                'total_points': 0,
                'spi': 0.0
            }
        
        # Calculate Grade Points (Simple Logic for now)
        # >90: 10, >80: 9, >70: 8, >60: 7, >50: 6, >40: 5, <40: 0
        marks = res.marks_obtained or 0
        points = 0
        grade = 'F'
        if marks >= 90: points, grade = 10, 'AA'
        elif marks >= 80: points, grade = 9, 'AB'
        elif marks >= 70: points, grade = 8, 'BB'
        elif marks >= 60: points, grade = 7, 'BC'
        elif marks >= 50: points, grade = 6, 'CC'
        elif marks >= 40: points, grade = 5, 'CD'
        else: points, grade = 0, 'FF'
        
        # Assuming 3 credits per subject for simplicity if not defined
        credits = res.paper.subject.weekly_lectures or 3
        
        exams_data[exam_event.id]['results'].append({
            'subject': res.paper.subject.name,
            'marks': marks,
            'total': res.paper.total_marks,
            'grade': grade,
            'points': points,
            'credits': credits
        })
        
        exams_data[exam_event.id]['total_credits'] += credits
        exams_data[exam_event.id]['total_points'] += (points * credits)

    # Calculate SPI for each exam
    overall_points = 0
    overall_credits = 0
    
    events_list = []
    for eid, data in exams_data.items():
        if data['total_credits'] > 0:
            data['spi'] = round(data['total_points'] / data['total_credits'], 2)
        
        overall_points += data['total_points']
        overall_credits += data['total_credits']
        events_list.append(data)
        
    # Sort events by date descending (Latest First)
    events_list.sort(key=lambda x: x['event'].start_date, reverse=True)

    cgpi = round(overall_points / overall_credits, 2) if overall_credits > 0 else 0.0

    return render_template('student/academics.html', 
                           student=student, 
                           exams=events_list, 
                           cgpi=cgpi)

@student_bp.route('/academics/marksheet/<int:exam_id>')
@login_required
def download_marksheet(exam_id):
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    results = StudentResult.query.filter_by(student_id=student.id).join(ExamPaper).filter(ExamPaper.exam_event_id == exam_id).all()
    
    if not results:
        return "Marksheet not found", 404
        
    exam_event = results[0].paper.exam_event
    
    processed_results = []
    total_credits = 0
    total_points = 0
    total_marks_obtained = 0
    total_max_marks = 0
    
    for res in results:
        marks = res.marks_obtained or 0
        points = 0
        grade = 'F'
        if marks >= 90: points, grade = 10, 'AA'
        elif marks >= 80: points, grade = 9, 'AB'
        elif marks >= 70: points, grade = 8, 'BB'
        elif marks >= 60: points, grade = 7, 'BC'
        elif marks >= 50: points, grade = 6, 'CC'
        elif marks >= 40: points, grade = 5, 'CD'
        else: points, grade = 0, 'FF'
        
        # Assuming credits based on weekly lectures
        credits = res.paper.subject.weekly_lectures or 3
        
        processed_results.append({
            'code': f"SUB{res.paper.subject.id}",
            'subject': res.paper.subject.name,
            'marks': marks,
            'max_marks': res.paper.total_marks,
            'grade': grade,
            'points': points,
            'credits': credits
        })
        
        total_credits += credits
        total_points += (points * credits)
        total_marks_obtained += marks
        total_max_marks += res.paper.total_marks

    spi = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    
    return render_template('student/marksheet_print.html',
                           student=student,
                           exam=exam_event,
                           results=processed_results,
                           spi=spi,
                           total_marks_obtained=total_marks_obtained,
                           total_max_marks=total_max_marks)

@student_bp.route('/notes')
@login_required
def notes():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Fetch subjects for the student's current semester with syllabus pre-loaded
    from sqlalchemy.orm import joinedload
    subjects = Subject.query.options(joinedload(Subject.syllabus)).filter_by(
        course_name=student.course_name,
        semester=student.semester
    ).all()
    
    return render_template('student/notes.html', student=student, subjects=subjects)

@student_bp.route('/syllabus/<int:subject_id>')
@login_required
def download_syllabus(subject_id):
    # Security: Ensure student is enrolled in this subject's course/sem
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    syllabus = Syllabus.query.filter_by(subject_id=subject_id).first_or_404()
    
    # Check if subject matches student's academic path
    if syllabus.subject.course_name != student.course_name or syllabus.subject.semester != student.semester:
        flash('Unauthorized syllabus access.', 'error')
        return redirect(url_for('student.notes'))

    return send_file(
        io.BytesIO(syllabus.file_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=syllabus.filename
    )

@student_bp.route('/events')
@login_required
def events():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Fetch upcoming events
    events_list = UniversityEvent.query.filter_by(is_upcoming=True).order_by(UniversityEvent.date).all()
    
    # Check registrations
    registrations = EventRegistration.query.filter_by(student_id=student.id).all()
    registered_ids = {r.event_id for r in registrations}
    
    return render_template('student/events.html', student=student, events=events_list, registered_ids=registered_ids)

@student_bp.route('/events/image/<int:event_id>')
def event_image(event_id):
    event = UniversityEvent.query.get_or_404(event_id)
    if event.image_data:
        return send_file(
            io.BytesIO(event.image_data),
            mimetype=event.image_mimetype or 'image/png',
            as_attachment=False,
            download_name=f"event_{event.id}.png"
        )
    return '', 404

@student_bp.route('/events/register/<int:event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Check if existing
    existing = EventRegistration.query.filter_by(student_id=student.id, event_id=event_id).first()
    if existing:
        return {'status': 'already_registered'}, 200
        
    new_reg = EventRegistration(student_id=student.id, event_id=event_id)
    db.session.add(new_reg)
    db.session.commit()
    
    return {'status': 'success', 'message': 'Registered successfully'}, 200

@student_bp.route('/notices')
@login_required
def notices():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Fetch all notices, ordered by latest first
    all_notices = Notice.query.order_by(Notice.created_at.desc()).all()
    
    return render_template('student/notices.html', student=student, notices=all_notices)

@student_bp.route('/fees')
@login_required
def fees():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    records = FeeRecord.query.filter_by(student_id=student.id).order_by(FeeRecord.due_date.desc()).all()
    
    pending_fees = [r for r in records if r.status == 'Pending' or r.status == 'Overdue']
    history_fees = [r for r in records if r.status == 'Paid']
    
    return render_template('student/fees.html', student=student, pending_fees=pending_fees, history_fees=history_fees)

@student_bp.route('/fees/pay/<int:fee_id>', methods=['POST'])
@login_required
def pay_fee(fee_id):
    fee = FeeRecord.query.get_or_404(fee_id)
    if fee.status == 'Paid':
        return {'status': 'already_paid'}, 200
    
    # Simulate Payment
    fee.status = 'Paid'
    fee.payment_date = datetime.utcnow()
    fee.payment_mode = 'Online'
    fee.amount_paid = fee.amount_due
    fee.transaction_reference = f"TXN{int(datetime.utcnow().timestamp())}{fee.id}"
    
    db.session.commit()
    return {'status': 'success', 'message': 'Payment successful!'}, 200

@student_bp.route('/fees/receipt/<int:fee_id>')
@login_required
def fee_receipt(fee_id):
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    fee = FeeRecord.query.get_or_404(fee_id)
    
    if fee.status != 'Paid':
        return "Receipt not available for pending fees.", 403
        
    return render_template('student/receipt.html', student=student, fee=fee)

@student_bp.route('/queries')
@login_required
def queries():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    status_filter = request.args.get('status', 'all')
    
    query = StudentQuery.query.filter_by(student_id=student.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter.capitalize())
        
    queries = query.order_by(StudentQuery.updated_at.desc()).all()
    
    # Pre-fetch subjects and faculty for the "Ask Query" modal
    subjects = Subject.query.filter_by(course_name=student.course_name, semester=student.semester).all()
    
    return render_template('student/queries.html', student=student, queries=queries, filter=status_filter, subjects=subjects)

@student_bp.route('/queries/create', methods=['POST'])
@login_required
def create_query():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    subject_id = request.form.get('subject_id')
    title = request.form.get('title')
    content = request.form.get('content')
    
    # Resolve Faculty from Subject
    subject = Subject.query.get(subject_id)
    if not subject or not subject.faculty_id:
        flash('Invalid Subject or No Faculty assigned.', 'error')
        return redirect(url_for('student.queries'))

    # Create Query
    new_query = StudentQuery(
        student_id=student.id,
        faculty_id=subject.faculty_id,
        subject_id=subject.id,
        title=title,
        status='Pending'
    )
    db.session.add(new_query)
    db.session.flush()
    
    # Add Initial Message
    initial_msg = QueryMessage(
        query_id=new_query.id,
        sender_type='student',
        content=content
    )
    
    # Handle Image Upload (Optional)
    image = request.files.get('image')
    if image and image.filename:
        image.stream.seek(0)
        file_data = image.read()
        if len(file_data) > 0:
            print(f"DEBUG: Creating Query Image. Name: {image.filename}, Size: {len(file_data)} bytes")
            initial_msg.image_data = file_data
            initial_msg.image_mimetype = image.mimetype
        else:
            print("DEBUG: Image file is empty")
        
    db.session.add(initial_msg)
    db.session.commit()
    
    return redirect(url_for('student.query_chat', query_id=new_query.id))

@student_bp.route('/queries/<int:query_id>')
@login_required
def query_chat(query_id):
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    query = StudentQuery.query.get_or_404(query_id)
    
    # Security Check
    if query.student_id != student.id:
        return "Unauthorized", 403
        
    return render_template('student/query_chat.html', student=student, query=query)

@student_bp.route('/queries/<int:query_id>/message', methods=['POST'])
@login_required
def send_message(query_id):
    query = StudentQuery.query.get_or_404(query_id)
    
    # Prevent chatting if resolved
    if query.status == 'Resolved':
        flash('This query is resolved and cannot be reopened.', 'error')
        return redirect(url_for('student.query_chat', query_id=query_id))
        
    content = request.form.get('content')
    
    new_msg = QueryMessage(
        query_id=query.id,
        sender_type='student',
        content=content
    )
    
    image = request.files.get('image')
    if image and image.filename:
        image.stream.seek(0)
        file_data = image.read()
        if len(file_data) > 0:
            print(f"DEBUG: Receiving Image. Name: {image.filename}, Size: {len(file_data)} bytes, Type: {image.mimetype}")
            new_msg.image_data = file_data
            new_msg.image_mimetype = image.mimetype
        else:
             print("DEBUG: Image file is empty")
        
    db.session.add(new_msg)
    
    # Update Query Status to Pending if it was Answered
    if query.status == 'Answered':
        query.status = 'Pending'
    
    query.updated_at = datetime.utcnow()
    db.session.commit()
    
    return redirect(url_for('student.query_chat', query_id=query_id))

@student_bp.route('/queries/<int:query_id>/resolve', methods=['POST'])
@login_required
def resolve_query(query_id):
    query = StudentQuery.query.get_or_404(query_id)
    query.status = 'Resolved'
    db.session.commit()
    return redirect(url_for('student.query_chat', query_id=query_id))

@student_bp.route('/queries/image/<int:message_id>')
@login_required
def message_image(message_id):
    msg = QueryMessage.query.get_or_404(message_id)
    if not msg.image_data:
        print(f"DEBUG: No image data for message {message_id}")
        return "No image", 404
    
    # Simple serve without download_name to avoid forcing download/icon behavior
    return send_file(
        io.BytesIO(msg.image_data),
        mimetype=msg.image_mimetype or 'image/jpeg'
    )

@student_bp.route('/exams')
@login_required
def exams():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # 1. Upcoming Exams (Schedule)
    # Fetch active exam events for student's course/semester
    upcoming_events = ExamEvent.query.filter_by(
        course_name=student.course_name,
        semester=student.semester,
        is_published=True
    ).order_by(ExamEvent.start_date).all()
    
    # 2. Past Results
    # Fetch results grouped by Exam Event
    # We join Result -> Paper -> Event
    results = StudentResult.query.filter_by(student_id=student.id).all()
    
    # Group results by Exam Event
    history = {}
    for res in results:
        event = res.paper.exam_event
        if event not in history:
            history[event] = {'total_marks': 0, 'obtained_marks': 0, 'papers': []}
        
        history[event]['papers'].append(res)
        history[event]['total_marks'] += res.paper.total_marks
        history[event]['obtained_marks'] += (res.marks_obtained or 0)
        
    return render_template('student/exams.html', student=student, upcoming_events=upcoming_events, result_history=history)

@student_bp.route('/id-card')
@login_required
def id_card():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    return render_template('student/id_card.html', student=student)

@student_bp.route('/id-card/report-lost', methods=['POST'])
@login_required
def report_lost_card():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    student.id_card_status = 'Lost'
    db.session.commit()
    
    flash('ID Card reported as lost. Please contact administration for a replacement.', 'warning')
    return redirect(url_for('student.id_card'))





@student_bp.route('/timetable')
@login_required
def timetable():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Fetch Timetable entries
    entries = Timetable.query.filter_by(
        course_name=student.course_name,
        semester=student.semester
    ).order_by(Timetable.period_number).all()
    
    # Structure Data: Days -> Slots
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    schedule = {day: [] for day in days_order}

    # Fetch Schedule Settings (Fall back if missing)
    # Assumes one setting per course/semester
    from app.models import ScheduleSettings
    settings = ScheduleSettings.query.filter_by(
        course_name=student.course_name, 
        semester=student.semester
    ).first()
    
    # Default: Start 09:00 AM, 1 hour duration if no settings
    base_start_hour = 9
    base_start_min = 0
    slot_duration_min = 60 

    if settings:
        base_start_hour = settings.start_time.hour
        base_start_min = settings.start_time.minute
        # Simplified: derive duration from total time / slots (heuristic)
        # For now, let's stick to fixed 60 mins or implement better logic if needed
    
    from datetime import timedelta, datetime, date
    
    for entry in entries:
        if entry.day_of_week in schedule:
            p_idx = entry.period_number - 1 # Period is usually 1-indexed
            
            if settings:
                s_time, e_time = settings.get_period_times(entry.period_number)
                entry.start_time = s_time
                entry.end_time = e_time
            else:
                start_minutes = (base_start_hour * 60) + base_start_min + (p_idx * slot_duration_min)
                start_dt = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=start_minutes)
                end_dt = start_dt + timedelta(minutes=slot_duration_min)
                entry.start_time = start_dt.time()
                entry.end_time = end_dt.time()
            # Fake room number if missing
            entry.room_number = "Main Block" 
            
            schedule[entry.day_of_week].append(entry)
            
    # Remove Sunday if empty
    if not schedule['Sun']:
        del schedule['Sun']
        
    # Sort slots within days by period_number
    for day in schedule:
        schedule[day].sort(key=lambda x: x.period_number)
            
    return render_template('student/timetable.html', student=student, schedule=schedule)

@student_bp.route('/scholarship', methods=['GET', 'POST'])
@login_required
def scholarship():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    results = []
    searched = False
    
    # Mock Scholarship Database (Real-world examples)
    SCHOLARSHIP_DB = [
        {
            'name': 'National Scholarship Portal (NSP) - Central Sector Scheme',
            'provider': 'Govt of India',
            'amount': '₹10,000 - ₹20,000 / year',
            'url': 'https://scholarships.gov.in/',
            'max_income': 800000,
            'categories': ['General', 'OBC', 'SC', 'ST'],
            'genders': ['Male', 'Female', 'Other']
        },
        {
            'name': 'Post Matric Scholarship for SC Students',
            'provider': 'State Governments',
            'amount': 'Full Tuition Fee + Allowance',
            'url': 'https://socialjustice.gov.in/schemes',
            'max_income': 250000,
            'categories': ['SC'],
            'genders': ['Male', 'Female', 'Other']
        },
        {
            'name': 'HDFC Badhte Kadam Scholarship',
            'provider': 'HDFC Bank',
            'amount': 'Up to ₹1,00,000',
            'url': 'https://www.hdfcbank.com/personal/borrow/popular-loans/educational-loan/scholarship',
            'max_income': 600000,
            'categories': ['General', 'OBC', 'SC', 'ST'],
            'genders': ['Male', 'Female', 'Other']
        },
        {
            'name': 'AICTE Pragati Scholarship for Girls',
            'provider': 'AICTE',
            'amount': '₹50,000 / year',
            'url': 'https://www.aicte-india.org/schemes/students-schemes',
            'max_income': 800000,
            'categories': ['General', 'OBC', 'SC', 'ST'],
            'genders': ['Female']
        },
        {
            'name': 'Reliance Foundation Undergraduate Scholarship',
            'provider': 'Reliance Foundation',
            'amount': 'Up to ₹2,00,000',
            'url': 'https://www.reliancefoundation.org/',
            'max_income': 1500000,
            'categories': ['General', 'OBC', 'SC', 'ST'],
            'genders': ['Male', 'Female', 'Other']
        },
        {
            'name': 'ONGC Scholarship for OBC/SC/ST',
            'provider': 'ONGC',
            'amount': '₹48,000 / year',
            'url': 'https://ongcscholar.org/',
            'max_income': 450000,
            'categories': ['OBC', 'SC', 'ST'],
            'genders': ['Male', 'Female', 'Other']
        }
    ]

    if request.method == 'POST':
        searched = True
        income = float(request.form.get('income', 0))
        category = request.form.get('category')
        gender = request.form.get('gender')
        
        # Filtering Logic
        for sch in SCHOLARSHIP_DB:
            # Check Income
            if income > sch['max_income']:
                continue
                
            # Check Category
            if category not in sch['categories']:
                continue
                
            # Check Gender
            if gender not in sch['genders']:
                continue
                
            results.append(sch)
            
    return render_template('student/scholarship.html', student=student, results=results, searched=searched)

from werkzeug.security import generate_password_hash, check_password_hash

@student_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    student = StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            try:
                student.phone_number = request.form.get('phone_number')
                student.address = request.form.get('address')
                student.guardian_name = request.form.get('guardian_name')
                student.guardian_contact = request.form.get('guardian_contact')
                
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating profile.', 'error')
                
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Incorrect current password.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
            else:
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Password changed successfully!', 'success')
                
        return redirect(url_for('student.settings'))
            
    return render_template('student/settings.html', student=student)

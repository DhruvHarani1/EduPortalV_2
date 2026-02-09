from flask import render_template, request
from flask_login import login_required
from datetime import datetime, date, timedelta, timezone
from app.models import FeeRecord, StudentQuery, QueryMessage, FacultyProfile, Attendance, Timetable
from flask_login import current_user, login_required
from flask import render_template, request, redirect, url_for, flash, send_file
import io
from app.extensions import db
from . import faculty_bp

@faculty_bp.route('/dashboard')
@login_required
def dashboard():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # 1. Stats
    mentees_count = StudentProfile.query.filter_by(mentor_id=faculty.id).count()
    pending_queries = StudentQuery.query.filter_by(faculty_id=faculty.id, status='Pending').count()
    
    # 2. Today's Schedule & Attendance Check
    today_name = datetime.now().strftime('%A') # e.g. "Monday"
    todays_classes = Timetable.query.filter_by(faculty_id=faculty.id, day_of_week=today_name).order_by(Timetable.period_number).all()
    
    total_pending_attendance = 0
    today_date = date.today()
    
    for entry in todays_classes:
        # Time calc
        from app.models import ScheduleSettings
        settings = ScheduleSettings.query.filter_by(course_name=entry.course_name, semester=entry.semester).first()
        if settings:
            s_time, e_time = settings.get_period_times(entry.period_number)
            entry.display_time = f"{s_time.strftime('%I:%M %p')} - {e_time.strftime('%I:%M %p')}"
        else:
            base_start_hour = 9
            start_minutes = (base_start_hour * 60) + ((entry.period_number - 1) * 60)
            start_time = datetime.combine(today_date, datetime.min.time()) + timedelta(minutes=start_minutes)
            end_time = start_time + timedelta(minutes=60)
            entry.display_time = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
        
        # Check Attendance for this Subject + Date
        # If count > 0, assumed marked
        marked_count = Attendance.query.filter_by(
            subject_id=entry.subject_id, 
            date=today_date
        ).count()
        
        if marked_count > 0:
            entry.attendance_marked = True
        else:
            entry.attendance_marked = False
            total_pending_attendance += 1
            
    # 3. Recent Notices (Inbox + Sent)
    recent_notices = Notice.query.filter(
        (Notice.target_type == 'all') | 
        ((Notice.target_type == 'faculty') & ((Notice.target_faculty_id == None) | (Notice.target_faculty_id == faculty.id))) |
        (Notice.sender_faculty_id == faculty.id)
    ).order_by(Notice.created_at.desc()).limit(5).all()

    return render_template('faculty_dashboard.html', 
                           faculty=faculty,
                           mentees_count=mentees_count,
                           pending_queries=pending_queries,
                           todays_classes=todays_classes,
                           total_pending_attendance=total_pending_attendance,
                           recent_notices=recent_notices,
                           today_date=datetime.now())

@faculty_bp.route('/fees')
@login_required
def fees():
    # Fetch all fee records (In a real app, filter by faculty's students)
    records = FeeRecord.query.order_by(FeeRecord.due_date.desc()).all()
    return render_template('faculty/fees.html', records=records)

@faculty_bp.route('/fees/mark_paid/<int:fee_id>', methods=['POST'])
@login_required
def mark_paid(fee_id):
    fee = FeeRecord.query.get_or_404(fee_id)
    fee.status = 'Paid'
    fee.payment_date = datetime.now(timezone.utc)
    fee.payment_mode = 'Cash/Office'
    fee.transaction_reference = f"OFFICE-MANUAL-{fee.id}-{int(datetime.now(timezone.utc).timestamp())}"
    db.session.commit()
    return {'status': 'success'}

@faculty_bp.route('/queries')
@login_required
def queries():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Check for filters
    status = request.args.get('status', 'all')
    
    query = StudentQuery.query.filter_by(faculty_id=faculty.id)
    if status != 'all':
        query = query.filter_by(status=status.capitalize())
        
    queries = query.order_by(StudentQuery.updated_at.desc()).all()
    
    return render_template('faculty/queries.html', queries=queries, filter=status)

@faculty_bp.route('/queries/<int:query_id>', methods=['GET', 'POST'])
@login_required
def query_chat(query_id):
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    query = StudentQuery.query.get_or_404(query_id)
    
    if query.faculty_id != faculty.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        content = request.form.get('content')
        image_file = request.files.get('image')
        
        if content or image_file:
            msg = QueryMessage(
                query_id=query.id,
                sender_type='faculty',
                content=content
            )
            
            if image_file and image_file.filename != '':
                msg.image_data = image_file.read()
                msg.image_mimetype = image_file.mimetype
                
            db.session.add(msg)
            
            # Update status to Answered
            if query.status == 'Pending':
                 query.status = 'Answered'
            
            query.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for('faculty.query_chat', query_id=query_id))

    return render_template('faculty/query_chat.html', query=query)

# --- New Faculty Routes Placeholders ---

from app.models import FeeRecord, StudentQuery, QueryMessage, FacultyProfile, Subject, Syllabus, StudentProfile, Timetable, Attendance, ExamEvent, ExamPaper, StudentResult
from werkzeug.utils import secure_filename

# ... (existing imports)

@faculty_bp.route('/classes', methods=['GET', 'POST'])
@login_required
def classes():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        if 'syllabus_file' in request.files:
            file = request.files['syllabus_file']
            subject_id = request.form.get('subject_id')
            
            if file and file.filename != '' and subject_id:
                filename = secure_filename(file.filename)
                # Ensure only PDF
                if not filename.lower().endswith('.pdf'):
                    flash('Only PDF files are allowed.', 'error')
                else:
                    file_data = file.read()
                    
                    # check if exists
                    existing = Syllabus.query.filter_by(subject_id=subject_id).first()
                    if existing:
                        existing.filename = filename
                        existing.file_data = file_data
                        existing.upload_date = datetime.now(timezone.utc)
                    else:
                        new_syllabus = Syllabus(subject_id=subject_id, filename=filename, file_data=file_data)
                        db.session.add(new_syllabus)
                    
                    db.session.commit()
                    flash('Syllabus uploaded successfully!', 'success')
            else:
                flash('No file selected.', 'error')
        
        elif 'search_enrollment' in request.form:
             enrollment_id = request.form.get('search_enrollment').strip()
             student = StudentProfile.query.filter_by(enrollment_number=enrollment_id).first()
             if student:
                 return redirect(url_for('faculty.student_detail', student_id=student.id))
             else:
                 flash('Student not found with that Enrollment ID.', 'error')
                 
        return redirect(url_for('faculty.classes'))

    # Fetch Subjects
    subjects = Subject.query.filter_by(faculty_id=faculty.id).all()
    
    # Enrich with student count
    subject_data = []
    for sub in subjects:
        # Count students in this course & semester
        student_count = StudentProfile.query.filter_by(
            course_name=sub.course_name,
            semester=sub.semester
        ).count()
        
        # Count actual scheduled lectures from Timetable
        lecture_count = Timetable.query.filter_by(subject_id=sub.id).count()
        
        subject_data.append({
            'subject': sub,
            'student_count': student_count,
            'lecture_count': lecture_count,
            'is_elective': False # Placeholder for future logic
        })

    return render_template('faculty/classes.html', subject_data=subject_data)

@faculty_bp.route('/student/<int:student_id>')
@login_required
def student_detail(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    return render_template('faculty/student_detail.html', student=student)

@faculty_bp.route('/classes/syllabus/<int:subject_id>')
@login_required
def download_syllabus(subject_id):
    syllabus = Syllabus.query.filter_by(subject_id=subject_id).first_or_404()
    from flask import send_file
    import io
    return send_file(
        io.BytesIO(syllabus.file_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=syllabus.filename
    )

@faculty_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    subjects = Subject.query.filter_by(faculty_id=faculty.id).all()
    
    # --- 1. HANDLE ATTENDANCE SUBMISSION (POST) ---
    if request.method == 'POST':
        subj_id = request.form.get('subject_id')
        date_val = request.form.get('date')
        target_subject = Subject.query.get_or_404(subj_id)
        
        for key in request.form:
            if key.startswith('status_'):
                student_id = int(key.split('_')[1])
                status = request.form[key]
                
                # Update or Create record
                att = Attendance.query.filter_by(
                    student_id=student_id,
                    subject_id=subj_id,
                    date=datetime.strptime(date_val, '%Y-%m-%d').date()
                ).first()
                
                if att:
                    att.status = status
                else:
                    new_att = Attendance(
                        student_id=student_id,
                        course_name=target_subject.course_name,
                        date=datetime.strptime(date_val, '%Y-%m-%d').date(),
                        status=status,
                        subject_id=subj_id,
                        faculty_id=faculty.id
                    )
                    db.session.add(new_att)
        
        db.session.commit()
        flash('Attendance updated successfully!', 'success')
        # Return to the SAME marking view after saving
        return redirect(url_for('faculty.attendance', mode='mark', subject_id=subj_id, date=date_val))

    # --- 2. GET PARAMETERS ---
    mode = request.args.get('mode') # 'mark' or None
    selected_subject_id = request.args.get('subject_id', type=int)
    selected_date_str = request.args.get('date')
    page = request.args.get('page', 1, type=int)

    # Initialize variables
    attendance_data = []
    stats = {'present': 0, 'absent': 0, 'total': 0, 'percentage': 0}
    selected_subject = None
    lecture_history = []
    pagination = {}
    marking_mode = False
    low_attendance_list = []

    # --- 3. LOGIC BRANCHING ---

    # A. MARKING MODE (Requires explicit mode='mark')
    if mode == 'mark' and selected_subject_id and selected_date_str:
        marking_mode = True
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            selected_subject = Subject.query.get_or_404(selected_subject_id)
            
            # Fetch Students for this subject's class (course/semester)
            students = StudentProfile.query.filter_by(
                course_name=selected_subject.course_name,
                semester=selected_subject.semester
            ).order_by(StudentProfile.enrollment_number).all()
            
            # Fetch Existing Attendance
            existing_records = Attendance.query.filter_by(
                subject_id=selected_subject_id,
                date=selected_date
            ).all()
            
            status_map = {att.student_id: att.status for att in existing_records}
            
            for student in students:
                current_status = status_map.get(student.id, 'Present') 
                attendance_data.append({'student': student, 'status': current_status})
                if current_status == 'Present': stats['present'] += 1
                else: stats['absent'] += 1
                    
            stats['total'] = len(students)
            if stats['total'] > 0:
                stats['percentage'] = round((stats['present'] / stats['total']) * 100, 1)

            # Low Attendance Calculation
            all_subject_attendance = Attendance.query.filter_by(subject_id=selected_subject_id).all()
            student_stats = {} # {id: {total: 0, present: 0}}
            for rec in all_subject_attendance:
                if rec.student_id not in student_stats: student_stats[rec.student_id] = {'total': 0, 'present': 0}
                student_stats[rec.student_id]['total'] += 1
                if rec.status == 'Present': student_stats[rec.student_id]['present'] += 1
            
            for student in students:
                s_stat = student_stats.get(student.id, {'total': 0, 'present': 0})
                pct = (s_stat['present'] / s_stat['total'] * 100) if s_stat['total'] > 0 else 100.0
                if pct < 75:
                    low_attendance_list.append({
                        'student': student,
                        'percentage': round(pct, 1),
                        'attended': s_stat['present'],
                        'total': s_stat['total']
                    })
        except ValueError:
            flash('Invalid date provided for marking.', 'error')
            marking_mode = False

    # B. DASHBOARD MODE (Default or if marking mode fails)
    if not marking_mode:
        all_lectures = []
        
        # Build Timetable Cache
        timetable_map = {} # {DayName: [Slots]}
        slots_query = Timetable.query.filter_by(faculty_id=faculty.id)
        if selected_subject_id:
            slots_query = slots_query.filter_by(subject_id=selected_subject_id)
            selected_subject = Subject.query.get(selected_subject_id)
        
        faculty_slots = slots_query.all()
        for slot in faculty_slots:
            if slot.day_of_week not in timetable_map: timetable_map[slot.day_of_week] = []
            timetable_map[slot.day_of_week].append(slot)

        # Determine Date Range to display
        if selected_date_str:
            try:
                date_range = [datetime.strptime(selected_date_str, '%Y-%m-%d').date()]
            except ValueError:
                flash('Invalid date. Showing recent history instead.', 'error')
                date_range = [date.today() - timedelta(days=i) for i in range(30)]
        else:
            date_range = [date.today() - timedelta(days=i) for i in range(30)]

        # Find lectures for the date range
        for curr_date in date_range:
            day_name = curr_date.strftime('%A')
            if day_name in timetable_map:
                for slot in timetable_map[day_name]:
                    marked_count = Attendance.query.filter_by(subject_id=slot.subject_id, date=curr_date).count()
                    all_lectures.append({
                        'date': curr_date,
                        'date_str': curr_date.strftime('%Y-%m-%d'),
                        'subject': slot.subject,
                        'time': f"{9 + (slot.period_number-1)}:00 - {10 + (slot.period_number-1)}:00",
                        'status': 'Marked' if marked_count > 0 else 'Pending'
                    })
        
        all_lectures.sort(key=lambda x: x['date'], reverse=True)

        # Pagination
        per_page = 5
        total_items = len(all_lectures)
        start = (page - 1) * per_page
        end = start + per_page
        lecture_history = all_lectures[start:end]
        pagination = {
            'page': page,
            'total_pages': (total_items + per_page - 1) // per_page,
            'has_next': end < total_items,
            'has_prev': start > 0
        }

    return render_template(
        'faculty/attendance.html',
        faculty=faculty,
        subjects=subjects,
        selected_subject=selected_subject,
        selected_date=selected_date_str,
        attendance_data=attendance_data,
        stats=stats,
        lecture_history=lecture_history,
        pagination=pagination,
        marking_mode=marking_mode,
        low_attendance_list=low_attendance_list
    )

    return render_template(
        'faculty/attendance.html', 
        lecture_history=lecture_history,
        pagination=pagination,
        subjects=subjects, 
        selected_subject=selected_subject,
        selected_date=selected_date_str, # Keep valid if selected
        attendance_data=attendance_data,
        stats=stats,
        pending_count=pending_count,
        low_attendance_list=locals().get('low_attendance_list', [])
    )

@faculty_bp.route('/attendance/export/csv')
@login_required
def export_attendance_csv():
    import csv
    import io
    from flask import make_response

    subject_id = request.args.get('subject_id')
    date_str = request.args.get('date')
    
    if not subject_id or not date_str:
        flash('Please select a subject and date to export.', 'error')
        return redirect(url_for('faculty.attendance'))
        
    subject = Subject.query.get_or_404(subject_id)
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Fetch Data (Reuse Logic or Refactor - Reusing for speed)
    existing_records = Attendance.query.filter_by(subject_id=subject_id, date=date_obj).all()
    record_map = {r.student_id: r.status for r in existing_records}
    
    students = StudentProfile.query.filter_by(
            course_name=subject.course_name,
            semester=subject.semester
        ).order_by(StudentProfile.enrollment_number).all()

    # Generate CSV
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Enrollment', 'Name', 'Status', 'Date', 'Subject', 'Course'])
    
    for stu in students:
        status = record_map.get(stu.id, 'Unmarked')
        cw.writerow([
            stu.enrollment_number, 
            stu.display_name, 
            status, 
            date_str, 
            subject.name, 
            f"{subject.course_name} Sem {subject.semester}"
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=attendance_{subject.name}_{date_str}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@faculty_bp.route('/attendance/print')
@login_required
def print_attendance_report():
    subject_id = request.args.get('subject_id')
    date_str = request.args.get('date')
    
    if not subject_id or not date_str:
        return "Missing arguments", 400
        
    subject = Subject.query.get_or_404(subject_id)
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    existing_records = Attendance.query.filter_by(subject_id=subject_id, date=date_obj).all()
    record_map = {r.student_id: r.status for r in existing_records}
    
    students = StudentProfile.query.filter_by(course_name=subject.course_name, semester=subject.semester).order_by(StudentProfile.enrollment_number).all()
    
    final_data = []
    stats = {'present': 0, 'absent': 0, 'total': 0}
    
    for stu in students:
        status = record_map.get(stu.id, 'Unmarked')
        final_data.append({'student': stu, 'status': status})
        if status == 'Present': stats['present'] += 1
        elif status == 'Absent': stats['absent'] += 1
    
    stats['total'] = len(students)
    
    return render_template(
        'faculty/attendance_print.html',
        subject=subject,
        date_str=date_str,
        data=final_data,
        stats=stats
    )

@faculty_bp.route('/material', methods=['GET', 'POST'])
@login_required
def material():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    subjects = Subject.query.filter_by(faculty_id=faculty.id).all()
    
    if request.method == 'POST':
        subj_id = request.form.get('subject_id')
        link_url = request.form.get('resource_link')
        
        subject = Subject.query.get_or_404(subj_id)
        
        # Security: Ensure ownership
        if subject.faculty_id != faculty.id:
            flash('Unauthorized action.', 'error')
            return redirect(url_for('faculty.material'))

        if link_url:
             # Basic validation
            if not link_url.startswith(('http://', 'https://')):
                link_url = 'https://' + link_url
            subject.resource_link = link_url
            db.session.commit()
            flash(f'Resource link updated for {subject.name}.', 'success')
        else:
            # Clear link? Or error? Letting them clear it if empty
            subject.resource_link = None
            db.session.commit()
            flash(f'Resource link removed for {subject.name}.', 'info')
            
        return redirect(url_for('faculty.material'))

    return render_template('faculty/material.html', subjects=subjects)

# Download route removed (Links are external)

# Delete route removed (Managed via update)

@faculty_bp.route('/marks', methods=['GET', 'POST'])
@login_required
def marks():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # 1. Fetch Active Exams
    # For now, fetching all. In real app, filter by date or 'is_active'
    exam_events = ExamEvent.query.order_by(ExamEvent.start_date.desc()).all()
    
    selected_exam_id = request.args.get('exam_id', type=int)
    selected_paper_id = request.args.get('paper_id', type=int)
    
    papers = []
    selected_exam = None
    selected_paper = None
    students_data = [] # List of {student, result_obj_or_none}
    
    # 2. If Exam Selected, Fetch Papers for this Faculty
    if selected_exam_id:
        selected_exam = ExamEvent.query.get_or_404(selected_exam_id)
        
        # Get subjects taught by faculty
        faculty_subject_ids = [s.id for s in faculty.subjects_taught]
        
        # Fetch papers for this exam AND taught by faculty
        papers = ExamPaper.query.filter(
            ExamPaper.exam_event_id == selected_exam_id,
            ExamPaper.subject_id.in_(faculty_subject_ids)
        ).all()
        
    # 3. If Paper Selected, Fetch Students and Results
    if selected_paper_id:
        selected_paper = ExamPaper.query.get_or_404(selected_paper_id)
        
        # Security: Ensure faculty teaches this subject
        if selected_paper.subject.faculty_id != faculty.id:
            flash('Unauthorized access to this paper.', 'error')
            return redirect(url_for('faculty.marks'))
            
        # Fetch Students (Course/Sem matches Paper's Subject)
        students = StudentProfile.query.filter_by(
            course_name=selected_paper.subject.course_name,
            semester=selected_paper.subject.semester
        ).order_by(StudentProfile.enrollment_number).all()
        
        # Fetch Existing Results
        existing_results = StudentResult.query.filter_by(exam_paper_id=selected_paper_id).all()
        result_map = {res.student_id: res for res in existing_results}
        
        for stu in students:
            students_data.append({
                'student': stu,
                'result': result_map.get(stu.id)
            })

    # 4. Handle POST (Save Marks)
    if request.method == 'POST':
        if not selected_paper:
             flash('No paper selected.', 'error')
             return redirect(url_for('faculty.marks'))
             
        count = 0
        for data in students_data:
            stu = data['student']
            input_name = f'marks_{stu.id}'
            
            if input_name in request.form:
                marks_val = request.form.get(input_name)
                
                # Logic: If empty, maybe treat as Absent or None?
                # If present, update or create
                
                res = data['result']
                if not res:
                    res = StudentResult(
                        exam_paper_id=selected_paper.id,
                        student_id=stu.id
                    )
                    db.session.add(res)
                
                if marks_val and marks_val.strip() != '':
                    try:
                        val = float(marks_val)
                        if val < 0 or val > selected_paper.total_marks:
                            flash(f'Invalid marks for {stu.enrollment_number}. Max is {selected_paper.total_marks}', 'error')
                            continue
                        res.marks_obtained = val
                        res.status = 'Present'
                        # Fail logic? If < 33%?
                        res.is_fail = (val < (selected_paper.total_marks * 0.33)) # Simple rule
                    except ValueError:
                         flash(f'Invalid number for {stu.enrollment_number}', 'error')
                else:
                    # If empty, mark as Null or Absent? 
                    # Let's say if unchecked 'present', it's absent.
                    # Simplified: If empty string, do nothing or set None
                    pass # Keep previous or ignore
                
                count += 1
        
        db.session.commit()
        flash(f'Updated marks for {count} students.', 'success')
        return redirect(url_for('faculty.marks', exam_id=selected_exam_id, paper_id=selected_paper_id))

    return render_template(
        'faculty/marks.html', 
        exam_events=exam_events, 
        papers=papers, 
        selected_exam=selected_exam,
        selected_paper=selected_paper,
        students_data=students_data
    )

@faculty_bp.route('/mentorship')
@login_required
def mentorship():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    # Mentees are available via backref 'mentees' from StudentProfile
    # Or query explicit
    mentees = StudentProfile.query.filter_by(mentor_id=faculty.id).all()
    
    return render_template('faculty/mentorship.html', mentees=mentees)

@faculty_bp.route('/mentorship/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_mentee(student_id):
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    student = StudentProfile.query.get_or_404(student_id)
    
    # Security: Check if this faculty is the mentor
    if student.mentor_id != faculty.id:
        flash('Unauthorized: You can only edit details of your assigned mentees.', 'error')
        return redirect(url_for('faculty.mentorship'))
        
    if request.method == 'POST':
        try:
            student.display_name = request.form.get('display_name')
            student.enrollment_number = request.form.get('enrollment_number')
            student.course_name = request.form.get('course_name')
            student.semester = request.form.get('semester', type=int)
            student.batch_year = request.form.get('batch_year')
            student.phone_number = request.form.get('phone_number')
            student.address = request.form.get('address')
            student.guardian_name = request.form.get('guardian_name')
            student.guardian_contact = request.form.get('guardian_contact')
            student.id_card_status = request.form.get('id_card_status')
            
            dob_str = request.form.get('date_of_birth')
            if dob_str and dob_str.strip():
                student.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            else:
                student.date_of_birth = None
            
            db.session.commit()
            flash(f'Details for {student.display_name} updated successfully!', 'success')
            return redirect(url_for('faculty.mentorship'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating mentee: {str(e)}', 'error')
            
    return render_template('faculty/edit_mentee.html', student=student)

from app.models import FeeRecord, StudentQuery, QueryMessage, FacultyProfile, Notice, StudentProfile, Subject, UniversityEvent, EventRegistration

# ... (Previous imports remain, just adding models to line 4 manually if needed, 
# but simply overwriting the notices function is safer)

@faculty_bp.route('/notices', methods=['GET', 'POST'])
@login_required
def notices():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        target_type = request.form.get('target_type')
        
        target_course = request.form.get('target_course') # If type is class
        target_semester = request.form.get('target_semester') # If type is class
        target_student_id = request.form.get('target_student_id') # If individual
        
        # Handle "Mentees" logic -> Can be implemented as individual notices OR a group tag
        # For now, if "mentees", we might create one notice with type 'mentees' 
        # (assuming frontend filters handle it) OR create individual notices.
        # Let's stick to storing 'mentees' in target_type for efficiency.
        
        notice = Notice(
            title=title,
            content=content,
            category=category,
            target_type=target_type,
            sender_faculty_id=faculty.id,
            target_course=target_course if target_type == 'class' else None,
            target_semester=target_semester if target_type == 'class' else None,
            target_student_id=target_student_id if target_type == 'individual' else None
        )
        
        db.session.add(notice)
        db.session.commit()
        flash('Notice sent successfully!', 'success')
        return redirect(url_for('faculty.notices'))

    # Fetch Notices
    # 1. Sent by Me
    sent_notices = Notice.query.filter_by(sender_faculty_id=faculty.id).order_by(Notice.created_at.desc()).all()
    
    # 2. Received (Admin -> All or Admin -> Faculty (not implemented yet, but 'all' works))
    # Assuming Admin senders have sender_faculty_id = None
    received_notices = Notice.query.filter(
        (Notice.target_type == 'all') | 
        ((Notice.target_type == 'faculty') & ((Notice.target_faculty_id == None) | (Notice.target_faculty_id == faculty.id)))
    ).filter(Notice.sender_faculty_id == None).order_by(Notice.created_at.desc()).all()
    
    # Context Data for Form
    mentees = StudentProfile.query.filter_by(mentor_id=faculty.id).all()
    # Subjects taught for Class/Course selection
    subjects_taught = Subject.query.filter_by(faculty_id=faculty.id).all()
    # Unique Courses/Sems taught
    my_classes = set()
    for sub in subjects_taught:
        if sub.course_name and sub.semester:
            my_classes.add((sub.course_name, sub.semester))
    
    return render_template('faculty/notices.html', 
                           sent_notices=sent_notices, 
                           received_notices=received_notices,
                           mentees=mentees,
                           my_classes=sorted(list(my_classes)))

@faculty_bp.route('/schedule')
@login_required
def schedule():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Get current day
    today_name = datetime.now(timezone.utc).strftime('%A') # e.g. "Monday"
    # For Demo purposes, if it's Sunday, show Monday's schedule so the user sees something
    if today_name == 'Sunday':
        today_name = 'Monday' # Demo fallback
        flash('Showing Monday Schedule (Weekend Override)', 'info')

    slots = Timetable.query.filter_by(
        faculty_id=faculty.id, 
        day_of_week=today_name
    ).order_by(Timetable.period_number).all()
    
    schedule_data = []
    current_time = datetime.now(timezone.utc).time() # UTC time, might need offset for display logic
    
    # Base Time: 9:00 AM
    base_hour = 9 
    
    for slot in slots:
        # Calculate Time
        from app.models import ScheduleSettings
        settings = ScheduleSettings.query.filter_by(course_name=slot.course_name, semester=slot.semester).first()
        if settings:
            s_time, e_time = settings.get_period_times(slot.period_number)
            t_str = f"{s_time.strftime('%I:%M %p')} - {e_time.strftime('%I:%M %p')}"
        else:
            start_h = base_hour + (slot.period_number - 1)
            end_h = start_h + 1
            t_str = f"{start_h if start_h <= 12 else start_h-12}:00 - {end_h if end_h <= 12 else end_h-12}:00 {'AM' if start_h < 12 else 'PM'}"
        
        # Student Count
        count = StudentProfile.query.filter_by(
            course_name=slot.course_name,
            semester=slot.semester
        ).count()
        
        schedule_data.append({
            'time_str': t_str,
            'subject': slot.subject.name,
            'course_detail': f"{slot.course_name} • Sem {slot.semester}",
            'room': slot.room_number,
            'student_count': count,
            'attendance_marked': False # Placeholder logic
        })
        
    return render_template('faculty/schedule.html', schedule=schedule_data, day_name=today_name)


@faculty_bp.route('/events')
@login_required
def events():
    # Fetch upcoming events
    events_list = UniversityEvent.query.filter_by(is_upcoming=True).order_by(UniversityEvent.date).all()
    return render_template('faculty/events.html', events=events_list)

@faculty_bp.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    event = UniversityEvent.query.get_or_404(event_id)
    # Get registered students
    registrations = EventRegistration.query.filter_by(event_id=event.id).all()
    return render_template('faculty/event_detail.html', event=event, registrations=registrations)

@faculty_bp.route('/event/image/<int:event_id>')
def event_image(event_id):
    from flask import Response
    event = UniversityEvent.query.get_or_404(event_id)
    if not event.image_data:
        return "", 404
    return Response(event.image_data, mimetype=event.image_mimetype)

@faculty_bp.route('/timetable')
@login_required
def timetable():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Fetch Timetable entries
    entries = Timetable.query.filter_by(faculty_id=faculty.id).order_by(Timetable.period_number).all()
    
    # Structure Data: Days -> Slots
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    schedule = {day: [] for day in days_order}
    
    for entry in entries:
        if entry.day_of_week in schedule:
            # We can calculate times if we had a settings model, but for now 
            # we rely on period number or just display it simply.
            # Mirroring student logic for consistency if possible, or simple list.
            
            # Simple Time Logic (09:00 Start, 1 hr slots)
            from app.models import ScheduleSettings
            settings = ScheduleSettings.query.filter_by(course_name=entry.course_name, semester=entry.semester).first()
            if settings:
                s_time, e_time = settings.get_period_times(entry.period_number)
                entry.start_time = s_time
                entry.end_time = e_time
            else:
                base_start_hour = 9
                start_minutes = (base_start_hour * 60) + ((entry.period_number - 1) * 60)
                
                start_time = datetime.combine(date.today(), datetime.min.time()) + timedelta(minutes=start_minutes)
                end_time = start_time + timedelta(minutes=60)
                entry.start_time = start_time.time()
                entry.end_time = end_time.time()
            
            # Room logic
            entry.room_number = getattr(entry, 'room_number', 'Room 101')
            
            schedule[entry.day_of_week].append(entry)
            
    # Remove empty days if desired, or keep for grid structure. 
    # Keeping mostly full week except Sunday usually good.
    if not schedule['Sunday']:
        del schedule['Sunday']
        
    return render_template('faculty/timetable.html', faculty=faculty, schedule=schedule)

@faculty_bp.route('/reports/lost-cards')
@login_required
def report_lost_cards():
    faculty = FacultyProfile.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Ideally filter by students relevant to faculty(optional), but for "Lost Cards", 
    # usually it's a general report or filtered by Dept. 
    # Showing all lost cards for now as faculty might need to know about any student.
    lost_cards = StudentProfile.query.filter_by(id_card_status='Lost').all()
    
    return render_template('faculty/report_lost_cards.html', lost_cards=lost_cards)

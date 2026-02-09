from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Subject, Timetable, FacultyProfile, StudentProfile, ScheduleSettings, Course
from . import admin_bp
import random
import math
from datetime import datetime, time, date, timedelta

@admin_bp.route('/timetable', methods=['GET'])
@login_required
def timetable_landing():
    # step 1: Select Course and Semester
    # Fetch courses from standard Course definition
    courses_query = Course.query.with_entities(Course.code).all()
    courses = sorted([c.code for c in courses_query])
    return render_template('timetable_landing.html', courses=courses)

@admin_bp.route('/timetable/setup', methods=['GET', 'POST'])
@login_required
def timetable_setup():
    course = request.args.get('course') or request.form.get('course')
    semester = request.args.get('semester') or request.form.get('semester')
    
    if not course or not semester:
        flash('Please select course and semester.', 'error')
        return redirect(url_for('admin.timetable_landing'))

    semester = int(semester)
    
    # Fetch existing subjects explicitly assigned to this course/sem
    assigned_subjects = Subject.query.filter_by(course_name=course, semester=semester).all()
    
    # Fetch all subjects for the dropdown (filtered by course and semester)
    all_subjects = Subject.query.filter_by(course_name=course, semester=semester).order_by(Subject.name).all()
    
    faculty_members = FacultyProfile.query.all()
    
    return render_template('timetable_setup.html', 
                           course=course, 
                           semester=semester, 
                           subjects=assigned_subjects,
                           all_subjects=all_subjects,
                           faculty_members=faculty_members)

@admin_bp.route('/timetable/add_subject', methods=['POST'])
@login_required
def add_subject():
    # Helper to add subject via AJAX or Form
    course = request.form.get('course')
    semester = request.form.get('semester')
    
    subject_id = request.form.get('subject_id') # If selecting existing
    name = request.form.get('name') # If creating new (fallback)
    
    faculty_id = request.form.get('faculty_id')
    lectures = request.form.get('lectures')
    
    try:
        if subject_id:
            # proper linking of existing subject
            subject = Subject.query.get(subject_id)
            if subject:
                subject.course_name = course
                subject.semester = semester
                if faculty_id:
                    subject.faculty_id = faculty_id
                if lectures:
                    subject.weekly_lectures = lectures
                db.session.commit()
                flash('Subject linked successfully', 'success')
            else:
                flash('Subject not found', 'error')
        
        elif name:
            # Creating new
            subject = Subject(
                name=name,
                course_name=course,
                semester=semester,
                faculty_id=faculty_id,
                weekly_lectures=lectures
            )
            db.session.add(subject)
            db.session.commit()
            flash('Subject added successfully', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding subject: {e}', 'error')
        
    return redirect(url_for('admin.timetable_setup', course=course, semester=semester))

@admin_bp.route('/timetable/generate', methods=['POST'])
@login_required
def generate_timetable():
    course = request.form.get('course')
    semester = int(request.form.get('semester'))
    days_per_week = int(request.form.get('days_per_week', 5)) # Default 5
    slots_per_day = int(request.form.get('slots_per_day', 8)) # Default 8
    
    # Parse Time Inputs
    start_time_str = request.form.get('start_time', '09:00')
    end_time_str = request.form.get('end_time', '17:00')
    
    try:
        start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
    except ValueError:
        flash('Invalid time format. Using defaults 09:00 - 17:00', 'warning')
        start_time_obj = datetime.strptime('09:00', '%H:%M').time()
        end_time_obj = datetime.strptime('17:00', '%H:%M').time()

    # Save Settings
    settings = ScheduleSettings.query.filter_by(course_name=course, semester=semester).first()
    if not settings:
        settings = ScheduleSettings(course_name=course, semester=semester)
        db.session.add(settings)
    
    settings.start_time = start_time_obj
    settings.end_time = end_time_obj
    settings.slots_per_day = slots_per_day
    settings.days_per_week = days_per_week
    
    # Recess (Now Automatic middle)
    settings.recess_duration = int(request.form.get('recess_duration', 0))
    settings.recess_after_slot = slots_per_day // 2
    
    db.session.commit() # Save settings first
    
    # 1. Clear existing timetable for this course/sem
    Timetable.query.filter_by(course_name=course, semester=semester).delete()
    
    # 2. Get Subjects
    subjects = Subject.query.filter_by(course_name=course, semester=semester).all()
    
    # 3. Algorithm
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][:days_per_week]
    total_slots = days_per_week * slots_per_day
    
    pool = []
    # 1. Add minimum required lectures
    for sub in subjects:
        for _ in range(sub.weekly_lectures):
            pool.append(sub)
            
    # 2. FILL LOGIC
    if subjects and len(pool) < total_slots:
        while len(pool) < total_slots:
             for sub in subjects:
                 if len(pool) >= total_slots:
                     break
                 pool.append(sub)
            
    random.shuffle(pool)
    
    subject_daily_limits = {}
    for sub in subjects:
        count = pool.count(sub)
        subject_daily_limits[sub.id] = math.ceil(count / days_per_week)
    
    schedule = {day: {p: None for p in range(1, slots_per_day + 1)} for day in days}
    unplaced = []
    
    for item in pool:
        placed = False
        for day in days:
            if placed: break
            
            daily_count = sum(1 for p in range(1, slots_per_day+1) 
                              if schedule[day][p] and schedule[day][p].id == item.id)
            
            limit = subject_daily_limits.get(item.id, 2)
            if daily_count >= limit:
                continue 
                
            for period in range(1, slots_per_day + 1):
                if schedule[day][period] is None:
                    # TODO: Global Faculty Check here if needed
                    schedule[day][period] = item
                    placed = True
                    break
        
        if not placed:
            unplaced.append(item.name)
            
    # 4. Save to DB
    for day in days:
        for period in range(1, slots_per_day + 1):
            sub = schedule[day][period]
            if sub:
                slot = Timetable(
                    course_name=course,
                    semester=semester,
                    day_of_week=day,
                    period_number=period,
                    subject_id=sub.id,
                    faculty_id=sub.faculty_id
                )
                db.session.add(slot)
    
    db.session.commit()
    
    if unplaced:
        flash(f"Warning: Could not place {len(unplaced)} lectures.", 'warning')
    else:
        flash('Timetable generated successfully!', 'success')
        
    return redirect(url_for('admin.view_timetable', course=course, semester=semester))

@admin_bp.route('/timetable/view', methods=['GET', 'POST'])
@login_required
def view_timetable():
    course = request.args.get('course')
    semester = request.args.get('semester')
    
    if not course or not semester:
        return redirect(url_for('admin.timetable_landing'))
        
    slots = Timetable.query.filter_by(course_name=course, semester=int(semester)).all()
    settings = ScheduleSettings.query.filter_by(course_name=course, semester=int(semester)).first()
    
    # Defaults if no settings found (shouldn't happen if generated via app)
    slots_per_day = settings.slots_per_day if settings else 8
    
    if slots:
        max_period = max([s.period_number for s in slots] + [slots_per_day])
    else:
        max_period = slots_per_day
        
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    active_days = set([s.day_of_week for s in slots])
    
    if settings:
        final_days = days[:settings.days_per_week]
    elif not active_days:
        final_days = days[:5]
    else:
         grid_days = [d for d in days if d in active_days]
         if len(grid_days) < 5: final_days = days[:5]
         else: final_days = grid_days

    # Calculate Time Slots
    time_headers = []
    if settings:
        for p in range(1, max_period + 1):
            s_time, e_time = settings.get_period_times(p)
            
            # Format display
            # Create dummy datetime to use strftime
            dummy_dt_s = datetime.combine(date.today(), s_time)
            dummy_dt_e = datetime.combine(date.today(), e_time)
            time_headers.append(f"{dummy_dt_s.strftime('%I:%M %p')} - {dummy_dt_e.strftime('%I:%M %p')}")
    else:
        time_headers = [f"Period {p+1}" for p in range(max_period)]

    grid = {day: {p: None for p in range(1, max_period + 1)} for day in final_days}
    
    for s in slots:
        if s.day_of_week in grid and s.period_number in grid[s.day_of_week]:
            grid[s.day_of_week][s.period_number] = s
            
    subjects = Subject.query.filter_by(course_name=course, semester=int(semester)).all()

    return render_template('timetable_view.html', 
                           grid=grid, 
                           days=final_days, 
                           periods=range(1, max_period+1), # 1-based index for logic
                           time_headers=time_headers, # 0-based index list for display
                           course=course,
                           semester=semester,
                           subjects=subjects,
                           settings=settings)

@admin_bp.route('/timetable/update_slot', methods=['POST'])
@login_required
def update_slot():
    # AJAX Endpoint for drag-drop or dropdown change
    data = request.json
    slot_id = data.get('slot_id') # If editing existing
    day = data.get('day')
    period = data.get('period')
    subject_id = data.get('subject_id')
    course = data.get('course')
    semester = data.get('semester')
    
    if not subject_id:
        # Clear slot
        if slot_id:
            Timetable.query.filter_by(id=slot_id).delete()
    else:
        subject = Subject.query.get(subject_id)
        if slot_id:
            slot = Timetable.query.get(slot_id)
            slot.subject_id = subject_id
            slot.faculty_id = subject.faculty_id
        else:
            # Create new
            slot = Timetable(
                course_name=course,
                semester=semester,
                day_of_week=day,
                period_number=period,
                subject_id=subject_id,
                faculty_id=subject.faculty_id
            )
            db.session.add(slot)
            
    db.session.commit()
    return jsonify({'status': 'success'})

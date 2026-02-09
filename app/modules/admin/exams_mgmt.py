from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import ExamEvent, ExamPaper, Subject, StudentProfile, StudentResult, Course
from datetime import datetime

exams_bp = Blueprint('exams', __name__)

@exams_bp.route('/exams', methods=['GET'])
@login_required
def exams_dashboard():
    # List all exam events
    events = ExamEvent.query.order_by(ExamEvent.start_date.desc()).all()
    return render_template('exams/dashboard.html', events=events)

@exams_bp.route('/exams/create', methods=['GET', 'POST'])
@login_required
def create_exam_event():
    if request.method == 'POST':
        name = request.form.get('name')
        course = request.form.get('course')
        semester = request.form.get('semester')
        academic_year = request.form.get('academic_year')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        
        if end_date < start_date:
            flash('End Date cannot be before Start Date.', 'error')
            return redirect(url_for('.create_exam_event'))
        
        event = ExamEvent(
            name=name,
            course_name=course,
            semester=semester,
            academic_year=academic_year,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(event)
        db.session.commit()
        flash('Exam Event Created!', 'success')
        return redirect(url_for('.schedule_exam', event_id=event.id))

    # Fetch courses from standard Course definition
    # Use Course.code (e.g. B.Tech) to match Subject.course_name which stores the Course Code
    courses_query = Course.query.with_entities(Course.code, Course.name).all()
    # Pass dicts to template for code/name separation
    courses = [{'code': c.code, 'name': c.name} for c in courses_query]
    return render_template('exams/create_event.html', courses=courses)

@exams_bp.route('/exams/<int:event_id>/schedule', methods=['GET', 'POST'])
@login_required
def schedule_exam(event_id):
    event = ExamEvent.query.get_or_404(event_id)
    subjects = Subject.query.filter_by(course_name=event.course_name, semester=event.semester).all()
    
    if request.method == 'POST':
        # Form handling for creating Papers
        for sub in subjects:
            date_str = request.form.get(f'date_{sub.id}')
            start_str = request.form.get(f'start_{sub.id}')
            end_str = request.form.get(f'end_{sub.id}')
            marks_str = request.form.get(f'marks_{sub.id}')
            
            if date_str and start_str and end_str:
                # Check if paper exists
                paper = ExamPaper.query.filter_by(exam_event_id=event.id, subject_id=sub.id).first()
                
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                start_obj = datetime.strptime(start_str, '%H:%M').time()
                end_obj = datetime.strptime(end_str, '%H:%M').time()
                try:
                    total_marks = int(marks_str) if marks_str else 100
                except ValueError:
                    total_marks = 100
                
                if paper:
                    paper.date = date_obj
                    paper.start_time = start_obj
                    paper.end_time = end_obj
                    paper.total_marks = total_marks
                else:
                    paper = ExamPaper(
                        exam_event_id=event.id,
                        subject_id=sub.id,
                        date=date_obj,
                        start_time=start_obj,
                        end_time=end_obj,
                        total_marks=total_marks
                    )
                    db.session.add(paper)
        
        if request.form.get('action') == 'publish':
            event.is_published = True
            flash('Schedule published successfully!', 'success')
        else:
            flash('Schedule updated successfully!', 'success')
        
        db.session.commit()
    
    # Pre-fetch existing papers logic for template
    existing_papers = {p.subject_id: p for p in event.papers}
    
    return render_template('exams/schedule_exam.html', event=event, subjects=subjects, papers=existing_papers)

@exams_bp.route('/exams/export', methods=['GET', 'POST'])
@login_required
def export_results():
    if request.method == 'POST':
        import csv
        from io import StringIO
        from flask import Response

        event_id = request.form.get('event_id')
        event = ExamEvent.query.get_or_404(event_id)
        
        course = event.course_name
        semester = event.semester
        academic_year = event.academic_year

        # 1. Fetch Students
        students = StudentProfile.query.filter_by(course_name=course, semester=semester).order_by(StudentProfile.enrollment_number).all()

        # 2. Prepare CSV
        si = StringIO()
        cw = csv.writer(si)

        # Header
        cw.writerow(['Exam Event: ' + event.name])
        cw.writerow(['Course: ' + course, 'Semester: ' + str(semester), 'Year: ' + academic_year])
        cw.writerow([]) # Empty line
        
        # Dynamic Header based on Papers
        # We want: [Enrollment, Name, Subject1, Subject2, ..., Total, %]
        papers = ExamPaper.query.filter_by(exam_event_id=event.id).all()
        paper_subjects = {p.subject_id: p.subject.name for p in papers if p.subject}
        sorted_subjects = sorted(paper_subjects.values()) # Alphabetic order for columns? Or By Date?
        
        # Let's sort by Date
        papers.sort(key=lambda x: x.date if x.date else datetime.max.date())
        sorted_paper_ids = [p.id for p in papers]
        sorted_subject_names = [p.subject.name for p in papers if p.subject]
        
        header_row = ['Enrollment No', 'Name'] + sorted_subject_names + ['Total Marks', 'Obtained Marks', 'Percentage', 'Status']
        cw.writerow(header_row)

        # Data
        for student in students:
            row = [student.enrollment_number, student.display_name]
            
            # Placeholder marks for each subject
            total_max = 0
            total_obtained = 0
            
            for paper in papers:
                # TODO: Retrieve actual mark
                # mark = StudentResult.query...
                # For now empty
                row.append('') # Marks for this subject
                total_max += paper.total_marks
            
            row.append(total_max) # Total Marks
            row.append('') # Obtained
            row.append('') # %
            row.append('') # Status
            
            cw.writerow(row)

        output =  Response(si.getvalue(), mimetype="text/csv")
        output.headers["Content-Disposition"] = f"attachment; filename=results_{event.name.replace(' ', '_')}_{academic_year}.csv"
        return output

    # GET: Show Form (Only Published Events)
    events = ExamEvent.query.filter_by(is_published=True).order_by(ExamEvent.start_date.desc()).all()
    return render_template('exams/export_results.html', events=events)

@exams_bp.route('/exams/<int:event_id>/view', methods=['GET'])
@login_required
def view_schedule(event_id):
    event = ExamEvent.query.get_or_404(event_id)
    # Sort papers by date
    papers = sorted(event.papers, key=lambda p: p.date if p.date else datetime.max.date())
    return render_template('exams/view_schedule.html', event=event, papers=papers)

@exams_bp.route('/exams/<int:event_id>/recandidates', methods=['GET'])
@login_required
def recandidates_report(event_id):
    event = ExamEvent.query.get_or_404(event_id)
    
    # Query for Failures OR Absentees
    # We need to join with ExamPaper to filter by event_id
    results = db.session.query(StudentResult).join(ExamPaper).filter(
        ExamPaper.exam_event_id == event.id,
        (StudentResult.is_fail == True) | (StudentResult.status == 'Absent')
    ).all()
    
    return render_template('exams/recandidates.html', event=event, results=results)

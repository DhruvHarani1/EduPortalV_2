from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Subject, FacultyProfile, StudentProfile, Course

subjects_bp = Blueprint('subjects', __name__)

@subjects_bp.route('/subjects', methods=['GET'])
@login_required
def subject_list():
    # Fetch all subjects
    subjects = Subject.query.all()
    
    # Data for assignment modal
    faculty_list = FacultyProfile.query.all()
    courses = Course.query.order_by(Course.code).all()
    
    return render_template('subjects/subject_list.html', 
                           subjects=subjects, 
                           faculty_list=faculty_list, 
                           courses=courses)

@subjects_bp.route('/subjects/create', methods=['POST'])
@login_required
def create_subject():
    name = request.form.get('name')
    course = request.form.get('course')
    semester = request.form.get('semester')
    academic_year = request.form.get('academic_year')
    
    if name:
        sub = Subject(
            name=name,
            course_name=course if course else None,
            semester=int(semester) if semester else None,
            academic_year=academic_year if academic_year else None
        )
        db.session.add(sub)
        db.session.commit()
        flash(f'Subject "{name}" created successfully.', 'success')
    else:
        flash('Subject name is required.', 'error')
    return redirect(url_for('.subject_list'))

@subjects_bp.route('/subjects/assign', methods=['POST'])
@login_required
def assign_subject():
    subject_id = request.form.get('subject_id')
    sub = Subject.query.get_or_404(subject_id)
    course = request.form.get('course')
    semester = request.form.get('semester')
    academic_year = request.form.get('academic_year')
    sub.course_name = course
    sub.semester = semester
    sub.academic_year = academic_year
    
    db.session.commit()
    flash('Subject assigned successfully!', 'success')
    return redirect(url_for('.subject_list'))

@subjects_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    sub = Subject.query.get_or_404(subject_id)
    db.session.delete(sub)
    db.session.commit()
    flash('Subject deleted.', 'info')
    return redirect(url_for('.subject_list'))

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.extensions import db
from app.models import Course
from . import admin_bp

@admin_bp.route('/courses')
@login_required
def courses_list():
    courses = Course.query.order_by(Course.code).all()
    return render_template('courses_list.html', courses=courses)

@admin_bp.route('/courses/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        dept = request.form.get('department')
        duration = request.form.get('duration_years', 4)
        semesters = request.form.get('total_semesters', 8)

        if Course.query.filter_by(code=code).first():
            flash(f'Course code {code} already exists.', 'error')
            return redirect(url_for('admin.courses_list'))

        try:
            new_course = Course(
                name=name,
                code=code,
                department=dept,
                duration_years=int(duration),
                total_semesters=int(semesters)
            )
            db.session.add(new_course)
            db.session.commit()
            flash(f'Course {code} added successfully!', 'success')
            return redirect(url_for('admin.courses_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding course: {str(e)}', 'error')
            return redirect(url_for('admin.courses_list'))
            
    return redirect(url_for('admin.courses_list'))

@admin_bp.route('/courses/delete/<int:id>', methods=['POST'])
@login_required
def delete_course(id):
    course = Course.query.get_or_404(id)
    try:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting course: {str(e)}', 'error')
    return redirect(url_for('admin.courses_list'))

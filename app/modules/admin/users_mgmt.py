from flask import render_template, request, flash, redirect, url_for, current_app, Response, make_response
from datetime import datetime
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, StudentProfile, FacultyProfile, Subject, Course
from . import admin_bp
import csv
import io
import os
from werkzeug.utils import secure_filename

# --- Student Management ---
@admin_bp.route('/students')
@login_required
def students_list():
    query = StudentProfile.query.join(User)
    
    # 1. Search (Query)
    search_query = request.args.get('q')
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            (StudentProfile.enrollment_number.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (StudentProfile.course_name.ilike(search_filter))
        )
    
    # 2. Filters
    course_filter = request.args.get('course')
    if course_filter:
        query = query.filter(StudentProfile.course_name == course_filter)
        
    semester_filter = request.args.get('semester')
    if semester_filter:
        query = query.filter(StudentProfile.semester == int(semester_filter))

    students = query.all()
    
    # Get distinct options for filters
    courses = db.session.query(StudentProfile.course_name).distinct().all()
    courses = [c[0] for c in courses]
    
    semesters = db.session.query(StudentProfile.semester).distinct().order_by(StudentProfile.semester).all()
    semesters = [s[0] for s in semesters]

    return render_template(
        'student_list.html', 
        students=students, 
        courses=courses, 
        semesters=semesters,
        search_query=search_query,
        course_filter=course_filter,
        semester_filter=int(semester_filter) if semester_filter else None
    )

@admin_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        enrollment = request.form.get('enrollment_number')
        course = request.form.get('course_name')
        semester = request.form.get('semester')

        if User.query.filter_by(email=email).first():
            flash(f'Email {email} already exists.', 'error')
            return redirect(url_for('admin.add_student'))

        try:
            user = User(email=email, role='student')
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # Parse date if provided
            dob_str = request.form.get('date_of_birth')
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

            student = StudentProfile(
                user_id=user.id,
                display_name=name,
                enrollment_number=enrollment,
                course_name=course,
                semester=semester,
                batch_year=request.form.get('batch_year'),
                date_of_birth=dob,
                phone_number=request.form.get('phone_number'),
                address=request.form.get('address'),
                guardian_name=request.form.get('guardian_name'),
                guardian_contact=request.form.get('guardian_contact'),
                mentor_id=request.form.get('mentor_id') or None,
                id_card_status=request.form.get('id_card_status', 'Active')
            )
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('admin.students_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'error')

    faculty_list = FacultyProfile.query.all()
    courses = Course.query.order_by(Course.code).all()
    
    return render_template('student_add.html', faculty_list=faculty_list, courses=courses)

@admin_bp.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = StudentProfile.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        enrollment = request.form.get('enrollment_number')
        course = request.form.get('course_name')
        semester = request.form.get('semester')
        
        # Check email uniqueness if changed
        if email != student.user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already in use.', 'error')
                return render_template('student_edit.html', student=student)
            student.user.email = email
            
        student.display_name = name
        student.enrollment_number = enrollment
        student.course_name = course
        student.semester = semester
        student.batch_year = request.form.get('batch_year')
        
        dob_str = request.form.get('date_of_birth')
        student.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        
        student.phone_number = request.form.get('phone_number')
        student.address = request.form.get('address')
        student.guardian_name = request.form.get('guardian_name')
        student.guardian_contact = request.form.get('guardian_contact')
        student.mentor_id = request.form.get('mentor_id') or None
        student.id_card_status = request.form.get('id_card_status', 'Active')
        
        try:
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('admin.students_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'error')
            
    faculty_list = FacultyProfile.query.all()
    courses = Course.query.order_by(Course.code).all()
    
    return render_template('student_edit.html', student=student, faculty_list=faculty_list, courses=courses)

@admin_bp.route('/students/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    student = StudentProfile.query.get_or_404(id)
    try:
        user = student.user
        db.session.delete(student)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
        
    return redirect(url_for('admin.students_list'))

@admin_bp.route('/students/import', methods=['GET', 'POST'])
@login_required
def import_students():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file provided.', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
            
        if file:
            try:
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                count = 0
                errors = []
                
                for row in csv_reader:
                    name = row.get('name')
                    email = row.get('email')
                    password = row.get('password')
                    enrollment = row.get('enrollment_number')
                    course = row.get('course_name')
                    semester = row.get('semester')
                    
                    if not all([email, password, enrollment]):
                        errors.append(f"Skipped row with missing base fields: {row}")
                        continue
                        
                    if User.query.filter_by(email=email).first():
                        errors.append(f"Skipped existing email: {email}")
                        continue
                        
                    user = User(email=email, role='student')
                    user.set_password(password)
                    db.session.add(user)
                    db.session.flush()
                    
                    student = StudentProfile(
                        user_id=user.id,
                        display_name=name,
                        enrollment_number=enrollment, 
                        course_name=course,
                        semester=semester
                    )
                    db.session.add(student)
                    count += 1
                
                db.session.commit()
                flash(f'Imported {count} students successfully.', 'success')
                if errors:
                    for err in errors[:5]: # Show first 5 errors to avoid flooding
                        flash(err, 'warning')
                        
                return redirect(url_for('admin.students_list'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing CSV: {str(e)}', 'error')
    
    return render_template('student_import_csv.html')

# --- Faculty Management ---

@admin_bp.route('/faculty/photo/<int:id>')
def serve_faculty_photo(id):
    faculty = FacultyProfile.query.get_or_404(id)
    if not faculty.photo_data:
        # Return default image or 404
        return redirect(url_for('static', filename='img/default_user.png'))
    
    response = make_response(faculty.photo_data)
    response.headers.set('Content-Type', faculty.photo_mimetype or 'image/jpeg')
    return response

@admin_bp.route('/faculty')
@login_required
def faculty_list():
    faculty_members = FacultyProfile.query.all()
    return render_template('faculty_list.html', faculty_members=faculty_members)

@admin_bp.route('/faculty/view/<int:id>')
@login_required
def view_faculty(id):
    faculty = FacultyProfile.query.get_or_404(id)
    return render_template('faculty_view.html', faculty=faculty)

@admin_bp.route('/faculty/add', methods=['GET', 'POST'])
@login_required
def add_faculty():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        designation = request.form.get('designation')
        department = request.form.get('department')
        experience = request.form.get('experience')
        specialization = request.form.get('specialization')
        # Retrieve list of selected subject names
        selected_subject_names = request.form.getlist('assigned_subjects')
        
        # Store as comma-separated string for display
        faculty_assigned_str = ", ".join(selected_subject_names) if selected_subject_names else None
        
        # Photo Upload (Binary)
        photo_data = None
        photo_mimetype = None
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                photo_data = file.read()
                photo_mimetype = file.mimetype

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('admin.add_faculty'))

        try:
            # Create User
            user = User(email=email, role='faculty')
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # Create Profile
            faculty = FacultyProfile(
                user_id=user.id,
                display_name=name,
                designation=designation,
                department=department,
                experience=experience,
                specialization=specialization,
                assigned_subject=faculty_assigned_str,
                photo_data=photo_data,
                photo_mimetype=photo_mimetype
            )
            db.session.add(faculty)
            db.session.flush() # Get ID
            
            # Link Subjects (Multi)
            if selected_subject_names:
                # Set new links
                subjects_to_link = Subject.query.filter(Subject.name.in_(selected_subject_names)).all()
                for sub in subjects_to_link:
                    sub.faculty_id = faculty.id
            
            db.session.commit()
            flash('Faculty added successfully!', 'success')
            return redirect(url_for('admin.faculty_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding faculty: {str(e)}', 'error')

    subjects = Subject.query.all()
    return render_template('faculty_add.html', subjects=subjects)

@admin_bp.route('/faculty/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_faculty(id):
    faculty = FacultyProfile.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        designation = request.form.get('designation')
        department = request.form.get('department')
        experience = request.form.get('experience')
        specialization = request.form.get('specialization')
        # Retrieve list of selected subject names
        selected_subject_names = request.form.getlist('assigned_subjects')
        
        # Update Profile String
        faculty.assigned_subject = ", ".join(selected_subject_names) if selected_subject_names else None
        
        try:
            # Handle Subject Linking (Multi)
            
            # 1. Unlink subjects that are currently assigned to this faculty but NOT in the selected list
            # Fetch all subjects currently owned by this faculty
            existing_subjects = Subject.query.filter_by(faculty_id=faculty.id).all()
            for sub in existing_subjects:
                if sub.name not in selected_subject_names:
                    sub.faculty_id = None
            
            # 2. Link selected subjects
            if selected_subject_names:
                new_subjects = Subject.query.filter(Subject.name.in_(selected_subject_names)).all()
                for sub in new_subjects:
                    sub.faculty_id = faculty.id
            
            db.session.commit()
            flash('Faculty updated successfully!', 'success')
            return redirect(url_for('admin.faculty_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating faculty: {str(e)}', 'error')

    subjects = Subject.query.all()
    return render_template('faculty_edit.html', faculty=faculty, subjects=subjects)

@admin_bp.route('/faculty/delete/<int:id>', methods=['POST'])
@login_required
def delete_faculty(id):
    faculty = FacultyProfile.query.get_or_404(id)
    try:
        user = faculty.user
        db.session.delete(faculty)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash('Faculty deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting faculty: {str(e)}', 'error')
        
    return redirect(url_for('admin.faculty_list'))

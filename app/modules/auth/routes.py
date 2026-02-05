from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models import User
from . import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    role = request.args.get('role')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') # Hidden input in the form
        
        user = User.query.filter_by(email=email).first()
        # TODO: In production, check if user.role matches the requested role!
        
        if user and user.check_password(password):
            # Strict Role Validation
            if user.role != role:
                flash(f'Access Denied: Account exists but does not belong to the {role.capitalize()} domain.')
                return render_template('login.html', role=role)

            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student.dashboard'))
            return redirect(url_for('main.index'))
            
        flash('Invalid email or password.')
    
    # If no role selected, show selection screen
    if not role:
        return render_template('selection.html')
        
    return render_template('login.html', role=role)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

from flask import render_template
from . import main_bp

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/features/student')
def features_student():
    return render_template('features_student.html')

@main_bp.route('/features/faculty')
def features_faculty():
    return render_template('features_faculty.html')

@main_bp.route('/features/admin')
def features_admin():
    return render_template('features_admin.html')

@main_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main_bp.route('/documentation')
def documentation():
    return render_template('documentation.html')

@main_bp.route('/api-reference')
def api_reference():
    return render_template('api_reference.html')

@main_bp.route('/help-center')
def help_center():
    return render_template('help_center.html')

@main_bp.route('/system-status')
def system_status():
    return render_template('system_status.html')

@main_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@main_bp.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@main_bp.route('/cookie-settings')
def cookie_settings():
    return render_template('cookie_settings.html')

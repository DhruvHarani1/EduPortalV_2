from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='templates')

from . import routes, users_mgmt, notices_mgmt, timetable_mgmt, exams_mgmt, subjects_mgmt, courses_mgmt

admin_bp.register_blueprint(exams_mgmt.exams_bp)
admin_bp.register_blueprint(subjects_mgmt.subjects_bp)
from . import academics_mgmt, reports_mgmt
admin_bp.register_blueprint(reports_mgmt.reports_bp)

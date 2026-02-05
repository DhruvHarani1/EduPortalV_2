from flask import Flask
from config import config
from app.extensions import db, migrate, login_manager

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register Filters
    import base64
    @app.template_filter('b64encode')
    def b64encode_filter(data):
        if not data:
            return ''
        return base64.b64encode(data).decode('utf-8')

    # Register Blueprints
    from app.modules.main import main_bp
    app.register_blueprint(main_bp)

    from app.modules.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.modules.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.modules.faculty import faculty_bp
    app.register_blueprint(faculty_bp, url_prefix='/faculty')

    from app.modules.student import student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    return app

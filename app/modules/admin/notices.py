from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.extensions import db
from app.models import Notice
from . import admin_bp

@admin_bp.route('/notices')
@login_required
def notices_list():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('notice_list.html', notices=notices)

@admin_bp.route('/notices/add', methods=['GET', 'POST'])
@login_required
def add_notice():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        audience = request.form.get('audience')

        try:
            notice = Notice(title=title, content=content, audience=audience)
            db.session.add(notice)
            db.session.commit()
            flash('Notice published successfully!', 'success')
            return redirect(url_for('admin.notices_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding notice: {str(e)}', 'error')

    return render_template('notice_add.html')

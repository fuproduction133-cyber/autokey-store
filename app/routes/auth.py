"""
AutoKey Store - Authentication Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User
from app.forms import RegisterForm, LoginForm, ChangePasswordForm
from datetime import datetime, timedelta
import re

bp = Blueprint('auth', __name__, url_prefix='/auth')


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5/hour;2/minute", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        if not form.terms.data:
            flash('Bạn phải đồng ý với điều khoản sử dụng.', 'danger')
            return render_template('auth/register.html', form=form)

        if not is_valid_email(email):
            flash('Email không hợp lệ.', 'danger')
            return render_template('auth/register.html', form=form)

        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng.', 'danger')
            return render_template('auth/register.html', form=form)

        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.', 'danger')
            return render_template('auth/register.html', form=form)

        user = User(username=username, email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("20/minute;100/hour", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))

    form = LoginForm()
    if form.validate_on_submit():
        username_or_email = form.username.data.strip()
        password = form.password.data

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email.lower())
        ).first()

        if user is None:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.is_active_user:
            flash('Tài khoản đã bị vô hiệu hóa.', 'danger')
            return render_template('auth/login.html', form=form)

        if user.is_locked():
            remaining = (user.locked_until - datetime.utcnow()).total_seconds()
            minutes = int(remaining // 60) + 1
            flash(f'Tài khoản bị khóa tạm thời. Vui lòng thử lại sau {minutes} phút.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.check_password(password):
            user.failed_login()
            remaining = (user.locked_until - datetime.utcnow()).total_seconds() if user.is_locked() else 0
            if remaining > 0:
                flash(f'Tài khoản bị khóa tạm thời. Thử lại sau {int(remaining//60)+1} phút.', 'danger')
            else:
                flash(f'Tên đăng nhập hoặc mật khẩu không đúng. ({5 - user.login_attempts} lần thử còn lại)', 'warning')
            return render_template('auth/login.html', form=form)

        user.reset_login_attempts()
        remember = request.form.get('remember') == 'on'
        login_user(user, remember=remember)

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('shop.index'))

    return render_template('auth/login.html', form=form)


@bp.route('/terms')
def terms():
    return render_template('auth/terms.html')


@bp.route('/privacy')
def privacy():
    return render_template('auth/privacy.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công.', 'success')
    return redirect(url_for('shop.index'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = current_user
        if not user.check_password(form.current_password.data):
            flash('Mật khẩu hiện tại không đúng.', 'danger')
            return render_template('auth/change_password.html', form=form)

        user.set_password(form.password.data)
        db.session.commit()
        flash('Đổi mật khẩu thành công!', 'success')
        return redirect(url_for('shop.settings'))

    return render_template('auth/change_password.html', form=form)

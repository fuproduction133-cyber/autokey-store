"""
Script cập nhật mật khẩu admin từ .env.
Chạy: python update_admin_password.py
"""
from app import create_app, db
from app.models import User
import os

app = create_app()

with app.app_context():
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'change-this-password')

    admin = User.query.filter_by(username=admin_username).first()
    if admin:
        admin.set_password(admin_password)
        admin.login_attempts = 0
        admin.locked_until = None
        db.session.commit()
        print(f"Đã cập nhật mật khẩu admin '{admin_username}'")
    else:
        admin = User(username=admin_username, email=f"{admin_username}@admin.local", is_admin=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"Đã tạo admin '{admin_username}'")

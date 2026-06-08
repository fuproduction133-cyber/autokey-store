"""
AutoKey Store - Flask Application Factory
"""
import os
from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()


def create_app(config_name=None):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'), static_folder=os.path.join(base_dir, 'static'))

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32).hex())
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'autokey.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400
    app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECRET_KEY', os.urandom(16).hex())[:16]

    env = os.getenv('FLASK_ENV', 'development')
    is_production = env == 'production'
    if is_production:
        app.config['PREFERRED_URL_SCHEME'] = 'https'

    # Secure cookie - bật khi có HTTPS thật
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() in ('true', '1', 'yes')

    # Rate limiting
    app.config['RATELIMIT_DEFAULT'] = '200/minute'
    app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
    app.config['RATELIMIT_STRATEGY'] = 'fixed-window'
    app.config['RATELIMIT_HEADERS_ENABLED'] = True

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': 'Quá nhiều yêu cầu. Vui lòng thử lại sau.'}), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({'error': 'Lỗi server. Vui lòng thử lại sau.'}), 500

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))

    @app.before_request
    def force_https():
        if is_production and request.scheme != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)

    @app.before_request
    def ensure_admin_exists():
        from app.models import User
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password = os.getenv('ADMIN_PASSWORD')
        if admin_username and admin_password:
            admin = User.query.filter_by(username=admin_username).first()
            if not admin:
                admin = User(username=admin_username, email=f"{admin_username}@admin.local", is_admin=True)
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
            else:
                admin.login_attempts = 0
                admin.locked_until = None
                db.session.commit()

    from app.routes import auth, shop, admin, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(shop.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Download-Options'] = 'noopen'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if is_production:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        return response

    return app

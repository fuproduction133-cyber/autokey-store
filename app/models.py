"""
AutoKey Store - Database Models
"""
from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
import secrets
import string


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    orders = db.relationship('Order', backref='user', lazy='dynamic')

    def set_password(self, password):
        import bcrypt
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def failed_login(self):
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()

    def reset_login_attempts(self):
        self.login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
        db.session.commit()


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    products = db.relationship('Product', backref='category', lazy='dynamic')


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    keys = db.relationship('Key', backref='product', lazy='dynamic')
    orders = db.relationship('Order', backref='product', lazy='dynamic')

    @property
    def available_keys(self):
        return self.keys.filter_by(status='available').count()

    def has_stock(self):
        return self.available_keys > 0


class Key(db.Model):
    __tablename__ = 'keys'

    id = db.Column(db.Integer, primary_key=True)
    key_value = db.Column(db.String(500), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    status = db.Column(db.String(20), default='available')
    sold_at = db.Column(db.DateTime, nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_key(length=20):
        chars = string.ascii_uppercase + string.digits
        return '-'.join(''.join(secrets.choice(chars) for _ in range(5)) for _ in range(4))


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    payment_amount_received = db.Column(db.Integer, default=0)
    vietqr_amount = db.Column(db.Integer, nullable=False)
    vietqr_account_no = db.Column(db.String(50))
    vietqr_transaction_id = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=15))
    completed_at = db.Column(db.DateTime, nullable=True)

    key = db.relationship('Key', backref='order', uselist=False)

    @staticmethod
    def generate_order_code():
        return f"AK{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(9000)+1000}"

    def is_expired(self):
        return datetime.utcnow() > self.expires_at


class PaymentCallback(db.Model):
    __tablename__ = 'payment_callbacks'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    callback_data = db.Column(db.Text)
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# AutoKey Store - Mua bán Key tự động

## Giới thiệu
Trang web mua bán key tự động với thanh toán VietQR. Khách hàng thanh toán qua mã QR, hệ thống tự động gửi key vào tài khoản.

## Tính năng
- Đăng ký / Đăng nhập tài khoản
- Mua key tự động qua VietQR
- Tự động gửi key sau khi thanh toán
- Admin panel quản lý sản phẩm & keys
- Bảo mật cao: rate limiting, CSRF, password hashing, brute-force protection

## Cài đặt

### 1. Tạo môi trường ảo
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình
Tạo file `.env` trong thư mục gốc:
```env
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=development
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
VIETQR_BANK_ID=MBBank
VIETQR_ACCOUNT_NO=1234567890
VIETQR_ACCOUNT_NAME=YOUR_NAME
```

### 4. Khởi tạo database
```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

### 5. Tạo admin user
```bash
flask shell
>>> from app import create_app, db
>>> from app.models import User
>>> app = create_app()
>>> with app.app_context():
...     u = User(username='admin', email='admin@example.com', is_admin=True)
...     u.set_password('your-password')
...     db.session.add(u)
...     db.session.commit()
>>> exit()
```

### 6. Chạy server
```bash
python run.py
```

Mở trình duyệt: http://127.0.0.1:5000

## Cấu trúc thư mục
```
autokey/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── models.py         # Database models
│   ├── routes/           # API routes
│   │   ├── auth.py       # Auth routes
│   │   ├── shop.py       # Shop routes
│   │   └── admin.py      # Admin routes
│   ├── forms.py          # WTForms
│   └── utils.py          # Helpers
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/           # HTML templates
├── instance/             # SQLite DB
├── .env                  # Environment config
└── run.py                # Entry point
```

## Bảo mật
- Rate limiting trên tất cả API endpoints
- Brute-force protection (5 attempts / 15 phút)
- CSRF tokens trên mọi form
- Password hashing với bcrypt
- Session security (httponly, secure cookies)
- Input sanitization & validation
- XSS prevention headers

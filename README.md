# autokey-store
AutoKey Store - Bán key game, phần mềm tự động

## Giới thiệu
Trang web mua bán key tự động với thanh toán VietQR. Khách hàng thanh toán qua mã QR, hệ thống tự động gửi key vào tài khoản.

## Tính năng
- Đăng ký / Đăng nhập tài khoản
- Mua key tự động qua VietQR
- Tự động gửi key sau khi thanh toán
- Admin panel quản lý sản phẩm & keys
- Bảo mật cao: rate limiting, CSRF, password hashing, brute-force protection

## Cài đặt (chạy local)

### 1. Clone repo
```bash
git clone https://github.com/fuproduction133-cyber/autokey-store.git
cd autokey-store
```

### 2. Tạo môi trường ảo
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 4. Cấu hình
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

### 5. Chạy server
```bash
python run.py
```

Mở trình duyệt: http://127.0.0.1:5000

## Deploy lên Render (autokey365.io.vn)

Xem file `DEPLOY_GUIDE.md` để hướng dẫn chi tiết deploy lên Render + custom domain.

## Cấu trúc thư mục
```
autokey/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── models.py         # Database models
│   ├── routes/           # API routes
│   │   ├── auth.py       # Auth routes
│   │   ├── shop.py       # Shop routes
│   │   ├── admin.py      # Admin routes
│   │   └── api.py        # API routes
│   ├── forms.py          # WTForms
│   └── utils/            # Helpers (VietQR)
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/            # HTML templates
├── instance/             # SQLite DB (local)
├── .env                  # Environment config
├── render.yaml           # Render deployment config
├── Dockerfile            # Docker deployment
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

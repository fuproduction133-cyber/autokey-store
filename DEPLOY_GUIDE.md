# Hướng dẫn Deploy lên Render + Domain autokey365.io.vn

## Mục lục
1. [Deploy lên Render từ GitHub](#1-deploy-lên-render-từ-github)
2. [Cấu hình Database PostgreSQL](#2-cấu-hình-database-postgresql)
3. [Cấu hình Environment Variables](#3-cấu-hình-environment-variables)
4. [Custom Domain trên Render](#4-custom-domain-trên-render)
5. [Cấu hình DNS cho autokey365.io.vn](#5-cấu-hình-dns-cho-autokey365iovn)

---

## 1. Deploy lên Render từ GitHub

### Bước 1.1: Tạo tài khoản Render
1. Truy cập [dashboard.render.com](https://dashboard.render.com)
2. Đăng nhập bằng **GitHub** (nhanh nhất)

### Bước 1.2: Tạo Blueprint (dùng render.yaml)
Render sẽ tự động deploy web service và database từ `render.yaml`.

1. Trên Render Dashboard, click **New +** → **Blueprint**
2. Connect repo GitHub `fuproduction133-cyber/autokey-store`
3. Click **Apply Blueprint**
4. Render sẽ tạo:
   - `autokey-store` (Web Service) — Python 3.11, port 5000
   - `autokey-db` (PostgreSQL) — Starter plan miễn phí
5. Click **Save Blueprint**

> **Lưu ý:** `render.yaml` đã được cấu hình sẵn. Không cần tạo thủ công từng service.

---

## 2. Cấu hình Database PostgreSQL

Sau khi Blueprint deploy xong (hoặc dùng render.yaml tự tạo):

1. Vào **Render Dashboard** → **PostgreSQL** → `autokey-db`
2. Copy **Connection String** (có dạng `postgresql://user:password@host:5432/dbname`)
3. Trong Web Service `autokey-store` → **Environment**:
   - Tìm biến `DATABASE_URL`
   - Đảm bảo nó đã được set đúng từ `fromDatabase` trong render.yaml
   - Nếu chưa có, thêm thủ công:
     ```
     DATABASE_URL=postgresql://xxx@xxx:xxx@dpg-xxx.a.postgresql.render.com:5432/autokey_db
     ```

---

## 3. Cấu hình Environment Variables

Trong Web Service `autokey-store` → **Environment** → **Add Environment Variable**:

| Key | Value | Ghi chú |
|-----|-------|---------|
| `FLASK_ENV` | `production` | Bắt buộc |
| `SECRET_KEY` | `secrets.token_hex(32)` (tạo mới) | **Rất quan trọng!** Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_USERNAME` | `admin` | Tuỳ chỉnh |
| `ADMIN_PASSWORD` | `YourStrongPassword123@` | **Đổi ngay** password mạnh |
| `VIETQR_BANK_ID` | `MBBank` | Hoặc ngân hàng bạn dùng |
| `VIETQR_ACCOUNT_NO` | `1234567890` | **Thay số tài khoản thật** |
| `VIETQR_ACCOUNT_NAME` | `NGUYEN VAN A` | **Tên chủ tài khoản thật** |
| `SESSION_COOKIE_SECURE` | `true` | HTTPS bật thì mới `true` |

Sau khi thêm `SECRET_KEY`, click **Deploy** → **Manual Deploy** → **Deploy latest commit**.

---

## 4. Custom Domain trên Render

### Bước 4.1: Cấu hình Custom Domain trên Render
1. Vào Web Service `autokey-store` → **Settings**
2. Kéo xuống **Custom Domains**
3. Click **Add Custom Domain**
4. Nhập: `autokey365.io.vn`
5. Render sẽ hiển thị **CNAME records** cần thêm vào DNS:

```
Type: CNAME
Name: autokey365
Value: autokey-store.onrender.com
TTL: Auto
```

### Bước 4.2: Bật HTTPS (Free Auto SSL)
1. Sau khi thêm domain, click vào domain `autokey365.io.vn`
2. Bật **HTTPS** → Render tự động cấp SSL certificate qua Let's Encrypt

---

## 5. Cấu hình DNS cho autokey365.io.vn

### Nếu dùng Cloudflare (khuyến nghị)
1. Đăng nhập [dash.cloudflare.com](https://dash.cloudflare.com)
2. Chọn domain `autokey365.io.vn`
3. Vào **DNS** → **Records** → **Add record**:

| Type | Name | Target | Proxy |
|------|------|--------|-------|
| CNAME | `autokey365` | `autokey-store.onrender.com` | ✅ Proxied |

> **Quan trọng:** Để Proxy = **Proxied** (orange cloud) để dùng SSL miễn phí của Cloudflare.

### Nếu dùng DNS của nhà đăng ký domain khác
Thêm CNAME record:
```
autokey365  IN  CNAME  autokey-store.onrender.com
```

---

## Kiểm tra sau khi deploy

✅ Truy cập `https://autokey365.io.vn` — web lên
✅ Truy cập `https://autokey365.io.vn/admin` — login admin
✅ Thanh toán VietQR hoạt động
✅ SSL certificate tự động (Render + Cloudflare)

---

## Troubleshooting

### Lỗi "Application failed to start"
- Kiểm tra `DATABASE_URL` đã set đúng chưa
- Kiểm tra `SECRET_KEY` đã có chưa
- Xem **Logs** trong Render để biết lỗi cụ thể

### Database migration
- Chạy lệnh trong Render Shell hoặc trigger redeploy sau khi thêm biến

### HTTPS không hoạt động
- Chờ 5-10 phút sau khi cấu hình DNS
- Đảm bảo Cloudflare Proxy bật
- Render SSL có thể mất vài phút xác thực

---

## Thông tin quan trọng

- **Render Free Tier:** Service ngủ sau 15 phút không dùng, lần đầu truy cập sẽ chậm ~30s (spin up)
- **PostgreSQL Free:** 1GB storage, 250MB RAM
- **HTTPS:** Tự động miễn phí qua Let's Encrypt
- **Custom Domain:** Miễn phí

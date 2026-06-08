"""
AutoKey Store - API Routes
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import limiter, csrf
from app.models import Order, Product
from datetime import datetime

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/products')
def api_products():
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': p.id, 'name': p.name, 'slug': p.slug,
        'price': p.price, 'stock': p.available_keys,
        'image': p.image_url, 'has_stock': p.has_stock()
    } for p in products])


@bp.route('/product/<int:product_id>')
def api_product(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify({
        'id': p.id, 'name': p.name, 'slug': p.slug,
        'description': p.description, 'price': p.price,
        'stock': p.available_keys, 'image': p.image_url,
        'has_stock': p.has_stock()
    })


@bp.route('/order/<order_code>/status')
@login_required
def api_order_status(order_code):
    order = Order.query.filter_by(order_code=order_code, user_id=current_user.id).first_or_404()
    return jsonify({
        'status': order.payment_status,
        'order_code': order.order_code,
        'amount': order.amount,
        'key': order.key.key_value if order.key else None,
        'created_at': order.created_at.isoformat(),
        'expires_at': order.expires_at.isoformat() if order.expires_at else None,
    })


@bp.route('/order/<order_code>/poll-payment')
@login_required
@limiter.limit("30/minute")
def api_poll_payment(order_code):
    order = Order.query.filter_by(order_code=order_code, user_id=current_user.id).first_or_404()
    if order.payment_status == 'completed':
        return jsonify({'status': 'completed', 'key': order.key.key_value if order.key else None})
    elif order.is_expired() and order.payment_status == 'pending':
        order.payment_status = 'expired'
        return jsonify({'status': 'expired'})
    return jsonify({'status': 'pending', 'expires_at': order.expires_at.isoformat()})


@bp.route('/vietqr')
@limiter.exempt
def api_vietqr():
    """Generate VietQR image for a given amount and order."""
    import os
    amount = request.args.get('amount', type=int)
    order_code = request.args.get('order_code', '')

    bank_id = os.getenv('VIETQR_BANK_ID', 'MBBank')
    account_no = os.getenv('VIETQR_ACCOUNT_NO', '')
    account_name = os.getenv('VIETQR_ACCOUNT_NAME', '')

    if not account_no:
        return jsonify({'error': 'VietQR chưa được cấu hình', 'qr_url': None, 'qr_image': None})

    from app.utils.vietqr import VIETQR_BANKS, generate_qr_image
    bank_code = VIETQR_BANKS.get(bank_id, VIETQR_BANKS['MBBank'])['id']

    # Build VietQR deep link
    vietqr_url = (
        f"https://qr-only.vietqr.io/{bank_code}/{account_no}"
        f"?amount={amount}&add_info={order_code}&account_name={account_name}&template=compact"
    )

    # Generate local QR image as fallback
    qr_b64 = generate_qr_image(vietqr_url, size=280)

    return jsonify({
        'qr_url': vietqr_url,
        'qr_image': f"data:image/png;base64,{qr_b64}",
        'bank': bank_id,
        'account_no': account_no[-4:].rjust(len(account_no), '*'),
        'amount': amount,
        'order_code': order_code,
    })


@bp.route('/upload/image', methods=['POST'])
@login_required
@limiter.limit('10/minute')
@csrf.exempt
def api_upload_image():
    """Upload and auto-resize product image."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    import os
    from PIL import Image
    from datetime import datetime as dt
    from werkzeug.utils import secure_filename

    # Validate MIME type from header (not just extension)
    allowed_mimes = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
    file_mime = file.content_type or ''
    if file_mime.lower() not in allowed_mimes:
        return jsonify({'success': False, 'error': 'Loại file không hợp lệ'}), 400

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, 'static', 'uploads', 'products')
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    allowed_ext = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    if ext not in allowed_ext:
        return jsonify({'success': False, 'error': f'Chỉ chấp nhận: {", ".join(allowed_ext)}'}), 400

    # Prevent path traversal
    safe_name = secure_filename(file.filename or 'image')
    safe_base = os.path.splitext(safe_name)[0]
    if not safe_base:
        safe_base = 'image'

    max_w, max_h = 600, 600
    timestamp = dt.now().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}_{safe_base[:40]}.jpg"
    filepath = os.path.join(upload_dir, filename)

    # Prevent overwriting existing files
    if os.path.exists(filepath):
        os.remove(filepath)

    try:
        file.stream.seek(0)
        file.seek(0)
        img = Image.open(file.stream)

        # Verify it's actually a valid image
        img.verify()

        file.stream.seek(0)
        file.seek(0)
        img = Image.open(file.stream)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        w, h = img.size
        if w < 10 or h < 10 or w > 8000 or h > 8000:
            return jsonify({'success': False, 'error': 'Kích thước ảnh không hợp lệ'}), 400

        ratio = min(max_w / w, max_h / h, 1.0)
        if ratio < 1.0:
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        img.save(filepath, 'JPEG', quality=85, optimize=True)

        # File size limit (2MB)
        file_size = os.path.getsize(filepath)
        if file_size > 2 * 1024 * 1024:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'Ảnh quá lớn (tối đa 2MB)'}), 400

        return jsonify({
            'success': True,
            'url': f'/static/uploads/products/{filename}',
            'filename': filename,
        })
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'error': f'Lỗi xử lý ảnh: {str(e)}'}), 500


@bp.route('/process-payment', methods=['POST'])
@limiter.limit("10/minute")
def api_process_payment():
    """Manual payment confirmation endpoint (for webhook/callback integration)."""
    from app import db
    from app.models import Order
    from app.utils.payment import process_order

    data = request.get_json() or {}
    order_code = data.get('order_code', '')
    amount_received = data.get('amount', 0)
    transaction_id = data.get('transaction_id', '')

    order = Order.query.filter_by(order_code=order_code).first()
    if not order:
        return jsonify({'success': False, 'error': 'Order not found'}), 404

    order.payment_amount_received = amount_received
    order.vietqr_transaction_id = transaction_id
    order.paid_at = datetime.utcnow()

    db.session.commit()
    success, message = process_order(order)

    return jsonify({'success': success, 'message': message})

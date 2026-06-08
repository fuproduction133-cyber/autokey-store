"""
AutoKey Store - Payment Processing
"""
from app import db
from app.models import Order, Key
from flask import session
import os


def process_order(order):
    """
    Process a completed order: assign key and mark order as completed.
    Returns (success: bool, message: str)
    """
    if order.payment_status == 'completed':
        return True, 'Đơn hàng đã được xử lý trước đó.'

    if order.payment_status == 'expired':
        return False, 'Đơn hàng đã hết hạn.'

    if order.payment_status == 'cancelled':
        return False, 'Đơn hàng đã bị hủy.'

    available_key = Key.query.filter_by(product_id=order.product_id, status='available').first()

    if not available_key:
        return False, 'Không còn key available. Vui lòng liên hệ admin.'

    available_key.status = 'sold'
    available_key.sold_at = order.paid_at or __import__('datetime').datetime.utcnow()
    available_key.order_id = order.id

    order.payment_status = 'completed'
    order.completed_at = __import__('datetime').datetime.utcnow()
    order.key = available_key

    db.session.commit()

    return True, f'Giao dịch thành công! Key: {available_key.key_value}'


def verify_payment(amount_sent, expected_amount, tolerance_pct=2):
    """
    Verify if the payment amount is within acceptable range.
    Default 2% tolerance for bank transfer variations.
    """
    if amount_sent < expected_amount * (100 - tolerance_pct) / 100:
        return False
    return True


def process_manual_payment(order_code, amount_received, transaction_id=None):
    """Admin manual payment verification."""
    from datetime import datetime
    order = Order.query.filter_by(order_code=order_code).first()
    if not order:
        return False, 'Không tìm thấy đơn hàng.'

    order.payment_amount_received = amount_received
    order.payment_status = 'paid'
    order.paid_at = datetime.utcnow()
    if transaction_id:
        order.vietqr_transaction_id = transaction_id

    db.session.commit()
    success, message = process_order(order)
    return success, message


def generate_payment_page_url(order_code, amount):
    """Generate VietQR payment page URL."""
    bank_id = os.getenv('VIETQR_BANK_ID', 'MBBank')
    account_no = os.getenv('VIETQR_ACCOUNT_NO', '')
    bank_info = __import__('app.utils.vietqr', fromlist=['VIETQR_BANKS']).VIETQR_BANKS.get(bank_id, {})
    bank_code = bank_info.get('id', 'MBVU')

    return (
        f"https://qr-only.vietqr.io/{bank_code}/{account_no}"
        f"?amount={amount}&add_info={order_code}&template=compact"
    )

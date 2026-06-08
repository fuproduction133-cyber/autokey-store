"""
AutoKey Store - VietQR Utilities
"""
import os
import qrcode
import io
import base64
from urllib.parse import urlencode


# VietQR supported banks
VIETQR_BANKS = {
    'MBBank': {'id': 'MBVU', 'name': 'MB Bank'},
    'Vietcombank': {'id': 'VCB', 'name': 'Vietcombank'},
    'VietinBank': {'id': 'ICB', 'name': 'VietinBank'},
    'BIDV': {'id': 'BIDV', 'name': 'BIDV'},
    'Agribank': {'id': 'AGB', 'name': 'Agribank'},
    'TPBank': {'id': 'TPB', 'name': 'TPBank'},
    'Techcombank': {'id': 'TCB', 'name': 'Techcombank'},
    'ACB': {'id': 'ACB', 'name': 'ACB'},
    'MSB': {'id': 'MSB', 'name': 'Maritime Bank'},
    'SHB': {'id': 'SHB', 'name': 'SHB'},
    'Sacombank': {'id': 'STB', 'name': 'Sacombank'},
    'Eximbank': {'id': 'EIB', 'name': 'Eximbank'},
    'SeABank': {'id': 'SSB', 'name': 'SeABank'},
    'VPBank': {'id': 'VPB', 'name': 'VPBank'},
    'HDBank': {'id': 'HDB', 'name': 'HD Bank'},
    'OCB': {'id': 'OCB', 'name': 'OCB'},
    'PVCombank': {'id': 'PVC', 'name': 'PVCombank'},
    'ShinhanBank': {'id': 'SHBVN', 'name': 'Shinhan Bank'},
    'UOB': {'id': 'UOB', 'name': 'UOB'},
    'StandardChartered': {'id': 'SCBVN', 'name': 'Standard Chartered'},
}


def get_default_bank():
    return {
        'bank_id': os.getenv('VIETQR_BANK_ID', 'MBBank'),
        'account_no': os.getenv('VIETQR_ACCOUNT_NO', ''),
        'account_name': os.getenv('VIETQR_ACCOUNT_NAME', ''),
    }


def generate_qr_url(amount, order_code, account_no=None, account_name=None, bank_id=None):
    """
    Generate VietQR URL for payment.
    amount: int (VND)
    order_code: str
    """
    bank_id = bank_id or os.getenv('VIETQR_BANK_ID', 'MBBank')
    account_no = account_no or os.getenv('VIETQR_ACCOUNT_NO', '')
    account_name = account_name or os.getenv('VIETQR_ACCOUNT_NAME', '')

    if bank_id not in VIETQR_BANKS:
        bank_id = 'MBBank'

    bank_code = VIETQR_BANKS[bank_id]['id']

    qr_content = f"00020101021138{bank_code}00{account_no}0206{order_code}030704090000{amount}05400105VietQR00000000000000"

    params = {
        'accountName': account_name,
        'accountNo': account_no,
        'acqId': bank_code,
        'amount': str(amount),
        'addInfo': order_code,
        'format': 'text',
        'template': 'compact',
    }

    vietqr_url = f"https://api.vietqr.io/v2/{bank_code.lower()}/{account_no}/generate-qr-code"

    return vietqr_url, params


def generate_qr_image(data_url, size=280):
    """
    Generate QR code image from VietQR API URL.
    Returns base64 encoded PNG.
    """
    try:
        import requests
        resp = requests.post(
            data_url,
            json={
                'accountNo': '',
                'accountName': '',
                'acqId': '',
                'amount': 0,
                'addInfo': '',
                'format': 'text',
                'template': 'compact',
            },
            timeout=10
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get('code') == '00':
                data = result['data']['qrDataURL']
                return data
    except Exception:
        pass

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def generate_vietqr_url_direct(amount, order_code):
    """
    Generate VietQR deep link URL for direct bank app scanning.
    """
    bank_id = os.getenv('VIETQR_BANK_ID', 'MBBank')
    account_no = os.getenv('VIETQR_ACCOUNT_NO', '')
    account_name = os.getenv('VIETQR_ACCOUNT_NAME', '')

    bank_code = VIETQR_BANKS.get(bank_id, VIETQR_BANKS['MBBank'])['id']

    vietqr_io_url = (
        f"https://qr-only.vietqr.io/{bank_code}/{account_no}"
        f"?amount={amount}&add_info={order_code}&account_name={account_name}"
    )

    return vietqr_io_url


def format_price(amount):
    """Format price to VND string."""
    return f"{amount:,}".replace(",", ".") + " VND"

"""
AutoKey Store - Shop Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from app import db
from app.models import Product, Order, Key, Category
from app.utils import vietqr
from datetime import datetime

bp = Blueprint('shop', __name__, url_prefix='')


@bp.route('/')
def index():
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    products = Product.query.filter_by(is_active=True).order_by(Product.id.desc()).all()
    return render_template('shop/index.html', products=products, categories=categories)


@bp.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    return render_template('shop/product.html', product=product, related=related)


@bp.route('/category/<slug>')
def category(slug):
    cat = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    products = Product.query.filter_by(category_id=cat.id, is_active=True).order_by(Product.id.desc()).all()
    return render_template('shop/category.html', category=cat, products=products, categories=categories)


@bp.route('/buy/<int:product_id>', methods=['GET', 'POST'])
@login_required
def buy(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()

    if not product.has_stock():
        flash('Sản phẩm hiện đang hết hàng.', 'danger')
        return redirect(url_for('shop.product_detail', slug=product.slug))

    existing = Order.query.filter_by(
        user_id=current_user.id, product_id=product_id, payment_status='pending'
    ).filter(Order.expires_at > datetime.utcnow()).first()

    if existing:
        return render_template('shop/checkout.html', order=existing, product=product,
                               qr_url=existing.vietqr_amount)

    order = Order(
        order_code=Order.generate_order_code(),
        user_id=current_user.id,
        product_id=product.id,
        amount=product.price,
        vietqr_amount=product.price,
    )
    db.session.add(order)
    db.session.commit()

    qr_data = vietqr.generate_qr_url(
        amount=product.price,
        order_code=order.order_code,
        account_no=session.get('vietqr_account_no'),
        account_name=session.get('vietqr_account_name'),
        bank_id=session.get('vietqr_bank_id', 'MBBank'),
    )

    return render_template('shop/checkout.html', order=order, product=product, qr_data=qr_data)


@bp.route('/order/<order_code>')
@login_required
def order_detail(order_code):
    order = Order.query.filter_by(order_code=order_code, user_id=current_user.id).first_or_404()
    return render_template('shop/order.html', order=order)


@bp.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('shop/my_orders.html', orders=orders)


@bp.route('/check-payment/<order_code>')
@login_required
def check_payment(order_code):
    order = Order.query.filter_by(order_code=order_code, user_id=current_user.id).first_or_404()
    return {
        'status': order.payment_status,
        'order_code': order.order_code,
        'amount': order.amount,
    }


@bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    if q:
        products = Product.query.filter(
            Product.is_active == True,
            Product.name.ilike(f'%{q}%')
        ).all()
    else:
        products = Product.query.filter_by(is_active=True).order_by(Product.id.desc()).all()
    return render_template('shop/index.html', products=products, categories=categories, search_q=q)


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if session.get('vietqr_bank_id'):
        bank_id = session['vietqr_bank_id']
    else:
        import os
        bank_id = os.getenv('VIETQR_BANK_ID', 'MBBank')

    return render_template('shop/settings.html', bank_id=bank_id)

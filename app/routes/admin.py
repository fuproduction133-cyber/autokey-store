"""
AutoKey Store - Admin Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from functools import wraps
from app import db, limiter
from app.models import User, Product, Category, Key, Order
from app.forms import ProductForm, CategoryForm, KeyAddForm, ManualOrderForm
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('shop.index'))
        return f(*args, **kwargs)
    return decorated


@bp.route('/')
@limiter.limit('60/minute')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_orders = Order.query.count()
    completed_orders = Order.query.filter_by(payment_status='completed').count()
    pending_orders = Order.query.filter_by(payment_status='pending').count()
    total_products = Product.query.count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    stats = {
        'total_revenue': sum(o.amount for o in Order.query.filter_by(payment_status='completed').all()),
        'today_revenue': sum(o.amount for o in Order.query.filter(
            Order.payment_status == 'completed',
            Order.paid_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).all()),
        'out_of_stock': Product.query.filter(Product.stock <= 0, Product.is_active == True).count(),
    }

    return render_template('admin/dashboard.html',
                           total_users=total_users, total_orders=total_orders,
                           completed_orders=completed_orders, pending_orders=pending_orders,
                           total_products=total_products, recent_orders=recent_orders,
                           stats=stats, now=datetime.utcnow())


@bp.route('/products')
@admin_required
def products():
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('admin/products.html', products=products)


@bp.route('/products/add', methods=['GET', 'POST'])
@limiter.limit('30/minute')
@admin_required
def add_product():
    form = ProductForm()
    if request.method == 'GET':
        form.is_active.data = True
    categories = [(0, '-- Không chọn --')] + [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    form.category_id.choices = categories

    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if Product.query.filter_by(slug=slug).first():
            flash('Slug đã tồn tại.', 'danger')
            return render_template('admin/product_form.html', form=form, action='Thêm sản phẩm')

        product = Product(
            name=form.name.data.strip(),
            slug=slug,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            image_url=request.form.get('image_url', ''),
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()

        for i in range(form.stock.data):
            key = Key(key_value=Key.generate_key(), product_id=product.id)
            db.session.add(key)
        db.session.commit()

        flash('Thêm sản phẩm thành công!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', form=form, action='Thêm sản phẩm')


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    categories = [(0, '-- Không chọn --')] + [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    form.category_id.choices = categories

    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        existing = Product.query.filter(Product.slug == slug, Product.id != product_id).first()
        if existing:
            flash('Slug đã tồn tại.', 'danger')
            return render_template('admin/product_form.html', form=form, action='Sửa sản phẩm', product=product)

        product.name = form.name.data.strip()
        product.slug = slug
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.category_id = form.category_id.data if form.category_id.data != 0 else None
        product.image_url = request.form.get('image_url', '')
        # is_active giữ nguyên không cần checkbox
        db.session.commit()

        diff = form.stock.data - Key.query.filter_by(product_id=product.id, status='available').count()
        if diff > 0:
            for i in range(diff):
                key = Key(key_value=Key.generate_key(), product_id=product.id)
                db.session.add(key)
            db.session.commit()
        elif diff < 0:
            keys_to_delete = Key.query.filter_by(product_id=product.id, status='available').limit(abs(diff)).all()
            for k in keys_to_delete:
                db.session.delete(k)
            db.session.commit()

        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', form=form, action='Sửa sản phẩm', product=product)


@bp.route('/products/<int:product_id>/delete')
@limiter.limit('20/minute')
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Xóa sản phẩm thành công.', 'success')
    return redirect(url_for('admin.products'))


@bp.route('/products/<int:product_id>/keys', methods=['GET', 'POST'])
@admin_required
def manage_keys(product_id):
    product = Product.query.get_or_404(product_id)
    form = KeyAddForm()
    keys = Key.query.filter_by(product_id=product_id).order_by(Key.id.desc()).all()

    if form.validate_on_submit():
        lines = [l.strip() for l in form.keys_text.data.strip().split('\n') if l.strip()]
        count = 0
        for line in lines:
            key = Key(key_value=line, product_id=product.id)
            db.session.add(key)
            count += 1
        product.stock = Key.query.filter_by(product_id=product.id, status='available').count() + \
                        (Key.query.filter_by(product_id=product.id, status='sold').count() -
                         Key.query.filter_by(product_id=product.id, status='sold').filter(
                             Key.order_id.in_([o.id for o in Order.query.filter_by(payment_status='refunded').all()]
                         )).count())
        db.session.commit()
        product.stock = Key.query.filter_by(product_id=product.id, status='available').count()
        db.session.commit()
        flash(f'Thêm {count} keys thành công!', 'success')
        return redirect(url_for('admin.manage_keys', product_id=product_id))

    return render_template('admin/keys.html', product=product, keys=keys, form=form)


@bp.route('/categories')
@admin_required
def categories():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=categories)


@bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if Category.query.filter_by(slug=slug).first():
            flash('Slug đã tồn tại.', 'danger')
            return render_template('admin/category_form.html', form=form, action='Thêm danh mục')

        cat = Category(
            name=form.name.data.strip(),
            slug=slug,
            description=form.description.data,
            is_active=form.is_active.data,
            sort_order=form.sort_order.data or 0,
        )
        db.session.add(cat)
        db.session.commit()
        flash('Thêm danh mục thành công!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', form=form, action='Thêm danh mục')


@bp.route('/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        existing = Category.query.filter(Category.slug == slug, Category.id != cat_id).first()
        if existing:
            flash('Slug đã tồn tại.', 'danger')
            return render_template('admin/category_form.html', form=form, action='Sửa danh mục', category=cat)

        cat.name = form.name.data.strip()
        cat.slug = slug
        cat.description = form.description.data
        cat.is_active = form.is_active.data
        cat.sort_order = form.sort_order.data or 0
        db.session.commit()
        flash('Cập nhật danh mục thành công!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', form=form, action='Sửa danh mục', category=cat)


@bp.route('/categories/<int:cat_id>/delete')
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash('Xóa danh mục thành công.', 'success')
    return redirect(url_for('admin.categories'))


@bp.route('/orders')
@admin_required
def orders():
    status = request.args.get('status')
    if status:
        orders = Order.query.filter_by(payment_status=status).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders, filter_status=status)


@bp.route('/orders/<int:order_id>/manual-complete')
@admin_required
def manual_complete(order_id):
    from app.utils.payment import process_order
    order = Order.query.get_or_404(order_id)
    success, message = process_order(order)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.orders'))


@bp.route('/users')
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@bp.route('/users/<int:user_id>/toggle-status')
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Không thể thay đổi trạng thái admin.', 'danger')
    else:
        user.is_active_user = not user.is_active_user
        db.session.commit()
        flash(f'Trạng thái người dùng đã được cập nhật.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng.', 'danger')
        else:
            user = User(username=username, email=email, is_admin=request.form.get('is_admin') == 'on')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'Tạo tài khoản "{username}" thành công!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', action='Tạo người dùng')


@bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Không thể reset mật khẩu admin.', 'danger')
        return redirect(url_for('admin.users'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password:
            flash('Mật khẩu mới không được để trống.', 'danger')
            return render_template('admin/reset_password.html', user=user)

        if new_password != confirm_password:
            flash('Mật khẩu xác nhận không khớp.', 'danger')
            return render_template('admin/reset_password.html', user=user)

        user.set_password(new_password)
        user.reset_login_attempts()
        db.session.commit()
        flash(f'Đã reset mật khẩu cho "{user.username}".', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/reset_password.html', user=user)

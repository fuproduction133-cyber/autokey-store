"""
AutoKey Store - Entry Point
"""
from app import create_app, db
from app.models import User, Product, Category, Key, Order
import os

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@autokey.local', is_admin=True)
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'change-me-immediately'))
            db.session.add(admin)
            db.session.commit()
            print('[AutoKey] Admin user created from ADMIN_PASSWORD env var.')

        if not Category.query.first():
            cats = [
                Category(name='Game Keys', slug='game-keys', description='Product Keys cho game', sort_order=1),
                Category(name='Phần mềm', slug='software', description='License phần mềm', sort_order=2),
                Category(name='Dịch vụ', slug='service', description='Dịch vụ số', sort_order=3),
            ]
            for c in cats:
                db.session.add(c)
            db.session.commit()

        if not Product.query.first():
            cat = Category.query.filter_by(slug='game-keys').first()
            sample_products = [
                {
                    'name': 'Steam Wallet 100,000 VND',
                    'slug': 'steam-wallet-100k',
                    'description': 'Gift Card Steam Wallet 100,000 VND. Giao key tự động ngay sau khi thanh toán.',
                    'price': 100000,
                    'stock': 50,
                    'image_url': 'https://cdn-icons-png.flaticon.com/512/5968/5968853.png',
                },
                {
                    'name': 'Steam Wallet 200,000 VND',
                    'slug': 'steam-wallet-200k',
                    'description': 'Gift Card Steam Wallet 200,000 VND. Giao key tự động ngay sau khi thanh toán.',
                    'price': 200000,
                    'stock': 30,
                    'image_url': 'https://cdn-icons-png.flaticon.com/512/5968/5968853.png',
                },
                {
                    'name': 'Spotify Premium 1 Tháng',
                    'slug': 'spotify-premium-1-thang',
                    'description': 'Tài khoản Spotify Premium 1 tháng. Giao key tự động qua email.',
                    'price': 35000,
                    'stock': 100,
                    'image_url': 'https://cdn-icons-png.flaticon.com/512/2111/2111624.png',
                },
                {
                    'name': 'Netflix Premium 1 Tháng',
                    'slug': 'netflix-premium-1-thang',
                    'description': 'Tài khoản Netflix Premium HD. Giao key tự động ngay sau thanh toán.',
                    'price': 85000,
                    'stock': 20,
                    'image_url': 'https://cdn-icons-png.flaticon.com/512/5977/5977591.png',
                },
            ]
            for p in sample_products:
                prod = Product(category_id=cat.id, **p, is_active=True)
                db.session.add(prod)
                db.session.commit()
                for i in range(p['stock']):
                    k = Key(key_value=Key.generate_key(), product_id=prod.id)
                    db.session.add(k)
                db.session.commit()
            print('[AutoKey] Sample products created.')

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    print(f'[AutoKey] Starting server on http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=debug)

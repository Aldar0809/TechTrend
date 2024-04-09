import os
from collections import Counter
from flask import abort, render_template, redirect, url_for, request, session, flash, send_file, send_from_directory
from sqlalchemy.exc import IntegrityError
from .extensions import app, db
from .models import Product, Category, Brand, Order, OrderItem
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from .models import User, Review
from datetime import datetime
from pdf_check import generate_invoice_pdf
from werkzeug.security import generate_password_hash, check_password_hash

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def custom_date_format(date):
    now = datetime.now()
    if date.year != now.year:
        return date.strftime('%d %B %Y')
    else:
        return date.strftime('%d %B')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/about_us')
def about_us():
    cart_count = len(session.get('cart', []))
    return render_template('about_us.html', cart_count=cart_count)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Пользователь с таким email адресом уже существует.', 'error')
            # Пользователь с таким email уже существует
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Учетной записи с этими данными не существует.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    cart_count = len(session.get('cart', []))
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')

        # Обновляем имя и email пользователя, если они были изменены
        if new_name and new_name != current_user.name:
            current_user.name = new_name
        if new_email and new_email != current_user.email:
            current_user.email = new_email

        db.session.commit()
        flash('Информация о пользователе успешно обновлена.', 'success')
        return redirect(url_for('account'))

    return render_template('account.html', cart_count=cart_count)


@app.route('/')
def index():
    category_id = request.args.get('category')
    brand_id = request.args.get('brand')

    products_query = Product.query

    if category_id:
        products_query = products_query.filter_by(category_id=category_id)
    if brand_id:
        products_query = products_query.filter_by(brand_id=brand_id)

    products = products_query.all()

    # Получить количество товаров в корзине из сессии
    cart_count = len(session.get('cart', []))

    # Получить список всех категорий и брендов для фильтров
    categories = Category.query.all()
    brands = Brand.query.all()

    return render_template('index.html', cart_count=cart_count, products=products, categories=categories, brands=brands)


@login_required
@app.route('/products')
def product_list():
    if current_user.role != 'admin':
        abort(403)
    products = Product.query.all()
    return render_template('product_list.html', products=products)


@login_required
@app.route('/product/create_product', methods=['GET', 'POST'])
def create_product():
    if current_user.role != 'admin':
        abort(403)
    elif request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        category_id = request.form['category']
        brand_id = request.form['brand']
        image = request.form['image']

        product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            brand_id=brand_id,
            image=image
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('product_list'))

    categories = Category.query.all()
    brands = Brand.query.all()
    return render_template('product_form.html', categories=categories, brands=brands)


@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    cart_count = len(session.get('cart', []))
    product = Product.query.get_or_404(product_id)
    if not product:
        abort(404)
    if request.method == 'POST':
        comment = request.form['comment']
        if comment:
            review = Review(comment=comment, product_id=product_id)
            db.session.add(review)
            db.session.commit()
            return redirect(url_for('product_detail', product_id=product_id))
    return render_template('product_detail.html', product=product, cart_count=cart_count)


@login_required
@app.route('/add_review', methods=['POST'])
def add_review():
    if current_user.is_authenticated:
        product_id = request.form.get('product_id')
        text = request.form.get('comment')
        user_id = current_user.id
        if text:
            review = Review(text=text, product_id=product_id, user_id=user_id)
            db.session.add(review)
            db.session.commit()
            return redirect(url_for('product_detail', product_id=product_id))
    # В случае, если пользователь не аутентифицирован, вы можете перенаправить его на страницу входа
    flash('Вы должны войти, чтобы оставить отзыв.', 'error')
    return redirect(url_for('login'))


@login_required
@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    if current_user.role != 'admin':
        abort(403)
    product = Product.query.get(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = request.form['price']
        product.category_id = request.form['category']
        product.brand_id = request.form['brand']
        product.image = request.form['image']
        db.session.commit()
        return redirect(url_for('product_list'))

    categories = Category.query.all()
    brands = Brand.query.all()
    return render_template('product_form.html', product=product, categories=categories, brands=brands)


@login_required
@app.route('/product/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    if current_user.role != 'admin':
        abort(403)
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Продукт успешно удален', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Не удается удалить товар, поскольку он связан с существующими заказами.', 'error')
    return redirect(url_for('product_list'))


@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get('product_id')
    if product_id:
        cart = session.get('cart', [])
        if int(product_id) in cart:
            cart.remove(int(product_id))
            session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        action = request.form.get('action')
        if product_id and action:
            product = Product.query.get(product_id)
            if action == 'add':
                cart = session.get('cart', [])
                cart.append(product.id)
                session['cart'] = cart
            elif action == 'remove':
                cart = session.get('cart', [])
                if product.id in cart:
                    cart.remove(product.id)
                    session['cart'] = cart
    cart_ids = session.get('cart', [])
    cart_items = Counter(cart_ids)
    products = Product.query.filter(Product.id.in_(cart_items.keys())).all()
    for product in products:
        product.quantity = cart_items[product.id]
    return render_template('cart.html', cart_items=products)


@login_required
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # Получение информации о доставке и оплате
        customer_name = request.form.get('customer_name')
        customer_address = request.form.get('customer_address')
        payment_method = request.form.get('payment_method')

        # Проверка наличия товаров в корзине
        cart = session.get('cart', [])
        if not cart:
            flash('Корзина пуста. Добавьте товары перед оформлением заказа.', 'warning')
            return redirect(url_for('cart'))

        # Создание нового заказа
        order = Order(
            user=current_user,
            customer_name=customer_name,
            customer_address=customer_address,
            payment_method=payment_method
        )
        db.session.add(order)

        # Добавление товаров из корзины в заказ
        for product_id in cart:
            product = Product.query.get(product_id)
            order_item = OrderItem(
                order=order,
                product=product,
                quantity=1  # Можно добавить логику для количества
            )
            db.session.add(order_item)

        db.session.commit()
        session['cart'] = []
        return redirect(url_for('order_confirmation', order_id=order.id))

    return render_template('checkout.html')


@login_required
@app.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    cart_count = len(session.get('cart', []))
    order = Order.query.get(order_id)
    if order.user_id != current_user.id:
        abort(404)
    return render_template('order_confirmation.html', order=order, cart_count=cart_count)


@app.route('/orders')
@login_required
def order_list():
    cart_count = len(session.get('cart', []))
    orders = current_user.orders  # Получаем заказы текущего пользователя
    role = False
    if current_user.role == 'admin':
        orders = Order.query.all()
        role = True
    return render_template('order_list.html', orders=orders, cart_count=cart_count, role=role)


@login_required
@app.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    if current_user.is_authenticated:
        order = Order.query.get(order_id)
        if order.user_id == current_user.id:
            if order:
                order.status = 'Отменен'
                db.session.commit()
                flash('Заказ успешно отменен.', 'success')
            else:
                flash('Заказ не найден.', 'danger')
            return redirect(url_for('order_list'))
        else:
            abort(404)
    abort(404)


@login_required
@app.route('/order/<int:order_id>')
def order_details(order_id):
    try:
        role = False
        if current_user.role == 'admin':
            role = True
        if current_user.is_authenticated:
            order = Order.query.get(order_id)
            cart_count = len(session.get('cart', []))
            if order.user_id != current_user.id and role is False:
                abort(404)
            return render_template('order_details.html', order=order, cart_count=cart_count, role=role)
        abort(404)
    except AttributeError:
        abort(404)


@app.route('/order/<int:order_id>/change_status', methods=['POST'])
@login_required
def change_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('new_status')
    order.status = new_status
    db.session.commit()
    return redirect(url_for('order_details', order_id=order_id))


# Обработка ошибки 404 (Page Not Found)
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# Обработка ошибки 403 (Access Denied)
@app.errorhandler(403)
def access_denied(error):
    return render_template('403.html'), 403


@login_required
@app.route('/generate_invoice/<int:order_id>')
def generate_invoice(order_id):
    order = Order.query.get(order_id)
    if current_user.is_authenticated and order.user_id != current_user.id:
        # Создайте PDF счета
        pdf_file = generate_invoice_pdf(order)
        # Отправьте файл пользователю
        directory = os.path.dirname(os.path.abspath(pdf_file))
        filename = os.path.basename(pdf_file)
        return send_from_directory(directory, filename, as_attachment=True)
    abort(404)


app.jinja_env.filters['custom_date_format'] = custom_date_format

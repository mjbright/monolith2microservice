#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange, Length
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os,sys

PORT=5000
if len(sys.argv) > 1:
    PORT=sys.argv[1]

import socket, platform

image = os.getenv('CONTAINER_IMAGE', '')

opsystem = platform.system()
#print(opsystem)
match opsystem:
    case "Linux":
        serverhost=socket.gethostname()
        serverip=socket.gethostbyname(socket.gethostname())
    case "Darwin":
        serverhost=socket.gethostname()
        serverip=[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.
SOCK_DGRAM)]][0][1]
    case _:
        print(f'Unknown OS type {opsystem}')
        sys.exit(1)

## -- COLORS: --------------------------------------------------------------------------------
BLACK = "\033[0;30m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
BROWN = "\033[0;33m"
BLUE = "\033[0;34m"
PURPLE = "\033[0;35m"
CYAN = "\033[0;36m"
LIGHT_GRAY = "\033[0;37m"
DARK_GRAY = "\033[1;30m"
LIGHT_RED = "\033[1;31m"
LIGHT_GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
LIGHT_BLUE = "\033[1;34m"
LIGHT_PURPLE = "\033[1;35m"
LIGHT_CYAN = "\033[1;36m"
LIGHT_WHITE = "\033[1;37m"
BOLD = "\033[1m"
FAINT = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
NEGATIVE = "\033[7m"
CROSSED = "\033[9m"
END = "\033[0m"
## -- COLORS: --------------------------------------------------------------------------------


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///online_shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(UserMixin, db.Model):
    """User model for authentication and customer management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

class Category(db.Model):
    """Product categories for catalog organization"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    """Product catalog model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    image_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True)

class CartItem(db.Model):
    """Shopping cart items"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    """Order management"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text, nullable=False)
    billing_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    """Individual items in an order"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

class StockMovement(db.Model):
    """Stock control and inventory tracking"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)  # 'in', 'out', 'adjustment'
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))
    reference_id = db.Column(db.Integer)  # Could reference order_id for sales
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

# ============================================================================
# FORMS
# ============================================================================

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int)
    image_url = StringField('Image URL')
    submit = SubmitField('Save Product')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Category')

class CheckoutForm(FlaskForm):
    shipping_address = TextAreaField('Shipping Address', validators=[DataRequired()])
    billing_address = TextAreaField('Billing Address', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', 
                                choices=[('credit_card', 'Credit Card'), 
                                        ('paypal', 'PayPal'), 
                                        ('bank_transfer', 'Bank Transfer')])
    submit = SubmitField('Place Order')

# ============================================================================
# LOGIN MANAGER
# ============================================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================================
# BUSINESS LOGIC SERVICES (Designed for future microservice separation)
# ============================================================================

class CatalogService:
    """Catalog management service"""

    @staticmethod
    def get_all_products(category_id=None, active_only=True):
        query = Product.query
        if active_only:
            query = query.filter_by(is_active=True)
        if category_id:
            query = query.filter_by(category_id=category_id)
        return query.all()

    @staticmethod
    def get_product_by_id(product_id):
        return Product.query.get(product_id)

    @staticmethod
    def search_products(search_term):
        return Product.query.filter(
            Product.name.contains(search_term) | 
            Product.description.contains(search_term)
        ).filter_by(is_active=True).all()

    @staticmethod
    def get_categories():
        return Category.query.all()

class StockService:
    """Stock control service"""

    @staticmethod
    def check_availability(product_id, quantity):
        product = Product.query.get(product_id)
        return product and product.stock_quantity >= quantity

    @staticmethod
    def reserve_stock(product_id, quantity, reason="Order placement", reference_id=None):
        product = Product.query.get(product_id)
        if product and product.stock_quantity >= quantity:
            product.stock_quantity -= quantity

            # Record stock movement
            movement = StockMovement(
                product_id=product_id,
                movement_type='out',
                quantity=quantity,
                reason=reason,
                reference_id=reference_id
            )
            db.session.add(movement)
            db.session.commit()
            return True
        return False

    @staticmethod
    def add_stock(product_id, quantity, reason="Stock replenishment"):
        product = Product.query.get(product_id)
        if product:
            product.stock_quantity += quantity

            # Record stock movement
            movement = StockMovement(
                product_id=product_id,
                movement_type='in',
                quantity=quantity,
                reason=reason
            )
            db.session.add(movement)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_stock_movements(product_id=None):
        query = StockMovement.query
        if product_id:
            query = query.filter_by(product_id=product_id)
        return query.order_by(StockMovement.created_at.desc()).all()

class CartService:
    """Shopping cart service"""

    @staticmethod
    def add_to_cart(user_id, product_id, quantity=1):
        existing_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

        if existing_item:
            existing_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)

        db.session.commit()
        return True

    @staticmethod
    def get_cart_items(user_id):
        return CartItem.query.filter_by(user_id=user_id).all()

    @staticmethod
    def update_cart_item(user_id, product_id, quantity):
        cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
        if cart_item:
            if quantity <= 0:
                db.session.delete(cart_item)
            else:
                cart_item.quantity = quantity
            db.session.commit()
            return True
        return False

    @staticmethod
    def clear_cart(user_id):
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()

    @staticmethod
    def get_cart_total(user_id):
        cart_items = CartService.get_cart_items(user_id)
        total = 0
        for item in cart_items:
            total += item.product.price * item.quantity
        return total

class BillingService:
    """Billing and order management service"""

    @staticmethod
    def create_order(user_id, shipping_address, billing_address, payment_method):
        cart_items = CartService.get_cart_items(user_id)

        if not cart_items:
            return None, "Cart is empty"

        # Calculate total
        total_amount = 0
        order_items_data = []

        for cart_item in cart_items:
            if not StockService.check_availability(cart_item.product_id, cart_item.quantity):
                return None, f"Insufficient stock for {cart_item.product.name}"

            item_total = cart_item.product.price * cart_item.quantity
            total_amount += item_total

            order_items_data.append({
                'product_id': cart_item.product_id,
                'quantity': cart_item.quantity,
                'unit_price': cart_item.product.price,
                'total_price': item_total
            })

        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment_method=payment_method
        )
        db.session.add(order)
        db.session.flush()  # Get order ID

        # Create order items and reserve stock
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.session.add(order_item)

            # Reserve stock
            StockService.reserve_stock(
                item_data['product_id'], 
                item_data['quantity'], 
                f"Order #{order.id}",
                order.id
            )

        # Clear cart
        CartService.clear_cart(user_id)

        db.session.commit()
        return order, None

    @staticmethod
    def get_user_orders(user_id):
        return Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order_by_id(order_id):
        return Order.query.get(order_id)

    @staticmethod
    def update_order_status(order_id, status):
        order = Order.query.get(order_id)
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def update_payment_status(order_id, payment_status):
        order = Order.query.get(order_id)
        if order:
            order.payment_status = payment_status
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

# ============================================================================
# ROUTES - FRONTEND STORE
# ============================================================================

## -- START OF asciitext hack for wget/curl requests --------------------------------------------------

def ascii(url):
    #print(f'url={url}')
    ret = ''
    if not url.endswith(f':{PORT}/1'):
        ret = readfile('static/img/store.txt')

    sourceip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    now = datetime.now(timezone.utc)
    statusline = f'[{now}] Request from {sourceip} to {serverhost}/{serverip}:{PORT}\n'
    if image != '':
        color=''
        end=''
        if 'v1' in image: color=CYAN
        if 'v2' in image: color=GREEN
        if 'v3' in image: color=RED
        if color != '':   end=END
        statusline = f'[{color}{image}{END}] {statusline}{end}'

    ret += statusline
    print(statusline)
    return ret

## -- END   OF asciitext hack for wget/curl requests --------------------------------------------------

@app.route('/1')
def statusLine():
    return ascii(request.base_url)

@app.route('/')
def index():
    ua = request.headers.get('User-Agent').lower()
    print(ua)
    if 'curl/' in ua or 'wget/' in ua or 'httpie/' in ua:
        return ascii(request.base_url)

    """Homepage with featured products"""
    products = CatalogService.get_all_products()
    categories = CatalogService.get_categories()
    return render_template('index.html', products=products, categories=categories)

def readfile(path, mode='r'):
    ifd = open(path, mode)
    ret=ifd.read()
    ifd.close()
    return ret

#@app.route('/style/custom.css')
#def style():
#    return readfile('style/custom.css')

@app.route('/products')
def products():
    """Product listing page"""
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')

    if search:
        products = CatalogService.search_products(search)
    else:
        products = CatalogService.get_all_products(category_id)

    categories = CatalogService.get_categories()
    return render_template('products.html', products=products, categories=categories, 
                         selected_category=category_id, search=search)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = CatalogService.get_product_by_id(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products'))
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart"""
    quantity = int(request.form.get('quantity', 1))

    if not StockService.check_availability(product_id, quantity):
        flash('Insufficient stock available', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

    CartService.add_to_cart(current_user.id, product_id, quantity)
    flash('Product added to cart', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    """Shopping cart page"""
    cart_items = CartService.get_cart_items(current_user.id)
    total = CartService.get_cart_total(current_user.id)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
@login_required
def update_cart():
    """Update cart item quantities"""
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity'))

    CartService.update_cart_item(current_user.id, product_id, quantity)
    flash('Cart updated', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process"""
    form = CheckoutForm()

    if form.validate_on_submit():
        order, error = BillingService.create_order(
            current_user.id,
            form.shipping_address.data,
            form.billing_address.data,
            form.payment_method.data
        )

        if order:
            flash(f'Order #{order.id} placed successfully!', 'success')
            return redirect(url_for('order_confirmation', order_id=order.id))
        else:
            flash(error, 'error')

    cart_items = CartService.get_cart_items(current_user.id)
    total = CartService.get_cart_total(current_user.id)

    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))

    return render_template('checkout.html', form=form, cart_items=cart_items, total=total)

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = BillingService.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        flash('Order not found', 'error')
        return redirect(url_for('index'))
    return render_template('order_confirmation.html', order=order)

@app.route('/my_orders')
@login_required
def my_orders():
    """User's order history"""
    orders = BillingService.get_user_orders(current_user.id)
    return render_template('my_orders.html', orders=orders)

# ============================================================================
# ROUTES - AUTHENTICATION
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    form = RegisterForm()

    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'error')
            return render_template('register.html', form=form)

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('register.html', form=form)

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ============================================================================
# ROUTES - ADMIN PANEL (Backend Management)
# ============================================================================

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    # Dashboard statistics
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders)

@app.route('/admin/products')
@login_required
def admin_products():
    """Admin product management"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    """Add new product"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock_quantity=form.stock_quantity.data,
            category_id=form.category_id.data,
            image_url=form.image_url.data
        )
        db.session.add(product)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', form=form, title='Add Product')

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    """Edit existing product"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()

        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', form=form, title='Edit Product')

@app.route('/admin/categories')
@login_required
def admin_categories():
    """Admin category management"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/category/add', methods=['GET', 'POST'])
@login_required
def admin_add_category():
    """Add new category"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()

        flash('Category added successfully!', 'success')
        return redirect(url_for('admin_categories'))

    return render_template('admin/category_form.html', form=form, title='Add Category')

@app.route('/admin/orders')
@login_required
def admin_orders():
    """Admin order management"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    """Admin order detail view"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/order/<int:order_id>/update_status', methods=['POST'])
@login_required
def admin_update_order_status(order_id):
    """Update order status"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    status = request.form.get('status')
    if BillingService.update_order_status(order_id, status):
        flash('Order status updated successfully!', 'success')
    else:
        flash('Failed to update order status', 'error')

    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/stock')
@login_required
def admin_stock():
    """Stock management"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    products = Product.query.all()
    movements = StockService.get_stock_movements()
    return render_template('admin/stock.html', products=products, movements=movements)

@app.route('/admin/stock/add', methods=['POST'])
@login_required
def admin_add_stock():
    """Add stock to product"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity'))
    reason = request.form.get('reason', 'Manual stock addition')

    if StockService.add_stock(product_id, quantity, reason):
        flash('Stock added successfully!', 'success')
    else:
        flash('Failed to add stock', 'error')

    return redirect(url_for('admin_stock'))

# ============================================================================
# API ENDPOINTS (For future microservice integration)
# ============================================================================

@app.route('/api/products')
def api_products():
    """API endpoint for products"""
    products = CatalogService.get_all_products()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': float(p.price),
        'stock': p.stock_quantity,
        'category': p.category.name if p.category else None
    } for p in products])

@app.route('/api/stock/<int:product_id>')
def api_stock_check(product_id):
    """API endpoint for stock checking"""
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'product_id': product_id,
            'stock_quantity': product.stock_quantity,
            'available': product.stock_quantity > 0
        })
    return jsonify({'error': 'Product not found'}), 404

# ============================================================================
# INITIALIZATION AND SAMPLE DATA
# ============================================================================

def init_db():
    """Initialize database with sample data"""
    db.create_all()

    # Check if data already exists
    if User.query.first():
        return

    # Create admin user
    admin = User(
        username='admin',
        email='admin@shop.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)

    # Create regular user
    user = User(
        username='customer',
        email='customer@shop.com',
        password_hash=generate_password_hash('customer123')
    )
    db.session.add(user)

    # Create categories
    categories = [
        Category(name='Electronics', description='Electronic devices and gadgets'),
        Category(name='Clothing', description='Fashion and apparel'),
        Category(name='Books', description='Books and literature'),
        Category(name='Home & Garden', description='Home improvement and gardening')
    ]

    for category in categories:
        db.session.add(category)

    db.session.commit()

    # Create sample products
    products = [
        Product(name='Smartphone', description='Latest smartphone with advanced features', 
               price=599.99, stock_quantity=50, category_id=1),
        Product(name='Laptop', description='High-performance laptop for work and gaming', 
               price=1299.99, stock_quantity=25, category_id=1),
        Product(name='T-Shirt', description='Comfortable cotton t-shirt', 
               price=19.99, stock_quantity=100, category_id=2),
        Product(name='Jeans', description='Classic blue jeans', 
               price=49.99, stock_quantity=75, category_id=2),
        Product(name='Python Programming Book', description='Learn Python programming', 
               price=39.99, stock_quantity=30, category_id=3),
        Product(name='Garden Tools Set', description='Complete set of garden tools', 
               price=89.99, stock_quantity=20, category_id=4)
    ]

    for product in products:
        db.session.add(product)

    db.session.commit()
    print("Database initialized with sample data!")

if __name__ == '__main__':
    with app.app_context():
        init_db()

    print("Starting Flask Online Shop...")
    print("Admin credentials: admin / admin123")
    print("Customer credentials: customer / customer123")
    app.run(debug=True, host='0.0.0.0', port=PORT)

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from app.db import get_db
import os
from bson import ObjectId

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/', methods=['GET'])
def root():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.view_products'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        admin_hash = current_app.config.get('ADMIN_PASSWORD_HASH')
        
        if not admin_hash:
            # Fallback
            if password == current_app.config.get('ADMIN_PASSWORD'):
                session['admin_logged_in'] = True
                flash('Successfully logged in! (Legacy)', 'success')
                return redirect(url_for('admin.view_products'))
        elif check_password_hash(admin_hash, password):
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin.view_products'))
            
        flash('Invalid password.', 'error')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/products')
@admin_required
def view_products():
    db = get_db()
    if db is None:
        flash('Database not connected.', 'error')
        return render_template('admin/products.html', products=[])
    
    try:
        products = list(db.products.find().sort('date_created', -1))
        for p in products:
            p['_id'] = str(p['_id'])
        return render_template('admin/products.html', products=products)
    except Exception as e:
        current_app.logger.error(f"Error fetching products: {e}")
        return render_template('admin/products.html', products=[])

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        # ... validation logic using Pydantic could go here or strict form handling ...
        name = request.form.get('name')
        # Simplified for brevity, assume similar logic to original app.py but using get_db()
        # For now, minimal port logic:
        
        uploaded_image = request.files.get('image_file')
        image_filename = request.form.get('image') or 'factory-hero.jpg'

        if uploaded_image and uploaded_image.filename:
            ext = uploaded_image.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_IMAGE_EXTENSIONS:
                safe_name = secure_filename(uploaded_image.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                image_filename = f'{timestamp}_{safe_name}'
                # Save path needs to be absolute or relative to app root
                assets_folder = os.path.join(current_app.static_folder, 'assets')
                uploaded_image.save(os.path.join(assets_folder, image_filename))
        
        product_data = {
            'name': name,
            'description': request.form.get('description'),
            'type': request.form.get('type'),
            'quality': request.form.get('quality'),
            'image': image_filename,
            'features': [f.strip() for f in request.form.get('features','').split('\n') if f.strip()],
            'date_created': datetime.utcnow(),
            'date_updated': datetime.utcnow()
        }
        
        db = get_db()
        if db is not None:
            db.products.insert_one(product_data)
            flash('Product added.', 'success')
            return redirect(url_for('admin.view_products'))

    return render_template('admin/add_product.html')

@admin_bp.route('/products/edit/<product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    if db is None: return redirect(url_for('admin.view_products'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        image_filename = request.form.get('image') or 'factory-hero.jpg'

        uploaded_image = request.files.get('image_file')
        if uploaded_image and uploaded_image.filename:
            ext = uploaded_image.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_IMAGE_EXTENSIONS:
                safe_name = secure_filename(uploaded_image.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                image_filename = f'{timestamp}_{safe_name}'
                assets_folder = os.path.join(current_app.static_folder, 'assets')
                uploaded_image.save(os.path.join(assets_folder, image_filename))
        
        update_data = {
            'name': name,
            'description': request.form.get('description'),
            'type': request.form.get('type'),
            'quality': request.form.get('quality'),
            'image': image_filename,
            'features': [f.strip() for f in request.form.get('features','').split('\n') if f.strip()],
            'date_updated': datetime.utcnow()
        }
        
        db.products.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
        flash('Product updated.', 'success')
        return redirect(url_for('admin.view_products'))
    
    product = db.products.find_one({'_id': ObjectId(product_id)})
    if product:
        product['_id'] = str(product['_id'])
        product['features'] = '\n'.join(product.get('features', []))
        return render_template('admin/edit_product.html', product=product)
    return redirect(url_for('admin.view_products'))

@admin_bp.route('/products/delete/<product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    db = get_db()
    if db is not None:
        db.products.delete_one({'_id': ObjectId(product_id)})
        flash('Product deleted.', 'success')
    return redirect(url_for('admin.view_products'))

@admin_bp.route('/inquiries')
@admin_required
def view_inquiries():
    db = get_db()
    if db is None: return render_template('admin/inquiries.html', inquiries=[])
    
    # Aggregation logic
    pipeline = [
        {'$sort': {'date_submitted': -1}},
        {'$addFields': {
            'pid_obj': {
                '$convert': {
                    'input': '$product_id',
                    'to': 'objectId',
                    'onError': None,
                    'onNull': None
                }
            }
        }},
        {'$lookup': {
            'from': 'products',
            'localField': 'pid_obj',
            'foreignField': '_id',
            'as': 'product_doc'
        }},
        {'$unwind': {
            'path': '$product_doc',
            'preserveNullAndEmptyArrays': True
        }}
    ]
    inquiries = list(db.inquiries.aggregate(pipeline))
    # Post processing
    for i in inquiries:
        i['_id'] = str(i['_id'])
        # Date formatting...
        i['date_formatted'] = str(i.get('date_submitted', 'N/A'))
        
        prod_doc = i.get('product_doc')
        if prod_doc: i['product_name'] = prod_doc.get('name')
        elif i.get('product_id'): i['product_name'] = 'Not Found'
        else: i['product_name'] = None
        
    return render_template('admin/inquiries.html', inquiries=inquiries)

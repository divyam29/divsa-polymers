import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, make_response, session
from functools import wraps
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import certifi
from config import Config


# App initialization with environment-friendly defaults
app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')

# Load configuration from config.py (which reads .env)
app.config.from_object(Config)

# Expose secret key for extensions that read it directly
app.secret_key = app.config.get('SECRET_KEY')

# Site-wide settings (exposed to templates via context_processor)
SITE = {
    'name': 'Divsa Polymers',
    'url': app.config.get('SITE_URL', 'https://www.divsapolymers.com'),
    'phone': app.config.get('COMPANY_PHONE', '+918607125915'),
    'email': app.config.get('COMPANY_EMAIL', 'divyamjain29@gmail.com'),
    'address': 'Khasra No. 92//21 & 108//1/1, Dukheri Road, Dukheri, Ambala-133004, Haryana, India',
    'latitude': 30.2758361,
    'longitude': 76.8669546,
    'ga_measurement_id': app.config.get('GA_MEASUREMENT_ID', '')
}

# MongoDB connection
MONGO_URI = app.config.get('MONGODB_URI')
if not MONGO_URI:
    app.logger.warning('MONGODB_URI not configured in environment variables')

if MONGO_URI:
    # MongoDB connection with Render-compatible settings
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=60000,
        connectTimeoutMS=60000,
        socketTimeoutMS=60000,
        retryWrites=False,  # Disable retry writes to avoid SSL issues
        maxPoolSize=10,
        minPoolSize=1,
        waitQueueTimeoutMS=60000
    )
else:
    client = None
db = client['divsa'] if client is not None else None
inquiries_collection = db['inquiries'] if db is not None else None
products_collection = db['products'] if db is not None else None


# MongoDB connection verification (app startup)
if client is not None:
    try:
        client.admin.command('ping', timeoutMS=30000)
        app.logger.info('Successfully connected to MongoDB Atlas')
    except ServerSelectionTimeoutError as e:
        app.logger.error(f'MongoDB Atlas connection timeout - this may resolve on first request: {e}')
    except Exception as e:
        app.logger.error(f'Failed to connect to MongoDB Atlas at startup: {e}')



# --- Logging ---
if not app.debug:
    os.makedirs('logs', exist_ok=True)
    handler = RotatingFileHandler('logs/divsa.log', maxBytes=1024 * 1024, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Divsa Polymers startup')


@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
    response.headers['Permissions-Policy'] = 'geolocation=()'
    # HSTS only for HTTPS deployments
    response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


# Make SITE available in all templates
@app.context_processor
def inject_site():
    return dict(SITE=SITE)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/submit-inquiry', methods=['POST'])
def submit_inquiry():
    # Basic server-side validation and sanitization
    name = (request.form.get('name') or '').strip()
    email = (request.form.get('email') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    city = (request.form.get('city') or '').strip()
    business = (request.form.get('business') or '').strip()
    quantity = (request.form.get('quantity') or '').strip()
    product_id = (request.form.get('product_id') or '').strip()

    if not name or not email or not phone:
        flash('Please provide name, email and phone.', 'error')
        # Redirect back to products page if product_id exists, otherwise home
        if product_id:
            return redirect(url_for('products'))
        return redirect(url_for('home') + '#dealership')

    inquiry_data = {
        'name': name,
        'email': email,
        'phone': phone,
        'city': city,
        'business_info': business,
        'quantity_required': quantity if quantity else None,
        'product_id': product_id if product_id else None,
        'inquiry_type': 'product_quote' if product_id else 'general',
        'date_submitted': datetime.utcnow()
    }

    try:
        if inquiries_collection is not None:
            result = inquiries_collection.insert_one(inquiry_data)
            flash(f'Success! {name}, your inquiry has been saved.', 'success')
            app.logger.info('New inquiry saved: %s', email)
        else:
            app.logger.warning('No database configured; skipping save.')
            flash(f'Thank you {name}, we received your inquiry.', 'success')
    except ServerSelectionTimeoutError as e:
        flash('Database connection timeout. Please try again in a moment.', 'error')
        app.logger.error(f'MongoDB connection timeout while saving inquiry: {e}')
    except Exception as e:
        flash('There was an error saving your inquiry. Please try again later.', 'error')
        app.logger.exception('Error saving inquiry')

    # Redirect to thank-you page for better conversion tracking
    return redirect(url_for('thank_you'))


# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == app.config.get('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_products'))
        else:
            flash('Invalid password. Please try again.', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/inquiries')
@admin_required
def view_inquiries():
    if inquiries_collection is None:
        flash('No database configured.', 'error')
        inquiries_list = []
    else:
        try:
            inquiries_list = list(inquiries_collection.find().sort('date_submitted', -1))
            # Convert ObjectId to string and fetch product names if product_id exists
            from bson import ObjectId
            from bson.errors import InvalidId
            
            for inquiry in inquiries_list:
                # Convert _id to string safely
                if '_id' in inquiry:
                    inquiry['_id'] = str(inquiry['_id'])
                
                # Format date for display
                if 'date_submitted' in inquiry and inquiry['date_submitted']:
                    try:
                        if hasattr(inquiry['date_submitted'], 'strftime'):
                            inquiry['date_formatted'] = inquiry['date_submitted'].strftime('%Y-%m-%d %H:%M')
                        else:
                            inquiry['date_formatted'] = str(inquiry['date_submitted'])
                    except:
                        inquiry['date_formatted'] = 'N/A'
                else:
                    inquiry['date_formatted'] = 'N/A'
                
                product_id = inquiry.get('product_id')
                inquiry['product_name'] = None
                
                # Only try to fetch product if product_id exists and is not empty
                if product_id and products_collection is not None:
                    try:
                        # Handle both string and ObjectId product_id
                        if isinstance(product_id, str):
                            # Try to convert string to ObjectId
                            try:
                                product_oid = ObjectId(product_id)
                            except (InvalidId, ValueError):
                                # If conversion fails, product_id might be invalid
                                inquiry['product_name'] = 'Invalid Product ID'
                                continue
                        else:
                            product_oid = product_id
                        
                        # Look up the product
                        product = products_collection.find_one({'_id': product_oid})
                        if product:
                            inquiry['product_name'] = product.get('name', 'Unknown Product')
                        else:
                            inquiry['product_name'] = 'Product Not Found'
                    except Exception as e:
                        app.logger.warning(f'Error fetching product for inquiry: {e}')
                        inquiry['product_name'] = 'Error Loading Product'
        except Exception as e:
            app.logger.error(f'Error fetching inquiries: {e}')
            app.logger.exception('Full error traceback:')
            flash(f'Error loading inquiries: {str(e)}', 'error')
            inquiries_list = []
    
    return render_template('admin/inquiries.html', inquiries=inquiries_list)


# Admin Product Management Routes
@app.route('/admin/products')
@admin_required
def admin_products():
    if products_collection is None:
        flash('No database configured.', 'error')
        products_list = []
    else:
        try:
            products_list = list(products_collection.find().sort('date_created', -1))
            # Convert ObjectId to string for template rendering
            for product in products_list:
                product['_id'] = str(product['_id'])
        except Exception as e:
            app.logger.error(f'Error fetching products: {e}')
            flash('Error loading products.', 'error')
            products_list = []
    return render_template('admin/products.html', products=products_list)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        product_type = (request.form.get('type') or '').strip()
        quality = (request.form.get('quality') or '').strip()
        image = (request.form.get('image') or '').strip()
        features_str = (request.form.get('features') or '').strip()
        
        # Convert features string to list
        features = [f.strip() for f in features_str.split('\n') if f.strip()]
        
        if not name or not description or not product_type or not quality:
            flash('Please fill in all required fields (name, description, type, quality).', 'error')
            return render_template('admin/add_product.html')
        
        product_data = {
            'name': name,
            'description': description,
            'type': product_type,
            'quality': quality,
            'image': image or 'factory-hero.jpg',  # Default image
            'features': features,
            'date_created': datetime.utcnow(),
            'date_updated': datetime.utcnow()
        }
        
        try:
            if products_collection is not None:
                products_collection.insert_one(product_data)
                flash(f'Product "{name}" added successfully!', 'success')
                app.logger.info(f'New product added: {name}')
                return redirect(url_for('admin_products'))
            else:
                flash('No database configured. Product not saved.', 'error')
        except Exception as e:
            flash(f'Error saving product: {str(e)}', 'error')
            app.logger.exception('Error saving product')
    
    return render_template('admin/add_product.html')


@app.route('/admin/products/edit/<product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    from bson import ObjectId
    
    if products_collection is None:
        flash('No database configured.', 'error')
        return redirect(url_for('admin_products'))
    
    try:
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        if not product:
            flash('Product not found.', 'error')
            return redirect(url_for('admin_products'))
        
        if request.method == 'POST':
            name = (request.form.get('name') or '').strip()
            description = (request.form.get('description') or '').strip()
            product_type = (request.form.get('type') or '').strip()
            quality = (request.form.get('quality') or '').strip()
            image = (request.form.get('image') or '').strip()
            features_str = (request.form.get('features') or '').strip()
            
            # Convert features string to list
            features = [f.strip() for f in features_str.split('\n') if f.strip()]
            
            if not name or not description or not product_type or not quality:
                flash('Please fill in all required fields.', 'error')
                product['features'] = '\n'.join(product.get('features', []))
                return render_template('admin/edit_product.html', product=product)
            
            update_data = {
                'name': name,
                'description': description,
                'type': product_type,
                'quality': quality,
                'image': image or 'factory-hero.jpg',
                'features': features,
                'date_updated': datetime.utcnow()
            }
            
            products_collection.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': update_data}
            )
            flash(f'Product "{name}" updated successfully!', 'success')
            return redirect(url_for('admin_products'))
        
        # Convert features list to string for textarea
        product['features'] = '\n'.join(product.get('features', []))
        product['_id'] = str(product['_id'])
        return render_template('admin/edit_product.html', product=product)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        app.logger.exception('Error editing product')
        return redirect(url_for('admin_products'))


@app.route('/admin/products/delete/<product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    from bson import ObjectId
    
    if products_collection is None:
        flash('No database configured.', 'error')
        return redirect(url_for('admin_products'))
    
    try:
        result = products_collection.delete_one({'_id': ObjectId(product_id)})
        if result.deleted_count > 0:
            flash('Product deleted successfully!', 'success')
        else:
            flash('Product not found.', 'error')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'error')
        app.logger.exception('Error deleting product')
    
    return redirect(url_for('admin_products'))


# Product routes
@app.route('/pvc-garden-pipes')
def pvc_garden_pipes():
    faqs = [
        {"question": "Are your PVC garden pipes UV resistant?", "answer": "Yes — our garden pipes are UV stabilized for long outdoor life."},
        {"question": "What sizes are available?", "answer": "We supply 1/2 inch to 2 inch diameters in various lengths and thicknesses."},
        {"question": "Do you provide bulk discounts for distributors?", "answer": "Yes — competitive distributor pricing is available on application."},
        {"question": "Is delivery available PAN India?", "answer": "We ship nationwide with reliable logistics partners."}
    ]
    return render_template('pvc-garden-pipes.html', faqs=faqs)


@app.route('/pvc-braided-pipes')
def pvc_braided_pipes():
    faqs = [
        {"question": "Are braided pipes suitable for high-pressure use?", "answer": "Yes — braided reinforcement increases burst pressure tolerance."},
        {"question": "What materials are used in the braid?", "answer": "High-strength synthetic fibers with corrosion-resistant coatings."},
        {"question": "Can braided pipes be used in agriculture and industry?", "answer": "Yes — suitable for both heavy-duty agricultural and light industrial use."},
        {"question": "What warranty do you provide?", "answer": "Standard manufacturer warranty applies; extended warranties available for bulk customers."}
    ]
    return render_template('pvc-braided-pipes.html', faqs=faqs)


@app.route('/pvc-recycled-pipes')
def pvc_recycled_pipes():
    faqs = [
        {"question": "Are recycled PVC pipes as strong as virgin PVC?", "answer": "Our recycled products meet strict QA standards and perform comparably for many applications."},
        {"question": "What percentage of recycled content is used?", "answer": "The recycled content varies by product line and is disclosed on specification sheets."},
        {"question": "Do recycled pipes meet regulatory standards?", "answer": "Yes — they are produced under controlled processes to meet safety specs."},
        {"question": "Can I request a material safety data sheet (MSDS)?", "answer": "Yes — MSDS are available on request for all product lines."}
    ]
    return render_template('pvc-recycled-pipes.html', faqs=faqs)


@app.route('/products')
def products():
    # Try to fetch products from database, fallback to empty list
    if products_collection is not None:
        try:
            products_list = list(products_collection.find().sort('date_created', -1))
            # Convert ObjectId to string and ensure all required fields exist
            products_data = []
            for product in products_list:
                product_dict = {
                    'id': str(product.get('_id', '')),
                    'name': product.get('name', 'Unnamed Product'),
                    'type': product.get('type', ''),
                    'quality': product.get('quality', 'Standard'),
                    'image': product.get('image', 'factory-hero.jpg'),
                    'description': product.get('description', ''),
                    'features': product.get('features', [])
                }
                products_data.append(product_dict)
        except Exception as e:
            app.logger.error(f'Error fetching products: {e}')
            products_data = []
    else:
        products_data = []
    
    # If no products in database, show empty state
    return render_template('products.html', products=products_data)


# City / Local pages
@app.route('/pvc-pipes-in-ambala')
def pvc_pipes_in_ambala():
    return render_template('pvc-pipes-in-ambala.html', city='Ambala')


@app.route('/pvc-pipes-in-delhi')
def pvc_pipes_in_delhi():
    return render_template('pvc-pipes-in-delhi.html', city='Delhi')


@app.route('/pvc-pipes-in-punjab')
def pvc_pipes_in_punjab():
    return render_template('pvc-pipes-in-punjab.html', city='Punjab')


@app.route('/thank-you')
def thank_you():
    return render_template('thank-you.html')


@app.route('/infrastructure')
def infrastructure():
    return render_template('infrastructure.html')


# Serve favicon (from assets folder)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'assets'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# SEO Sitemap - for Google/Bing indexing
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': url_for('home', _external=True), 'priority': '1.0', 'changefreq': 'weekly'},
        {'loc': url_for('products', _external=True), 'priority': '0.9', 'changefreq': 'weekly'},
        {'loc': url_for('pvc_garden_pipes', _external=True), 'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': url_for('pvc_braided_pipes', _external=True), 'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': url_for('pvc_recycled_pipes', _external=True), 'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': url_for('infrastructure', _external=True), 'priority': '0.8', 'changefreq': 'monthly'},
        {'loc': url_for('pvc_pipes_in_ambala', _external=True), 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': url_for('pvc_pipes_in_delhi', _external=True), 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': url_for('pvc_pipes_in_punjab', _external=True), 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': url_for('thank_you', _external=True), 'priority': '0.5', 'changefreq': 'yearly'}
    ]
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f"<loc>{p['loc']}</loc>")
        sitemap_xml.append(f"<changefreq>{p.get('changefreq', 'monthly')}</changefreq>")
        sitemap_xml.append(f"<priority>{p['priority']}</priority>")
        sitemap_xml.append('</url>')
    sitemap_xml.append('</urlset>')
    response = make_response('\n'.join(sitemap_xml))
    response.headers['Content-Type'] = 'application/xml'
    return response


@app.route('/robots.txt')
def robots_txt():
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin',
        f"Sitemap: {url_for('sitemap', _external=True)}"
    ]
    response = make_response('\n'.join(lines))
    response.headers['Content-Type'] = 'text/plain'
    return response


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    app.run(host=host, port=port, debug=app.config['DEBUG'])
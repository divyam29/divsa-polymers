import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, make_response
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
    'phone': app.config.get('COMPANY_PHONE', '+91-173-1234567'),
    'address': 'Plot No. 21, Industrial Area, Ambala Cantt, Ambala, Haryana 134006, India',
    'latitude': 30.3782,
    'longitude': 76.7767,
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

    if not name or not email or not phone:
        flash('Please provide name, email and phone.', 'error')
        return redirect(url_for('home') + '#dealership')

    inquiry_data = {
        'name': name,
        'email': email,
        'phone': phone,
        'city': city,
        'business_info': business,
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


@app.route('/admin/inquiries')
def view_inquiries():
    if inquiries_collection is None:
        return 'No database configured.'
    all_inquiries = list(inquiries_collection.find().sort('date_submitted', -1))
    return f"Total Inquiries: {len(all_inquiries)}<br>" + "<br>".join([f"{i.get('name')} ({i.get('email')}) from {i.get('city')}" for i in all_inquiries])


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


# Serve favicon (if present in static)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# SEO Sitemap - for Google/Bing indexing
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': url_for('home', _external=True), 'priority': '1.0', 'changefreq': 'weekly'},
        {'loc': url_for('pvc_garden_pipes', _external=True), 'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': url_for('pvc_braided_pipes', _external=True), 'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': url_for('pvc_recycled_pipes', _external=True), 'priority': '0.9', 'changefreq': 'monthly'},
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=app.config['DEBUG'])
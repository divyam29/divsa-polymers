import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, make_response
from pymongo import MongoClient
from bson.objectid import ObjectId
import certifi
from config import Config


# App initialization with environment-friendly defaults
app = Flask(__name__, static_url_path='/static',static_folder='static', template_folder='templates')

# Load configuration from config.py (which reads .env)
app.config.from_object(Config)

# Expose secret key for extensions that read it directly
app.secret_key = app.config.get('SECRET_KEY')

# MongoDB connection
MONGO_URI = app.config.get('MONGODB_URI')
if not MONGO_URI:
    app.logger.warning('MONGODB_URI not configured in environment variables')

if MONGO_URI:
    # Use certifi for SSL certificate verification
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
else:
    client = None
db = client['divsa'] if client is not None else None
inquiries_collection = db['inquiries'] if db is not None else None


# MongoDB connection verification (app startup)
if client is not None:
    try:
        client.admin.command('ping')
        app.logger.info('Successfully connected to MongoDB Atlas')
    except Exception as e:
        app.logger.error(f'Failed to connect to MongoDB Atlas: {e}')



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


# --- Security headers ---
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
    response.headers['Permissions-Policy'] = 'geolocation=()'
    # HSTS only for HTTPS deployments
    response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


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
        result = inquiries_collection.insert_one(inquiry_data)
        flash(f'Success! {name}, your inquiry has been saved.', 'success')
        app.logger.info('New inquiry saved: %s', email)
    except Exception as e:
        flash('There was an error saving your inquiry. Please try again later.', 'error')
        app.logger.exception('Error saving inquiry')

    return redirect(url_for('home') + '#dealership')


@app.route('/admin/inquiries')
def view_inquiries():
    all_inquiries = list(inquiries_collection.find().sort('date_submitted', -1))
    return f"Total Inquiries: {len(all_inquiries)}<br>" + "<br>".join([f"{i.get('name')} ({i.get('email')}) from {i.get('city')}" for i in all_inquiries])


# Serve favicon (if present in static)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# SEO Sitemap - for Google/Bing indexing
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': url_for('home', _external=True), 'priority': '1.0', 'changefreq': 'weekly'},
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
        'Disallow:',
        f"Sitemap: {url_for('sitemap', _external=True)}"
    ]
    response = make_response('\n'.join(lines))
    response.headers['Content-Type'] = 'text/plain'
    return response


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=app.config['DEBUG'])
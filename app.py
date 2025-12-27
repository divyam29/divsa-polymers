import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy


# App initialization with environment-friendly defaults
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'divsa_secret_key')

# Database configuration (use DATABASE_URL in production)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', '0') == '1'

db = SQLAlchemy(app)


# --- Database Model ---
class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100))
    business_info = db.Column(db.Text)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)


# Ensure database exists
with app.app_context():
    db.create_all()


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

    new_inquiry = Inquiry(name=name, email=email, phone=phone, city=city, business_info=business)

    try:
        db.session.add(new_inquiry)
        db.session.commit()
        flash(f'Success! {new_inquiry.name}, your inquiry has been saved.', 'success')
        app.logger.info('New inquiry saved: %s', new_inquiry.email)
    except Exception as e:
        db.session.rollback()
        flash('There was an error saving your inquiry. Please try again later.', 'error')
        app.logger.exception('Error saving inquiry')

    return redirect(url_for('home') + '#dealership')


@app.route('/admin/inquiries')
def view_inquiries():
    all_inquiries = Inquiry.query.order_by(Inquiry.date_submitted.desc()).all()
    return f"Total Inquiries: {len(all_inquiries)}<br>" + "<br>".join([f"{i.name} ({i.email}) from {i.city}" for i in all_inquiries])


# Serve favicon (if present in static)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# Simple sitemap.xml generation for SEO (extend as needed)
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': url_for('home', _external=True), 'priority': '1.0'},
    ]
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f"<loc>{p['loc']}</loc>")
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
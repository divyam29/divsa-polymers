import os
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, make_response, send_from_directory
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import certifi
from config import Config

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
app.config.from_object(Config)
app.secret_key = app.config.get('SECRET_KEY')

SITE = {
    'name': 'Divsa Polymers',
    'url': app.config.get('SITE_URL', 'https://www.divsapolymers.com'),
    'phone': app.config.get('COMPANY_PHONE', '+91-173-1234567'),
    'address': 'Plot No. 21, Industrial Area, Ambala Cantt, Ambala, Haryana 134006, India',
    'latitude': 30.3782,
    'longitude': 76.7767,
    'ga_measurement_id': app.config.get('GA_MEASUREMENT_ID', '')
}

# MongoDB connection (optional)
MONGO_URI = app.config.get('MONGODB_URI')
client = None
if MONGO_URI:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=60000)

inquiries_collection = None
if client is not None:
    db = client.get_database('divsa')
    inquiries_collection = db.get_collection('inquiries')


@app.context_processor
def inject_site():
    return dict(SITE=SITE)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/submit-inquiry', methods=['POST'])
def submit_inquiry():
    name = (request.form.get('name') or '').strip()
    email = (request.form.get('email') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    city = (request.form.get('city') or '').strip()
    business = (request.form.get('business') or '').strip()

    if not name or not email or not phone:
        flash('Please provide name, email and phone.', 'error')
        return redirect(url_for('home') + '#dealership')

    data = {'name': name, 'email': email, 'phone': phone, 'city': city, 'business': business, 'date_submitted': datetime.utcnow()}

    try:
        if inquiries_collection is not None:
            inquiries_collection.insert_one(data)
            app.logger.info('Saved inquiry: %s', email)
        flash('Thank you! Your inquiry was received.', 'success')
    except ServerSelectionTimeoutError:
        flash('Database timeout. Please try again shortly.', 'error')
    except Exception as e:
        app.logger.exception('Error saving inquiry')
        flash('There was an error saving your inquiry. Please try again later.', 'error')

    return redirect(url_for('thank_you'))


# Product pages
@app.route('/pvc-garden-pipes')
def pvc_garden_pipes():
    faqs = [
        {"question": "Are your PVC garden pipes UV resistant?", "answer": "Yes — UV stabilized for outdoor use."},
        {"question": "What sizes are available?", "answer": "From 1/2\" to 2\" diameters in multiple lengths."},
        {"question": "Do you ship PAN India?", "answer": "Yes — nationwide logistics available."},
        {"question": "Are bulk discounts available?", "answer": "Yes — contact sales for distributor pricing."}
    ]
    return render_template('pvc-garden-pipes.html', faqs=faqs)


@app.route('/pvc-braided-pipes')
def pvc_braided_pipes():
    faqs = [
        {"question": "What is the burst pressure?", "answer": "High burst resistance — see spec sheets for exact values."},
        {"question": "Is it kink resistant?", "answer": "Yes — braided design prevents kinks."},
        {"question": "Can I get commercial packaging?", "answer": "Yes — tailored packing for trade orders."},
        {"question": "Do you offer warranty?", "answer": "Standard warranty applies; extended options available."}
    ]
    return render_template('pvc-braided-pipes.html', faqs=faqs)


@app.route('/pvc-recycled-pipes')
def pvc_recycled_pipes():
    faqs = [
        {"question": "Are recycled pipes eco-friendly?", "answer": "Yes — made with controlled recycled content to reduce footprint."},
        {"question": "Do they maintain strength?", "answer": "Yes — quality-controlled to meet performance standards."},
        {"question": "Is certification available?", "answer": "Certificates and MSDS available on request."},
        {"question": "Can distributors order samples?", "answer": "Yes — contact sales to receive samples."}
    ]
    return render_template('pvc-recycled-pipes.html', faqs=faqs)


@app.route('/pvc-conduits')
def pvc_conduits():
    faqs = [
        {"question": "Are conduits flame-retardant?", "answer": "We offer self-extinguishing conduit options."},
        {"question": "Do you supply fittings?", "answer": "Yes — compatible fittings and accessories are available."},
        {"question": "What sizes?", "answer": "Standard conduit sizes stocked from 16mm to 50mm."},
        {"question": "Can I get custom lengths?", "answer": "Yes — contact sales for custom orders."}
    ]
    return render_template('pvc-conduits.html', faqs=faqs)


# City pages
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


@app.route('/sitemap.xml')
def sitemap():
    urls = [
        url_for('home', _external=True),
        url_for('pvc_garden_pipes', _external=True),
        url_for('pvc_braided_pipes', _external=True),
        url_for('pvc_recycled_pipes', _external=True),
        url_for('pvc_conduits', _external=True),
        url_for('pvc_pipes_in_ambala', _external=True),
        url_for('pvc_pipes_in_delhi', _external=True),
        url_for('pvc_pipes_in_punjab', _external=True),
        url_for('thank_you', _external=True)
    ]
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f"<loc>{u}</loc>")
        sitemap_xml.append('<changefreq>monthly</changefreq>')
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
    app.run(host=host, port=port, debug=app.config.get('DEBUG', False))

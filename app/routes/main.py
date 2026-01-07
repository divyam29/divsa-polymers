from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, current_app, make_response
from datetime import datetime
from app.db import get_db
from app.utils.email import send_inquiry_email
from app.models.validation import InquiryModel
from pydantic import ValidationError
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/products')
def products():
    db = get_db()
    products_list = []
    if db is not None:
        try:
            products_list = list(db.products.find().sort('date_created', -1))
            for p in products_list:
                p['id'] = str(p['_id'])
        except Exception as e:
            current_app.logger.error(f'Error fetching products: {e}')
    return render_template('products.html', products=products_list)

@main_bp.route('/submit-inquiry', methods=['POST'])
def submit_inquiry():
    try:
        # Validate with Pydantic
        form_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'city': request.form.get('city'),
            'business_info': request.form.get('business'),
            'quantity_required': request.form.get('quantity'),
            'product_id': request.form.get('product_id')
        }
        
        # Pydantic validation
        inquiry = InquiryModel(**form_data)
        
        data = inquiry.model_dump()
        data['date_submitted'] = datetime.utcnow()
        data['inquiry_type'] = 'product_quote' if data.get('product_id') else 'general'

        db = get_db()
        if db is not None:
            db.inquiries.insert_one(data)
            flash(f"Success! {data['name']}, your inquiry has been saved.", 'success')
            send_inquiry_email(data)
            return redirect(url_for('main.thank_you'))
        else:
            flash('System error: Database not connected. Please try again later or call us directly.', 'error')
            return redirect(url_for('main.home') + '#dealership')

    except ValidationError as e:
        for error in e.errors():
            field = error['loc'][0]
            msg = error['msg']
            flash(f"Error in {field}: {msg}", 'error')
        return redirect(url_for('main.home') + '#dealership')
    except Exception as e:
        current_app.logger.error(f'Inquiry error: {e}')
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('main.home') + '#dealership')

@main_bp.route('/thank-you')
def thank_you():
    return render_template('thank-you.html')

# Static pages
@main_bp.route('/pvc-garden-pipes')
def pvc_garden_pipes():
    faqs = [
        {"question": "Are your PVC garden pipes UV resistant?", "answer": "Yes — our garden pipes are UV stabilized for long outdoor life."},
        {"question": "What sizes are available?", "answer": "We supply 1/2 inch to 2 inch diameters in various lengths and thicknesses."},
        {"question": "Do you provide bulk discounts for distributors?", "answer": "Yes — competitive distributor pricing is available on application."},
        {"question": "Is delivery available PAN India?", "answer": "We ship nationwide with reliable logistics partners."}
    ]
    return render_template('pvc-garden-pipes.html', faqs=faqs)

@main_bp.route('/pvc-braided-pipes')
def pvc_braided_pipes():
    faqs = [
        {"question": "Are braided pipes suitable for high-pressure use?", "answer": "Yes — braided reinforcement increases burst pressure tolerance."},
        {"question": "What materials are used in the braid?", "answer": "High-strength synthetic fibers with corrosion-resistant coatings."},
        {"question": "Can braided pipes be used in agriculture and industry?", "answer": "Yes — suitable for both heavy-duty agricultural and light industrial use."},
        {"question": "What warranty do you provide?", "answer": "Standard manufacturer warranty applies; extended warranties available for bulk customers."}
    ]
    return render_template('pvc-braided-pipes.html', faqs=faqs)

@main_bp.route('/pvc-recycled-pipes')
def pvc_recycled_pipes():
    faqs = [
        {"question": "Are recycled PVC pipes as strong as virgin PVC?", "answer": "Our recycled products meet strict QA standards and perform comparably for many applications."},
        {"question": "What percentage of recycled content is used?", "answer": "The recycled content varies by product line and is disclosed on specification sheets."},
        {"question": "Do recycled pipes meet regulatory standards?", "answer": "Yes — they are produced under controlled processes to meet safety specs."},
        {"question": "Can I request a material safety data sheet (MSDS)?", "answer": "Yes — MSDS are available on request for all product lines."}
    ]
    return render_template('pvc-recycled-pipes.html', faqs=faqs)

@main_bp.route('/infrastructure')
def infrastructure():
    return render_template('infrastructure.html')

# SEO Pages
@main_bp.route('/pvc-pipes-in-ambala')
def pvc_pipes_in_ambala(): return render_template('pvc-pipes-in-ambala.html', city='Ambala')

@main_bp.route('/pvc-pipes-in-delhi')
def pvc_pipes_in_delhi(): return render_template('pvc-pipes-in-delhi.html', city='Delhi')

@main_bp.route('/pvc-pipes-in-punjab')
def pvc_pipes_in_punjab(): return render_template('pvc-pipes-in-punjab.html', city='Punjab')

@main_bp.route('/robots.txt')
def robots_txt():
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin',
        f"Sitemap: {url_for('main.sitemap', _external=True)}"
    ]
    response = make_response('\n'.join(lines))
    response.headers['Content-Type'] = 'text/plain'
    return response

@main_bp.route('/sitemap.xml')
def sitemap():
    # ... sitemap logic ...
    # Simplified for brevity
    pages = [
         {'loc': url_for('main.home', _external=True), 'priority': '1.0'},
         # ... add others
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        xml.append(f"<url><loc>{p['loc']}</loc></url>")
    xml.append('</urlset>')
    response = make_response('\n'.join(xml))
    response.headers['Content-Type'] = 'application/xml'
    return response

@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'assets'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

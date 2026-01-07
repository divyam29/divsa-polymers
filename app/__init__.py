from flask import Flask, request
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from app.utils.logging import configure_logging
from app.db import init_app

csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    csrf.init_app(app)
    init_app(app) # Database teardown
    configure_logging(app)

    # Context processors
    @app.context_processor
    def inject_site():
        configured_url = (app.config.get('SITE_URL') or '').strip()
        base_url = configured_url.rstrip('/') if configured_url else request.url_root.rstrip('/')
        return dict(SITE={
            'name': 'Divsa Polymers',
            'brand_line': 'Divsa Polymers by Adinath Industries',
            'parent_name': 'Adinath Industries',
            'url': base_url,
            'phone': app.config.get('COMPANY_PHONE', '+918607125915'),
            'email': app.config.get('COMPANY_EMAIL', 'divyamjain29@gmail.com'),
            'address': 'Khasra No. 92//21 & 108//1/1, Dukheri Road, Dukheri, Ambala-133004, Haryana, India',
            'latitude': 30.2758361,
            'longitude': 76.8669546,
            'ga_measurement_id': app.config.get('GA_MEASUREMENT_ID', ''),
            'service_regions': ['Ambala', 'Haryana', 'Punjab', 'Delhi', 'North India'],
            'managing_partners': ['Mohit Jain', 'Divyam Jain'],
            'group_experience_years': 30,
            'founding_year': 1994
        })

    # Blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    return app

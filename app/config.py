import os
from dotenv import load_dotenv

# Load .env from project root
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(os.path.dirname(basedir), '.env')
load_dotenv(env_path)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    SITE_URL = os.environ.get('SITE_URL', 'https://www.divsapolymers.com')

    # Security settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '1') == '1'
    ADMIN_LOGIN_LIMIT = 5
    ADMIN_LOGIN_WINDOW_SECONDS = 900
    
    # Admin authentication
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')

    # MongoDB Atlas configuration
    MONGODB_URI = os.environ.get('MONGODB_URI', '')
    
    # Email (SMTP) settings for inquiry notifications
    EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '1') == '1'
    EMAIL_FROM = os.environ.get('EMAIL_FROM', EMAIL_USERNAME)
    EMAIL_TO_ADMIN = os.environ.get('EMAIL_TO_ADMIN', 'divyamjain29@gmail.com')
    
    # Legacy database configuration (SQLite)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # default to sqlite in project root
        db_path = os.path.join(basedir, 'database.db')
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path.replace('\\', '/')


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True

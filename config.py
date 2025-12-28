import os
from dotenv import load_dotenv

# Load .env from project root
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
load_dotenv(env_path)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'divsa_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'

    # MongoDB Atlas configuration
    MONGODB_URI = os.environ.get('MONGODB_URI', '')
    
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


class TestingConfig(Config):
    TESTING = True
    DEBUG = True

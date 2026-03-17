import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')
    JWT_EXPIRY_HOURS = 24

    # MySQL Database config
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'ecommerce_db')

    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # Razorpay
    RAZORPAY_KEY_ID     = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

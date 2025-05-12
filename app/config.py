import os

# Base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

    # Flask-WTF (CSRF) settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = SECRET_KEY  # uses the same key; you can also set a separate env var

    # Session settings
    SESSION_COOKIE_SECURE = False   # <-- set True in production (HTTPS only)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Application settings
    DEBUG = True
    TESTING = False

from flask import Flask
import os

application = Flask(__name__)
application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'

from app.api.courses import courses_api
application.register_blueprint(courses_api, url_prefix="/api")

import app.routes


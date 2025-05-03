from flask import Flask
import os

application = Flask(__name__)
application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'

import app.routes

from app.api.courses import courses_api
application.register_blueprint(courses_api)

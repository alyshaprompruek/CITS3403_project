from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config
import os

application = Flask(__name__)
application.config.from_object(Config)
db = SQLAlchemy(application)
migrate = Migrate(application, db)
login = LoginManager(application)
login.login_view = 'login'

application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'

import app.routes

import app.models

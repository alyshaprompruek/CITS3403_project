from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    unit_code = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.student_id'), nullable=False)
    user = db.relationship('User', backref=db.backref('units', lazy=True))
    target_score = db.Column(db.Float, nullable=True)
    outline_url = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.String(500), nullable=True)  # Store the unit summary
    links = db.Column(db.JSON, nullable=True)  # Store a list of dictionaries [{"name": "Link Name", "url": "Link URL"}]

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.student_id'), nullable=False)
    weighting = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    grade = db.Column(db.Float, nullable=True)
    task_name = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(20), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    unit = db.relationship('Unit', backref=db.backref('tasks', lazy=True))


# ShareAccess model for sharing records between users
from datetime import datetime

class ShareAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    share_token = db.Column(db.String(64), unique=True, nullable=False)
    from_user = db.Column(db.String(120), nullable=False)
    to_user = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
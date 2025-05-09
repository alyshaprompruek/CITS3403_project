from app import db

class User(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

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

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.student_id'), nullable=False)
    weighting = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # [exam, assignment, assessment, other]
    notes = db.Column(db.Text, nullable=True)
    grade = db.Column(db.Float, nullable=True)
    task_name = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(20), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    unit = db.relationship('Unit', backref=db.backref('tasks', lazy=True))
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import re


class User(db.Model):
    student_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        """
        Sets the user's password after validating its strength.
        """
        if not self.is_strong_password(password):
            raise ValueError(
                "Password must be at least 8 characters long, "
                "include an uppercase letter, a number, and a special character."
            )
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifies the provided password. First tries the hashed password,
        then falls back to legacy plaintext. If plaintext matches, re-hashes
        and upgrades the stored password to a proper hash.
        """
        from app import db

        # 1) Try the normal hash check
        try:
            if check_password_hash(self.password_hash, password):
                return True
        except ValueError:
            # If the stored password_hash isn't a valid werkzeug hash
            pass

        # 2) Legacy fallback: compare plaintext
        if self.password_hash == password:
            # 3) Upgrade to a proper hash for next time
            self.set_password(password)
            db.session.add(self)
            db.session.commit()
            return True

        # 4) Nothing matched
        return False

    @staticmethod
    def is_strong_password(password):
        """
        Validates if the provided password is strong enough.
        """
        pattern = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        return re.match(pattern, password) is not None

    def __repr__(self):
        return f"<User {self.email}>"


class Unit(db.Model):
    # map the Python attr "unit_id" onto the existing DB column "id"
    unit_id     = db.Column(
        'id',            # actual column name in SQLite
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    semester    = db.Column(db.String(20), nullable=False)
    year        = db.Column(db.Integer, nullable=False)
    name        = db.Column(db.String(120), nullable=False)
    unit_code   = db.Column(db.String(20), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.student_id'), nullable=False)
    target_score = db.Column(db.Float, nullable=True)
    outline_url  = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('units', lazy=True))

    def __repr__(self):
        return f"<Unit {self.unit_code} ({self.name})>"


class Task(db.Model):
    # map the Python attr "task_id" onto the existing DB column "id"
    task_id    = db.Column(
        'id',            # actual column name in SQLite
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id    = db.Column(db.Integer, db.ForeignKey('user.student_id'), nullable=False)
    # point this FK at unit.id (the real column name in SQLite)
    unit_id    = db.Column(
        db.Integer,
        db.ForeignKey('unit.id'),
        nullable=False
    )
    weighting  = db.Column(db.Float, nullable=False)
    type       = db.Column(db.String(20), nullable=False)
    notes      = db.Column(db.Text, nullable=True)
    grade      = db.Column(db.Float, nullable=True)
    task_name  = db.Column(db.String(120), nullable=True)
    date       = db.Column(db.String(20), nullable=True)

    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    unit = db.relationship('Unit', backref=db.backref('tasks', lazy=True))

    def __repr__(self):
        return f"<Task {self.task_name} for Unit {self.unit.unit_code}>"

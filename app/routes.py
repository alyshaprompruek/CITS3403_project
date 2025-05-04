from flask import render_template, request, redirect, session, url_for
from app.models import user
from app.forms import SignUpForm, LoginForm
from app import application 

users = []  # Temporary list to store users

@application.route('/')
def homepage():
    user = session.get("user", None)
    return render_template('homepage.html', user=user)

@application.route('/signup', methods=["POST", "GET"])
def signup():
    form = SignUpForm()
    if request.method == "GET":
        return render_template('signup.html', SignUpForm=form)
    elif request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            new_user = user(
                email=email, 
                password=password
            )

            users.append(new_user)
            session["user"] = new_user.to_dict()
            return redirect(url_for('dashboard'))

@application.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template('login.html', form=form)
    elif request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            for user in users:
                if user.email == email and user.password == password:
                    session["user"] = user.to_dict()
                    return redirect(url_for('dashboard'))
            
            return render_template('login.html', form=form, error="Invalid email or password.")

@application.route('/dashboard')
def dashboard():
    if "user" in session:
        user = session["user"]
        return render_template('dashboard.html', user=user)
    else:
        return redirect(url_for('homepage'))

@application.route('/track_grades')
def track_grades():
    if "user" in session:
        user = session["user"]
        return render_template('track_grades.html', user=user)
    else:
        return redirect(url_for('homepage'))

@application.route('/settings')
def settings():
    if "user" in session:
        user = session["user"]
        return render_template('settings.html', user=user)
    else:
        return redirect(url_for('homepage'))

@application.route('/api/logout', methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect(url_for('homepage'))

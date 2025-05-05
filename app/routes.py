from flask import render_template, request, redirect, session, url_for
from app.models import User, Unit, Task
from app.forms import SignUpForm, LoginForm
from app import application, db

@application.route('/')
def homepage():
    user_id = session.get("user_id", None)
    return render_template('homepage.html', user_id=user_id)

@application.route('/signup', methods=["POST", "GET"])
def signup():
    form = SignUpForm()
    error = None
    
    if request.method == "GET":
        return render_template('signup.html', form=form, error=error)
    elif request.method == "POST":
        if form.validate_on_submit():
            try:
                email = form.email.data
                password = form.password.data

                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    error = "Email already registered. Please use a different email or login."
                    return render_template('signup.html', form=form, error=error)

                new_user = User(
                    email=email, 
                    password=password
                )

                db.session.add(new_user)
                db.session.commit()  # Commit to generate the student_id

                session["user_id"] = new_user.student_id
                return redirect(url_for('dashboard'))
            
            except Exception as e:
                db.session.rollback()  # Roll back if there's an error
                error = f"An error occurred during registration: {str(e)}"
                
        else:
            # Form validation failed
            error = "Please check your information and try again."
            
        return render_template('signup.html', form=form, error=error)

@application.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    error = None
    
    if request.method == "GET":
        return render_template('login.html', form=form, error=error)
    elif request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            try:
                # Query the database for the user with the given email
                user = User.query.filter_by(email=email).first()
                
                # Check if user exists and password matches
                if user and user.password == password: #not any hashing done yet
                    session["user_id"] = user.student_id
                    return redirect(url_for('dashboard'))
                else:
                    error = "Invalid email or password."
            
            except Exception as e:
                error = f"An error occurred during login: {str(e)}"
        else:
            error = "Please check your information and try again."
            
        return render_template('login.html', form=form, error=error)

@application.route('/dashboard')
def dashboard():
    if "user_id" in session: 
        user_id = session["user_id"]
        
        # Query the database to get the complete user object
        user = User.query.get(user_id)
        
        # Check if user exists in database
        if user:
            return render_template('dashboard.html', user=user)
        else:
            # User ID in session but not found in database - clear session and redirect
            session.pop("user_id", None)
    return redirect(url_for('homepage'))

@application.route('/track_grades')
def track_grades():
    if "user_id" in session: 
        user_id = session["user_id"]
        
        # Query the database to get the complete user object
        user = User.query.get(user_id)
        
        # Check if user exists in database
        if user:
            return render_template('track_grades.html', user=user)
        else:
            # User ID in session but not found in database - clear session and redirect
            session.pop("user_id", None)
    return redirect(url_for('homepage'))

@application.route('/settings')
def settings():
    if "user_id" in session: 
        user_id = session["user_id"]
        
        # Query the database to get the complete user object
        user = User.query.get(user_id)
        
        # Check if user exists in database
        if user:
            return render_template('settings.html', user=user)
        else:
            # User ID in session but not found in database - clear session and redirect
            session.pop("user_id", None)
    return redirect(url_for('homepage'))


@application.route('/api/logout', methods=["POST"])
def logout():
    session.pop("user_id", None)
    return redirect(url_for('homepage'))

#prints out thes session info - used for debuggiing
@application.route('/debug/session')
def debug_session():
    return dict(session)
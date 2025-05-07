from flask import render_template, request, redirect, session, url_for, flash
from app.models import User, Unit, Task
from app.forms import SignUpForm, LoginForm, AddUnitForm
from app import application, db
from datetime import datetime
import logging


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
                error = "Please try again later, an error occurred"
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
            current_year = datetime.now().year  # Get the current year
            return render_template('dashboard.html', user=user, current_year=current_year)
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
        form = AddUnitForm()
        user_id = session["user_id"]
        
        # Query the database to get the complete user object
        user = User.query.get(user_id)
        
        # Check if user exists in database
        if user:
            return render_template('settings.html', user=user, form=form)
        else:
            # User ID in session but not found in database - clear session and redirect
            session.pop("user_id", None)
    return redirect(url_for('homepage'))

@application.route('/api/add_unit', methods=["POST"])
def add_unit():
    if "user_id" in session: 
        form = AddUnitForm()
        user_id = session["user_id"]
        
        # Query the database to get the complete user object
        user = User.query.get(user_id)
        
        # Check if user exists in database
        if user and form.validate_on_submit():
            try:
                name = form.name.data
                unit_code = form.unit_code.data
                semester = form.semester.data
                year = form.year.data
                goal_grade = form.goal_grade.data
                

                # Check if the unit already exists for the user
                existing_unit = Unit.query.filter_by(
                    name=name,
                    unit_code=unit_code,
                    semester=semester,
                    year=year,
                    goal_grade=form.goal_grade.data,
                    user_id=user_id
                ).first()

                if existing_unit:
                    error = "This unit has already been added."
                    return render_template('settings.html', user=user, form=form, error=error)

                new_unit = Unit(
                    name=name, 
                    unit_code=unit_code,
                    semester=semester,
                    year=year,
                    goal_grade=form.goal_grade.data,
                    user_id=user_id
                )

                db.session.add(new_unit)
                db.session.commit()  # Commit to save the new unit

                return render_template('settings.html', user=user, form=form, success="Unit added successfully")
            except Exception as e:
                db.session.rollback()
                error = "Please try again later, an error occurred"
                return render_template('settings.html', user=user, form=form, error=error)

@application.route("/api/update_unit", methods=["POST"])
def update_unit():
    if "user_id" in session: 
        form = AddUnitForm()
        user_id = session["user_id"]
        
        # Query the database to get the complete user object
        user = User.query.get(user_id)
        unit_id = request.form.get("unit_id")
        unit = Unit.query.get(unit_id)

        if not unit:
            flash("Unauthorized or invalid unit.", "danger")
            return redirect(url_for("dashboard"))

        # Update fields
        unit.name = request.form["name"]
        unit.unit_code = request.form["unit_code"]
        unit.year = request.form["year"]
        unit.semester = request.form["semester"]
        unit.goal_grade = request.form["goal_grade"]  

        db.session.commit()
        flash("Unit updated successfully!", "success")
        return redirect(url_for("dashboard"))
    return redirect(url_for('homepage'))

import logging

@application.route('/api/delete_unit', methods=["POST"])
def delete_unit():
    if "user_id" in session:
        user_id = session["user_id"]
        unit_id = request.form.get("unit_id")

        logging.info(f"Attempting to delete unit. User ID: {user_id}, Unit ID: {unit_id}")

        # Query the unit to delete
        unit = Unit.query.filter_by(id=unit_id, user_id=user_id).first()

        if unit:
            try:
                db.session.delete(unit)
                db.session.commit()
                logging.info("Unit deleted successfully.")
                return {"success": True}, 200
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error deleting unit: {e}")
                return {"success": False, "error": "An error occurred while deleting the unit."}, 500
        else:
            logging.warning("Unit not found or unauthorized action.")
            return {"success": False, "error": "Unit not found or unauthorized action."}, 404

    logging.warning("Unauthorized access.")
    return {"success": False, "error": "Unauthorized access."}, 401



@application.route('/api/logout', methods=["POST"])
def logout():
    session.pop("user_id", None)
    return redirect(url_for('homepage'))

#prints out thes session info - used for debugging
#Remove at production
@application.route('/debug/session')
def debug_session():
    return dict(session)

@application.route('/debug/db')
def debug_db():
    with application.app_context():  # Ensure context is active
        users = User.query.all()
        units = Unit.query.all()
        return {
            "users": [str(user) for user in users],
            "units": [str(unit) for unit in units]
        }
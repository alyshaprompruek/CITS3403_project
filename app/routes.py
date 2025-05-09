from flask import render_template, request, redirect, session, url_for, flash
from app.models import User, Unit, Task
from app.forms import SignUpForm, LoginForm, AddUnitForm
from app import application, db
from app.services.analytics import calculate_user_statistics


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
            stats = calculate_user_statistics(user_id)
            print(">>> unit_scores:", stats["unit_scores"])
            print(">>> recommendations:", stats["recommendations"])
            print(">>> top_unit:", stats["top_unit"])
            print(">>> wam:", stats["wam"])

            user.wam = stats["wam"]
            user.gpa = stats["gpa"]
            user.top_unit = stats["top_unit"]

            return render_template("dashboard.html", user=user, unit_scores=stats["unit_scores"],
                                   recommendations=stats["recommendations"],
                                   ranked_units=stats["ranked_units"]
                                   )
        else:
            # User ID in session but not found in database - clear session and redirect
            session.pop("user_id", None)
    return redirect(url_for('homepage'))

@application.route('/track_grades')
def track_grades():
    if "user_id" in session: 
        form = AddUnitForm()
        user_id = session["user_id"]
        
        # Query the database to get the complete user object
        user = User.query.get(user_id)
        
        # Check if user exists in database
        if user:
            return render_template('track_grades.html', user=user, form=form)
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

                target_score = request.form.get("target_score", None)
                outline_url = request.form.get("outline_url", None)

                # Check if the unit already exists for the user
                existing_unit = Unit.query.filter_by(
                    name=name,
                    unit_code=unit_code,
                    semester=semester,
                    year=year,
                    user_id=user_id
                ).first()

                if existing_unit:
                    error = "This unit has already been added."
                    return render_template('track_grades.html', user=user, form=form, error=error)

                new_unit = Unit(
                    name=name,
                    unit_code=unit_code,
                    semester=semester,
                    year=year,
                    user_id=user_id,
                    target_score=target_score,
                    outline_url=outline_url
                )

                db.session.add(new_unit)
                db.session.commit()  # Commit to save the new unit

                return render_template('track_grades.html', user=user, form=form, success="Unit added successfully")
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
        unit.target_score = request.form.get("target_score", unit.target_score)
        unit.outline_url = request.form.get("outline_url", unit.outline_url)

        db.session.commit()
        flash("Unit updated successfully!", "success")
        return redirect(url_for("dashboard"))
    return redirect(url_for('homepage'))



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


# API endpoint to serve units and their tasks for the logged-in user
@application.route("/api/units")
def get_units():
    if "user_id" not in session:
        return {"error": "Unauthorized"}, 401

    user_id = session["user_id"]
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    unit_list = []
    for unit in Unit.query.filter_by(user_id=user_id).all():
        tasks = Task.query.filter_by(user_id=user_id, unit_id=unit.id).all()
        assessments = []
        for task in tasks:
            assessments.append({
                "task_name": task.task_name,
                "score": str(task.grade),
                "weight": f"{task.weighting}%",
                "date": task.date,
                "note": task.notes
            })

        unit_list.append({
            "unit_id": unit.id,
            "unit_name": unit.unit_code,
            "target_score": unit.target_score,
            "assessments": assessments
        })

    return {"units": unit_list}



# API endpoint to add an assessment/task directly
@application.route('/api/add_assessment', methods=["POST"])
def add_assessment():
    if "user_id" not in session:
        return {"error": "Unauthorized"}, 401

    user_id = session["user_id"]
    data = request.json
    try:
        # Temporary default value for `type` field to avoid database constraint errors.
        # TODO: Replace with user-selected type from frontend (e.g., exam, assignment, etc.)
        new_task = Task(
            user_id=user_id,
            unit_id=data["unit_id"],
            task_name=data["task_name"],
            grade=data["score"],
            weighting=float(data["weight"].strip('%')),
            date=data["date"],
            notes=data.get("note", ""),
            type=data["type"] if "type" in data else "other"  # Default to 'other' if not provided
        )
        db.session.add(new_task)
        db.session.commit()
        return {"success": True}
    except Exception as e:
        import sys
        db.session.rollback()
        return {"success": False, "error": str(e)}, 500
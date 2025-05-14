from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from app.models import User, Unit, Task
from app.forms import SignUpForm, LoginForm, AddUnitForm, AddTaskForm
from app import application, db
from app.services.analytics import calculate_user_statistics
from app.utils import fetch_unit_details_and_summary  # Import the utility function
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

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

            editUnitForm = AddUnitForm()

            return render_template("dashboard.html", user=user, unit_scores=stats["unit_scores"],
                                   recommendations=stats["recommendations"],
                                   ranked_units=stats["ranked_units"],
                                   editUnitForm=editUnitForm,
                                   )
        else:
            # User ID in session but not found in database - clear session and redirect
            session.pop("user_id", None)
    return redirect(url_for('homepage'))

@application.route('/track_grades', methods=['GET', 'POST'])
def track_grades():
    if 'user_id' not in session:
        return redirect(url_for('homepage'))

    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('homepage'))

    add_unit_form = AddUnitForm()
    add_task_form = AddTaskForm()

    # Sort units by year (descending), then semester (descending)
    sorted_units = sorted(user.units, key=lambda u: (-u.year, -int(u.semester)))

    # Get selected unit
    selected_unit = None
    unit_id = request.args.get('unit_id')  # Check for unit_id in query parameters
    if unit_id:
        selected_unit = Unit.query.filter_by(id=unit_id, user_id=user.student_id).first()
    elif request.method == 'POST' and 'unit_id' in request.form:
        unit_id = request.form.get('unit_id')
        selected_unit = Unit.query.filter_by(id=unit_id, user_id=user.student_id).first()
    elif sorted_units:  # Default to most recent unit if none selected
        selected_unit = sorted_units[0]

    # Prepopulate unit_id in add_task_form if selected_unit exists
    if selected_unit:
        add_task_form.unit_id.data = selected_unit.id

    # Serialize tasks for the selected unit
    serialized_tasks = []
    if selected_unit:
        serialized_tasks = [
            {
                'task_name': task.task_name,
                'grade': task.grade,
                'weighting': task.weighting,
                'date': task.date,
                'notes': task.notes,
                'type': task.type
            }
            for task in selected_unit.tasks
        ]

    # Get AI content
    ai_summary = ''
    ai_suggestions = ''
    if selected_unit:
        # Summary
        ai_summary = selected_unit.summary or 'No summary available for this unit.'
        
        # Suggestions
        suggestions = []
        if selected_unit.links and isinstance(selected_unit.links, list) and selected_unit.links:
            suggestions.append('<p class="mb-2">Recommended resources:</p><ul class="list-unstyled">')
            for link in selected_unit.links:
                if isinstance(link, dict) and 'name' in link and 'url' in link:
                    suggestions.append(f'<li><a href="{link["url"]}" target="_blank" rel="noopener noreferrer" class="text-info">{link["name"]}</a></li>')
            suggestions.append('</ul>')
        else:
            suggestions.append('<p class="mb-2 text-muted">No learning resources available for this unit.</p>')

        if selected_unit.outline_url:
            suggestions.append(
                f'<p class="mb-2">Course Outline:</p>'
                f'<p><a href="{selected_unit.outline_url}" target="_blank" rel="noopener noreferrer" class="text-info">View Course Outline</a></p>'
            )
        
        # Study tips based on task grades
        valid_tasks = [t for t in selected_unit.tasks if t.grade is not None]
        if valid_tasks:
            avg_grade = sum(t.grade for t in valid_tasks) / len(valid_tasks)
            if avg_grade < 70:
                suggestions.append(
                    f'<div class="alert alert-warning mt-3">'
                    f'<strong>Study Tip:</strong> Your average grade is {avg_grade:.1f}%. '
                    f'Focus on the resources above and schedule regular study sessions.'
                    f'</div>'
                )
            elif avg_grade >= 90:
                suggestions.append(
                    f'<div class="alert alert-success mt-3">'
                    f'<strong>Great Job!</strong> Your average grade is {avg_grade:.1f}%. '
                    f'Keep up the excellent work!'
                    f'</div>'
                )
            else:
                suggestions.append(
                    f'<div class="alert alert-info mt-3">'
                    f'<strong>Study Tip:</ xmaxima:'
                    f'<strong>Study Tip:</strong> Your average grade is {avg_grade:.1f}%. '
                    f'Regular review of course materials can help maintain your performance.'
                    f'</div>'
                )
        
        ai_suggestions = ''.join(suggestions)

    return render_template(
        'track_grades.html',
        user=user,
        sorted_units=sorted_units,
        addUnitForm=add_unit_form,
        addTaskForm=add_task_form,
        selected_unit=selected_unit,
        ai_summary=ai_summary,
        ai_suggestions=ai_suggestions,
        task_error=request.args.get('task_error'),
        add_unit_success=request.args.get('add_unit_success'),
        add_unit_error=request.args.get('add_unit_error'),
        serialized_tasks=serialized_tasks  # Pass serialized tasks
    )

@application.route('/api/add_task', methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for('track_grades', task_error='Unauthorized'))

    user_id = session["user_id"]
    add_task_form = AddTaskForm()

    if not add_task_form.validate_on_submit():
        return redirect(url_for('track_grades', unit_id=add_task_form.unit_id.data, task_error='Invalid form data'))

    unit_id = add_task_form.unit_id.data
    unit = Unit.query.get(unit_id)
    if not unit or unit.user_id != user_id:
        return redirect(url_for('track_grades', unit_id=unit_id, task_error='Invalid unit'))

    # Calculate total weighting of existing tasks
    existing_weight = sum(task.weighting for task in unit.tasks if task.weighting is not None)
    new_weight = add_task_form.weight.data
    if existing_weight + new_weight > 100:
        return redirect(url_for('track_grades', unit_id=unit_id, task_error='Total weighting cannot exceed 100%'))

    try:
        new_task = Task(
            user_id=user_id,
            unit_id=unit_id,
            task_name=add_task_form.task_name.data,
            grade=add_task_form.score.data,
            weighting=new_weight,
            date=add_task_form.date.data.strftime('%Y-%m-%d'),
            notes=add_task_form.note.data or "",
            type=add_task_form.type.data
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('track_grades', unit_id=unit_id, success='Task added successfully'))
    except ValueError as e:
        db.session.rollback()
        return redirect(url_for('track_grades', unit_id=unit_id, task_error=f'Invalid numeric value: {str(e)}'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('track_grades', unit_id=unit_id, task_error=str(e)))

@application.route('/api/add_unit', methods=["POST"])
def add_unit():
    if "user_id" not in session:
        return redirect(url_for('homepage'))

    user_id = session["user_id"]
    add_unit_form = AddUnitForm()
    user = User.query.get(user_id)

    if not user:
        session.pop('user_id', None)
        return redirect(url_for('homepage'))

    if not add_unit_form.validate_on_submit():
        return redirect(url_for('track_grades', add_unit_error='Invalid form data'))

    try:
        name = add_unit_form.name.data
        unit_code = add_unit_form.unit_code.data
        semester = add_unit_form.semester.data
        year = add_unit_form.year.data

        # Check if the unit already exists for the user
        existing_unit = Unit.query.filter_by(
            name=name,
            unit_code=unit_code,
            semester=semester,
            year=year,
            user_id=user_id
        ).first()

        if existing_unit:
            return redirect(url_for('track_grades', add_unit_error='This unit has already been added'))

        # Fetch summary and links using API
        summary, links = fetch_unit_details_and_summary(unit_code, API_KEY)

        # Create new unit with summary and links
        new_unit = Unit(
            name=name,
            unit_code=unit_code,
            semester=semester,
            year=year,
            user_id=user_id,
            target_score=None,
            outline_url=None,
            summary=summary,
            links=links
        )

        db.session.add(new_unit)
        db.session.commit()

        # Redirect to track_grades with the new unit selected
        return redirect(url_for('track_grades', unit_id=new_unit.id, add_unit_success='Unit added successfully'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('track_grades', add_unit_error=f'Error adding unit: {str(e)}'))

@application.route("/api/update_unit", methods=["POST"])
def update_unit():
    if "user_id" not in session:
        return redirect(url_for("homepage"))

    addUnitForm = addUnitForm()
    if addUnitForm.validate_on_submit():
        user_id = session["user_id"]
        unit_pk = request.addUnitForm.get("unit_pk")
        unit = Unit.query.get(unit_pk)

        if not unit or unit.user_id != user_id:
            flash("Unauthorized or invalid unit.", "danger")
            return redirect(url_for("dashboard"))

        # Store old unit code for comparison
        old_code = unit.unit_code

        # Update unit attributes from form data
        unit.name = addUnitForm.name.data
        unit.unit_code = addUnitForm.unit_code.data
        unit.year = addUnitForm.year.data
        unit.semester = addUnitForm.semester.data

        # Check if unit code has changed and update summary/links if needed
        if unit.unit_code != old_code:
            summary, links = fetch_unit_details_and_summary(unit.unit_code, API_KEY)
            unit.summary = summary
            unit.links = links

        try:
            db.session.commit()
            flash("Unit updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating unit: {str(e)}", "danger")
    else:
        # Provide specific error messages for form validation failures
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "danger")

    return redirect(url_for("dashboard"))


@application.route('/api/logout', methods=["POST"])
def logout():
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



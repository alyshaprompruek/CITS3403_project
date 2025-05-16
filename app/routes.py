from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from flask_login import login_required, login_user, logout_user, current_user
from app.models import User, Unit, Task, ShareAccess
from app.forms import SignUpForm, LoginForm, AddUnitForm, AddTaskForm, EditUnitForm, ShareForm
from datetime import datetime, timedelta
import secrets
from app import application, db
from app.services.analytics import calculate_user_statistics
from app.utils import fetch_unit_details_and_summary  # Import the utility function
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

@application.route('/')
def homepage():
    return render_template('homepage.html')

@application.route("/share/view/<token>")
@login_required
def view_shared_dashboard(token):
    share = ShareAccess.query.filter_by(share_token=token).first()

    if not share or share.to_user != current_user.email:
        flash("You do not have permission to view this shared dashboard, here is your own dashboard.", "danger")
        return redirect(url_for("dashboard"))

    #Check its not expired
    if share.expires_at < datetime.utcnow():
        flash("This shared dashboard link has expired, here is your own dashboard.", "danger")
        return redirect(url_for("dashboard"))

    shared_user = User.query.filter_by(email=share.from_user).first()
    if not shared_user:
        flash("The original shared user no longer exists, here is your own dashboard.", "danger")
        return redirect(url_for("dashboard"))

    stats = calculate_user_statistics(shared_user)
    editUnitForm = AddUnitForm()

    return render_template(
        "dashboard.html",
        user=shared_user,
        wam=stats["wam"],
        gpa=stats["gpa"],
        top_unit=stats["top_unit"],
        unit_scores=stats["unit_scores"],
        recommendations=stats["recommendations"],
        ranked_units=stats["ranked_units"],
        editUnitForm=editUnitForm,
        readonly_view=True,
        shared_from=share.from_user,
        shared_unit_id=share.unit_selection
    )

@application.route('/signup', methods=["GET","POST"])
def signup():
    form = SignUpForm()
    error = None

    if request.method == "GET":
        return render_template('signup.html', form=form, error=error)

    elif request.method == "POST":
        if form.validate_on_submit():
            email    = form.email.data
            password = form.password.data

         
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error = "Email already registered. Please log in or use a different address."
                return render_template('signup.html', form=form, error=error)

            try:
                # Create & hash
                new_user = User(email=email)
                new_user.set_password(password)

                db.session.add(new_user)
                db.session.commit()

                # Put the user as current_user using the login_user function
                login_user(new_user)
                return redirect(url_for('dashboard'))

            except Exception as e:
                db.session.rollback()
                error = f"An error occurred during registration: {e}"

        else:
            # Collect all form validation errors into a single message
            error_messages = []
            for field, errors in form.errors.items():
                for err in errors:
                    error_messages.append(err)

            error = " ".join(error_messages)  # Or use '<br>'.join(...) for line breaks

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
                if user and user.check_password(password): #hash
                    login_user(user)
                    return redirect(url_for('dashboard'))
                else:
                    error = "Invalid email or password."
            
            except Exception as e:
                error = "Please try again later, an error occurred"
        else:
            error = "Please check your information and try again."
            
        return render_template('login.html', form=form, error=error)

@application.route('/dashboard')
@login_required
def dashboard():
    stats = calculate_user_statistics(current_user)

    current_user.wam = stats["wam"]
    current_user.gpa = stats["gpa"]
    current_user.top_unit = stats["top_unit"]

    editUnitForm = EditUnitForm()

    return render_template("dashboard.html", user=current_user, unit_scores=stats["unit_scores"],
                            recommendations=stats["recommendations"],
                            ranked_units=stats["ranked_units"],
                            editUnitForm=editUnitForm,
                            )

@application.route('/track_grades', methods=['GET', 'POST'])
@login_required
def track_grades():
    add_unit_form = AddUnitForm()
    add_task_form = AddTaskForm()
    edit_unit_form = EditUnitForm()

    # Sort units by year (descending), then semester (descending)
    sorted_units = sorted(current_user.units, key=lambda u: (-u.year, -int(u.semester)))

    # Get selected unit
    selected_unit = None
    unit_id = None

    # Prioritize form data (from unit selection buttons)
    if request.method == 'POST' and 'unit_id' in request.form:
        unit_id = request.form.get('unit_id')
    elif request.args.get('unit_id'):  # Fallback to query parameters
        unit_id = request.args.get('unit_id')

    if unit_id:
        selected_unit = Unit.query.filter_by(id=unit_id, user_id=current_user.student_id).first()
        if not selected_unit:
            flash('Invalid unit selected.', 'danger')
            return redirect(url_for('track_grades'))  # Clear query params

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
            avg_grade = sum(t.grade * t.weighting for t in valid_tasks) / sum(t.weighting for t in valid_tasks)
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
                    f'<strong>Study Tip:</strong> Your average grade is {avg_grade:.1f}%. '
                    f'Regular review of course materials can help maintain your performance.'
                    f'</div>'
                )
        
        ai_suggestions = ''.join(suggestions)

    return render_template(
        'track_grades.html',
        user=current_user,
        sorted_units=sorted_units,
        addUnitForm=add_unit_form,
        addTaskForm=add_task_form,
        editUnitForm=edit_unit_form,
        selected_unit=selected_unit,
        ai_summary=ai_summary,
        ai_suggestions=ai_suggestions,
        serialized_tasks=serialized_tasks
    )

@application.route('/delete_unit', methods=['POST'])
@login_required
def delete_unit():
    unit_id = request.form.get("unit_id")
    unit = Unit.query.get(unit_id)

    if unit and unit.user_id == current_user.student_id:
        try:
            db.session.delete(unit)
            db.session.commit()
            flash("Unit and associated tasks deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to delete unit: {str(e)}", "danger")
    else:
        flash("Unauthorized or invalid unit.", "danger")

    return redirect(url_for("track_grades"))

@application.route('/api/add_task', methods=["POST"])
@login_required
def add_task():
    add_task_form = AddTaskForm()

    if not add_task_form.validate_on_submit():
        flash('Invalid form data. Please check your input.', 'danger')
        return redirect(url_for('track_grades', unit_id=add_task_form.unit_id.data))

    unit_id = add_task_form.unit_id.data
    unit = Unit.query.get(unit_id)
    if not unit or unit.user_id != current_user.student_id:
        flash('Invalid unit selected.', 'danger')
        return redirect(url_for('track_grades', unit_id=unit_id))

    # Calculate total weighting of existing tasks
    existing_weight = sum(task.weighting for task in unit.tasks if task.weighting is not None)
    new_weight = add_task_form.weight.data
    if existing_weight + new_weight > 100:
        flash('Total weighting cannot exceed 100%.', 'danger')
        return redirect(url_for('track_grades', unit_id=unit_id))

    try:
        new_task = Task(
            user_id=current_user.student_id,
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
        flash('Task added successfully!', 'success')
        return redirect(url_for('track_grades', unit_id=unit_id))
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid numeric value: {str(e)}', 'danger')
        return redirect(url_for('track_grades', unit_id=unit_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding task: {str(e)}', 'danger')
        return redirect(url_for('track_grades', unit_id=unit_id))

@application.route('/api/add_unit', methods=["POST"])
@login_required
def add_unit():
    add_unit_form = AddUnitForm()

    if not add_unit_form.validate_on_submit():
        print(add_unit_form.errors)  # Debugging: Print form validation errors to the console
        flash('Invalid form data. Please check your input.', 'danger')
        return redirect(url_for('track_grades'))

    try:
        name = add_unit_form.name.data
        unit_code = add_unit_form.unit_code.data
        semester = add_unit_form.semester.data
        year = add_unit_form.year.data
        target_score = add_unit_form.target_score.data

        # Check if the unit already exists for the user
        existing_unit = Unit.query.filter_by(
            name=name,
            unit_code=unit_code,
            semester=semester,
            year=year,
            user_id=current_user.student_id
        ).first()

        if existing_unit:
            flash('This unit has already been added.', 'danger')
            return redirect(url_for('track_grades'))

        # Fetch summary and links using API
        summary, links = fetch_unit_details_and_summary(unit_code, API_KEY)

        # Create new unit with summary and links
        new_unit = Unit(
            name=name,
            unit_code=unit_code,
            semester=semester,
            year=year,
            user_id=current_user.student_id,
            target_score=target_score,
            outline_url=None,
            summary=summary,
            links=links
        )

        db.session.add(new_unit)
        db.session.commit()

        flash('Unit added successfully!', 'success')
        return redirect(url_for('track_grades', unit_id=new_unit.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding unit: {str(e)}', 'danger')
        return redirect(url_for('track_grades'))

@application.route("/api/update_unit", methods=["POST"])
@login_required
def update_unit():
    editUnitForm = EditUnitForm()
    try:
        unit_id = editUnitForm.unit_id.data
    except:
        unit_id = None
    if editUnitForm.validate_on_submit():
        unit_id = editUnitForm.unit_id.data  # Use unit_id from the form
        unit = Unit.query.get(unit_id)

        if not unit or unit.user_id != current_user.student_id:
            flash("Unauthorized or invalid unit.", "danger")
            return redirect(url_for("dashboard"))

        # Store old unit code for comparison
        old_code = unit.unit_code

        # Update unit attributes from form data
        unit.name = editUnitForm.name.data
        unit.target_score = editUnitForm.target_score.data
        unit.unit_code = editUnitForm.unit_code.data
        unit.year = editUnitForm.year.data
        unit.semester = editUnitForm.semester.data

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
        for field, errors in editUnitForm.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "danger")

    return redirect(url_for("track_grades", unit_id=unit_id))

@application.route('/api/logout', methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@application.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)


# --- Sharing page and create_share logic ---
@application.route('/sharing', methods=['GET'])
@login_required
def sharing_page():
    form = ShareForm()

    form.unit_selection.choices = [(unit.id, f"{unit.unit_code} | Sem {unit.semester} {unit.year}") for unit in current_user.units]
    # Fetch share records
    outgoing_shares = ShareAccess.query.filter_by(from_user=current_user.email).all()
    incoming_shares = ShareAccess.query.filter_by(to_user=current_user.email).all()
    return render_template('sharing.html', user=current_user, form=form,
                           outgoing_shares=outgoing_shares,
                           incoming_shares=incoming_shares)

@application.route('/create_share', methods=['POST'])
@login_required
def create_share():
    form = ShareForm()

    # Set the choices for unit_selection before validation to avoid inconsistency
    form.unit_selection.choices = [(unit.id, f"{unit.unit_code} | Sem {unit.semester} {unit.year}") 
                                  for unit in current_user.units]
    
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        expires_at = form.expires_at.data #is just date not datetime
        unit_selection = form.unit_selection.data

        # Ensure the recipient email is not the same as the current user's email
        if email == current_user.email:
            flash("You cannot share with yourself.", "danger")
            return redirect(url_for('sharing_page'))

        # Confirm that the email exists in the User table
        recipient_user = User.query.filter_by(email=email).first()
        if not recipient_user:
            flash("The specified email does not belong to a registered user.", "danger")
            return redirect(url_for('sharing_page'))
        
        # Check if the expiry date is in the past
        if expires_at < datetime.utcnow().date():
            flash("The expiry date cannot be in the past.", "danger")
            return redirect(url_for('sharing_page'))
        
        token = secrets.token_urlsafe(16)

        new_share = ShareAccess(
            share_token=token,
            from_user=current_user.email,
            to_user=email, 
            unit_selection=unit_selection,
            expires_at=expires_at #sqlite will convert to datetime object at midnight
        )

        db.session.add(new_share)
        db.session.commit()

        flash(f"Shared with {email} (expires: {expires_at})", "success")
        return redirect(url_for('sharing_page'))

    flash("Failed to share. Please check the input.", "danger")
    return redirect(url_for('sharing_page'))

@application.route('/remove_share', methods=['POST'])
@login_required
def remove_share():
    share_id = request.form.get('share_id')
    share = ShareAccess.query.get(share_id)
    if share and share.from_user == current_user.email:
        db.session.delete(share)
        db.session.commit()
        flash("Share access successfully removed.", "success")
    else:
        flash("Could not remove share access.", "danger")
    return redirect(url_for('sharing_page'))


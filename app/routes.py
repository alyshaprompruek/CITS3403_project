import os
import secrets
from datetime import datetime, timedelta

from flask import (
    render_template, request, redirect, url_for,
    flash
)
from flask_login import (
    login_required, login_user,
    logout_user, current_user
)

from app import application, db
from app.models import User, Unit, Task, ShareAccess
from app.forms import (
    SignUpForm, LoginForm,
    AddUnitForm, AddTaskForm,
    EditUnitForm, ShareForm
)
from app.services.analytics import calculate_user_statistics
from app.utils import fetch_unit_details_and_summary
from dotenv import load_dotenv

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
        flash(
            "You do not have permission to view this shared dashboard, here is your own dashboard.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    if share.expires_at < datetime.utcnow():
        flash(
            "This shared dashboard link has expired, here is your own dashboard.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    shared_user = User.query.filter_by(email=share.from_user).first()
    if not shared_user:
        flash(
            "The original shared user no longer exists, here is your own dashboard.",
            "danger"
        )
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


@application.route('/signup', methods=["GET", "POST"])
def signup():
    form = SignUpForm()
    error = None

    if request.method == "GET":
        return render_template('signup.html', form=form, error=error)

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error = "Email already registered. Please log in or use a different address."
            return render_template('signup.html', form=form, error=error)

        try:
            new_user = User(email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            error = f"An error occurred during registration: {e}"
    else:
        # Collect validation errors
        error = " ".join(
            err for errs in form.errors.values() for err in errs
        )

    return render_template('signup.html', form=form, error=error)


@application.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    error = None

    if request.method == "GET":
        return render_template('login.html', form=form, error=error)

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid email or password."
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

    return render_template(
        "dashboard.html",
        user=current_user,
        unit_scores=stats["unit_scores"],
        recommendations=stats["recommendations"],
        ranked_units=stats["ranked_units"],
        editUnitForm=editUnitForm,
    )


@application.route('/track_grades', methods=['GET', 'POST'])
@login_required
def track_grades():
    # 1. Instantiate forms
    add_unit_form  = AddUnitForm()
    add_task_form  = AddTaskForm()
    edit_unit_form = EditUnitForm()

    # 2. Sort units for sidebar
    sorted_units = sorted(
        current_user.units,
        key=lambda u: (-u.year, -int(u.semester))
    )

    # 3. Determine selected_unit
    selected_unit = None
    if request.method == 'POST' and 'unit_id' in request.form:
        unit_id = request.form['unit_id']
    else:
        unit_id = request.args.get('unit_id')

    if unit_id:
        selected_unit = Unit.query.filter_by(
            id=unit_id,
            user_id=current_user.student_id
        ).first()
        if not selected_unit:
            flash('Invalid unit selected.', 'danger')
            return redirect(url_for('track_grades'))

    # 4. Pre-populate task form
    if selected_unit:
        add_task_form.unit_id.data = selected_unit.id

    # 5. Build AI summary & suggestions
    ai_summary     = ''
    ai_suggestions = ''
    if selected_unit:
        ai_summary = selected_unit.summary or 'No summary available for this unit.'
        suggestions = []

        if selected_unit.links:
            suggestions.append('<p class="mb-2">Recommended resources:</p><ul>')
            for l in selected_unit.links:
                suggestions.append(
                    f'<li><a href="{l["url"]}" target="_blank">{l["name"]}</a></li>'
                )
            suggestions.append('</ul>')
        else:
            suggestions.append('<p class="text-muted">No resources available.</p>')

        if selected_unit.outline_url:
            suggestions.append(
                '<p class="mb-2">Course Outline:</p>'
                f'<p><a href="{selected_unit.outline_url}" target="_blank">View Outline</a></p>'
            )

        valid_tasks = [t for t in selected_unit.tasks if t.grade is not None]
        if valid_tasks:
            avg_grade = sum(t.grade * t.weighting for t in valid_tasks) \
                        / sum(t.weighting for t in valid_tasks)
            if avg_grade < 70:
                suggestions.append(
                    f'<div class="alert alert-warning">'
                    f'Your avg grade is {avg_grade:.1f}%. Focus study on recommended resources.'
                    '</div>'
                )
            elif avg_grade >= 90:
                suggestions.append(
                    f'<div class="alert alert-success">'
                    f'Great job! Avg grade {avg_grade:.1f}%.</div>'
                )
            else:
                suggestions.append(
                    f'<div class="alert alert-info">'
                    f'Avg grade {avg_grade:.1f}%. Keep up the review.</div>'
                )

        ai_suggestions = ''.join(suggestions)

    # ── NEW: Compute target_score & serialize tasks for Chart.js ──
    target_score = float(selected_unit.target_score) if selected_unit else 0
    serialized_tasks = [
        {
            'task_name': t.task_name,
            'grade':     t.grade,
            'weighting': t.weighting,
            'date':      t.date,
            'notes':     t.notes,
            'type':      t.type
        }
        for t in (selected_unit.tasks if selected_unit else [])
    ]

    # 6. Render the template with everything
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
        serialized_tasks=serialized_tasks,
        target_score=target_score
    )


@application.route('/delete_unit', methods=['POST'])
@login_required
def delete_unit():
    unit_id = request.form.get("unit_id")
    unit = Unit.query.get(unit_id)

    if unit and unit.user_id == current_user.student_id:
        try:
            ShareAccess.query.filter_by(unit_selection=unit_id).delete()
            db.session.delete(unit)
            db.session.commit()
            flash("Unit and associated tasks deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to delete unit: {e}", "danger")
    else:
        flash("Unauthorized or invalid unit.", "danger")

    return redirect(url_for("track_grades"))


@application.route('/api/add_task', methods=["POST"])
@login_required
def add_task():
    form = AddTaskForm()
    if not form.validate_on_submit():
        flash('Invalid form data. Please check your input.', 'danger')
        return redirect(url_for('track_grades', unit_id=form.unit_id.data))

    unit = Unit.query.get(form.unit_id.data)
    if not unit or unit.user_id != current_user.student_id:
        flash('Invalid unit selected.', 'danger')
        return redirect(url_for('track_grades', unit_id=form.unit_id.data))

    existing_weight = sum(t.weighting for t in unit.tasks if t.weighting)
    if existing_weight + form.weight.data > 100:
        flash('Total weighting cannot exceed 100%.', 'danger')
        return redirect(url_for('track_grades', unit_id=form.unit_id.data))

    try:
        new_task = Task(
            user_id=current_user.student_id,
            unit_id=unit.id,
            task_name=form.task_name.data,
            grade=form.score.data,
            weighting=form.weight.data,
            date=form.date.data.strftime('%Y-%m-%d'),
            notes=form.note.data or "",
            type=form.type.data
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding task: {e}', 'danger')

    return redirect(url_for('track_grades', unit_id=unit.id))


@application.route('/api/add_unit', methods=["POST"])
@login_required
def add_unit():
    form = AddUnitForm()
    if not form.validate_on_submit():
        flash('Invalid form data. Please check your input.', 'danger')
        return redirect(url_for('track_grades'))

    ts = float(form.target_score.data)
    summary, links = fetch_unit_details_and_summary(form.unit_code.data, API_KEY)

    new_unit = Unit(
        name=form.name.data,
        unit_code=form.unit_code.data,
        semester=form.semester.data,
        year=int(form.year.data),
        user_id=current_user.student_id,
        target_score=ts,
        outline_url=None,
        summary=summary,
        links=links
    )
    db.session.add(new_unit)
    db.session.commit()
    flash('Unit added successfully!', 'success')
    return redirect(url_for('track_grades', unit_id=new_unit.id))


@application.route("/api/update_unit", methods=["POST"])
@login_required
def update_unit():
    form = EditUnitForm()
    unit_id = form.unit_id.data or None

    if form.validate_on_submit():
        unit = Unit.query.get(int(unit_id))
        if not unit or unit.user_id != current_user.student_id:
            flash("Unauthorized or invalid unit.", "danger")
            return redirect(url_for("track_grades"))

        old_code = unit.unit_code
        unit.name         = form.name.data
        unit.unit_code    = form.unit_code.data
        unit.semester     = form.semester.data
        unit.year         = int(form.year.data)
        unit.target_score = float(form.target_score.data)

        if unit.unit_code != old_code:
            summary, links = fetch_unit_details_and_summary(unit.unit_code, API_KEY)
            unit.summary = summary
            unit.links   = links

        db.session.commit()
        flash("Unit updated successfully!", "success")
    else:
        for f, errs in form.errors.items():
            for e in errs:
                flash(f"{f}: {e}", "danger")

    return redirect(url_for('track_grades', unit_id=unit_id))


@application.route('/api/logout', methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for('homepage'))


@application.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)


@application.route('/sharing', methods=['GET'])
@login_required
def sharing_page():
    form = ShareForm()
    form.unit_selection.choices = [
        (u.id, f"{u.unit_code} | Sem {u.semester} {u.year}")
        for u in current_user.units
    ]
    outgoing_shares = ShareAccess.query.filter_by(from_user=current_user.email).all()
    incoming_shares = ShareAccess.query.filter_by(to_user=current_user.email).all()
    return render_template(
        'sharing.html',
        user=current_user,
        form=form,
        outgoing_shares=outgoing_shares,
        incoming_shares=incoming_shares
    )


@application.route('/create_share', methods=['POST'])
@login_required
def create_share():
    form = ShareForm()
    form.unit_selection.choices = [
        (u.id, f"{u.unit_code} | Sem {u.semester} {u.year}")
        for u in current_user.units
    ]

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        expires_at = form.expires_at.data
        unit_selection = form.unit_selection.data

        if email == current_user.email:
            flash("You cannot share with yourself.", "danger")
            return redirect(url_for('sharing_page'))

        recipient_user = User.query.filter_by(email=email).first()
        if not recipient_user:
            flash("The specified email does not belong to a registered user.", "danger")
            return redirect(url_for('sharing_page'))

        if expires_at < datetime.utcnow().date():
            flash("The expiry date cannot be in the past.", "danger")
            return redirect(url_for('sharing_page'))

        token = secrets.token_urlsafe(16)
        new_share = ShareAccess(
            share_token=token,
            from_user=current_user.email,
            to_user=email,
            unit_selection=unit_selection,
            expires_at=expires_at
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

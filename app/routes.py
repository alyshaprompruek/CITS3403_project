from flask import render_template, request, redirect, session, url_for, flash
from app.models import User, Unit, Task
from app.forms import SignUpForm, LoginForm, AddUnitForm
from app import application, db
from app.services.analytics import calculate_user_statistics


@application.route('/')
def homepage():
    user_id = session.get("user_id", None)
    return render_template('homepage.html', user_id=user_id)


@application.route('/signup', methods=["GET", "POST"])
def signup():
    form = SignUpForm()

    # POST and all fields valid
    if form.validate_on_submit():
        email    = form.email.data
        password = form.password.data

        # duplicate-email check
        if User.query.filter_by(email=email).first():
            flash("This email is already registered. Please use a different email or log in.", "warning")
            return render_template('signup.html', form=form)

        # create new user
        new_user = User(email=email)
        try:
            new_user.set_password(password)
        except ValueError as ve:
            # your password‐strength errors
            flash(str(ve), "danger")
            return render_template('signup.html', form=form)

        # commit, log in, redirect
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.student_id
        return redirect(url_for('dashboard'))

    # If this is a POST *and* form.validate_on_submit() == False,
    # flash every single field error so the user can see exactly what went wrong.
    if request.method == "POST":
        for field_name, error_list in form.errors.items():
            for err in error_list:
                # e.g. "Password: Must include at least one uppercase…"
                label = getattr(form, field_name).label.text
                flash(f"{label}: {err}", "danger")

    # GET, or after any flashed errors, re-render
    return render_template('signup.html', form=form)

@application.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    error = None

    if request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            try:
                user = User.query.filter_by(email=email).first()
                if user and user.check_password(password):
                    session["user_id"] = user.student_id
                    return redirect(url_for('dashboard'))
                else:
                    error = "Invalid email or password."
            except Exception:
                error = "Please try again later, an error occurred."
        else:
            error = "Please check your information and try again."
        
        return render_template('login.html', form=form, error=error)

    # GET
    return render_template('login.html', form=form, error=error)


@application.route('/dashboard')
def dashboard():
    if "user_id" in session:
        user_id = session["user_id"]
        user = User.query.get(user_id)

        if user:
            stats = calculate_user_statistics(user_id)
            user.wam = stats["wam"]
            user.gpa = stats["gpa"]
            user.top_unit = stats["top_unit"]

            return render_template(
                "dashboard.html",
                user=user,
                unit_scores=stats["unit_scores"],
                recommendations=stats["recommendations"],
                ranked_units=stats["ranked_units"]
            )
        else:
            session.pop("user_id", None)

    return redirect(url_for('homepage'))


@application.route('/track_grades')
def track_grades():
    if "user_id" in session:
        form = AddUnitForm()
        user_id = session["user_id"]
        user = User.query.get(user_id)

        if user:
            return render_template('track_grades.html', user=user, form=form)
        else:
            session.pop("user_id", None)

    return redirect(url_for('homepage'))


@application.route('/settings')
def settings():
    if "user_id" in session:
        user_id = session["user_id"]
        user = User.query.get(user_id)

        if user:
            return render_template('settings.html', user=user)
        else:
            session.pop("user_id", None)

    return redirect(url_for('homepage'))


@application.route('/api/add_unit', methods=["POST"])
def add_unit():
    if "user_id" in session:
        form = AddUnitForm()
        user_id = session["user_id"]
        user = User.query.get(user_id)

        if user and form.validate_on_submit():
            try:
                name = form.name.data
                unit_code = form.unit_code.data
                semester = form.semester.data
                year = form.year.data

                target_score = request.form.get("target_score", None)
                outline_url = request.form.get("outline_url", None)

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
                db.session.commit()
                return render_template('track_grades.html', user=user, form=form, success="Unit added successfully")
            except Exception:
                db.session.rollback()
                error = "Please try again later, an error occurred"
                return render_template('track_grades.html', user=user, form=form, error=error)

    return redirect(url_for('homepage'))


@application.route("/api/update_unit", methods=["POST"])
def update_unit():
    if "user_id" in session:
        form = AddUnitForm()
        user_id = session["user_id"]
        user = User.query.get(user_id)

        unit_id = request.form.get("unit_id")
        unit = Unit.query.get(unit_id)

        if not unit:
            flash("Unauthorized or invalid unit.", "danger")
            return redirect(url_for("dashboard"))

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

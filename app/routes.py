import os
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from app import application, db
from app.models import User, Unit, Task, ShareAccess 
from app.forms import SignUpForm, LoginForm, AddUnitForm, EditUnitForm, AddTaskForm, ShareForm
from datetime import datetime
import secrets
from app.services.analytics import calculate_user_statistics
from app.utils import fetch_unit_details_and_summary

# … other routes …

@application.route('/track_grades', methods=['GET', 'POST'])
@login_required
def track_grades():
    # 1. instantiate your forms
    add_unit_form  = AddUnitForm()
    add_task_form  = AddTaskForm()
    edit_unit_form = EditUnitForm()

    # 2. sort the units for your sidebar
    sorted_units = sorted(
        current_user.units,
        key=lambda u: (-u.year, -int(u.semester))
    )

    # 3. determine which unit is “selected” (by POST or GET param)
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

    # 4. pre‐populate add_task_form.unit_id
    if selected_unit:
        add_task_form.unit_id.data = selected_unit.id

    # 5. Build AI summary & suggestions exactly as you had before
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

        # your existing grade‐based tip logic…
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

    # ── NEW: compute target_score & serialize task list for Chart.js ──
    target_score = float(selected_unit.target_score) if selected_unit else 0

    serialized_tasks = []
    if selected_unit:
        serialized_tasks = [
            {
                'task_name': t.task_name,
                'grade':     t.grade,
                'weighting': t.weighting,
                'date':      t.date,
                'notes':     t.notes,
                'type':      t.type
            }
            for t in selected_unit.tasks
        ]

    # 6. render with everything
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

@application.route('/api/add_unit', methods=['POST'])
@login_required
def add_unit():
    form = AddUnitForm()
    if not form.validate_on_submit():
        flash('Invalid form data. Please check your input.', 'danger')
        return redirect(url_for('track_grades'))

    # convert from string like "80" to float 80.0
    ts = float(form.target_score.data)

    # fetch summary & links…
    summary, links = fetch_unit_details_and_summary(form.unit_code.data, os.getenv("API_KEY"))

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

@application.route('/api/update_unit', methods=['POST'])
@login_required
def update_unit():
    form = EditUnitForm()
    if form.validate_on_submit():
        unit = Unit.query.get(int(form.unit_id.data))
        if not unit or unit.user_id != current_user.student_id:
            flash("Unauthorized or invalid unit.", "danger")
            return redirect(url_for("track_grades"))

        # apply edits (cast target_score to float)
        unit.name         = form.name.data
        unit.unit_code    = form.unit_code.data
        unit.semester     = form.semester.data
        unit.year         = int(form.year.data)
        unit.target_score = float(form.target_score.data)

        # if code changed, re-fetch summary/links…
        # [your existing logic]

        db.session.commit()
        flash("Unit updated successfully!", "success")
    else:
        for f, errs in form.errors.items():
            for e in errs:
                flash(f"{f}: {e}", "danger")

    return redirect(url_for('track_grades', unit_id=form.unit_id.data))

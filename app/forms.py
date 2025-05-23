from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, FloatField, DateField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, Regexp
from datetime import datetime


class SignUpForm(FlaskForm):
    email = StringField(
        'Email', 
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    password = PasswordField(
        'Password', 
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long."),
            Regexp(
                r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
                message="Password does not meet complexity requirements"
            )
        ]
    )
    submit = SubmitField('Sign Up')
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Log In')

class AddUnitForm(FlaskForm):
    unit_id = HiddenField('Unit ID')  # Required for sharing
    name = StringField('Unit Name', validators=[DataRequired(), Length(max=120)])
    unit_code = StringField('Unit Code', validators=[DataRequired(), Length(max=20)])
    semester = SelectField('Semester', choices=[('1', '1'), ('2', '2')], validators=[DataRequired()])
   
    # Define available years (e.g., the current year and previous years)
    current_year = datetime.now().year
   # Define the last 5 years as options for the user
    year_choices = [(str(year), str(year)) for year in range(current_year - 5, current_year + 1)]
    
    target_score = SelectField(
        'Target Grade',
        choices=[('HD', 'High Distinction (80-100%)'), ('D', 'Distinction (70-79%)'), ('C', 'Credit (60-69%)'), ('P', 'Pass (50-59%)')],
        validators=[DataRequired()]
    )

    year = SelectField('Year of Completion', choices=year_choices, default=str(current_year), validators=[DataRequired()])
    target_score = FloatField('Target Score (%)', validators=[NumberRange(min=0, max=100)])
    submit = SubmitField('Add Unit')

class EditUnitForm(FlaskForm):
    unit_id = HiddenField('Unit ID', validators=[DataRequired()])  # Add hidden field for unit_id
    name = StringField('Unit Name', validators=[DataRequired(), Length(max=120)])
    unit_code = StringField('Unit Code', validators=[DataRequired(), Length(max=20)])
    semester = SelectField('Semester', choices=[('1', '1'), ('2', '2')], validators=[DataRequired()])
   
    # Define available years (e.g., the current year and previous years)
    current_year = datetime.now().year
   # Define the last 5 years as options for the user
    year_choices = [(str(year), str(year)) for year in range(current_year - 5, current_year + 1)]

    year = SelectField('Year of Completion', choices=year_choices, default=str(current_year), validators=[DataRequired()])
    target_score = FloatField('Target Score (%)', validators=[NumberRange(min=0, max=100)])
    submit = SubmitField('Edit Unit')

class AddTaskForm(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired(), Length(max=120)])
    score = FloatField('Score', validators=[DataRequired(), NumberRange(min=0, max=100)])
    weight = FloatField('Weight (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    date = DateField('Date', validators=[DataRequired()])
    note = TextAreaField('Note', validators=[Optional(), Length(max=500)])
    type = SelectField('Assessment Type', choices=[
        ('assessment', 'Assessment'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    unit_id = HiddenField('Unit ID', validators=[DataRequired()]) #needed so it can be passed to the endpoint 
    submit = SubmitField('Add Task')

# ShareForm for sharing page
class ShareForm(FlaskForm):
    email = StringField('Recipient Email', validators=[DataRequired(), Email(), Length(max=120)])
    expires_at = DateField('Expiry Date', validators=[DataRequired()])
    unit_selection = SelectField('Select Unit to Share', validators=[DataRequired()])
    submit = SubmitField('Share')
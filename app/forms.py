from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from datetime import datetime



class SignUpForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        'Password', 
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters long.")
        ]
    )
    submit = SubmitField('Sign Up')
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Log In')

class AddUnitForm(FlaskForm):
    name = StringField('Unit Name', validators=[DataRequired(), Length(max=120)])
    unit_code = StringField('Unit Code', validators=[DataRequired(), Length(max=20)])
    semester = SelectField('Semester', choices=[('1', '1'), ('2', '2')], validators=[DataRequired()])
   
    # Define available years (e.g., the current year and previous years)
    current_year = datetime.now().year
   # Define the last 5 years as options for the user
    year_choices = [(str(year), str(year)) for year in range(current_year - 5, current_year + 1)]

    year = SelectField('Year of Completion', choices=year_choices, default=str(current_year), validators=[DataRequired()])
    submit = SubmitField('Add Unit')




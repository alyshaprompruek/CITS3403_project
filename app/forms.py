from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class SignUpForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign Up')
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Log In')

class AddUnitForm(FlaskForm):
    name = StringField('Unit Name', validators=[DataRequired(), Length(max=120)])
    unit_code = StringField('Unit Code', validators=[DataRequired(), Length(max=20)])
    semester = SelectField('Semester', choices=[('1', '1'), ('2', '2')], validators=[DataRequired()])
    year = StringField('Year', validators=[DataRequired(), Length(min=4, max=4)])
    submit = SubmitField('Add Unit')




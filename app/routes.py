from flask import render_template, request, redirect, session, url_for
from app.models import user
from app.forms import SignUpForm
from app import application 


@application.route('/')
def homepage():
    #searches for index.html in the templates folder
    return render_template('homepage.html', user=None)

@application.route('/signup', methods=["POST","GET"])
def signup():
    form = SignUpForm()
    if request.method == "GET":
        return render_template('signup.html', SignUpForm=form)
    elif request.method == "POST":
        if form.validate_on_submit():
                email = form.email.data
                password = form.password.data
                role = form.role.data

                # Create a new user instance
                new_user = user(
                    email=email, 
                    studentBoolean=(role=='Student'), 
                    password=password
                )


                session["user"] = new_user.to_dict()

                return redirect(url_for('dashboard'))

@application.route('/dashboard')
def dashboard():
    if "user" in session:
        user = session["user"]
        return render_template('dashboard.html', user=user)
    else:
        return redirect(url_for('homepage'))




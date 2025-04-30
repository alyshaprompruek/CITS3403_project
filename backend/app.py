print("this is a testing message. app.py is working well. >< ")
from flask import Flask, render_template
from api.courses import courses_api
import os

app = Flask(
    __name__,
    template_folder="../frontend"  # instead of "/templates", i use rewrite the path to keep the structure clean.
)

app.register_blueprint(courses_api)

@app.route("/course")
def course():
    return render_template("course.html")  

if __name__ == "__main__":
    app.run(debug=True)
from web import app
from flask import render_template, request

@app.route("/", methods=["GET", "POST"])
def index_page():
    return home_page()

# Routes
@app.route("/python-web-counter/home.html", methods=["GET","POST"])
def home_page():
    msg = ""   
    
    if request.method == 'POST':
        if request.form['sub_button'] == 'button_1':
            msg = "GREEN"
            return render_template("/home.html", msg = msg)
        elif request.form['sub_button'] == 'button_2':
            msg = "RED"
            return render_template("/home.html", msg = msg)
    return render_template("/home.html")

# Errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

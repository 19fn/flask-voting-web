from web import app, db
from web.models import button_1, button_2
from flask import render_template, request

counter_btn_1 = 0
counter_btn_2 = 0

@app.route("/", methods=["GET", "POST"])
def index_page():
    return home_page()

# Routes
@app.route("/python-flask-demo/home.html", methods=["GET","POST"])
def home_page():
    global counter_btn_1
    global counter_btn_2
    
    btn1 = button_1()
    btn2 = button_2()
    butt1 = btn1.clicks
    butt2 = btn2.clicks

    msg = ""
    
    if request.method == 'POST':
        if request.form['sub_button'] == 'button_1':
            msg = "GREEN"
            counter_btn_1 += 1
            btn1 = button_1(
                clicks=counter_btn_1
            )
            db.session.add(btn1)
            db.session.commit()
            return render_template("/home.html", msg = msg, butt1 = butt1, butt2 = butt2)
        elif request.form['sub_button'] == 'button_2':
            msg = "RED"
            counter_btn_2 += 1
            btn2 = button_2(
                clicks=counter_btn_2
            )
            db.session.add(btn2)
            db.session.commit()
            return render_template("/home.html", msg = msg, butt1 = butt1, butt2 = butt2)
    return render_template("/home.html", butt1 = butt1, butt2 = butt2)

# Errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

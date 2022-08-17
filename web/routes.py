from web import app, db
from web.models import button
from web.plot import PieChart
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

    btn = button.query.filter_by(id=1).first()
    counter_btn_1 = btn.green_click
    counter_btn_2 = btn.red_click

    img = PieChart(counter_btn_1,counter_btn_2)

    msg = ""

    if request.method == 'POST':
        if request.form['sub_button'] == 'button_1':
            msg = "GREEN"
            counter_btn_1 += 1
            btn.green_click = counter_btn_1
            db.session.add(btn)
            db.session.commit()
            return render_template("/home.html", msg = msg, btn = btn)
        elif request.form['sub_button'] == 'button_2':
            msg = "RED"
            counter_btn_2 += 1
            btn.red_click = counter_btn_2
            db.session.add(btn)
            db.session.commit()
            return render_template("/home.html", msg = msg, btn = btn)
    return render_template("/home.html", btn = btn, url ='./web/imgs/plt.png')

# Errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

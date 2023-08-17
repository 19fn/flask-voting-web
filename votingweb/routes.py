from votingweb import app, db
from votingweb.models import button
from flask import render_template, request, flash, redirect, url_for

# Call vote page from root
@app.route("/", methods=["GET", "POST"])
def index_page():
    return vote_page()

# Here you can vote
@app.route("/voting", methods=["GET","POST"])
def vote_page():
    # Define counters as globals variables
    global counter_btn_1
    global counter_btn_2

    # Read counters from the database
    btn = button.query.filter_by(id=1).first()
    counter_btn_1 = btn.btn_1
    counter_btn_2 = btn.btn_2

    if request.method == 'POST':
        if request.form['sub_button'] == 'button_1':
            # Add one to button_1 counter
            counter_btn_1 += 1
            # Save the new value for button_1
            btn.btn_1 = counter_btn_1
            db.session.add(btn)
            db.session.commit()
            flash("You voted green.", category="success")
            return redirect(url_for("index_page", btn = btn))
        elif request.form['sub_button'] == 'button_2':
            # Add one to button_2 counter
            counter_btn_2 += 1
            # Save the new value for button_2
            btn.btn_2 = counter_btn_2
            db.session.add(btn)
            db.session.commit()
            flash("You voted red.", category="danger")
            return redirect(url_for("index_page", btn = btn))
    return render_template("/home.html", btn = btn)

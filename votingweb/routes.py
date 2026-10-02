from flask import Blueprint, render_template, request, flash, redirect, url_for

from votingweb import db
from votingweb.models import button

bp = Blueprint("main", __name__)

# Call vote page from root
@bp.route("/", methods=["GET", "POST"])
def index_page():
    return vote_page()

# Here you can vote
@bp.route("/voting", methods=["GET","POST"])
def vote_page():
    # Define counters as globals variables
    global counter_btn_1
    global counter_btn_2

    # Read counters from the database
    btn = db.session.execute(db.select(button).filter_by(id=1)).scalar_one()
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
            return redirect(url_for(".index_page", btn = btn))
        elif request.form['sub_button'] == 'button_2':
            # Add one to button_2 counter
            counter_btn_2 += 1
            # Save the new value for button_2
            btn.btn_2 = counter_btn_2
            db.session.add(btn)
            db.session.commit()
            flash("You voted red.", category="danger")
            return redirect(url_for(".index_page", btn = btn))
    return render_template("/home.html", btn = btn)

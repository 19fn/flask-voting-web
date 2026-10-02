from flask import Blueprint, render_template, request, flash, redirect, url_for

from votingweb import db
from votingweb.models import COUNTERS_ID, button
from votingweb.results import vote_results

bp = Blueprint("main", __name__)

# Call vote page from root
@bp.route("/", methods=["GET", "POST"])
def index_page():
    return vote_page()

# Here you can vote
@bp.route("/voting", methods=["GET","POST"])
def vote_page():
    if request.method == 'POST':
        # Increment in SQL, not read-modify-write in Python: concurrent votes
        # would otherwise overwrite each other and lose increments.
        sub_button = request.form['sub_button']
        if sub_button == 'button_1':
            db.session.execute(
                db.update(button)
                .where(button.id == COUNTERS_ID)
                .values(btn_1=button.btn_1 + 1)
            )
            db.session.commit()
            flash("You voted green.", category="success")
            return redirect(url_for(".index_page"))
        elif sub_button == 'button_2':
            db.session.execute(
                db.update(button)
                .where(button.id == COUNTERS_ID)
                .values(btn_2=button.btn_2 + 1)
            )
            db.session.commit()
            flash("You voted red.", category="danger")
            return redirect(url_for(".index_page"))

    # Read counters from the database
    btn = db.session.execute(db.select(button).filter_by(id=COUNTERS_ID)).scalar_one()
    return render_template(
        "/home.html", btn=btn, results=vote_results(btn.btn_1, btn.btn_2)
    )

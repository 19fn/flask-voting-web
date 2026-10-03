from flask import (
    Blueprint, current_app, jsonify, render_template, request, flash, redirect,
    url_for,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

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


@bp.route("/healthz", methods=["GET"])
def healthz():
    """Health check: 200 if the database answers a read-only query, else 503.

    Only ``SELECT 1`` is run, so no data is modified. The response never
    includes the exception text, which can contain hosts or credentials; the
    details go to the server log only.
    """
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Health check failed: database unreachable")
        return jsonify(status="error", detail="database unavailable"), 503
    return jsonify(status="ok"), 200

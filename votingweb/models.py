import click
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError

from votingweb import db

# The counters live in a single row with this fixed primary key.
COUNTERS_ID = 1


# Define button table
class button(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    btn_1 = db.Column(db.Integer(), nullable=False)
    btn_2 = db.Column(db.Integer(), nullable=False)


def init_db():
    """Create the button table and its single counters row.

    Safe to run repeatedly and from several processes at once: the row has a
    fixed primary key, so a concurrent insert fails with a unique-constraint
    conflict, which is treated as "another process created it". Existing vote
    totals are never touched. Must be called inside an application context.
    """
    try:
        db.create_all()
    except OperationalError, ProgrammingError:
        # Another process may have created the table between the existence
        # check and CREATE TABLE. Only ignore the error if the table is there.
        db.session.rollback()
        if not inspect(db.engine).has_table(button.__tablename__):
            raise

    if db.session.get(button, COUNTERS_ID) is not None:
        return
    db.session.add(button(id=COUNTERS_ID, btn_1=0, btn_2=0))
    try:
        db.session.commit()
    except IntegrityError:
        # Lost the race: another startup inserted the row first.
        db.session.rollback()
        if db.session.get(button, COUNTERS_ID) is None:
            raise


@click.command("init-db")
def init_db_command():
    """Create the tables and the initial vote row."""
    init_db()
    click.echo("Database initialized.")

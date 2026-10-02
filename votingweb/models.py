import click

from votingweb import db


# Define button table
class button(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    btn_1 = db.Column(db.Integer(), nullable=False)
    btn_2 = db.Column(db.Integer(), nullable=False)


def init_db():
    """Create the button table and its single row. Safe to run repeatedly.

    Must be called inside an application context.
    """
    db.create_all()
    if db.session.get(button, 1) is None:
        db.session.add(button(id=1, btn_1=0, btn_2=0))
        db.session.commit()


@click.command("init-db")
def init_db_command():
    """Create the tables and the initial vote row."""
    init_db()
    click.echo("Database initialized.")

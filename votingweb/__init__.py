import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL

# Created unbound; attached to an app in create_app().
db = SQLAlchemy()


def database_url_from_env():
    """Return the database URL from the environment, or None.

    DATABASE_URL wins. Otherwise the URL is built from DB_HOST, DB_PORT
    (default 3306), DB_NAME, DB_USER and DB_PASSWORD for MySQL via PyMySQL.
    Special characters in the user or password are escaped.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    host = os.environ.get("DB_HOST")
    if not host:
        return None
    return URL.create(
        "mysql+pymysql",
        username=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=host,
        port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ.get("DB_NAME"),
    ).render_as_string(hide_password=False)


def create_app(config=None):
    """Application factory.

    ``config`` is an optional mapping applied last. Environment variables are
    only read for values it does not supply, so tests can pass e.g.
    ``{"SQLALCHEMY_DATABASE_URI": "sqlite://"}`` without touching the env.
    Set ``INIT_DB`` to False to skip creating and seeding the table.
    """
    app = Flask(__name__, template_folder="templates")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["INIT_DB"] = True
    config = dict(config or {})

    if "SECRET_KEY" not in config:
        app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    if "SQLALCHEMY_DATABASE_URI" not in config:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url_from_env()
    app.config.update(config)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError(
            "No database configured: set DATABASE_URL, or DB_HOST, DB_NAME, "
            "DB_USER and DB_PASSWORD."
        )

    db.init_app(app)

    from votingweb.models import init_db, init_db_command
    from votingweb.routes import bp

    app.register_blueprint(bp)
    app.cli.add_command(init_db_command)

    if app.config["INIT_DB"]:
        with app.app_context():
            init_db()

    return app

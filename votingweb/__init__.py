import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL

# Created unbound; attached to an app in create_app().
db = SQLAlchemy()
migrate = Migrate()


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

    ``SCHEMA_MODE`` (or the ``DB_SCHEMA_MODE`` variable) decides what startup
    does with the schema:

    * ``validate`` (default): read-only check that the database is at the
      migration head; fails with a clear error otherwise. Never runs DDL.
      Schema changes are made by ``flask db upgrade`` as a release step.
    * ``init``: create the tables and counters row directly (local/test).
      Default when ``TESTING`` is true.
    * ``skip``: do nothing. ``INIT_DB=False`` is the legacy spelling.
    """
    app = Flask(__name__, template_folder="templates")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    config = dict(config or {})

    if "SECRET_KEY" not in config:
        app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    if "SQLALCHEMY_DATABASE_URI" not in config:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url_from_env()
    app.config.update(config)
    if "SCHEMA_MODE" not in config:
        app.config["SCHEMA_MODE"] = (
            os.environ.get("DB_SCHEMA_MODE")
            or ("skip" if config.get("INIT_DB") is False else None)
            or ("init" if app.config.get("TESTING") else "validate")
        )

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError(
            "No database configured: set DATABASE_URL, or DB_HOST, DB_NAME, "
            "DB_USER and DB_PASSWORD."
        )

    db.init_app(app)
    from votingweb.schema import MIGRATIONS_DIR, check_schema, schema_mode

    migrate.init_app(app, db, directory=MIGRATIONS_DIR)

    from votingweb.models import init_db, init_db_command
    from votingweb.routes import bp

    app.register_blueprint(bp)
    app.cli.add_command(init_db_command)

    mode = schema_mode(app)
    with app.app_context():
        if mode == "init":
            init_db()
        elif mode == "validate":
            check_schema()

    return app

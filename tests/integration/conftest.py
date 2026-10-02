"""Fixtures for the integration tests (real MySQL, configured from the env).

The database comes from DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD,
exactly like the app. Run them through ``tests/integration/run.sh``.
"""
import pytest

from votingweb import create_app, db

CONFIG = {"SECRET_KEY": "integration", "TESTING": True}


def new_app(**extra):
    """Build an app against the configured MySQL (a "process start")."""
    return create_app({**CONFIG, **extra})


def stop_app(app):
    """Release the app's connections (a "process stop")."""
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture(autouse=True)
def clean_database():
    """Every test starts from an empty database (no tables)."""
    app = new_app(INIT_DB=False)
    with app.app_context():
        db.drop_all()
    stop_app(app)
    yield


@pytest.fixture
def app_factory():
    """Return new_app, and dispose every app it built after the test."""
    apps = []

    def factory(**extra):
        app = new_app(**extra)
        apps.append(app)
        return app

    yield factory
    for app in apps:
        stop_app(app)

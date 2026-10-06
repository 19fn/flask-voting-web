"""Schema migrations against a real MySQL 8.4 (first install, upgrade, locking)."""

import os
import subprocess
import sys

import pytest
from flask_migrate import upgrade

from votingweb import db
from votingweb.models import COUNTERS_ID, button
from votingweb.schema import SchemaError

GREEN = "button_1"
RED = "button_2"


def rows(app):
    with app.app_context():
        db.session.rollback()  # end any open transaction: see fresh data
        found = db.session.execute(db.select(button)).scalars().all()
        return [(r.id, r.btn_1, r.btn_2) for r in found]


def run_upgrade(app):
    with app.app_context():
        upgrade()


def test_first_install_then_validated_startup(app_factory):
    with pytest.raises(SchemaError):
        app_factory(SCHEMA_MODE="validate")  # empty database: refuses to start
    app = app_factory(SCHEMA_MODE="skip")
    run_upgrade(app)
    started = app_factory(SCHEMA_MODE="validate")
    assert rows(started) == [(COUNTERS_ID, 0, 0)]


def test_upgrade_of_populated_legacy_database_keeps_totals(app_factory):
    legacy = app_factory()  # init mode: old layout, no alembic_version
    client = legacy.test_client()
    for _ in range(3):
        client.post("/voting", data={"sub_button": GREEN})
    client.post("/voting", data={"sub_button": RED})

    app = app_factory(SCHEMA_MODE="skip")
    for _ in range(2):  # repeated execution is a no-op
        run_upgrade(app)
        assert rows(app) == [(COUNTERS_ID, 3, 1)]
    assert rows(app_factory(SCHEMA_MODE="validate")) == [(COUNTERS_ID, 3, 1)]


def test_concurrent_upgrade_processes_do_not_duplicate_the_row(app_factory):
    """Several `flask db upgrade` processes at once: the lock serializes them."""
    app = app_factory(SCHEMA_MODE="skip")
    env = {**os.environ, "DB_SCHEMA_MODE": "skip"}
    command = [sys.executable, "-m", "flask", "--app", "app", "db", "upgrade"]
    procs = [
        subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for _ in range(4)
    ]
    outputs = [p.communicate()[0].decode() for p in procs]
    assert [p.returncode for p in procs] == [0, 0, 0, 0], outputs
    assert rows(app) == [(COUNTERS_ID, 0, 0)]
    assert rows(app_factory(SCHEMA_MODE="validate")) == [(COUNTERS_ID, 0, 0)]

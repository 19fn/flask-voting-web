"""Integration tests against a real MySQL database."""
import threading

import pytest
from sqlalchemy import text

from votingweb import db
from votingweb.models import COUNTERS_ID, button

GREEN = "button_1"
RED = "button_2"


def rows(app):
    with app.app_context():
        db.session.rollback()  # end any open transaction: see fresh data
        found = db.session.execute(db.select(button)).scalars().all()
        return [(r.id, r.btn_1, r.btn_2) for r in found]


def server_version(app):
    with app.app_context():
        return db.session.execute(text("SELECT VERSION()")).scalar_one()


def test_runs_against_mysql(app_factory):
    app = app_factory()
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql")
    assert server_version(app)  # a real server answered


class TestStartupInitialization:
    def test_creates_exactly_one_counters_row(self, app_factory):
        app = app_factory()
        assert rows(app) == [(COUNTERS_ID, 0, 0)]

    def test_restarts_keep_one_row_and_its_totals(self, app_factory):
        app = app_factory()
        client = app.test_client()
        client.post("/voting", data={"sub_button": GREEN})
        client.post("/voting", data={"sub_button": GREEN})
        client.post("/voting", data={"sub_button": RED})

        for _ in range(3):
            restarted = app_factory()  # runs startup initialization again
            assert rows(restarted) == [(COUNTERS_ID, 2, 1)]

    def test_concurrent_startups_create_one_row(self, app_factory):
        count = 6
        barrier = threading.Barrier(count)
        errors = []
        apps = []

        def start():
            try:
                barrier.wait()
                apps.append(app_factory())
            except Exception as exc:  # reported in the main thread
                errors.append(exc)

        threads = [threading.Thread(target=start) for _ in range(count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert rows(apps[0]) == [(COUNTERS_ID, 0, 0)]


class TestPersistence:
    def test_votes_are_stored_in_mysql(self, app_factory):
        app = app_factory()
        client = app.test_client()
        client.post("/voting", data={"sub_button": GREEN})
        client.post("/voting", data={"sub_button": RED})
        client.post("/voting", data={"sub_button": RED})

        # Read through a separate app (its own connections), as a restarted
        # process would.
        other = app_factory()
        assert rows(other) == [(COUNTERS_ID, 1, 2)]

    def test_page_shows_votes_stored_before_a_restart(self, app_factory):
        app_factory().test_client().post("/voting", data={"sub_button": GREEN})

        page = app_factory().test_client().get("/")
        assert page.status_code == 200
        assert b"You voted" not in page.data
        assert rows(app_factory()) == [(COUNTERS_ID, 1, 0)]


class TestConcurrentVotes:
    @pytest.mark.parametrize("value, column", [(GREEN, 1), (RED, 2)])
    def test_no_increment_is_lost(self, app_factory, value, column):
        app = app_factory()
        threads_count, votes_each = 12, 8
        barrier = threading.Barrier(threads_count)
        failures = []

        def voter():
            client = app.test_client()
            barrier.wait()
            for _ in range(votes_each):
                resp = client.post("/voting", data={"sub_button": value})
                if resp.status_code != 302:
                    failures.append(resp.status_code)

        threads = [threading.Thread(target=voter) for _ in range(threads_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert failures == []
        (row,) = rows(app)
        assert row[column] == threads_count * votes_each
        assert row[3 - column] == 0

    def test_mixed_concurrent_votes_are_all_counted(self, app_factory):
        app = app_factory()
        per_button, votes_each = 8, 8
        barrier = threading.Barrier(per_button * 2)

        def voter(value):
            client = app.test_client()
            barrier.wait()
            for _ in range(votes_each):
                client.post("/voting", data={"sub_button": value})

        threads = [
            threading.Thread(target=voter, args=(value,))
            for value in (GREEN, RED)
            for _ in range(per_button)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = per_button * votes_each
        assert rows(app) == [(COUNTERS_ID, total, total)]

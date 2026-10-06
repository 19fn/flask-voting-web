"""Baseline: legacy `button` table and its single counters row.

Revision ID: 0001
Revises:
Create Date: 2026-10-05

Works for both a first install and an installation that already has the
table from the old startup `create_all()`:

* the table is created only when missing; an existing table is checked for the
  expected columns and otherwise left untouched (no reset, no rewrite);
* the counters row (id 1) is inserted only when the table has no rows at all,
  so existing totals are never reset or duplicated.

The totals are legacy aggregate data only. Nothing here creates ballots,
voters, eligibility, timestamps or audit records from them.
"""

import os

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLE = "button"
COLUMNS = {"id", "btn_1", "btn_2"}
ALLOW_ENV = "VOTINGWEB_ALLOW_DESTRUCTIVE"


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table(TABLE):
        found = {c["name"] for c in inspector.get_columns(TABLE)}
        if not COLUMNS <= found:
            raise RuntimeError(
                f"Existing table '{TABLE}' has columns {sorted(found)}, expected at "
                f"least {sorted(COLUMNS)}. Not touching it: fix it by hand from a backup."
            )
    else:
        op.create_table(
            TABLE,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("btn_1", sa.Integer(), nullable=False),
            sa.Column("btn_2", sa.Integer(), nullable=False),
        )

    button = sa.table(TABLE, sa.column("id"), sa.column("btn_1"), sa.column("btn_2"))
    count = bind.execute(sa.select(sa.func.count()).select_from(button)).scalar_one()
    if count == 0:
        op.bulk_insert(button, [{"id": 1, "btn_1": 0, "btn_2": 0}])


def downgrade():
    # Dropping the table destroys the legacy vote totals: operator action only.
    if os.environ.get(ALLOW_ENV) != "yes":
        raise RuntimeError(
            "Refusing to downgrade the baseline: it drops the legacy vote totals. "
            f"Take and verify a backup, then rerun with {ALLOW_ENV}=yes."
        )
    op.drop_table(TABLE)

#!/bin/sh
# Container start: apply schema migrations once (serialized by a database lock),
# then start the given command. The app itself only validates the schema.
# Set RUN_MIGRATIONS=0 to skip this when migrations run as a separate release step.
set -eu
if [ "${RUN_MIGRATIONS:-1}" != "0" ]; then
    DB_SCHEMA_MODE=skip python3 -m flask db upgrade
fi
exec "$@"

#!/usr/bin/env bash
# Run the integration tests against a throwaway MySQL through Docker Compose.
# Exits non-zero if the tests (or the build/startup) fail, and always removes
# the containers, network and volumes it created, on success, failure or Ctrl-C.
set -u

cd "$(dirname "$0")/../.." || exit 1
COMPOSE=(docker compose -f compose.integration.yaml)

cleanup() {
    "${COMPOSE[@]}" down --volumes --remove-orphans --timeout 5 >/dev/null 2>&1
}
trap cleanup EXIT
trap 'exit 130' INT TERM

"${COMPOSE[@]}" up --build --abort-on-container-exit --exit-code-from tests
exit $?

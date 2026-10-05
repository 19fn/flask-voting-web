# Flask Voting Web

Requires Python 3.14+ (the Docker image uses `python:3.14-slim-trixie`).

### Quick start with Make
`make` is the primary entry point for local tasks (macOS and Linux; the
Compose and integration targets also need Docker with Compose). Run `make` or
`make help` to list the targets.

| Target | What it does |
|---|---|
| `make install` | Creates the `venv` virtual environment and installs the runtime and development dependencies |
| `make run` | Runs the app locally with Flask on http://127.0.0.1:5000 |
| `make up` | Builds and starts the Compose stack (app + MySQL) in the background; creates `.env` from `.env.example` if missing |
| `make down` | Stops the Compose stack; votes are kept |
| `make logs` | Follows the Compose logs |
| `make reset` | Stops the Compose stack and deletes its volumes; all votes are lost |
| `make test` | Runs the unit tests |
| `make test-integration` | Runs the integration tests against a throwaway MySQL |
| `make check` | Runs every local quality gate (currently the unit tests) |

Every target exits non-zero when its step fails. Use another interpreter with
`make install PYTHON=python3.14`, another virtual environment directory with
`VENV=...`, and another address with `make run HOST=0.0.0.0 PORT=8000`.
The sections below describe what the targets do and the underlying commands.

### How to run it from Docker container.
First, pull the image
```
docker pull federicocabreraf/votingweb
```
Then, 
```
# you should have an existing db ready for allow connections
# setting FLASK_DEBUG=1 turns on debug mode
# to generate random secret key use: openssl rand -base64 64

docker run -d \
           -p 80:8080 \
           --name votingweb \
           --env "DB_HOST=my-database-ip" \
           --env "DB_NAME=my-db-name" \
           --env "DB_USER=my-user" \
           --env "DB_PASSWORD=my-super-password" \
           --env "FLASK_DEBUG=1" \
           --env "FLASK_SECRET_KEY=my-secret-key" \
           federicocabreraf/votingweb
```

Open in browser: http://your-ip

### How to run it with Docker Compose (app + MySQL)
```
make up       # build and start; open http://localhost:8080
make logs     # follow the logs
make down     # stop, keep the votes
make reset    # stop and delete the database volume
```
`make up` creates `.env` from `.env.example` when it does not exist yet.
The plain `docker compose` commands behind them are described here.

`compose.yaml` starts the app and a MySQL 8.4 database, so you need no database
of your own. The app starts only after the database reports healthy.

Create your local configuration once (`.env` is git-ignored; change the
placeholder passwords and secret key if you like)
```
cp .env.example .env
```
Start the stack (builds the image from the `Dockerfile`)
```
docker compose up --build
```
Open in browser: http://localhost:8080 (set `APP_PORT` in `.env` to use another port).
Add `-d` to run in the background and `docker compose logs -f` to follow the logs.

The app exposes `GET /healthz` (`200 {"status": "ok"}`, or `503` when the database
is unreachable); the Compose `app` service uses it as its healthcheck.

Stop the stack. Votes are kept in the `db-data` named volume, so they survive
this and app restarts (`docker compose restart app`)
```
docker compose down
```
Reset the stack: also delete the database volume, so all votes are lost and the
next `up` starts from an empty database
```
docker compose down -v
```
If you change the MySQL user, password or database name in `.env` after the
first start, reset the stack: MySQL only applies them to an empty volume.

### How to run it locally.
```
make install   # creates venv/ and installs the dependencies
make run       # http://127.0.0.1:5000
```
`make run` uses `DATABASE_URL` or the `DB_*` variables from your environment
(see below) and falls back to a SQLite file `db.sqlite3` when neither is set. It
sets a throwaway `FLASK_SECRET_KEY` if you have none.

The manual steps follow. First create a Python 3.14+ virtual environment.
```
python3.14 -m venv venv
```
Active them.

MacOS/Linux
```
source venv/bin/activate
```
Next, we'll install its dependencies

With venv activated
```
pip3 install -r requirements.txt
```
Check dependencies
```
pip3 freeze  
```
Finally, we should export their environment variables and run flask.

Database

You should have an existing db ready for allow connections. Either set a single URL
```
export DATABASE_URL="mysql+pymysql://db-user:db-password@db-host:3306/db-name"
```
or the individual variables (used only when `DATABASE_URL` is unset)
```
export DB_HOST=db-host
export DB_NAME=db-name
export DB_USER=db-user
export DB_PASSWORD=db-password
```

Flask

Set this to 1 to turn on debug mode
```
export FLASK_DEBUG=1
```
Generate secret key from shell using 
```
openssl rand -base64 64
```
Use it
```
export FLASK_SECRET_KEY=secret-key
```

Run flask
```
flask run
```
With specific host
```
flask run --host 127.0.0.1
```
With specifc port
```
flask run --port 8000
```
Or both
```
flask run --host=0.0.0.0 --port=8000
```
Per default flask runs on localhost and port 5000.

### Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | one of the two | – | Full SQLAlchemy URL, e.g. `mysql+pymysql://user:pass@host:3306/db`. Wins over `DB_*`. Special characters in the password must be URL-encoded. |
| `DB_HOST` | if no `DATABASE_URL` | – | MySQL host |
| `DB_PORT` | no | `3306` | MySQL port |
| `DB_NAME` | if no `DATABASE_URL` | – | Database name |
| `DB_USER` | if no `DATABASE_URL` | – | Database user |
| `DB_PASSWORD` | if no `DATABASE_URL` | – | Database password (escaped automatically) |
| `FLASK_SECRET_KEY` | yes | – | Signs the session; needed for the vote flash messages |
| `FLASK_DEBUG` | no | `0` | `1` turns on debug mode |

The app is built by `votingweb.create_app(config=None)`. On startup it creates the
`button` table and its single row if they are missing; this is safe to repeat.
You can also run it on its own with `flask init-db`.

### Running all local checks
```
make check
```
runs every local quality gate that exists: currently the unit tests. It does not
include `make test-integration`, which needs Docker.

### Running the unit tests
The unit tests live in `tests/unit`. They use SQLite and Flask's test client, so
they need no Docker, no MySQL and no environment variables. Each test builds its
own app with a fresh database.

```
make test
```
This installs the development dependencies into `venv` if needed and runs
`python -m pytest tests/unit`. Without Make: install them (they include the
runtime ones) in your virtual environment and run pytest
```
pip3 install -r requirements-dev.txt
python -m pytest tests/unit
```
They are plain `unittest` test cases, so `python3 -m unittest` also runs them
with only `requirements.txt` installed. To build an app with your own settings,
pass a mapping, e.g.
`create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "INIT_DB": False})`.

### Running the integration tests
The integration tests live in `tests/integration` and check the app against a real
MySQL 8.4 database (startup initialization creates exactly one counters row, also
after restarts and concurrent startups; votes persist; concurrent votes lose no
increments). They are not part of the default run: `python -m pytest` and
`python -m pytest tests/unit` only run the unit tests.

You only need Docker with Compose. From the repository root
```
make test-integration
```
which runs
```
tests/integration/run.sh
```
This uses `compose.integration.yaml` to start a throwaway MySQL (own project name,
no published ports, data on a tmpfs, fixed test-only credentials, so neither your
`.env` nor the development stack and its `db-data` volume are used) and runs the
tests in a test container built from `Dockerfile.integration`. The script exits
non-zero if anything fails, and always removes its containers, network and volumes
afterwards, whether the run passes, fails or is interrupted.

To run the tests directly against a MySQL you already have (it is emptied: the
tables are dropped before every test, so never point it at real data), set the
`DB_*` or `DATABASE_URL` variables and run
```
python -m pytest tests/integration
```

Open in browser: http://127.0.0.1:5000

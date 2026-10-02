# Flask Voting Web

Requires Python 3.14+ (the Docker image uses `python:3.14-slim-trixie`).

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

### How to run it locally.
You should create a Python 3.14+ virtual environment first.
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

### Running the unit tests
The unit tests live in `tests/unit`. They use SQLite and Flask's test client, so
they need no Docker, no MySQL and no environment variables. Each test builds its
own app with a fresh database.

Install the development dependencies (they include the runtime ones) in your
virtual environment
```
pip3 install -r requirements-dev.txt
```
Run the unit tests
```
python -m pytest tests/unit
```
They are plain `unittest` test cases, so `python3 -m unittest` also runs them
with only `requirements.txt` installed. To build an app with your own settings,
pass a mapping, e.g.
`create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "INIT_DB": False})`.

Open in browser: http://127.0.0.1:5000

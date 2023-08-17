# Flask Voting Web

### How to run it from Docker container.
First, pull the image
```
docker pull federicocabreraf/votingweb
```
Then, 
```
# you should have an existing db ready for allow connections
# setting flask_env to development turns on debug mode
# to generate random secret key use: openssl rand -base64 64

docker run -d \
           -p 80:8080 \
           --name votingweb \
           --env "DB_HOST=my-database-ip" \
           --env "DB_NAME=my-db-name" \
           --env "DB_USER=my-user" \
           --env "DB_PASSWORD=my-super-password" \
           --env "FLASK_ENV=development" \
           --env "FLASK_SECRET_KEY=my-secret-key"
           federicocabreraf/votingweb
```

Open in browser: http://your-ip

### How to run it locally.
You should create a python3 virtual environment first.
```
python3 -m venv venv
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

You should have an existing db ready for allow connections
```
export DB_HOST=db-host
export DB_NAME=db-name
export DB_USER=db-user
export DB_PASSWORD=db-password
```

Flask

Set this to 'development' to turn on debug-mode
```
export FLASK_ENV=flask-env
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

Open in browser: http://127.0.0.1:5000

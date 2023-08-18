# tagged image as federicocabreraf/votingweb
FROM python:3.8-slim-buster

# Dependencies
RUN apt-get update && apt-get install python3-dev default-libmysqlclient-dev build-essential -y

# Working directory
WORKDIR /votingweb

# Copy all files
COPY . .

# Open port 80 (http)
EXPOSE 80

# Set flask app environment variable
ENV FLASK_APP="app"

# Install virtual environment
RUN python3 -m venv venv

# Enable virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Install python dependencies
RUN python3 -m pip install -r requirements.txt

# Run flask --host=0.0.0.0 (This tells operating system to listen on all public IPs.)
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=80"]

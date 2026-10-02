# tagged image as federicocabreraf/votingweb
FROM python:3.14-slim-trixie

# Working directory
WORKDIR /votingweb

# Create the virtual environment and put it first on PATH
ENV VIRTUAL_ENV=/votingweb/venv
RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install python dependencies first to benefit from layer caching
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set flask app environment variable
ENV FLASK_APP="app"

# Flask listens on 8080
EXPOSE 8080

# Run flask --host=0.0.0.0 (This tells operating system to listen on all public IPs.)
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080"]

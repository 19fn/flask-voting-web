from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, template_folder="templates")

# Database credentials
server_name = os.environ["DB_HOST"] 
database_name = os.environ["DB_NAME"]
server_admin_login_name = os.environ["DB_USER"]
server_admin_login_password = os.environ["DB_PASSWORD"]

# Database string connection
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{server_admin_login_name}:{server_admin_login_password}@{server_name}:3306/{database_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "byiqpj0nZpJ+GnkPEFx86A=="

# SQLAlchemy
db = SQLAlchemy(app)

from votingweb import routes

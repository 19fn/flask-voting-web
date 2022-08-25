from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder="templates")

# SENSIBLE
server_name = ""
database_name = ""
server_admin_login_name = ""
server_admin_login_password = ""

# Database string connection
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{server_admin_login_name}:{server_admin_login_password}@{server_name}:3306/{database_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "byiqpj0nZpJ+GnkPEFx86A=="

# SQLAlchemy
db = SQLAlchemy(app)

from web import routes
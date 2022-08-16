from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder="templates")

uid = "root"
passwd = ""
ip = ""
database = "devtest_db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{uid}:{passwd}@{ip}:3306/{database}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "byiqpj0nZpJ+GnkPEFx86A=="

# SQLAlchemy
db = SQLAlchemy(app)

from web import routes
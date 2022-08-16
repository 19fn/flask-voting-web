from web import db

# Tables
class button_1(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    clicks = db.Column(db.Integer(), nullable=True)

class button_2(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    clicks = db.Column(db.Integer(), nullable=True)

class button(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    green_click = db.Column(db.Integer(), nullable=True)
    red_click = db.Column(db.Integer(), nullable=True)

db.create_all()
db.session.commit()
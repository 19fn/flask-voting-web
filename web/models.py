from web import db

# button table
class button(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    btn_1 = db.Column(db.Integer(), nullable=False)
    btn_2 = db.Column(db.Integer(), nullable=False)

# Create table
db.create_all()
db.session.commit()

# Add init value to button table
null_vote = button(btn_1=0, btn_2=0)
db.session.add(null_vote)
db.session.commit()
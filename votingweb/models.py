from votingweb import app, db

# Define button table
class button(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    btn_1 = db.Column(db.Integer(), nullable=False)
    btn_2 = db.Column(db.Integer(), nullable=False)

with app.app_context():
    # Create button table
    db.create_all()

    # Add init value to button table (only once)
    if db.session.get(button, 1) is None:
        db.session.add(button(id=1, btn_1=0, btn_2=0))
        db.session.commit()

# models.py

from extensions import db

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    tasks = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Text, nullable=True)
    memo = db.Column(db.Text, nullable=True)
    challenges = db.Column(db.Text, nullable=True)  
    next_plan = db.Column(db.Text, nullable=True)   

    def __repr__(self):
        return f'<Report {self.date}>'
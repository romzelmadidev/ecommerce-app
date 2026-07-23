from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    acct_number = db.Column(db.String(50), unique=True, nullable=False)

    transactions = db.relationship('OrderTransaction', backref='user', lazy=True)


class OrderTransaction(db.Model):
    __tablename__ = 'order_transactions'

    id = db.Column(db.String(36), primary_key=True)
    indiv_order_name = db.Column(db.Text, nullable=False)
    indiv_order_amt = db.Column(db.Text, nullable=False)
    total_amt = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='PENDING')

    acct_number = db.Column(db.String(50), db.ForeignKey('users.acct_number'), nullable=False)


from . import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))
    jwt_auth = db.Column(db.Boolean())
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f'User {self.username}'

    def save_user(self):
        db.session.add(self)
        db.session.commit()


class JWTBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jwt_token = db.Column(db.String(), nullable=False)
    username = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return f'Expired Token: {self.jwt_token}'

    def save_token(self):
        db.session.add(self)
        db.session.commit()

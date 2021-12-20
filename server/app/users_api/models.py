from . import db, bcrypt
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)  # index email?
    password = db.Column(db.String(80))
    jwt_auth = db.Column(db.Boolean())
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f'User {self.username}'

    def set_password(self, _password):
        self.password = bcrypt.generate_password_hash(_password)

    def check_password(self, _password):
        return bcrypt.check_password_hash(self.password, _password)

    def save_user(self):
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        user_dict = {}
        user_dict['_id'] = self.id
        user_dict['username'] = self.username
        user_dict['email'] = self.email
        return user_dict

    def to_JSON(self):
        return self.to_dict()


class JWTBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jwt_token = db.Column(db.String(), nullable=False)
    username = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return f'Expired Token: {self.jwt_token}'

    def save_token(self):
        db.session.add(self)
        db.session.commit()

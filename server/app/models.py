from app import db, bcrypt
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), nullable=False, unique=True, index=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(70), nullable=False, unique=True, index=True)
    password = db.Column(db.String(80), nullable=False)
    jwt_auth = db.Column(db.Boolean(), nullable=False)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f'User {self.username}'

    def set_password(self, _password):
        self.password = bcrypt.generate_password_hash(_password)

    def check_password(self, _password):
        return bcrypt.check_password_hash(self.password, _password)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        user_dict = {}
        user_dict['_id'] = self.id
        user_dict['username'] = self.username
        user_dict['email'] = self.email
        return user_dict

    def to_json(self):
        return self.to_dict()

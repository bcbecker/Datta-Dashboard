from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_class=Config):
    '''
    Binds all necessary objects to app instance, registers blueprints, configs from .env
    '''
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Bind any packages here
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register any blueprints here
    from .routes import users_api
    users_api.init_app(app)

    return app

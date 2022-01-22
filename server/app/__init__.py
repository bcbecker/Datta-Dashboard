from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import DevelopmentConfig


db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_class=DevelopmentConfig):
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
    from .users_api.routes import users_api
    users_api.init_app(app)

    # Add cli commands
    from .cli import test, prune_expired_tokens
    app.cli.add_command(test)
    app.cli.add_command(prune_expired_tokens)

    return app
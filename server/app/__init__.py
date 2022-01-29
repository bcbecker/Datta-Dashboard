from redis import Redis
import fakeredis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import TestingConfig


db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_class=TestingConfig):
    '''
    Binds all necessary objects to app instance, registers blueprints, configs from .env
    '''
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Redis blocklist config with mock for testing and time to live
    app.TTL = app.config['JWT_ACCESS_TOKEN_EXPIRES']
    
    if config_class == TestingConfig:
        app.redis_blocklist = fakeredis.FakeStrictRedis()
    else:
        app.redis_blocklist = Redis.from_url(app.config['REDIS_URL'])

    # Bind any packages here
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register any blueprints here
    from .auth.routes import auth
    auth.init_app(app)

    # Add cli commands
    from .cli import test
    app.cli.add_command(test)

    return app

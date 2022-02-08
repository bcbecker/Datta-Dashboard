from datetime import datetime, timedelta, timezone
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, get_jwt,
    set_access_cookies)
from app.models import User
from app import create_app, db
from config import configs


# Config, ProductionConfig, DevelopmentConfig, TestingConfig
app = create_app(config_class=configs['DevelopmentConfig'])


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}


@app.after_request
def refresh_expiring_jwt(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(seconds=450))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response


if __name__ == "__main__":
    app.run(host='0.0.0.0')

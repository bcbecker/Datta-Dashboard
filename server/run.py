from app.models import User
from app import create_app, db
from config import configs


# Config, ProductionConfig, DevelopmentConfig, TestingConfig
app = create_app(config_class=configs['DevelopmentConfig'])


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}


if __name__ == "__main__":
    app.run(host='0.0.0.0')

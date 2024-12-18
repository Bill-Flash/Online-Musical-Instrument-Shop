from flask import Flask
from flask_babel import Babel
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import config, Config
from sqlalchemy import MetaData
from flask_wtf import CSRFProtect


naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
babel = Babel()

mail = Mail()

async_mode = None
socketio = SocketIO()

def create_app(config_name):
    app = Flask(__name__)
    CSRFProtect(app)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app)
    # migrate.init_app(app, db)
    # for the blueprint so that it can be easily modulized
    # such as en/zh, and two portals
    from .main import main as main_blueprint
    from .staff import staff as staff_blueprint
    from .customer import main as customer_blueprint
    # in the future, there might be more blueprints here, notice the prefix
    app.register_blueprint(main_blueprint)
    app.register_blueprint(staff_blueprint, url_prefix='/staff')
    app.register_blueprint(customer_blueprint)

    socketio.init_app(app=app, async_mode=async_mode)
    return app


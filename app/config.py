class BaseConfig:
    """Base configuration with common settings."""

    # Flask internal settings
    DEBUG = False
    TESTING = False
    SECRET_KEY = "CHANGE_ME"

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:password@localhost/barber_system"

    # Flask-SocketIO settings
    SOCKETIO_MESSAGE_QUEUE = None


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root@localhost/barber_system_dev"


class ProductionConfig(BaseConfig):
    DEBUG = False
    # Real production database URL should be set via environment variable
    SQLALCHEMY_DATABASE_URI = None
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_change')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///parking.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': Config
}
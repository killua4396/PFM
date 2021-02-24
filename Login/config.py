import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.urandom(24)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/abc?charset=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = os.urandom(24)


class TestingConfig(Config):
    TESTING = True


config = {
    'development'   : DevelopmentConfig,
    'testing'       : TestingConfig,
    'production'    : ProductionConfig,
    'default'       : DevelopmentConfig
}
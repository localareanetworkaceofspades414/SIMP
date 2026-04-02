import os

class Config:
    DEBUG = False
    TESTING = False
    DATABASE_URI = os.environ.get('DATABASE_URI')

class ProductionConfig(Config):
    DATABASE_URI = os.environ.get('PROD_DATABASE_URI')

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URI = os.environ.get('DEV_DATABASE_URI')

class TestingConfig(Config):
    TESTING = True
    DATABASE_URI = os.environ.get('TEST_DATABASE_URI')

import datetime
import os

import app

basedir = os.path.abspath(os.path.dirname(__file__))
appdir = os.path.join(basedir, 'app')



class Config:
    WTF_CSRF_CHECK_DEFAULT = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    PRODUCT_PIC_IMG = os.path.join(appdir, 'static', 'img', 'product', 'pic')
    PRODUCT_PIC_POSTER = os.path.join(appdir, 'static', 'img', 'product', 'poster')
    PRODUCT_VIDEO = os.path.join(appdir, 'static', 'video')
    PROFILE_UPLOAD_DIR = os.path.join(basedir, 'app/static/img/profile/')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    MAIL_SERVER = 'smtp.qq.com'  # 发送邮箱的服务地址  这里设置为QQ邮箱服务器地址
    MAIL_PORT = '587'  # 发送端口为465或者587
    MAIL_USE_TLS = True  # 端口为587对应的服务

    MAIL_USERNAME = '1467797958@qq.com'  # 使用者的邮箱
    MAIL_PASSWORD = 'wggwwundxegtiagf'  # 不是QQ邮箱登录密码，是QQ邮箱授权码获取，用于第三方登录验证
    MAIL_DEFAULT_SENDER = '1467797958@qq.com'  # 默认发送者，暂时先设置为自己
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    LANGUAGES  = ['en','zh_Hans_CN']
    BABEL_DEFAULT_LOCALE = 'zh_Hans_CN'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False
    LANGUAGES  = ['en','zh_Hans_CN']
    BABEL_DEFAULT_LOCALE = 'zh_Hans_CN'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

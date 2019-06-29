# coding:utf-8
import redis


class Config(object):
    """配置信息"""

    SECRET_KEY = "DDFGWEv*dsfaggdas"

    SQLALCHEMY_DATABASE_URI = "mysql://root:wuzy@19920512@182.61.12.75:3306/flask"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST = "182.61.12.75"
    REDIS_PORT = 6379

    # flask_session配置
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中对session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 86400 # session 有效期 单位秒


class DevelopmentConfig(Config):
    """开发环境配置信息"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置信息"""
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}
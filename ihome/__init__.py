# coding: utf-8
import redis
from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
from utils.commons import ReConverter


db = SQLAlchemy()


redis_store = None


file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*1024, backupCount=10)
formatter = logging.Formatter("%(levelname)s %(filename)s:%(lineno)d %(message)s")
file_log_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_log_handler)
logging.basicConfig(level=logging.DEBUG)


def create_app(config_name):
    """
    创建flask的应用对象
    :param config_name: str 配置模式对名字（“develop”, "product"）
    :return:
    """
    app = Flask(__name__)

    # 根据配置模式的名字获取配置参数的类
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 使用init_app初始化db
    db.init_app(app)

    # 创建redis连接对象
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # # 利用flask_session 将session数据保存到redis中
    Session(app)

    # # 为flask补充csrf防护机制
    CSRFProtect(app)

    # 为flask添加自定义转换器
    app.url_map.converters["re"] = ReConverter

    from ihome import api_v1_0
    app.register_blueprint(api_v1_0.api, url_prefix="/api/v1.0")

    from ihome import web_html
    app.register_blueprint(web_html.html)

    return app

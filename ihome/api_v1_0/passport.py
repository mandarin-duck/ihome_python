# coding:utf-8
import re

from sqlalchemy.exc import IntegrityError

from . import api
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome import redis_store, db, constants
from ihome.models import User


@api.route("/users", methods=["POST"])
def register():
    """
    注册
    请求参数  手机号 验证码 秘密 确认密码
    请求方式 json
    :return:
    """
    req_data = request.get_json()
    mobile = req_data.get("mobile")
    sms_code = req_data.get("sms_code")
    password = req_data.get("password")
    password2 = req_data.get("password2")

    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次秘密不一样")
    if not re.match(r'1[34678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不对")
    try:
        redis_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取手机验证码错误")
    if redis_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="手机验证码失效")
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    if sms_code != redis_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="验证码不对")

    user = User(name=mobile, mobile=mobile)
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已经存在")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """
    登录
    :return:
    """
    json_data = request.get_json()
    mobile = json_data.get("mobile")
    password = json_data.get("password")

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    if not re.match(r'1[34578]', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机格式不对")

    user_ip = request.remote_addr

    try:
        access_nums = redis_store.get("access_num_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="请求次数过多,请稍后再试")

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None or not user.check_password(password):
        try:
            redis_store.incr("access_num_%s" % user_ip)
            redis_store.expire("access_num_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="用户不存在")

    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/session", methods=["GET"])
def check_login():
    """
    检查用户是否登录
    :return:
    """
    name = session.get("name")

    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route("/session", methods=["DELETE"])
def login_out():
    """
    退出
    :return:
    """
    session.clear()
    return jsonify(errno=RET.OK, errmsg="OK")
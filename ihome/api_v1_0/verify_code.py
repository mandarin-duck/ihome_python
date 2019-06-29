# coding:utf-8
import random

from . import api
from ihome import redis_store, constants
from flask import current_app, jsonify, make_response, request
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET
from ihome.libs.yuntongxun.sms import CCP


@api.route("/get_image_code/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取验证码
    :param image_code_id: 验证码缓存编号
    :return: 正常返回验证码图片, 异常返回json
    """
    name, text, image_data = captcha.generate_captcha()
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片验证码失败")
    response = make_response(image_data)
    response.headers["Content-type"] = "image/jpg"
    return response


@api.route("/sms_code/<re(r'1[3578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """
    发送手机验证码
    :param mobile:
    :return:
    """
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")

    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    try:
        redis_image_code = redis_store.get("image_code_%s" % image_code_id)
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if redis_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg="验证码过期")

    if redis_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="验证码错误")

    try:
        # 判断在60秒内用户有没有发送过验证码，如果有表示用户请求频繁，拒绝处理
        send_flg = redis_store.get("send_sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flg is not None:
            # 60秒内发送过验证码
            return jsonify(errno=RET.REQERR, errmsg="请求过于平凡，请60秒后再试")

    # 生成手机验证码信息
    sms_code = "%06d" % random.randint(0, 999999)

    try:
        redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存验证码异常")

    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="发送验证码异常")

    if result == 0:
        return jsonify(errno=RET.OK, errmsg="发送成功")
    else:
        return jsonify(errno=RET.THIRDERR, errmsg="发送失败")

# coding:utf-8
from ihome.models import User
from . import api
from flask import g, request, jsonify, current_app
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome import db
from ihome import constants
from ihome.utils.commons import login_required


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """
    设置用户头像
    :return:
    """
    user_id = g.get("user_id")

    image_file = request.files.get("avatar")

    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    image_data = image_file.read()

    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    avatar_url = constants.QINIU_URL_DOMAIN+file_name

    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})

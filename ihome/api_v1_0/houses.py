# coding:utf-8
import json
from datetime import datetime
from ihome.utils.commons import login_required
from . import api
from flask import jsonify, current_app, g, request, session
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.models import Area, House, Facility, HouseImage, User, Order
from ihome import constants
from ihome.utils.image_storage import storage


@api.route("/areas")
def get_area_info():
    """
    获取地区
    :return:
    """

    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            current_app.logger.error("hit redis area_info ")
            return resp_json, 200, {"Content-Type": "application/json"}

    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    area_dict_li = []

    for area in area_li:
        area_dict_li.append(area.to_dict())

    resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_li)

    resp_json = json.dumps(resp_dict)

    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)
    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """
    保存房屋信息
    {
        "title": "",
        "price": "",
        "area_id": "1",
        "address": "",
        "room_count": "",
        "acreage": "",
        "unit": "",
        "capacity": "",
        "deposit": "",
        "beds": "",
        "deposit": "",
        "min_days": "",
        "max_days": "",
        "facility": ["7", "8"]
    }
    :return:
    """
    user_id = g.user_id
    house_data = request.get_json()
    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅）
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")
    max_days = house_data.get("max_days")

    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, max_days, min_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    facility_ids = house_data.get("facility")

    if facility_ids:

        try:
            facilitys = Facility.query.filter(Facility.id.in_(facility_ids)).all()

        except Exception as e:

            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        if facilitys:
            house.facilities = facilitys

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """
    保存房屋图片
    :return:
    """
    image_file = request.files.get("house_image")

    house_id = request.form.get("house_id")

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.DATAEXIST, errmsg="房屋不存在")

    image_data = image_file.read()

    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存图片失败")

    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    if not house.index_image_url:
        house.index_image_url=file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据异常")

    image_url = constants.QINIU_URL_DOMAIN + file_name

    return jsonify(errno=RET.OK, errmsg="OK", data={"image_url": image_url})


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_house():
    """
    获取房东发布对房源信息
    :return:
    """
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """
    获取首页幻灯片展示的房屋基本信息
    :return:
    """
    try:
        # 获取缓存中对数据
        ret = redis_store.get("")
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house index info redis")
        return '{"errno": 0, "errmsg": "OK", "data": %s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        # 获取订单数最多的五条数据
        try:
            houses = Order.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)

            return jsonify(errno=RET.DBERR, errmsg="数据库查询失败")
        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="没有数据")

        houses_list = []

        for house in houses:
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        json_houses = json.dumps(houses_list)

        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPORES, json_houses)
        except Exception as e:
            current_app.logger.error(e)
        return '{"errno": 0, "errmsg": "OK", "data": %s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detial(house_id):
    """
    获取房屋详情信息
    :param house_id:
    :return:
    """

    user_id = session.get("user_id", "-1")

    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{"errno": 0, "errmsg": "OK", "data": {"user_id": %s, "house": %s}}' % (user_id, ret), 200, {"Content-Type": "application/json"}

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    try:
        # 将房屋数据转换为字典
        house_dict = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    json_house = json.dumps(house_dict)
    # 将房屋数据放入redis缓存
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRES_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    return '{"errno": 0, "errmsg": "OK", "data": {"user_id": %s, "house": %s}}' % (user_id, json_house), 200, {
        "Content-Type": "application/json"}


def get_house_list():
    """
    获取房屋列表页
    :return:
    """

    start_date = request.args.get("sd")
    end_date = request.args.get("ed")
    area_id = request.args.get("aid")
    sort_key = request.args.get("sk", "new")
    page = request.args.get("p")

    try:
        if start_date:
            start_date = datetime.strptime(start_date)
        if end_date:
            end_date = datetime.strptime(end_date)
        if start_date and end_date:
            assert end_date >= start_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="时间参数有误")

    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="区域参数有误")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)

    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json, 200, {"Content-Type": "application/json"}

    filter_parms = []

    confdlict_orders = None

    try:
        if start_date and end_date:
            confdlict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            confdlict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            confdlict_orders = Order.query.filter(Order.begin_date <= end_date)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if confdlict_orders:
        # 从订单中获取冲突对房屋id
        confdlict_house_ids = [order.house_id for order in confdlict_orders]

        # 如果冲突对房屋id不为空，向查询参数中添加条件
        if confdlict_house_ids:
            filter_parms.append(House.id.notin_(confdlict_house_ids))

    if area_id:
        filter_parms.append(House.area_id == area_id)

    if sort_key == "booking":
        house_query = House.query.filter(*filter_parms).order_by(House.order_count.desc())
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_parms).order_by(House.price.asc())
    elif sort_key == "price-des":
        house_query = House.query.filter(*filter_parms).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_parms).order_by(House.create_time.desc())


    try:
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    house_li = page_obj.items
    houses = []

    for house in house_li:
        houses.append(house.to_basic_dict())

    total_page = page_obj.pages

    resp_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses, "current_page": page})

    resp_json = json.dumps(resp_dict)

    if page <= total_page:
        redis_key = "house_%s_%s_%s_s%" % (start_date, end_date, area_id, sort_key)

        try:

            pipeline = redis_store.pipeline()
            pipeline.multi()
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {"Content-type": "application/json"}

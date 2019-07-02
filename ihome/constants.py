# coding:utf-8

# 图片验证码缓存有效期
IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码redis保存有效期，单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码对时间间隔
SEND_SMS_CODE_INTERVAL = 60

# 允许登录的错误次数
LOGIN_ERROR_MAX_TIMES = 5

# 封ip时间
LOGIN_ERROR_FORBID_TIME = 600

# 七牛云前缀
QINIU_URL_DOMAIN = "http://ptyao2ubt.bkt.clouddn.com/"

# 地区信息缓存时间
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页轮循房屋数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据的redis缓存时间
HOME_PAGE_DATA_REDIS_EXPORES = 7200

# 房屋详情页面数据redis缓存时间
HOUSE_DETAIL_REDIS_EXPIRES_SECOND = 7200

# 房屋列表页面每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 2

# 房屋分页数据缓存时间
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200
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
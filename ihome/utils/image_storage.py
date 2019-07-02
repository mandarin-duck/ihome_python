# coding:utf-8
from qiniu import Auth, put_data, etag, urlsafe_base64_encode
import qiniu.config


access_key = "ptQ11yNniTTgtIgUunARvOrbWHE9BB_sjys1eFIi"
secret_key = "QWC0mTVRdnxeK3RA33ZBSEy-RGAPskt2HirzZWSG"


def storage(file_data):
    """
    上传文件到七牛云服务器
    :return:
    """
    q = Auth(access_key, secret_key)

    bucket_name = "image_store"

    token = q.upload_token(bucket_name, None, 3600)

    ret, info = put_data(token, None, file_data)

    if info.status_code == 200:
        # 上传成功
        return ret.get("key")
    else:
        raise Exception("上传失败")


if __name__ == '__main__':
    with open("../static/images/home01.jpg", "rb") as f:
        file_data = f.read()
        data = storage(file_data)
        print data
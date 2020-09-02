
"""
采集器的请求Req
"""
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'origin':'https://space.bilibili.com',
}
class Req(object):
    def __init__(self, url_token: str, url_format: str, url_params: dict, setting: dict = dict()):
        self.url_token = url_token  # 唯一标识
        self.url = url_format.format(**url_params)
        self.header = HEADERS
        self.setting = setting
        #print(self.url)


def factory_req(cmd: str, **kwargs) -> Req:
    if cmd == "bili":
        uid = kwargs.get('uid', None)
        if uid:
            url_format = "http://api.bilibili.com/x/relation/stat?vmid={uid}"
            url_params = dict(**kwargs)
            return Req(url_token=uid, url_format=url_format, url_params=url_params)
        else:
            raise Exception
    else:
        raise Exception

import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
    'Accept': '*/*',
    'Connection': 'keep-alive'
}
"""
使用requests发送普通请求函数
"""


def get(url):
    """

    :param url:
    :return:
    (is_res_good,content)
    """
    with requests.get(url, allow_redirects=False, proxies=None) as res:
        if res.status_code == 200:
            ct = content_type(res)
            if ct == 'application/json':
                return (True, res.json(encoding='utf-8'))
            else:
                return (False, res.text)  # res.content
        else:
            print("GET失败:", res.status_code)
            return (False, None)


def content_type(res: requests.Response):
    content_type = res.headers.get('Content-Type', None)
    return content_type


# todo 改为make_request
def make_req(url: str, timeout: int = 9) -> tuple:
    """

    :param url:
    :param timeout:
    :return: (isGood,content_type,result:Response)
    """
    with requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=False, proxies=None, verify=False) as res:
        if res.status_code == 200:
            ct = content_type(res)
            return (True, ct, res)
        else:
            print("GET失败:", res.status_code)
            return (False, None, None)


if __name__ == '__main__':
    print(get('http://118.24.52.95/get_all/'))

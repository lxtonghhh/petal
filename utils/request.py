import requests
import urllib3
urllib3.disable_warnings()
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


def make_req(url: str, proxies: str = None, timeout: int = 9) -> tuple:
    """

    :param url:
    :param proxies: "122.224.65.197:3128"
    :param timeout:
    :return: (isGood,content_type,result:Response)
    """
    try:
        if not proxies:
            proxies = None
        else:
            #{"https": "47.100.104.247:8080", "http": "36.248.10.47:8080"}
            proxies = dict(http=str(proxies),https=str(proxies))
        with requests.get(url, timeout=timeout, allow_redirects=False, proxies=proxies, verify=False) as res:
            if res.status_code == 200:
                ct = content_type(res)
                return (True, ct, res)
            else:
                #print("GET失败: 请求失败状态码 ", res.status_code)
                return (False, str(res.status_code), None)
    except Exception as e:
        #print("GET失败: 请求异常 ", repr(e))
        return (False, repr(e), None)


if __name__ == '__main__':
    print(get('http://118.24.52.95/get_all/'))

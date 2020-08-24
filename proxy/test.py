from utils.request import make_req

def test_IP_by_request(proxy: str, url: str, timeout: int) -> tuple:
    """

    :param proxy:
    :param url:
    :param timeout:
    :return: (isGood,content_type,result:Response)
    """
    return make_req(url, proxy, timeout)

if __name__ == '__main__':
    pass

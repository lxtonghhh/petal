from typing import List
import asyncio, aiohttp
import time, random, re, requests
from utils.request import make_req


class IP(object):
    """Summary of class here.

    Longer class information....
    Longer class information....

    Attributes:
        proxy: str 'http://'+'{ip}:{port}'
        score: int quality of proxy,0 for useless
    """

    def __init__(self, proxy, score=1):
        self.proxy = proxy
        self.score = score


class ProxyFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def proxy_str_check(maybe_ip: str) -> bool:
        """
        确保正确的host:port格式
        :return:
        """
        try:

            # re.match 尝试从字符串的起始位置匹配一个模式，如果不是起始位置匹配成功的话，match()就返回none
            pattern_ip = re.compile(
                r'^((25[0-5])|(2[0-4][0-9])|(1[0-9][0-9])|([1-9][0-9])|([0-9]))(\.((25[0-5])|(2[0-4][0-9])|(1[0-9][0-9])|([1-9][0-9])|([0-9]))){3}$')
            # port [0,65535]
            pattern_port = re.compile(r'(^\d$)|(^[1-9]\d{1,3}$)|(^[1-5]\d{4}$)|(^6[0-5][0-5][0-3][0-5]$)')
            ip, port = maybe_ip.split(":")
            # print('ip ', re.match(pattern_ip, ip).group())
            # print('port ', re.match(pattern_port, port).group())
            if re.match(pattern_ip, ip) and re.match(pattern_port, port):
                return True
            else:
                return False

        except Exception:
            return False

    @staticmethod
    def freeProxy0(proxies=None) -> List[str]:
        """
        http://118.24.52.95/get_all/
        https://github.com/jhao104/proxy_pool/tree/1a3666283806a22ef287fba1a8efab7b94e94bac
        每日500次限额 超出限额后使用代理
        :param max_page:
        :return:
        """
        src_name = 'IP代理接口'
        print("使用来源： ", src_name)
        proxies = []
        url_format = 'http://118.24.52.95/get_all/'
        url = url_format
        good, content_type, res = make_req(url, proxies=proxies)
        if good and content_type == 'application/json':
            items = res.json(encoding='utf-8')
            cnt = 0
            for item in items:
                raw_ip = 'http://' + item['proxy']
                if ProxyFactory.proxy_str_check(raw_ip):
                    proxies.append(raw_ip)
                    cnt += 1
                else:
                    pass
            print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
        else:
            why = content_type
            print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy1(page_num=20, proxies=None) -> List[str]:
        """
        http://www.qydaili.com/free/?action=china&page=1
        齐云代理
        :param max_page:
        :return:
        """
        src_name = '齐云代理'
        print("使用来源： ", src_name)
        proxies = []
        url_format = 'https://www.7yip.cn/free/?action=china&page={page}'
        for i in range(page_num):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url)
            if good and content_type == 'text/html;charset=utf-8':
                items = re.findall(
                    r'<td.*?>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td.*?>(\d+)</td>',
                    res.text)
                cnt = 0
                for item in items:
                    raw_ip = 'http://' + item[0] + ":" + item[1]
                    if ProxyFactory.proxy_str_check(raw_ip):
                        proxies.append(raw_ip)
                        cnt += 1
                    else:
                        pass
                print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies


def generate_IP_by_scan() -> List[IP]:
    """
    轮流从多个来源中获取IP
    保证不重复 但可能为空
    :return: ['{host}:{port}']
    """
    sources = [ProxyFactory.freeProxy0, ProxyFactory.freeProxy1]
    factory = random.choice(sources)
    raw_IPs = set(factory(proxies=None))
    return [IP(proxy=ip) for ip in raw_IPs]


if __name__ == '__main__':
    print(generate_IP_by_scan())

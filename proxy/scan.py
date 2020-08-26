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


def debug(*info):
    print(info)
    exit()


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
    def freeProxy0(work_proxy=None) -> List[str]:
        """
        http://118.24.52.95/get_all/
        https://github.com/jhao104/proxy_pool/tree/1a3666283806a22ef287fba1a8efab7b94e94bac
        每日500次限额 超出限额后使用代理
        :param max_page:
        :return:
        """
        src_name = 'IP代理接口jhao104'
        print("使用来源0： ", src_name)
        proxies = []
        url_format = 'http://118.24.52.95/get_all/'
        url = url_format
        good, content_type, res = make_req(url, proxies=work_proxy)
        if good and content_type == 'application/json':
            items = res.json(encoding='utf-8')
            cnt = 0
            for item in items:
                raw_ip = item['proxy']
                if ProxyFactory.proxy_str_check(raw_ip):
                    proxies.append('http://' + raw_ip)
                    cnt += 1
                else:
                    pass
            print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
        else:
            why = content_type
            print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy1(page_num=20, work_proxy=None) -> List[str]:
        """
        https://www.7yip.cn/free/?action=china&page={page}
        齐云代理
        :param max_page:
        :return:
        """
        src_name = '齐云代理'
        print("使用来源1： ", src_name)
        proxies = []
        url_format = 'https://www.7yip.cn/free/?action=china&page={page}'
        for i in random.sample(list(range(page_num)), k=2):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url, proxies=work_proxy)
            if good and content_type == 'text/html;charset=utf-8':
                items = re.findall(
                    r'<td.*?>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td.*?>(\d+)</td>',
                    res.text)
                cnt = 0
                for item in items:
                    raw_ip = item[0] + ":" + item[1]
                    if ProxyFactory.proxy_str_check(raw_ip):
                        proxies.append('http://' + raw_ip)
                        cnt += 1
                    else:
                        pass
                print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy2(page_num=20, work_proxy=None) -> List[str]:
        """
        云代理 http://www.ip3366.net/free/
        注意频率
        :return:
        """
        src_name = '云代理'
        print("使用来源2： ", src_name)
        proxies = []
        url_formats = ['http://www.ip3366.net/free/?stype=1&page={page}',
                       "http://www.ip3366.net/free/?stype=2&page={page}"]
        for url_format in url_formats:
            for i in random.sample(list(range(page_num)), k=2):
                url = url_format.format(page=i + 1)
                good, content_type, res = make_req(url, proxies=work_proxy)
                if good and content_type == 'text/html':
                    items = re.findall(
                        r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>',
                        res.text)
                    cnt = 0
                    for item in items:
                        raw_ip = item[0] + ":" + item[1]
                        if ProxyFactory.proxy_str_check(raw_ip):
                            proxies.append('http://' + raw_ip)
                            cnt += 1
                        else:
                            pass
                    print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
                else:
                    why = content_type
                    print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy3(page_num=20, work_proxy=None) -> List[str]:
        """
        http://ip.jiangxianli.com/api/proxy_ips?page={page}
        免费代理库jiangxianli
        :return:
        """
        src_name = '免费代理库jiangxianli'
        print("使用来源3： ", src_name)
        proxies = []
        url_format = "https://ip.jiangxianli.com/api/proxy_ips?page={page}"
        for i in random.sample(list(range(page_num)), k=2):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url, proxies=work_proxy)
            print(url, good, content_type)
            if good and content_type == 'application/json':
                result_data = res.json(encoding='utf-8')
                items = result_data.get('data', dict(data=[])).get('data', [])
                if items:
                    cnt = 0
                    for item in items:
                        raw_ip = item['ip'] + ':' + item['port']
                        if ProxyFactory.proxy_str_check(raw_ip):
                            proxies.append('http://' + raw_ip)
                            cnt += 1
                        else:
                            pass
                    print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
                else:
                    print("---->通过来源：{0} {1} 获得0个IP".format(src_name, url))

            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy4(page_num=30, work_proxy=None) -> List[str]:
        """
        https://www.89ip.cn/index_{page}.html
        89代理
        :param max_page:
        :return:
        """
        src_name = '89代理'
        print("使用来源4： ", src_name)
        proxies = []
        url_format = 'https://www.89ip.cn/index_{page}.html'
        for i in random.sample(list(range(page_num)), k=2):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url, proxies=work_proxy)
            if good and 'text/html' in content_type:
                # \s* 0或多个空白字符
                items = re.findall(
                    r'<td>\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*</td>\s*<td>\s*(\d+)\s*</td>',
                    res.text)
                cnt = 0
                for item in items:
                    raw_ip = item[0] + ":" + item[1]
                    if ProxyFactory.proxy_str_check(raw_ip):
                        proxies.append('http://' + raw_ip)
                        cnt += 1
                    else:
                        pass
                print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy5(page_num=5, work_proxy=None) -> List[str]:
        """
        http://www.66ip.cn/{page}.html
        66代理
        :param max_page:
        :return:
        """
        src_name = '66代理'
        print("使用来源5： ", src_name)
        proxies = []
        url_format = 'http://www.66ip.cn/{page}.html'
        for i in random.sample(list(range(page_num)), k=2):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url, proxies=work_proxy)
            if good and 'text/html' in content_type:
                # \s* 0或多个空白字符
                items = re.findall(
                    r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td><td>(\d+)</td>',
                    res.text)
                cnt = 0
                for item in items:
                    raw_ip = item[0] + ":" + item[1]
                    if ProxyFactory.proxy_str_check(raw_ip):
                        proxies.append('http://' + raw_ip)
                        cnt += 1
                    else:
                        pass
                print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy6(page_num=10, work_proxy=None) -> List[str]:
        """
        https://www.kuaidaili.com/free/inha/{page}
        66代理
        :param max_page:
        :return:
        """
        src_name = '66代理'
        print("使用来源6： ", src_name)
        proxies = []
        url_format = 'https://www.kuaidaili.com/free/inha/{page}'
        for i in random.sample(list(range(page_num)), k=1):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url, proxies=work_proxy)
            if good and 'text/html' in content_type:
                # \s* 0或多个空白字符

                items = re.findall(
                    r'<td .*>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>\s*<td .*>(\d+)</td>',
                    res.text)
                cnt = 0
                for item in items:
                    raw_ip = item[0] + ":" + item[1]
                    if ProxyFactory.proxy_str_check(raw_ip):
                        proxies.append('http://' + raw_ip)
                        cnt += 1
                    else:
                        pass
                print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy7(page_num=100, work_proxy=None) -> List[str]:
        """
        http://www.xiladaili.com/gaoni/{page}/
        西拉代理
        :param max_page:
        :return:
        """
        src_name = '西拉代理'
        print("使用来源7： ", src_name)
        proxies = []
        url_format = 'http://www.xiladaili.com/gaoni/{page}/'
        for i in random.sample(list(range(page_num)), k=2):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url, proxies=work_proxy, timeout=15)
            if good and 'text/html' in content_type:
                # \s* 0或多个空白字符
                items = re.findall(
                    r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)</td>',
                    res.text)
                cnt = 0
                for item in items:
                    raw_ip = item[0] + ":" + item[1]
                    if ProxyFactory.proxy_str_check(raw_ip):
                        proxies.append('http://' + raw_ip)
                        cnt += 1
                    else:
                        pass
                print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies

    @staticmethod
    def freeProxy8(page_num=100, work_proxy=None) -> List[str]:
        """
        http://www.nimadaili.com/gaoni/{page}/
        西拉代理
        :param max_page:
        :return:
        """
        src_name = '尼玛代理'
        print("使用来源8： ", src_name)
        proxies = []
        url_format = 'http://www.nimadaili.com/gaoni/{page}/'
        for i in random.sample(list(range(page_num)), k=1):
            url = url_format.format(page=i + 1)
            good, content_type, res = make_req(url, proxies=work_proxy, timeout=15)

            if good and 'text/html' in content_type:
                # \s* 0或多个空白字符
                items = re.findall(
                    r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)</td>',
                    res.text)
                cnt = 0
                for item in items:
                    raw_ip = item[0] + ":" + item[1]
                    if ProxyFactory.proxy_str_check(raw_ip):
                        proxies.append('http://' + raw_ip)
                        cnt += 1
                    else:
                        pass
                print("---->通过来源：{0} {1} 获得{2}个IP".format(src_name, url, cnt))
            else:
                why = content_type
                print("---->通过来源：{0} {1} 获得IP失败 原因为{2}".format(src_name, url, why))
        return proxies


def generate_IP_by_scan(src=None) -> List[IP]:
    """
    轮流从多个来源中获取IP
    保证不重复 但可能为空
    :return: ['{host}:{port}']
    """
    if not src:
        sources = [
            ProxyFactory.freeProxy0, ProxyFactory.freeProxy1,
            ProxyFactory.freeProxy2, ProxyFactory.freeProxy3,
            ProxyFactory.freeProxy4, ProxyFactory.freeProxy5,
            ProxyFactory.freeProxy6, ProxyFactory.freeProxy7,
            ProxyFactory.freeProxy8
        ]
        factory = random.choice(sources)
    else:
        factory = src

    # work_proxy {host}:{port}
    raw_IPs = set(factory(work_proxy=None))
    return [IP(proxy=ip) for ip in raw_IPs]


if __name__ == '__main__':
    print(generate_IP_by_scan())

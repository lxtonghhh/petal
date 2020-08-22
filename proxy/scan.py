from typing import List
import asyncio, aiohttp
import time, random, re, requests
from db import get_db, DB_DATA, DB_IP, DB_TASK
import traceback
from utils.request import make_req
from proxy.common import IP

"""
while True
    选择一个来源 获取IP
    添加IP 写入redis ip:all
"""
TEST_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
    'Accept': '*/*',
}
TEST_URL_BILI = 'http://api.bilibili.com/x/relation/stat?vmid=38351330'
TEST_URL = TEST_URL_BILI


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
        proxies = []
        url_format = 'http://118.24.52.95/get_all/'
        url = url_format
        good, content_type, res = make_req(url, proxies=proxies)
        if good and content_type == 'application/json':
            items = res.json(encoding='utf-8')
            cnt = 0
            for item in items:
                raw_ip = item['proxy']
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
    def freeProxy1(page_num=20) -> List[str]:
        """
        http://www.qydaili.com/free/?action=china&page=1
        齐云代理
        :param max_page:
        :return:
        """
        src_name = '齐云代理'
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
                    raw_ip = item[0] + ":" + item[1]
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


def run_proxy_scan() -> List[str]:
    """
    轮流从多个来源中获取IP
    :return: ['{host}:{port}']
    """
    ips = ProxyFactory.freeProxy0(proxies=None)
    return ips


def app_scan_ip():
    def add_ip(ips: set):
        """
        将一组IP添加到队列中
        :param ips:{'123.125.114.21:80'}
        :return:
        """
        rdb = get_db(DB_IP)
        coll = "ip:all"
        """
        [{'proxy':'123.125.114.21:80'}]
        """
        items = [dict(proxy=ip) for ip in ips]
        return rdb.rpush(coll, items)

    app_name = "IP扫描"
    candidate = set()
    tick = 0
    # 一次性添加一组IP
    batch_num = 100
    while True:
        print("########第{0}次{1}开始".format(tick + 1, app_name))
        try:
            st = time.time()
            #步骤1 选择来源 获取IP
            ips = set(run_proxy_scan())
            if ips:
                candidate.update(ips)
                if len(candidate) > batch_num:
                    #步骤2 添加IP 写入redis ip:all
                    add_ip(candidate)
                    print("成功添加{0}个IP".format(len(candidate)))
                    candidate = set()
                else:
                    pass
            else:
                pass
            print("############第{0}次{1}结束 共有{2}个备选IP 用时{3}".format(tick + 1, app_name, len(ips), time.time() - st))
        except Exception as e:
            traceback.print_exc()
            print('执行主循环出现异常:', repr(e))
            print("########第{0}次{1}失败".format(tick + 1, app_name))

        finally:
            time.sleep(10 * random.random())
            tick += 1


if __name__ == '__main__':
    app_scan_ip()

from typing import List
import asyncio, aiohttp
import time, random, json
from db import get_db, DB_DATA, DB_IP, DB_TASK, parse_str
import traceback
from mixin import NodeMixin
import uuid

"""
从DB_IP ip:all获取测试IP
提供经过测试TEST_URL的可用IP
"""
TEST_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
    'Accept': '*/*',
}
TEST_URL_BILI = 'http://api.bilibili.com/x/relation/stat?vmid=38351330'
TEST_URL = TEST_URL_BILI



def get_ips() -> List[str]:
    """
    从redis中获取一组待测试IP
    :return: ['http://118.24.52.95','http://118.24.52.95',...]
    """
    """
    
    content
       [{'check_count': 417, 'fail_count': 0, 'last_status': 1, 'last_time': '2020-08-17 18:05:45',
              'proxy': '123.125.114.21:80', 'region': '', 'source': 'freeProxy09', 'type': ''}]
    :return:
    """
    rdb = get_db(DB_IP)
    coll = "ip:all"
    while True:

        """
        unknown_ips 确保有一定数量
        [
            {'proxy':'123.125.114.21:80'}
        ]
        """
        unknown_ips = parse_str(rdb.lpop(coll))
        # todo 用字符串的形式保存list很不优雅
        if unknown_ips:
            print("------>获取到{0}个待测试IP ".format(len(unknown_ips)), type(unknown_ips))
            return ['http://' + item['proxy'] for item in list(unknown_ips)]
        else:
            print("------>获取到0个待测试IP 即将重试")
            time.sleep(3 * random.random())


def run_proxy_test(test_num=200, test_url=TEST_URL, test_header=TEST_HEADER):
    def batch_task(todo_list) -> list:
        tasks = []
        # 自定义算法 timeout
        timeout = round(len(todo_list) / 20)
        for item in todo_list:
            task = asyncio.ensure_future(make_one_task(item, timeout))
            tasks.append(task)
        return tasks

    async def make_one_task(ip: str, timeout: int = 10) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                start = time.time()
                # allow_redirects = False禁止重定向
                async with session.get(test_url, headers=test_header, timeout=timeout, proxy=ip,
                                       allow_redirects=False) as res:
                    status_code = res.status
                    if status_code == 200:
                        # print('success', test_url, content)
                        print(status_code)
                        return dict(ip=ip, good=True, cost=time.time() - start)

                    else:
                        # print('fail', test_url, status_code, content)
                        return dict(ip=ip, good=False, cost=time.time() - start)
        except Exception as e:
            # print('执行单个任务出现异常 请求失败:', repr(e))
            return dict(ip=ip, good=False, cost=time.time() - start)

    tick = 0
    IP_DICT = {}
    good_ips = []
    loop = asyncio.get_event_loop()
    while tick < test_num:
        try:
            ip_pool = get_ips()
            print("######第{0}次测试开始 共有{1}个测试IP".format(tick + 1, len(ip_pool)))
            if len(ip_pool) > 0:
                try:
                    tasks = batch_task(ip_pool)
                    finished, unfinished = loop.run_until_complete(asyncio.wait(tasks))
                except Exception as e:
                    print('执行工作流出现异常:', repr(e))
                    print("######第{0}次测试失败".format(tick + 1))
                else:
                    print("######第{0}次测试完成结果： ".format(tick + 1))
                    for task in finished:
                        res = task.result()
                        ip = res.get('ip', 'empty')
                        info = IP_DICT.get(ip, dict(good=0, bad=0, cost=0))
                        if res.get('good', False):
                            # good
                            print(res)
                            good_ips.append(ip)
                            IP_DICT[ip] = dict(good=info['good'] + 1, bad=info['bad'],
                                               cost=info['cost'] + res.get('cost', 0))
                        else:
                            # bad
                            IP_DICT[ip] = dict(good=info['good'], bad=info['bad'] + 1,
                                               cost=info['cost'] + res.get('cost', 0))
                    print("######第{0}次测试完成 共有{1}个可用IP".format(tick + 1, len(good_ips)))
                finally:
                    pass
            else:
                # IP获取失败
                raise Exception('IP获取失败')

        except Exception as e:
            traceback.print_exc()
            print('执行IP测试出现异常:', repr(e))
            print("######第{0}次测试失败".format(tick + 1))
            time.sleep(7 * random.random())
        else:
            time.sleep(7 * random.random())
        finally:
            tick += 1
            good_ips = []
    # loop.close()
    res = [(ip, round(info['good'] / (info['good'] + info['bad']), 4),
            round(info['cost'] / (info['good'] + info['bad']), 4)) for ip, info in
           IP_DICT.items() if
           (info['good'] + info['bad']) > 0]
    res.sort(key=lambda x: x[1], reverse=True)
    return list(filter(lambda x: x[1] > 0, res))[0:15]


def app_provide_available_ip():
    def add_ip(ips: set):
        rdb = get_db(DB_IP)
        coll = "ip:available"
        rdb.delete(coll)
        return rdb.sadd(coll, *ips)

    candidate = set()
    tick = 0
    while True:
        print("########第{0}次IP测试开始".format(tick + 1))
        try:
            st = time.time()
            ips = set([item[0] for item in run_proxy_test(test_num=1)])
            if ips:
                candidate.update(ips)
                if len(candidate) > 3:
                    print("成功添加{0}个IP".format(add_ip(candidate)))
                    candidate = set()
                else:
                    pass
            else:
                pass
            print("############第{0}次工作流结束 本轮有{1}个可用IP 共{2}个可用IP 用时{3}".format(tick + 1, len(ips), len(candidate),
                                                                              time.time() - st))
        except Exception as e:
            print('执行主循环出现异常:', repr(e))
            print("########第{0}次IP测试失败".format(tick + 1))

        finally:
            time.sleep(10)
            tick += 1


import os

if __name__ == '__main__':
    rdb = get_db(DB_IP)
    coll = "ip:{target}".format(target='available')
    size = rdb.scard(coll)
    print(size, type(size),rdb.smembers(coll))

    # app_provide_available_ip()

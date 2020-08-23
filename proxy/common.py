from typing import List
import asyncio, aiohttp
import time, random, json
from db import get_db, DB_DATA, DB_IP, DB_TASK, parse_str
import traceback
from mixin import NodeMixin
import uuid
from .scan import generate_IP_by_scan, IP

TEST_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
    'Accept': '*/*',
}
TEST_URL_BILI = 'http://api.bilibili.com/x/relation/stat?vmid=38351330'


class IPManager(NodeMixin):
    """
    1.扫描IP
    检查可用IP池redis DB_IP ip:{target_name} (set)是否充足? 不足时从各个来源扫描IP保存到测试IP池self.pool中;充足则拷贝到测试IP池self.pool中
    2.维护高质量的IP池
    周期性测试测试IP池self.pool中IP对于不同TargetUrl的可用性，保存到可用IP池redis DB_IP ip:{target_name} (set) target_name对应不同TargetUrl
    todo 记录每个IP对应target_name的质量score 保存到redis DB_IP score (hash) proxy:dict(tar1:score1,tar2:score2)
    3.作为node接收msg 临时补充某个TargetUrl的IP池
    """

    def __init__(self):
        self.id = str(uuid.uuid1())  # 实例唯一id 用于注册 成为node
        self.register_node(self.id)

        self.targets = dict(
            bili=TEST_URL_BILI
        )
        self.test_pool = {target: set() for target in self.targets.keys()}
        self.min_supply = 5  # IP池最小供应量
        self.test_interval = 30

        self.isRunning = True
        self.dev_mode = False

    def msg_check(self):
        """
        检查是否有来自控制中心的消息
        :return:
        """
        # todo 纳入性能监控
        msg = self.receive_msg(self.id)
        if not msg:
            pass
        elif msg == 'stop':
            raise SystemExit
        elif msg == 'supply_ip':
            pass
        else:
            pass

    def do_test(self):
        """
        对于测试IP池中的IP进行不同TargetUrl的可用性测试 通过测试的保存到可用IP池 redis DB_IP ip:{target_name}
        todo 更新其质量信息
        :return:
        """
        pass

    def do_scan(self):
        """
        检查可用IP池是否充足 不足时从各个来源扫描IP 充足则拷贝
        更新到测试IP池self.test_pool
        :return:
        """
        rdb = get_db(DB_IP)
        for target_name in self.targets.keys():
            coll = "ip:{target}".format(target=target_name)
            size = rdb.scard(coll)
            # todo 保证不为空 目前为空抛出异常
            if size < self.min_supply:
                IPs = self._scan_ip()
                if not IPs:
                    raise Exception('No IP from this scan')
                else:
                    self.test_pool[target_name] = IPs
            else:
                raw_IPs = rdb.smembers(coll)
                if not raw_IPs:
                    raise Exception('No IP from this scan')
                else:
                    IPs = [IP(proxy=ip) for ip in raw_IPs]
                    self.test_pool[target_name] = IPs

    def _update_IPs(self, IPs, target):
        pass

    def _scan_ip(self) -> List(IP):
        """
        从来源扫描获取IP 保证不重复
        :return:
        """
        return generate_IP_by_scan()

    def run(self):
        while True:
            try:
                print("------------")
                # 功能 检查是否有来自控制中心的消息msg
                self.msg_check()
                # 功能 测试维护IP质量
                self.do_scan()
                # 功能 测试维护IP质量
                self.do_test()

            except Exception as e:
                print('Ooops Main Loop Error:', repr(e))
                if self.dev_mode:
                    traceback.print_exc()
                else:
                    pass
            except SystemExit:
                self._count_down()
                self.isRunning = False
            else:
                pass
            finally:
                if self.isRunning:
                    print("------------")
                    time.sleep(self.test_interval)
                else:
                    exit()

    def _count_down(self):
        seconds = 3
        for i in range(seconds, 0, -1):
            print("-" * i + "->Node{0} will be STOPPED in {1}".format(self.id, i))
            time.sleep(1)

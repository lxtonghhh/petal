import asyncio, aiohttp
from req import factory_req, Req
from proxy import app_provide_available_ip
from mixin import NodeMixin
from typing import List, Tuple, Set
from db import get_db, DB_DATA, DB_IP, DB_TASK, DB_STAT
import time, random, math, traceback
import enum
import uuid

"""
Worker 核心功能
1.IP的质量是瓶颈
以一个ip作为一次工作流 核心是把握每次工作流的效率 尽可能提高成功率
初始并发数为16 设置加速阈值 减速阈值 废弃阈值 根据每次工作流结束后的统计进行调整
2.从redis中获取可用IP
3.从队列获取任务打包成一次工作流 完成后打包进行持久化 失败任务放回

2020.8.21
根据bili的反爬频率限制 单个IP的good_QPS 理论上限为8-10 
目前性能瓶颈是IP质量 单个IP的good_QPS在 0.1-2
"""
BASE_CONCURRENCY = 16


class Worker(NodeMixin):

    def __init__(self):
        self.id = str(uuid.uuid1())  # 实例唯一id 用于注册 成为node
        # todo 离线模式
        self.register_node(self.id)
        self.isRunning = True  # 控制运行
        # self.good_data = []  # 成功任务的数据
        # self.bad_data = []
        self.good_total = 0  # 累计成功数
        self.all_totoal = 0
        self.good = set()  # 每次工作流成功任务的url_token
        self.all = set()  # 每次工作流全部任务的url_token
        self.ip = self._get_ip()
        self.start_time = time.time()  # 开始运行时间
        self.tick = 0  # 工作流次数
        self.timeout_all = 0
        self.timeout_good = 0
        self.timeout_bad = 0
        self.concurrency = BASE_CONCURRENCY
        self.capacity = 32  # 成功任务数据容量
        self.result = {}  # url_token:content
        # 性能监控定时器
        self.timer_interval = 60
        self.timer_start = time.time()  # 上一次定时器起点
        self.stat_task_cost = 0
        self.stat_data_cost = 0
        self.stat_ip_cost = 0
        self.stat_restore_cost = 0
        self.stat_good = 0
        self.stat_all = 0

    @property
    def interval(self) -> int:
        """
        每次工作流间隔时间算法
        :return:
        """
        return 0

    @property
    def timeout(self) -> int:
        """
        控制请求超时算法

        :return:
        """
        return 5

    def timer(self):
        """
        定时器 周期性记录性能
        计算间隔self.timer_interval
        计算一个周期内
        四大环节：
            获取任务用时 self.stat_task_cost
            采集数据用时 self.stat_data_cost
            更新IP用时 self.stat_ip_cost
            工作流结算用时 self.stat_restore_cost
        瞬时成功请求QPS self.stat_good / period
        平均成功请求QPS self.good_total / (ct - self.start_time
        瞬时所有请求QPS self.stat_all / period
        平均所有请求QPS self.all_totoal / (ct - self.start_time
        :return:
        """

        def _do_save(ct, period):
            if period <= 0:
                period = self.timer_interval
            else:
                pass
            print("------>开始一次性能监控 ", period)
            all_cost = sum([self.stat_task_cost,
                            self.stat_data_cost,
                            self.stat_ip_cost,
                            self.stat_restore_cost, ])
            result = dict(
                good_qps=round(self.stat_good / period, 4),
                good_qps_total=round(self.good_total / (ct - self.start_time), 4),
                all_qps=round(self.stat_all / period, 4),
                all_qps_total=round(self.all_totoal / (ct - self.start_time), 4),
                all_cost=round(all_cost, 4),
                task_cost=round(self.stat_task_cost / all_cost, 4),
                data_cost=round(self.stat_data_cost / all_cost, 4),
                ip_cost=round(self.stat_ip_cost / all_cost, 4),
                restore_cost=round(self.stat_restore_cost / all_cost, 4),

            )

            rdb = get_db(DB_STAT)
            coll = "stat:{0}".format(self.id)
            rdb.rpush(coll, result)
            self.stat_task_cost = 0
            self.stat_data_cost = 0
            self.stat_ip_cost = 0
            self.stat_restore_cost = 0
            self.stat_good = 0
            self.stat_all = 0
            print("------>完成一次性能监控 ", result)

        current_time = time.time()
        period = current_time - self.timer_start
        if period > self.timer_interval:
            # 完成一个周期 进行记录
            _do_save(ct=current_time, period=period)
            self.timer_start = time.time()
        else:
            pass

    def _get_ip(self) -> str:
        """
        确保从redis队列中获取一个IP
        :return:
        """
        # todo 统计IP获取效率
        rdb = get_db(DB_IP)
        coll = "ip:available"
        while True:
            ip = rdb.spop(coll)
            if not ip:
                time.sleep(random.random())
                continue
            else:
                return ip

    def msg_check(self):
        """
        检查是否有来自控制中心的消息
        :return:
        """
        # todo 纳入性能监控
        if self.receive_msg(self.id) == 'stop':
            raise SystemExit
        else:
            pass

    def fetch_task(self) -> List[Req]:
        st = time.time()
        todos = self._get_task()
        tasks = batch_req(todos, ip=self.ip, timeout=self.timeout)
        self.stat_task_cost += time.time() - st
        return tasks

    def update_ip(self):
        """
        完成一次工作流或者出现异常时调用
        确保IP质量 调整并发
        :return:
        """

        def _do_change():
            print("------>尝试更换IP：", self.ip)
            self._givaback_ip(self.ip)
            new_ip = self._get_ip()
            print("------>更换IP为：", new_ip)
            self.concurrency = BASE_CONCURRENCY
            self.ip = new_ip

        st = time.time()
        if len(self.all) == 0:
            pass
        elif len(self.good) / len(self.all) > 0.5:
            # 成功率高 提高并发
            self.concurrency *= 2
            if self.concurrency > 32:
                self.concurrency = 32
            else:
                pass
        elif len(self.good) / len(self.all) < 0.1:
            # 成功率极低 直接更换IP
            _do_change()
        elif len(self.good) / len(self.all) < 0.3:
            # 成功率比较低 降低并发
            pass
        else:
            # 保持现状
            pass
        self.stat_ip_cost += time.time() - st

    def _get_task(self) -> List[Req]:
        """
        从队列获取任务 将其封装成Req
        url_token保留在self.all
        :return:
        """
        # todo 统计任务获取效率
        rdb = get_db(DB_TASK)
        coll = "task:bili"

        tasks = []
        retry = 10  # 重试次数过多直接返回已有任务
        while len(tasks) < self.concurrency:
            task = rdb.lpop(coll)
            if not task:
                if retry <= 0:
                    break
                else:
                    retry -= 1
                    time.sleep(random.random())
                    continue
            else:
                tasks.append(task)
        self.all, res = parse_req(tasks)
        self.all_totoal += len(self.all)
        return res

    def _restore_before_stop(self):
        """
        退出前保存所有数据 返还相关信息
        :return:
        """
        if len(self.result) > 0:
            # 非严格按照self.capacity单位存储
            self._save()
            self.result = {}
        else:
            pass
        self._givaback_ip(self.ip)
        self._givaback_task()

    def restore(self):
        """
        完成一次工作流或者出现异常时调用
        对于good达到一定容量即存储 重置self.result
        对于self.all-self.good集合中的任务放回队列 重置self.good self.all
        :return:
        """
        st = time.time()
        if len(self.result) > self.capacity:
            # 非严格按照self.capacity单位存储
            self._save()
            self.result = {}
        else:
            pass
        self._givaback_task()
        self.stat_restore_cost += time.time() - st

    def reset(self):
        """
        结束一次工作流时调用
        :return:
        """
        self.good = set()
        self.all = set()

    def _save(self):
        rdb = get_db(DB_DATA)
        coll = "data:bili"
        print('------>保存{0}个完成任务 '.format(len(self.result.keys())))
        rdb.hmset(coll, self.result)

    def _givaback_ip(self, ip):
        rdb = get_db(DB_IP)
        coll = "ip:available"
        rdb.sadd(coll, ip)

    def _givaback_task(self):
        rdb = get_db(DB_TASK)
        coll = "task:bili"
        # List[str]
        todos = list(self.all - self.good)
        print('------>准备归还{0}个未完成任务 '.format(len(todos)), todos)

        if todos:
            # 不允许空数组
            print('------>完成归还后 队列中还有{0}个未完成任务 '.format(rdb.rpush(coll, *todos)))
        else:
            pass

    def run(self):
        loop = asyncio.get_event_loop()
        while True:
            try:
                self.timer()  # 性能监控计时
                self.msg_check()  # 检查是否有控制中心的消息
                # todo 处理任务打包可能发生的错误
                tasks = self.fetch_task()
                st_workflow = time.time()  # 记录工作流起始点
                print("######第{0}次工作流开始 共有{1}个任务 {2}".format(self.tick + 1, len(tasks), self.id))
                if len(tasks) > 0:
                    try:
                        # todo 是否存在unfinished
                        finished, unfinished = loop.run_until_complete(asyncio.wait(tasks))
                    except Exception as e:
                        print('执行工作流出现异常:', repr(e))
                        print("######第{0}次任务失败".format(self.tick + 1))
                    else:
                        print("######第{0}次任务完成结果： ".format(self.tick + 1))
                        # todo 封装处理结果
                        for task in finished:
                            res = task.result()
                            """
                            res{url_token,good,content,cost}
                            """
                            url_token = res.get('url_token', None)
                            if not url_token:
                                continue
                            else:
                                pass
                            if res.get('good', False):
                                # good
                                # self.good_data.append(dict(url_token=url_token, content=res.get('content', None)))
                                print(res, self.ip)
                                self.result[url_token] = res.get('content', None)
                                self.good.add(url_token)
                                self.good_total += 1
                                self.stat_good += 1
                                self.timeout_all += res.get('cost', 0)
                                self.stat_all += 1
                                self.timeout_good += res.get('cost', 0)
                            else:
                                # bad
                                # self.bad_data.append(dict(url_token=url_token, content=res.get('content', None)))
                                self.timeout_all += res.get('cost', 0)
                                self.stat_all += 1
                                self.timeout_bad += res.get('cost', 0)
                        good_qps = round(self.good_total / (time.time() - self.start_time), 2)
                        all_qps = round(self.all_totoal / (time.time() - self.start_time), 2)
                        print("######第{0}次任务完成 共有{1}/{2}个成功任务 累计成功{3}/{4} 成功QPS{5}/{6}"
                              .format(self.tick + 1,
                                      len(self.good),
                                      len(self.all),
                                      self.good_total,
                                      self.all_totoal,
                                      good_qps, all_qps))
                    finally:
                        pass
                        # print("------>事件循环是否仍在运行 ", loop.is_running())

                else:
                    # 任务获取失败
                    raise Exception('任务获取失败')
            except Exception as e:
                print('主循环出现异常:', repr(e))
                print("######第{0}次任务失败".format(self.tick + 1))
            except SystemExit:
                print("------>节点{0}收到控制中心的消息 即将停止运行".format(self.id))
                self.stop_node(self.id)
                self._restore_before_stop()
                # count_down倒计时
                seconds = 3
                for i in range(seconds, 0, -1):
                    print("-" * i + "->节点{0}将在{1}s后停止运行".format(self.id, i))
                    time.sleep(1)
                self.isRunning = False
            else:
                self.stat_data_cost += time.time() - st_workflow  # 记录本次工作流用时
            finally:
                # todo finally在调用了exit()都会执行 建议仅用于退出清算
                if self.isRunning:
                    print("######第{0}次任务结束后开始结算".format(self.tick + 1))
                    self.update_ip()
                    self.restore()
                    self.reset()
                    self.tick += 1
                    time.sleep(self.interval)
                else:
                    exit()
        loop.close()


BILI_USER = [str(1 + i) for i in range(100000)]
ONE_TEST = [str(1 + i) for i in range(100)]


def make_todo_list() -> List[Req]:
    return [factory_req('bili', uid=uid) for uid in ONE_TEST]


def parse_req(raw_tasks) -> Tuple[Set[str], List[Req]]:
    """
        raw_tasks
        ['1','2','3',...]
     """
    all = set()
    tasks = []
    for item in raw_tasks:
        if item:
            url_token = item
            all.add(url_token)
            tasks.append(factory_req(cmd='bili', uid=url_token))
        else:
            continue
    return (all, tasks)


def batch_req(todo_list: List[Req], ip: str, timeout=10) -> list:
    tasks = []
    for item in todo_list:
        task = asyncio.ensure_future(make_one_req(req=item, ip=ip, timeout=timeout))
        tasks.append(task)
    return tasks


def run():
    todos = make_todo_list()
    loop = asyncio.get_event_loop()
    try:
        tasks = batch_req(todos)
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
    except Exception as e:
        print(repr(e))


def get_content_type(res: aiohttp.ClientResponse):
    return res.headers.get('Content-Type', None)


async def make_one_req(req: Req, ip: str, timeout=10):
    """

    :param req_info -> Req

    :return: {url_token,good,content,cost}

    """
    try:
        async with aiohttp.ClientSession() as session:
            start = time.time()
            # proxy_auth=aiohttp.BasicAuth('user', 'pass')
            """
            async with resp:
            assert resp.status == 200
            """
            # allow_redirects = False禁止重定向
            async with session.get(req.url, headers=req.header, timeout=timeout, proxy=ip,
                                   allow_redirects=False) as res:
                status_code = res.status
                # content = await res.json(encoding='utf-8')
                if status_code == 200:
                    ct = get_content_type(res)
                    if 'application/json' in ct:
                        # 得到application/json类型的响应才算成功
                        print('success', req.url, ct)
                        content = await res.json(encoding='utf-8')
                        return dict(url_token=req.url_token, good=True, content=content, cost=time.time() - start)
                    else:
                        # content = await res.text()
                        return dict(url_token=req.url_token, good=False, content=None, cost=time.time() - start)
                else:
                    return dict(url_token=req.url_token, good=False, content=None, cost=time.time() - start)
    except Exception as e:
        # print('执行单个任务出现异常 请求失败:', repr(e))
        # traceback.print_exc()
        return dict(url_token=req.url_token, good=False, content=None, cost=time.time() - start)


def uoload_ip(ips=None):
    """
    清空并添加一批IP
    :return:
    """

    rdb = get_db(DB_IP)
    coll = "ip"
    rdb.delete(coll)
    return rdb.sadd(coll, *ips)


def upload_task(remove_repeat=True):
    """
    清空并添加一批任务
    :return:
    """
    pass
    rdb = get_db(DB_TASK)
    coll = "task:bili"
    rdb.delete(coll)
    tasks = [str(1 + i) for i in range(10000)]
    page_size = 100
    page_num = math.ceil(len(tasks) / page_size)
    page = 0
    if remove_repeat:
        # 需要去重
        rgb2 = get_db(DB_DATA)
        exist_tasks = rgb2.hkeys("data:bili")
        while page < page_num:
            candidate = tasks[page * page_size:page * page_size + page_size]
            batch = [task for task in candidate if task not in exist_tasks]
            print("添加{0}个任务到队列中".format(len(batch)))
            if batch:
                rdb.rpush(coll, *batch)
            else:
                pass
            page += 1
    else:
        while page < page_num:
            rdb.rpush(coll, *tasks[page * page_size:page * page_size + page_size])
            page += 1


def app():
    w = Worker()
    w.run()


class Cmd(enum.Enum):
    UPLOAD_IP = 0
    UPLOAD_TASK = 1
    APP = 2
    FETCH_IP = 3
    REFRESH_TASK = 4


if __name__ == '__main__':
    cmd = Cmd.APP
    if cmd == Cmd.UPLOAD_TASK:
        upload_task()
    elif cmd == Cmd.APP:
        app()
    elif cmd == Cmd.REFRESH_TASK:
        upload_task(remove_repeat=False)
    else:
        pass

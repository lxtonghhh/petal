from mixin import NodeMixin, NodeFaculty, NodeStatus
from base.message import Message, MessageCode
from typing import List, Tuple, Set
import time, random, math, traceback, json
import uuid


class Worker(NodeMixin):
    """
    节点管理
    处理消息
    生成id self.id
    """

    def __init__(self, faculty: NodeFaculty):
        self.id = str(uuid.uuid1())  # 实例唯一id 用于注册 成为node
        # todo 离线模式
        self.register_node(self.id, faculty)
        self.isRunning = True  # 控制运行
        self.dev_mode = True  # 开发模式打印错误栈

    def run(self):
        raise NotImplementedError

    def count_down(self):
        seconds = 3
        for i in range(seconds, 0, -1):
            print("-" * i + "->Node{0} will be STOPPED in {1}".format(self.id, i))
            time.sleep(1)

    def sleep(self, interval=1):
        time.sleep(interval)

    def msg_check(self):
        """
        检查是否有来自控制中心的消息 根据解析器执行具体处理 然后返回相关信息info
        对于msg优先执行专属self.special_parser
        若没有执行通用self.general_parse
        :return: info{}
        """
        msg = self.receive_msg(self.id)
        if not msg:
            pass
        else:
            print("收到消息:", msg)
            info1 = self.special_parser(msg)
            info2 = self.general_parser(msg, info1)
            return info2

    def special_parser(self, msg: Message) -> dict:
        """
        专属消息解析器 没有则执行通用消息解析器
        :param msg:
        :return: info [dict]
        """
        return {}

    def general_parser(self, msg: Message, info_before: dict) -> dict:
        """
        通用消息解析器 不可覆盖
        MessageCode.Stop触发SystemExit
        空消息通常为忽略
        :param msg:
        :param info_before:前一次解析执行的结果
        :return: info [dict]
        """
        if msg == MessageCode.Stop:
            raise SystemExit
        elif msg == MessageCode.Empty:
            return {}

    def sample_run(self):
        while True:
            try:
                # do work
                self.msg_check()
            except Exception as e:
                pass
                print('主循环出现异常:', repr(e))
            except SystemExit:
                self.stop_node(self.id)
                # do restore before exit
                self.count_down()
                self.isRunning = False
            else:
                pass
            finally:
                if self.isRunning:
                    time.sleep(1)
                else:
                    exit()


if __name__ == '__main__':
    a = {"age": 1}
    if a:
        print(1)
    else:
        print(2)

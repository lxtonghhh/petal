from mixin import NodeMixin
from typing import List, Tuple, Set
from db import get_db, DB_DATA, DB_IP, DB_TASK, DB_STAT
import time, random, math, traceback, json
import uuid
class Worker(NodeMixin):
    """
    节点管理
    处理消息
    生成id self.id
    """
    def __init__(self):
        self.id = str(uuid.uuid1())  # 实例唯一id 用于注册 成为node
        # todo 离线模式
        self.register_node(self.id)
        self.isRunning = True  # 控制运行
        self.dev_mode = True  # 开发模式打印错误栈

    def run(self):
        raise NotImplementedError

    def _count_down(self):
        seconds = 3
        for i in range(seconds, 0, -1):
            print("-" * i + "->Node{0} will be STOPPED in {1}".format(self.id, i))
            time.sleep(1)

    def msg_check(self):
        """
        检查是否有来自控制中心的消息
        对于msg优先执行专属self.special_parser
        若没有执行通用self.general_parse
        :return:
        """
        msg = self.receive_msg(self.id)
        if not msg:
            pass
        else:
            info = self.special_parser(msg)
            if info:
                return info
            else:
                return self.general_parser(msg)

    def special_parser(self, msg):
        """
        专属消息解析器
        :param msg:
        :return: info [dict]
        """
        return None

    def general_parser(self, msg):
        """
        通用消息解析器 不可覆盖
        :param msg:
        :return: info [dict]
        """
        pass


if __name__ == '__main__':
    pass


from typing import List, Tuple, Set
from helper.db import get_db, DB_CONTROL, db_loads
from base.worker import Worker, NodeFaculty, Message
import time

"""
值班员 1管理节点的运行 2接受来自Client命令执行 3服务中介
本身作为节点 主循环从自己的消息队列获取来自cli的消息作为命令
db: DB_CONTROL coll:node(nodekey:dict) 节点信息 {status,faculty} 
    运行状态status 
    职能faculty : collector monitor IP
db: DB_CONTROL coll:message(nodekey:list) 提供每个节点的消息队列 [{is_msg,code,name,content}]

Monitor提供服务发现功能 当其他node需要时直接向一个可用的Monitor发送消息即可 返回一个可用Monitor的nodekey 
find_to_who()
"""


def find_to_who() -> str:
    """
    todo 负载均衡
    如果当时没有可用 等待
    :return: 一个可用Monitor的nodekey
    """
    rdb = get_db(DB_CONTROL)
    coll = "node"
    while True:
        nodes = rdb.hgetall(coll)
        for nodekey, node_info in nodes.items():
            info = db_loads(node_info)
            if info.get('faculty', None) and info.get('status', 'Running'):
                print('找到可用Monitor', nodekey)
                return nodekey
            else:
                continue
        print('当前没有可用Monitor，继续搜索')
        time.sleep(5)


class Monitor(Worker):
    def __init__(self):
        super().__init__(faculty=NodeFaculty.Monitor)
        pass

    def do_send_msg(self, nodekey: str, msg: Message):
        """
        将Message序列化 加入nodekey的消息队列
        :param nodekey:
        :param msg:
        :return:
        """

        rdb = get_db(DB_CONTROL)
        coll = "message:{node}".format(node=nodekey)
        meg_str = msg.dumps()
        rdb.rpush(coll, meg_str)

    def special_parser(self, msg: Message):
        """
        处理主要来自cli的命令消息
        :param msg:
        :return:
        """
        pass

    def run(self):
        while True:
            try:
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
                    self.sleep()
                else:
                    exit()


def exe_get_node(nodekey: str):
    pass


def exe_stop_node(nodekey: str):
    rdb = get_db(DB_CONTROL)
    coll = "node"
    if not rdb.hexists(coll, nodekey):
        raise Exception("节点不存在", nodekey)
    else:
        info = db_loads(rdb.hget(coll, nodekey))
        print(info, type(info))
        status = info.get('status', None)
        if status and status == 'Running':
            _send_msg(nodekey, Message.Stop)
        else:
            raise Exception('节点已经停止', nodekey)


if __name__ == '__main__':
    m = Monitor()
    m.run()
    # stop_node("7b70489a-e837-11ea-805e-acfdcee0691e")

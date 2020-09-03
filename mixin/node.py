from base.message import Message, get_empty_message
from helper.db import get_db, DB_CONTROL, db_update_dict
import enum

"""
节点接口
db: DB_CONTROL coll:node(nodekey:dict) 节点运行状态 {status}
db: DB_CONTROL coll:message(nodekey:list) 提供每个节点的消息队列 [{cmd}]

"""


class NodeStatus(enum.Enum):
    Stopped = 0
    Running = 1


class NodeFaculty(enum.Enum):
    Collector = 1
    IP = 2
    Monitor = 3
    Client = 4


class NodeMixin(object):
    """
    节点与控制中心DB_CONTROL的交互
    """
    __slots__ = ()

    def register_node(self, nodekey: str, nodefaculty: NodeFaculty):
        """
        将实例在控制中心DB_CONTROL中注册 包括以下信息
            nodekey 唯一id 成为一个node
            status Running
            faculty 职能
        :return:
        """
        if not nodekey:
            raise Exception("无法注册 缺少id")
        else:
            rdb = get_db(DB_CONTROL)
            coll = "node"
            if rdb.hexists(coll, nodekey):
                raise Exception("无法注册 已存在同名node", nodekey)
            else:
                # todo 更新状态应该分离
                print('完成注册节点', nodekey)
                rdb.hset(coll, nodekey, dict(faculty=nodefaculty.name, status=NodeStatus.Running.name))

    def beat_node(self):
        """
        心跳检测 表示存活
        :return:
        """
        pass

    def receive_msg(self, nodekey: str) -> Message:
        """
        尝试从db: DB_CONTROL coll:message(nodekey:list)读取一个msg_str
        然后生成Message 队列中没有则生成空消息
        :return:
        """
        rdb = get_db(DB_CONTROL)
        coll = "message:{node}".format(node=nodekey)
        msg_str = rdb.lpop(coll)
        if not msg_str:
            return get_empty_message()
        else:
            print('------>收到到消息', msg_str)
            return Message.loads(msg_str)

    def stop_node(self, nodekey: str):
        """
        停止当前节点 更新注册信息
        :param nodekey:
        :return:
        """
        # todo 不存在是否应该处理?
        if not nodekey:
            pass
        else:
            rdb = get_db(DB_CONTROL)
            coll = "node"
            if rdb.hexists(coll, nodekey):
                # todo 更新状态应该分离
                old = rdb.hget(coll, nodekey)
                new = db_update_dict(old, dict(status=NodeStatus.Stopped.name))
                rdb.hset(coll, nodekey, new)
            else:
                pass

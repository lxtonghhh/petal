from monitor import Message, _send_msg
from db import get_db, DB_CONTROL

"""
节点接口
db: DB_CONTROL coll:node(nodekey:dict) 节点运行状态 {status}
db: DB_CONTROL coll:message(nodekey:list) 提供每个节点的消息队列 [{cmd}]

"""


class NodeMixin(object):
    """
    节点与控制中心DB_CONTROL的交互
    """
    __slots__ = ()

    def register_node(self, nodekey: str):
        """
        将实例在控制中心DB_CONTROL中注册 获得唯一id 成为一个node
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
                rdb.hset(coll, nodekey, dict(status="Running"))

    def beat_node(self):
        """
        心跳检测 表示存活
        :return:
        """
        pass

    def receive_msg(self, nodekey: str)->str:
        """
        尝试读取一个msg
        :return:
        """
        rdb = get_db(DB_CONTROL)
        coll = "message:{node}".format(node=nodekey)
        # todo 应传入消息解析器 而不应该在此处处理
        msg = rdb.lpop(coll)
        if not msg:
            return None
        else:
            print('------>收到到消息',msg)
            if msg == str(Message.Stop.value):
                return 'stop'
            else:
                return None
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
                rdb.hset(coll, nodekey, dict(status="Stopped"))
            else:
                pass


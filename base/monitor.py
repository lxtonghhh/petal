from typing import List, Tuple, Set
from helper.db import get_db, DB_CONTROL, db_loads
from base.worker import Worker, NodeFaculty, NodeStatus
from base.message import Message, MessageCode, get_empty_message, get_stop_message, get_res_message, do_send_msg, \
    do_receive_msg
import time, traceback

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
            if info.get('faculty', None) == NodeFaculty.Monitor.name \
                    and info.get('status', None) == NodeStatus.Running.name:
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

    def execute_cmd(self, msg: Message) -> Message:
        """
        处理Req类型消息，根据cmd调用执行函数exe，生成Res类型消息
        :param msg:
        :return:
        """
        ct = msg.content
        cmd = ct.get('cmd', None)

        exe = CmdMapping.get(cmd, None)
        if not exe:
            return get_empty_message()
        else:
            # 将content直接作为参数传入
            result = exe(self, **ct)
            if ct.get('need_res', False) == True:
                res_msg = get_res_message(src=self.id)
                # 需要将结果打包为dict
                res_msg.content = dict(res=result)
                return res_msg
            else:
                return get_empty_message(src=self.id)

    def special_parser(self, msg: Message):
        """
        处理主要来自cli的命令消息
        :param msg:
        :return:
        """
        if msg == MessageCode.Req:
            # 处理来自Client的Req类型消息
            target_nodekey = msg.src
            if not target_nodekey:
                # todo 缺少收件人
                pass
            else:
                res_msg = self.execute_cmd(msg)
                print('准备发送Res消息: ', res_msg)
                self.do_send_msg(target_nodekey, res_msg)
        else:
            pass

    def run(self):
        while True:
            try:
                self.msg_check()
            except Exception as e:
                pass
                print('主循环出现异常:', repr(e))
                traceback.print_exc(e)
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


# params中常用字段 nodekey:List[str]

def exe_cmd_get_node(cur_node: Worker, **params) -> List[dict]:
    """

    :param cur_node:
    :param params: nodekey:List[str]
    :return:
    """
    target_nodekeys = params.get('nodekey', [])
    rdb = get_db(DB_CONTROL)
    coll = "node"
    nodes = rdb.hgetall(coll)
    result = []
    if not target_nodekeys:
        # 未指定则默认返回全部存活节点信息
        for nodekey, node_info in nodes.items():
            info = db_loads(node_info)
            if info.get('status', None) == NodeStatus.Running.name:
                info.update(nodekey=nodekey)
                result.append(info)
            else:
                pass
    else:
        for nodekey, node_info in nodes.items():
            if nodekey in target_nodekeys:
                info = db_loads(node_info)
                info.update(nodekey=nodekey)
                result.append(info)
            else:
                pass
    print('result: ', result)
    return result


def exe_cmd_stop_node(cur_node: Worker, **params):
    """

    :param cur_node:
    :param params: nodekey:List[str]
    :return:
    """
    rdb = get_db(DB_CONTROL)
    coll = "node"
    target_nodekeys = params.get('nodekey', [])
    if not target_nodekeys:
        pass
    else:
        for nodekey in target_nodekeys:
            if not rdb.hexists(coll, nodekey):
                pass
            else:
                info = db_loads(rdb.hget(coll, nodekey))
                status = info.get('status', None)
                if status == NodeStatus.Running.name:
                    do_send_msg(nodekey, get_stop_message(src=cur_node.id))
                else:
                    pass


CmdMapping = {
    'get': exe_cmd_get_node,
    'stop': exe_cmd_stop_node,
}
if __name__ == '__main__':
    m = Monitor()
    m.run()

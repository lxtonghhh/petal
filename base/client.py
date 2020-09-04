from base.worker import Worker, NodeFaculty
from base.message import Message, MessageCode, get_req_message, do_send_msg, do_receive_msg
from base.monitor import find_to_who
from typing import Tuple
import time, traceback

"""
客户端与系统的cmd交互 专属消息类型Req Res 只发送Req类型消息 只接收Res类型消息
收到用户的命令cmd  
解析后调用相关执行函数exe处理
exe需要向Monitor发送有回复请求时：
    向Monitor发送Req类型消息 
    开始轮询等待一个对应的Res类型消息 本地会维护字典用于Req和Res的对应
    解析Res类型消息返回给用户
exe需要向Monitor发送无回复请求时：
    向Monitor发送Req类型消息 

支持命令 
quit 退出Cli
get -a 获得全部节点信息(节点id在本地映射为index)
get [index] 获得节点[index]信息
stop [index] 停止节点[index]运行
"""


def call_and_wait(my_nodekey: str, monitor_nodekey: str, req_msg: Message) -> Message:
    """
    向Monitor发送Req类型消息后 开始轮询自己的队列等待一个对应的Res类型消息
    todo 等待超时处理 轮询频率控制
    :param nodekey:
    :param req_msg:
    :return:
    """
    do_send_msg(monitor_nodekey, req_msg)
    while True:
        res_msg = do_receive_msg(my_nodekey)
        if res_msg == MessageCode.Res:
            return res_msg
        else:
            time.sleep(0.5)
            continue


def call_not_wait(monitor_nodekey: str, req_msg: Message):
    """
    向Monitor发送Req类型消息后 不等待Res
    :param nodekey:
    :param req_msg:
    :return:
    """
    do_send_msg(monitor_nodekey, req_msg)


# 执行函数至少带一个参数cur_node
def exe_quit_cli(cur_node: Worker, ):
    raise SystemExit


def exe_user_get_nodes(cur_node: Worker, target_nodekey: str):
    msg = get_req_message()
    if target_nodekey.strip() == '-a':
        # 获取全部node
        msg.content = dict(cmd='get', nodekey=[])
    else:
        msg.content = dict(cmd='get', nodekey=[target_nodekey.strip()])
    monitor_nodekey = find_to_who()
    res_msg = call_and_wait(cur_node.id, monitor_nodekey, msg)
    # 解析res content{nodes} nodes[{node}...] node{id,status,faculty}
    # todo fields 检查
    nodes = res_msg.content
    for node in nodes:
        print(node)


def exe_user_stop_node(cur_node: Worker, target_nodekey: str):
    msg = get_req_message()
    msg.content = dict(cmd='stop', nodekey=[target_nodekey.strip()])
    monitor_nodekey = find_to_who()
    call_not_wait(monitor_nodekey, msg)


CmdMapping = {
    'quit': exe_quit_cli,
    'get': exe_user_get_nodes,
    'stop': exe_user_stop_node,
}


class Client(Worker):
    def __init__(self):
        super().__init__(faculty=NodeFaculty.Client)

    def special_parser(self, msg: Message) -> dict:
        """
        专属消息解析器 没有则执行通用消息解析器
        :param msg:
        :return: info [dict]
        """
        return {}

    def parse_to_exe(self, raw_input: str) -> Tuple[bool, any, list]:
        """
        将输入命令字符串 转换为(是否有效命令，执行函数，参数列表)
        :param raw_input:
        :return:
        """
        # todo NameError: name 'function' is not defined 类型推断无法实现
        maybe_cmd, *args = raw_input.strip().split(' ')
        exe = CmdMapping.get(maybe_cmd, None)
        if not exe:
            is_cmd = False
        elif len(args) + 1 != get_args_num(exe):
            # 参数个数必须符合要求 执行函数至少带一个参数cur_node
            print("wrong args num: ", get_args_num(exe))
            is_cmd = False
        else:
            is_cmd = True
        return is_cmd, exe, args

    def run(self):
        while True:
            try:
                # do work
                ipt = input("$")
                is_cmd, exe, args = self.parse_to_exe(ipt)
                if is_cmd:
                    # print("Cmd:{0} will be executed.".format(theme_str(ipt)))
                    if args:
                        print(exe, *args)
                        exe(self, *args)
                    else:
                        exe(self)
                else:
                    print("Cmd:{0} is not supported.".format(theme_str(ipt)))
            except Exception as e:
                pass
                print('主循环出现异常:', repr(e))
                # todo 常见异常 JSON解析错误
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
                    self.sleep(0)
                else:
                    exit()


def theme_str(string: str) -> str:
    return '\033[1;32;43m{0}\033[0m'.format(string)


def get_args_num(func: object) -> int:
    # 输出的函数参数个数 func.__code__.co_argcount
    # 输出函数用到的所有变量名不止参数名 func.__code__.co_varnames
    return func.__code__.co_argcount


if __name__ == '__main__':
    client = Client()
    client.run()

import asyncio, aiohttp
from req import factory_req, Req
from proxy import app_provide_available_ip
from typing import List, Tuple, Set
from db import get_db,DB_CONTROL,parse_str
import time, random, math, traceback
import enum
import uuid

"""
管理节点的运行
db: DB_CONTROL coll:node(nodekey:dict) 节点运行状态 {status}
db: DB_CONTROL coll:message(nodekey:list) 提供每个节点的消息队列 [{cmd}]

"""


class Message(enum.Enum):
    Stop = 0


def _send_msg(nodekey: str, msg: Message):
    """

    :param nodekey:
    :param msg:
    :return:
    """
    rdb = get_db(DB_CONTROL)
    coll = "message:{node}".format(node=nodekey)
    if msg == Message.Stop:
        print('发出消息',nodekey,msg)
        rdb.rpush(coll, Message.Stop.value)
    else:
        raise Exception("消息类型不存在", msg)


def get_node(nodekey: str):
    pass


def all_nodes():
    pass


def stop_node(nodekey: str):
    rdb = get_db(DB_CONTROL)
    coll = "node"
    if not rdb.hexists(coll, nodekey):
        raise Exception("节点不存在", nodekey)
    else:
        info = parse_str(rdb.hget(coll, nodekey))
        print(info,type(info))
        status = info.get('status', None)
        if status and status == 'Running':
            _send_msg(nodekey, Message.Stop)
        else:
            raise Exception('节点已经停止', nodekey)


if __name__ == '__main__':
    stop_node("f116305c-e45d-11ea-9a75-acfdcee0691e")

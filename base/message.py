import enum
from helper.db import get_db, db_loads, db_dumps, DB_CONTROL


class MessageCode(enum.Enum):
    Empty = 0
    Stop = 1
    Req = 10  # 仅用于Client
    Res = 11  # 仅用于Client


def get_empty_message(src: str = None): return Message.make_message_by_quick(code=MessageCode.Empty, src=src)


def get_stop_message(src: str): return Message.make_message_by_quick(code=MessageCode.Stop, src=src)


def get_req_message(src: str): return Message.make_message_by_quick(code=MessageCode.Req, src=src)


def get_res_message(src: str): return Message.make_message_by_quick(code=MessageCode.Res, src=src)


class Message(object):
    """
    消息对象 用于节点间通信
    """
    allow_props = ['code', 'name', 'content', 'src']

    def __init__(self, code: MessageCode, content: dict, src: str):

        self.code = code.value  # 代码MessageCode.value [int]
        self.name = code.name  # 消息种类名称MessageCode.name [str]
        self.content = content  # 具体数据
        self.src = src  # 消息来源的nodekey

    def __bool__(self):
        """
        空消息的bool值为False
        :return:
        """
        if self.code == MessageCode.Empty.value:
            return False
        else:
            return True

    def __eq__(self, other: MessageCode):
        """
        直接与MessageCode比较
        :param other:
        :return:
        """
        if type(other) != MessageCode:
            return False
        else:
            return self.code == other.value

    def __setattr__(self, name, value):
        """
        支持修改属性 content'
        todo 属性特性 不可修改 code name
        :param name:
        :param value:
        :return:
        """
        if name not in Message.allow_props:
            raise Exception('Not allowed to set Attr of {0}'.format(name))
        else:
            if name == 'content':
                self.__dict__[name] = value if type(value) == dict else {}
            else:
                self.__dict__[name] = value

    def __str__(self):
        return "Message of {name}:{code} with {content}".format(name=self.name, code=self.code, content=self.content)

    def dumps(self):
        """
        为存储到redis中 将自身序列化
        :return: {is_msg,code,name,content}
        """
        return db_dumps(dict(is_msg=True, code=self.code, name=self.name, content=self.content, src=self.src))

    @staticmethod
    def loads(message_str: str):
        """
        从redis中获取到的序列化的msg 组装成Message对象
        无效则为空消息
        :param message_str: {is_msg,code,name,content}
        :return:
        """
        maybe_msg = db_loads(message_str)
        if maybe_msg.get('is_msg', False):
            code_name = maybe_msg.get('name', 'Empty')
            msg = Message.make_message_by_quick(code=MessageCode[code_name], src=maybe_msg.get('src', None))
            msg.content = maybe_msg.get('content', {})
            print('组装出消息对象: ', msg)
            return msg
        else:
            return get_empty_message()

    @staticmethod
    def make_message_by_quick(code: MessageCode, src: str):
        """
        根据code快速生成已定义好的消息 尚未定义content
        无效code生成空消息
        todo 错误消息
        :param code:
        :param src:生成消息的nodekey
        :return:
        """
        if type(code) != MessageCode:
            return Message(MessageCode.Empty, {}, src)
        else:
            return Message(code, {}, src)

    @staticmethod
    def make_message_by_template(code: MessageCode, src: str):
        """
        根据code生成常用模板消息 设置content
        无效code生成空消息或者无content
        :param code:
        :return:
        """
        msg = Message.make_message_by_quick(code, src)
        if code == MessageCode.Stop:
            msg.content = dict(value='stop')
        else:
            # 不设置content
            pass
        return msg


def do_send_msg(nodekey: str, msg: Message):
    """
    将Message序列化 加入nodekey的消息队列  位于redis:DB_CONTROL
    :param nodekey:
    :param msg:
    :return:
    """

    rdb = get_db(DB_CONTROL)
    coll = "message:{node}".format(node=nodekey)
    meg_str = msg.dumps()
    rdb.rpush(coll, meg_str)


def do_receive_msg(nodekey: str) -> Message:
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


if __name__ == '__main__':
    # 测试Message __eq__
    m = get_stop_message()
    print(m)
    mc1 = MessageCode.Stop
    mc2 = MessageCode.Empty
    print(m == mc1)
    print(m == mc2)
    print(m == 1)

    # 测试Message __bool__
    m = get_stop_message()
    if m:
        print(1)
    else:
        print(2)

    # 测试Message __setattr__
    try:
        m.content = 1
        m.age = 1
        print(m.content, m.name)
    except Exception as e:
        print(repr(e))

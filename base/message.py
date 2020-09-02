import enum
from helper.db import db_loads, db_dumps


class MessageCode(enum.Enum):
    Empty = 0
    Stop = 1


def get_empty_message(): return Message.make_message_by_quick(code=MessageCode.Empty)


def get_stop_message(): return Message.make_message_by_quick(code=MessageCode.Stop)


class Message(object):
    """
    消息对象 用于节点间通信
    """
    allow_props = ['code', 'name', 'content']

    def __init__(self, code: MessageCode, content: dict):
        self.code = code.value  # 代码MessageCode.value [int]
        self.name = code.name  # 消息种类名称MessageCode.name [str]
        self.content = content  # 具体数据

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

    def dumps(self):
        """
        为存储到redis中 将自身序列化
        :return: {is_msg,code,name,content}
        """
        return dict(is_msg=True, code=self.code.value, name=self.code.name, content=self.content)

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
            code = maybe_msg.get('code', MessageCode.Empty)
            msg = Message.make_message_by_quick(code=code)
            msg.content = maybe_msg.get('content', {})
            return msg
        else:
            return get_empty_message()

    @staticmethod
    def make_message_by_quick(code: MessageCode):
        """
        根据code快速生成已定义好的消息 尚未定义content
        无效code生成空消息
        todo 错误消息
        :param code:
        :return:
        """
        if code == MessageCode.Stop:
            return Message(code, {})
        else:
            code = MessageCode.Empty
            return Message(code, {})

    @staticmethod
    def make_message_by_template(code: MessageCode):
        """
        根据code生成常用模板消息 设置content
        无效code生成空消息或者无content
        :param code:
        :return:
        """
        msg = Message.make_message_by_quick(code)
        if code == MessageCode.Stop:
            msg.content = dict(value='stop')
        else:
            # 不设置content
            pass
        return msg


if __name__ == '__main__':

    # 测试Message __eq__
    m = get_stop_message()
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

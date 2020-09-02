import enum


class MessageCode(enum.Enum):
    Empty = 0
    Stop = 1


MessageMap = {
    MessageCode.Empty: 'Empty',
    MessageCode.Stop: 'Stop',
}
get_msg_name = lambda code: MessageMap[code]


def get_stop_message(): return Message.make_message_by_quick(code=MessageCode.Stop)


class Message(object):
    """
    消息对象 用于节点间通信
    """
    allow_props = ['code', 'name', 'content']

    def __init__(self, code: MessageCode, name: str, content: dict):
        self.code = code  # 代码 int
        self.name = name  # 消息种类名称 与code一一对应
        self.content = content  # 具体数据

    def __setattr__(self, name, value):
        """
        支持修改属性 content
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
            return Message(code, get_msg_name(code), {})
        else:
            code = MessageCode.Empty
            return Message(code, get_msg_name(code), {})

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
            msg.conten = dict(value='stop')
        else:
            # 不设置content
            pass
        return msg


if __name__ == '__main__':
    m = get_stop_message()
    m.content = 1
    m.age=1
    print(m.content,m.name)

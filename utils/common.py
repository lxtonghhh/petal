import re
def proxy_str_check(maybe_ip: str) -> bool:
    """
    确保正确的host:port格式
    :return:
    """
    try:
        # re.match 尝试从字符串的起始位置匹配一个模式，如果不是起始位置匹配成功的话，match()就返回none
        pattern_ip = re.compile(
            r'^((25[0-5])|(2[0-4][0-9])|(1[0-9][0-9])|([1-9][0-9])|([0-9]))(\.((25[0-5])|(2[0-4][0-9])|(1[0-9][0-9])|([1-9][0-9])|([0-9]))){3}$')
        # port [0,65535]
        pattern_port = re.compile(r'(^\d$)|(^[1-9]\d{1,3}$)|(^[1-5]\d{4}$)|(^6[0-5][0-5][0-3][0-5]$)')
        ip, port = maybe_ip.split(":")
        # print('ip ', re.match(pattern_ip, ip).group())
        # print('port ', re.match(pattern_port, port).group())
        if re.match(pattern_ip, ip) and re.match(pattern_port, port):
            return True
        else:
            return False

    except Exception as e:
        return False
if __name__ == '__main__':
    test = [
        '123.01.123.123:0',
        '123.01.123.123:111',
        '123.0.123.123:7777',
        '123.0.123.123:65535',
        '123.0.123.123:65555',
    ]
    for i in test:
        print(i, proxy_str_check(i))
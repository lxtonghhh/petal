from base.client import Client

"""
客户端与系统的交互
"""


def theme_str(string: str) -> str:
    return '\033[1;32;43m{0}\033[0m'.format(string)


def parse_to_cmd(raw_input: str) -> dict:
    pass


def main():
    exe_res = {}  # 执行结果
    cli = Client(exe_res)
    while True:
        ipt = input("$")
        cmd = parse_to_cmd(ipt)
        if not cmd:
            print("Cmd:{0} is not supported.".format(theme_str(cmd)))
            continue
        else:
            pass


if __name__ == '__main__':
    exit()
    main()

import redis, json
from setting import MY_CONFIG

DB_IP = 1
DB_TASK = 2
DB_DATA = 3
DB_STAT = 4
DB_CONTROL = 5

REDIS_CONFIG = MY_CONFIG


# decode_responses=True 默认为bytes类型
def get_db(db=DB_IP) -> redis.Redis:
    return redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=db, decode_responses=True,
                       password=REDIS_CONFIG['password'])


def db_dumps(save_obj: object):
    """

    使用json将对象序列化为字符串 以供redis存储
    目前支持list dict str
    不支持set
    todo pickle支持更多内置对象类型
    :param save_obj:
    :return:
    """
    if type(save_obj) in [dict,list]:
        return json.dumps(save_obj)
    elif type(save_obj) == str:
        return save_obj
    else:
        return None


def db_loads(res_str: str):
    """
    将redis返回的序列化对象字符串反序列化成对象
    :param res_str:
    :return:
    """
    if type(res_str) == str:
        return json.loads(res_str.replace("'", '"'), encoding='utf-8')
    else:
        return None


def parse_str(resStr: str):
    """
    将redis返回的序列化对象字符串反序列化成对象
    两种模式 pickle json
    :param resStr:
    :return:
    """
    if not resStr:
        return None
    else:
        return json.loads(resStr.replace("'", '"'), encoding='utf-8')


if __name__ == '__main__':
    rdb = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],
                      decode_responses=True,
                      password=REDIS_CONFIG['password'])
    rdb.set("age", 10)

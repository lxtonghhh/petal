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


def parse_str(resStr: str):
    """
    将redis返回的序列化对象字符串重新解析成对象
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
    rdb=get_db(DB_DATA)
    coll = "data:bili"
    print(rdb.hget(coll,'20001'))
    exist_tasks = rdb.hkeys("data:bili")
    print(len(exist_tasks))

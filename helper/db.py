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


def db_dumps(save_obj: object) -> str:
    """

    使用json将对象序列化为字符串 以供redis存储
    目前支持list dict str
    不支持set
    todo pickle支持更多内置对象类型
    :param save_obj:
    :return:
    """
    if type(save_obj) in [dict, list]:
        return json.dumps(save_obj)
    elif type(save_obj) == str:
        return save_obj
    else:
        # todo 防御int float等
        return str(save_obj)


def db_loads(res_str: str) -> dict:
    """
    将redis返回的序列化对象字符串反序列化成对象
    :param res_str:
    :return:
    """
    if type(res_str) == str:
        print(res_str.replace("'", '"'))
        return json.loads(res_str.replace("'", '"'))
    else:
        return {}


def db_update_dict(dict_str: str, new_dict: dict) -> dict:
    """
    更新redis中的dict 反序列化后返回新的dict
    :param dict_str:
    :param new_dict:
    :return:
    """
    if not dict_str:
        return new_dict
    else:
        old_dict = json.loads(dict_str.replace("'", '"'), encoding='utf-8')
        old_dict.update(new_dict)
        return old_dict

if __name__ == '__main__':

    s1='{"is_msg": True, "code": 0, "name": "Empty", "content": {"cmd": "get", "nodekey": []}}'

    s2={"is_msg": True, "code": 0, "name": "Empty", "content": {"cmd": "get", "nodekey": []}}
    print(json.dumps(s2))
    print(json.loads(json.dumps(s2)))
    exit()
    rdb = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],
                      decode_responses=True,
                      password=REDIS_CONFIG['password'])
    rdb.set("age", 10)

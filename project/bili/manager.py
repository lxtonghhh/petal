from db import get_db, DB_DATA
import json

SAMPLE_ITEM = {'code': 0, 'message': '0', 'ttl': 1,
               'data': {'mid': 22527, 'following': 18, 'whisper': 0, 'black': 0, 'follower': 1}}

parser = lambda itemStr: json.loads(s=itemStr.replace("'", '"'), encoding='utf-8')


class BiliStatManager():
    """
    管理任务分发
    结果存储
    """

    def arrange(self):
        pass

    def dump(self):
        pass


class BiliStatData(object):
    """
    数据库redis: DB_DATA data:bili
    url_token: SAMPLE_ITEM
    """

    @staticmethod
    def get(url_token) -> dict:
        rdb = get_db(DB_DATA)
        coll = "data:bili"
        return parser(rdb.hget(coll, url_token))

    @staticmethod
    def get_all() -> dict:
        """
        获取全部键值
        由于存储在redis上为key:objStr 需要将其序列化
        :return:
        """
        rdb = get_db(DB_DATA)
        coll = "data:bili"
        all_dict = rdb.hgetall(coll)

        print(len(all_dict))
        return {k: parser(v) for k, v in all_dict.items()}

    @staticmethod
    def validation(item: dict, url_token: str) -> bool:
        """
        检验格式及其真实性 假数据的mid恒为7 不与url_token一致
        :param item:
        :param url_token: 数据在采集层的唯一标识
        :return:
        """
        try:
            return str(item['data']['mid']) == str(url_token)
        except KeyError:
            return False


if __name__ == '__main__':
    ut='19999'
    item=BiliStatData.get(ut)
    print(item,type(item))
    print(BiliStatData.validation(item, ut))



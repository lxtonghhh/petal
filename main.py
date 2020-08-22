import asyncio, aiohttp
from req import factory_req, Req
from proxy import get_ip, get_ips
from typing import List

BILI_USER = [str(1+i) for i in range(100000)]
ONE_TEST=[str(1+i) for i in range(100)]

def make_todo_list() -> List[Req]:
    return [factory_req('bili', uid=uid) for uid in ONE_TEST]


def batch_req(todo_list: List[Req]) -> list:
    tasks = []
    for item in todo_list:
        task = asyncio.ensure_future(make_one_req(item))
        tasks.append(task)
    return tasks


def run():
    todos = make_todo_list()
    loop = asyncio.get_event_loop()
    try:
        tasks = batch_req(todos)
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
    except Exception as e:
        print(repr(e))


def get_content_type(res: aiohttp.ClientResponse):
    return res.headers.get('Content-Type', None)


async def make_one_req(req: Req):
    """

    :param req_info -> Req

    :return:
    """
    async with aiohttp.ClientSession() as session:
        try:
            # proxy_auth=aiohttp.BasicAuth('user', 'pass')
            """
            async with resp:
            assert resp.status == 200
            """
            async with session.get(req.url, headers=req.header, timeout=20,proxy='http://122.224.65.197:3128',allow_redirects = False) as res:
                status_code = res.status
                # content = await res.json(encoding='utf-8')


                if status_code == 200:
                    ct = get_content_type(res)
                    print('success', req.url, ct)
                    if 'application/json' in ct:
                        #得到application/json类型的响应才算成功
                        content = await res.json(encoding='utf-8')
                        print(content)
                    else:
                        content = await res.text()
                        print(res.url,content)
                        exit()
                        pass


                else:
                    print('fail', req.url, status_code)
        except Exception as e:
            print(repr(e))


if __name__ == '__main__':
    run()

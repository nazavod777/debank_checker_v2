from random import choice

from better_proxy import Proxy

with open(file='data/proxies.txt',
          mode='r',
          encoding='utf-8-sig') as file:
    proxies_list: list[str] = [
        Proxy.from_str(proxy=row.strip().rstrip().replace('https://', 'http://')
        if '://' in row.strip().rstrip()
        else f'http://{row.strip().rstrip()}').as_url for row in file
    ]


def get_proxy() -> str | None:
    if not proxies_list:
        return

    return choice(proxies_list)

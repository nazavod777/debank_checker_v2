import json
from json import dumps
from random import choices
from time import time

from utils import node_process


def generate_request_params(payload: dict,
                            method: str,
                            path: str) -> dict:
    method: str = method.upper()
    json_params: str = json.dumps(payload)

    node_process.stdin.write(f'{json_params}|{method}|{path}')
    node_process.stdin.flush()
    output_data: str = node_process.stdout.readline().strip()
    return_data: dict = json.loads(output_data)

    abc = 'abcdef0123456789'
    r_id = ''.join(choices(abc, k=32))
    r_time = str(int(time()))
    info = {
        'random_at': r_time,
        'random_id': r_id,
        'user_addr': None
    }
    account_header = dumps(info)

    return_data['account_header']: str = account_header

    return return_data

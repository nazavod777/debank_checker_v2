from curl_cffi.requests import AsyncSession

from .generate_request_params import generate_request_params


def set_headers(client: AsyncSession,
                payload: dict,
                path: str,
                method: str) -> None:
    request_params: dict = generate_request_params(
        payload=payload,
        method=method.upper(),
        path=path)

    client.headers['X-Api-Nonce']: str = request_params['nonce']
    client.headers['X-Api-Sign']: str = request_params['signature']
    client.headers['X-Api-Ts']: str = str(request_params['ts'])
    client.headers['account']: str = request_params['account_header']

import asyncio
from sys import platform

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.models import Response
from loguru import logger
from pyuseragents import random as random_useragent

from custom_types import FormattedAccount
from utils import format_account
from utils import loader, append_file, get_proxy, format_result
from utils.misc import set_headers

if platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Parser:
    def __init__(self,
                 account_data: FormattedAccount) -> None:
        self.account_data: FormattedAccount = account_data
        self.proxy: str | None = get_proxy()

    async def change_proxy(self,
                           client: AsyncSession) -> None:
        self.proxy: str | None = get_proxy()

        if not self.proxy:
            return

        client.proxies.update(
            {
                'http': self.proxy,
                'https': self.proxy
            }
        )

    async def get_total_usd_balance(self,
                                    client: AsyncSession) -> float:
        r: None = None

        while True:
            try:
                payload: dict = {
                    'user_addr': self.account_data.address.lower(),
                }

                set_headers(client=client,
                            payload=payload,
                            path='/asset/net_curve_24h',
                            method='GET')

                r: Response = await client.get(
                    url='https://api.debank.com/asset/net_curve_24h',
                    params=payload
                )

                usd_balance: float = r.json()['data']['usd_value_list'][-1][1]

                return usd_balance

            except Exception as error:
                await self.change_proxy(client=client)

                if r:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Total Balance: {error}, '
                        f'response: {r.text}'
                    )

                else:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Total Balance: {error}'
                    )

    async def get_used_chains(self,
                              client: AsyncSession) -> list[str]:
        r: None = None

        payload = {
            'id': self.account_data.address.lower(),
        }

        while True:
            try:
                set_headers(client=client,
                            payload=payload,
                            path='/user/used_chains',
                            method='GET')

                r: Response = await client.get(
                    url='https://api.debank.com/user/used_chains',
                    params=payload
                )

                chains: list[str] = r.json()['data']['chains']

                return chains

            except Exception as error:
                await self.change_proxy(client=client)

                if r:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Chains: {error}, '
                        f'response: {r.text}'
                    )

                else:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Chains: {error}'
                    )

    async def get_balance(self,
                          client: AsyncSession,
                          chains: list[str]) -> dict:
        r: None = None

        coins: dict = {}

        for current_chain in chains:
            while True:
                try:
                    payload: dict = {
                        'user_addr': self.account_data.address.lower(),
                        'chain': current_chain
                    }

                    set_headers(client=client,
                                payload=payload,
                                path='/token/balance_list',
                                method='GET')

                    r: Response = await client.get(
                        url='https://api.debank.com/token/balance_list',
                        params=payload
                    )

                    for coin in r.json()['data']:
                        try:
                            coin_in_usd = '?' if (coin["price"] is None) else coin["amount"] * coin["price"]
                            if isinstance(coin_in_usd, str) or isinstance(coin_in_usd, float):
                                if not coins.get(current_chain):
                                    coins[current_chain] = []

                                coins[current_chain].append({
                                    'amount': coin['amount'],
                                    'name': coin['name'],
                                    'ticker': coin['optimized_symbol'],
                                    'price': coin['price'],
                                    'logo_url': coin['logo_url']
                                })

                        except Exception as error:
                            logger.error(
                                f'{self.account_data.address} | Unexpected Error When Parsing Balance: {error}'
                            )

                except Exception as error:
                    await self.change_proxy(client=client)

                    if r:
                        logger.error(
                            f'{self.account_data.address} | Unexpected Error When Getting Token Balances: {error}, '
                            f'response: {r.text}'
                        )

                    else:
                        logger.error(
                            f'{self.account_data.address} | Unexpected Error When Getting Token Balances: {error}'
                        )

                else:
                    break

        return coins

    async def get_pools_balance(self,
                                client: AsyncSession) -> dict:
        r: None = None

        pools: dict = {}

        while True:
            try:
                payload: dict = {
                    'user_addr': self.account_data.address.lower(),
                }

                set_headers(client=client,
                            payload=payload,
                            path='/portfolio/project_list',
                            method='GET')

                r: Response = await client.get(url='https://api.debank.com/portfolio/project_list',
                                               params=payload)

                for pool in r.json()['data']:
                    try:
                        if not pools.get(pool['chain']):
                            pools[pool['chain']]: dict = {}

                        pools[pool['chain']][pool['name']]: list = []
                        for item in pool['portfolio_item_list']:
                            for coin in item['asset_token_list']:
                                pools[pool['chain']][pool['name']].append({
                                    'amount': coin['amount'],
                                    'name': coin['name'],
                                    'ticker': coin['optimized_symbol'],
                                    'price': coin['price'],
                                    'logo_url': coin['logo_url']
                                })

                    except Exception as error:
                        logger.error(
                            f'{self.account_data.address} | Unexpected Error When Parsing Pool Balance: {error}'
                        )

            except Exception as error:
                await self.change_proxy(client=client)

                if r:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Pool Balances: {error}, '
                        f'response: {r.text}'
                    )

                else:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Pool Balances: {error}'
                    )

            else:
                break

        return pools

    async def start_parser(self) -> None:
        client: AsyncSession = AsyncSession(
            verify=False,
            impersonate='chrome110',
            headers={
                'accept': '*/*',
                'accept-language': 'ru-RU,ru;q=0.9',
                'origin': 'https://debank.com',
                'referer': 'https://debank.com/',
                'source': 'web',
                'user-agent': random_useragent(),
                'x-api-ver': 'v2'
            },
            proxies={
                'http': self.proxy,
                'https': self.proxy
            } if self.proxy else None
        )
        total_usd_balance: float = await self.get_total_usd_balance(client=client)

        logger.info(f'{self.account_data.address} | Total USD Balance: {total_usd_balance}')

        chains_list: list[str] = await self.get_used_chains(client=client)

        logger.info(f'{self.account_data.address} | Used Chains: {len(chains_list)}')

        token_balances: dict = await self.get_balance(client=client,
                                                      chains=chains_list)

        tokens_balances_count: int = sum([len(token_balances[current_chain]) for current_chain in token_balances])

        logger.info(f'{self.account_data.address} | Tokens Balance: {tokens_balances_count}')

        pools_balances_count: int = sum([len(token_balances[current_chain]) for current_chain in token_balances])

        pools_balances: dict = await self.get_pools_balance(client=client)

        logger.info(f'{self.account_data.address} | Pools Balance: {pools_balances_count}')

        await format_result(account_data=self.account_data,
                            total_usd_balance=total_usd_balance,
                            token_balances=token_balances,
                            pools_balances=pools_balances)


async def start_parser(account_data: str) -> None:
    async with loader.semaphore:
        formatted_account: FormattedAccount | None = format_account(account_data=account_data)

        if not formatted_account:
            return

        try:
            await Parser(account_data=formatted_account).start_parser()

        except Exception as error:
            logger.error(f'{formatted_account.address} | Unexpected Error: {error}')

            async with asyncio.Lock():
                await append_file(
                    file_path='results/errors.txt',
                    file_content=f'{formatted_account.address}:{formatted_account.mnemonic if formatted_account.mnemonic else ""}:'
                                 f'{formatted_account.private_key if formatted_account.private_key else ""}\n'
                )

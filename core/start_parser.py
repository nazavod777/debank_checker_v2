import asyncio
import traceback
from sys import platform

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.models import Response
from loguru import logger
from pyuseragents import random as random_useragent

from custom_types import FormattedAccount
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

                if '<title>429 Too Many Requests</title>' in r.text:
                    logger.info(f'{self.account_data.address} | Too Many Requests')
                    await self.change_proxy(client=client)
                    continue

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

    async def get_tokens_used_chains(self,
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

                if '<title>429 Too Many Requests</title>' in r.text:
                    logger.info(f'{self.account_data.address} | Too Many Requests')
                    await self.change_proxy(client=client)
                    continue

                chains: list[str] = r.json()['data']['chains']

                return chains

            except Exception as error:
                await self.change_proxy(client=client)

                if r:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Tokens Chains: {error}, '
                        f'response: {r.text}'
                    )

                else:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting Tokens Chains: {error}'
                    )

    async def get_nft_used_chains(self,
                                  client: AsyncSession) -> list[str]:
        r: None = None

        payload = {
            'user_addr': self.account_data.address.lower(),
        }

        while True:
            try:
                set_headers(client=client,
                            payload=payload,
                            path='/nft/used_chains',
                            method='GET')

                r: Response = await client.get(
                    url='https://api.debank.com/nft/used_chains',
                    params=payload
                )

                if '<title>429 Too Many Requests</title>' in r.text:
                    logger.info(f'{self.account_data.address} | Too Many Requests')
                    await self.change_proxy(client=client)
                    continue

                chains: list[str] = r.json()['data']

                return chains

            except Exception as error:
                await self.change_proxy(client=client)

                if r:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting NFT Chains: {error}, '
                        f'response: {r.text}'
                    )

                else:
                    logger.error(
                        f'{self.account_data.address} | Unexpected Error When Getting NFT Chains: {error}'
                    )

    async def get_tokens_balance(self,
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

                    if '<title>429 Too Many Requests</title>' in r.text:
                        logger.info(f'{self.account_data.address} | Too Many Requests')
                        await self.change_proxy(client=client)
                        continue

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
                                f'{self.account_data.address} | Unexpected Error When Parsing Token Balance: {error}'
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

    async def get_nft_count(self,
                            client: AsyncSession,
                            chains: list[str]) -> int:
        r: None = None
        nfts_count: int = 0

        for current_chain in chains:
            while True:
                try:
                    payload: dict = {
                        'user_addr': self.account_data.address.lower(),
                        'chain': current_chain
                    }

                    set_headers(client=client,
                                payload=payload,
                                path='/nft/collection_list',
                                method='GET')

                    while True:
                        r: Response = await client.get(
                            url='https://api.debank.com/nft/collection_list',
                            params=payload
                        )

                        if '<title>429 Too Many Requests</title>' in r.text:
                            logger.info(f'{self.account_data.address} | Too Many Requests')
                            await self.change_proxy(client=client)
                            continue

                        if r.json()['data']['job'] is not None and r.json()['data']['job']['status'] == 'pending':
                            logger.info(f'{self.account_data.address} | NFT Balance Pending, sleeping 2 secs.')
                            await asyncio.sleep(delay=2)
                            continue

                        break

                    nfts_count += len(r.json()['data']['result']['data'])

                except Exception as error:
                    await self.change_proxy(client=client)

                    if r:
                        logger.error(
                            f'{self.account_data.address} | Unexpected Error When Getting NFT Balances: {error}, '
                            f'response: {r.text}'
                        )

                    else:
                        logger.error(
                            f'{self.account_data.address} | Unexpected Error When Getting NFT Balances: {error}'
                        )

                else:
                    break

        return nfts_count

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

                if '<title>429 Too Many Requests</title>' in r.text:
                    logger.info(f'{self.account_data.address} | Too Many Requests')
                    await self.change_proxy(client=client)
                    continue

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

        tokens_chains_list: list[str] = await self.get_tokens_used_chains(client=client)
        nft_chains_list: list[str] = await self.get_nft_used_chains(client=client)

        logger.info(
            f'{self.account_data.address} | Used Chains: Tokens - {len(tokens_chains_list)} | NFT - {len(nft_chains_list)}')

        nfts_count: int = await self.get_nft_count(client=client,
                                                   chains=nft_chains_list)
        logger.info(f'{self.account_data.address} | {nfts_count} NFT\'s')

        if total_usd_balance <= 0:
            await format_result(account_data=self.account_data,
                                total_usd_balance=total_usd_balance,
                                token_balances={},
                                pools_balances={},
                                nfts_count=nfts_count)
            return

        token_balances: dict = await self.get_tokens_balance(client=client,
                                                             chains=tokens_chains_list)

        tokens_balances_count: int = sum([len(token_balances[current_chain]) for current_chain in token_balances])

        logger.info(f'{self.account_data.address} | Tokens Balance: {tokens_balances_count}')

        pools_balances_count: int = sum([len(token_balances[current_chain]) for current_chain in token_balances])

        pools_balances: dict = await self.get_pools_balance(client=client)

        logger.info(f'{self.account_data.address} | Pools Balance: {pools_balances_count}')

        await format_result(account_data=self.account_data,
                            total_usd_balance=total_usd_balance,
                            token_balances=token_balances,
                            pools_balances=pools_balances,
                            nfts_count=nfts_count)


async def start_parser(account_data: FormattedAccount) -> None:
    async with loader.semaphore:
        try:
            return await Parser(account_data=account_data).start_parser()

        except Exception as error:
            print(traceback.format_exc())
            logger.error(f'{account_data.address} | Unexpected Error: {error}')

            async with asyncio.Lock():
                await append_file(
                    file_path='results/errors.txt',
                    file_content=f'{account_data.address}:{account_data.mnemonic if account_data.mnemonic else ""}:'
                                 f'{account_data.private_key if account_data.private_key else ""}\n'
                )

import asyncio
from os import mkdir
from os.path import exists
from sys import stderr, platform

from loguru import logger

from core import start_parser
from custom_types import FormattedAccount
from utils import format_account
from utils import loader

if platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    tasks: list[asyncio.Task] = [
        asyncio.create_task(coro=start_parser(account_data=current_account))
        for current_account in accounts_list
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    if not exists(path='results'):
        mkdir(path='results')

    with open(file='data/proxies.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        proxy_count: int = len([row.strip() for row in file if row.strip()])

    logger.success(f'Successfully Loaded {proxy_count} Proxies')

    with open(file='data/accounts.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        while True:
            data = file.read(16768)

            if not data:
                break

            accounts_list: list[str | FormattedAccount] = [row.strip().rstrip() for row in file]
            accounts_list: list[str | FormattedAccount] = list(set(accounts_list))
            accounts_list: list[FormattedAccount] = [format_account(account_data=row) for row in accounts_list]
            accounts_list: list[FormattedAccount] = [current_account for current_account in accounts_list if
                                                     current_account]

            loader.semaphore = asyncio.Semaphore(value=len(accounts_list))

            logger.info(f'Loaded Accounts: {len(accounts_list)}')

            try:
                import uvloop

                uvloop.run(main())

            except ModuleNotFoundError:
                asyncio.run(main())

    logger.success('Work has been successfully completed')
    input('\nPress Enter to Exit..')

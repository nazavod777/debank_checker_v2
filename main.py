import asyncio
from multiprocessing.dummy import Pool
from os import mkdir
from os.path import exists
from sys import stderr, platform

from loguru import logger

from core import start_parser
from custom_types import FormattedAccount
from utils import loader, format_account

if platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    loader.semaphore = asyncio.Semaphore(value=threads)

    tasks: list[asyncio.Task] = [
        asyncio.create_task(coro=start_parser(account_data=current_account))
        for current_account in formatted_accounts_list
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

    threads: int = int(input('\nThreads: '))
    last_account_data: str = ''

    with open(file='data/accounts.txt',
              mode='r+',
              encoding='utf-8-sig') as file:
        while True:
            data = file.read(16768)

            if not data:
                if not last_account_data:
                    break

                formatted_accounts_list: list[FormattedAccount] = format_account(account_data=last_account_data)

                if formatted_accounts_list:
                    print()
                    logger.info(f'Loaded Accounts: {len(formatted_accounts_list)}')

                    try:
                        import uvloop

                        uvloop.run(main())

                    except ModuleNotFoundError:
                        asyncio.run(main())

                break

            accounts_list: list[str] = [row for row in list(set([row.strip().rstrip()
                                                                 for row in data.split('\n')])) if row]
            accounts_list[0]: str = f'{last_account_data}{accounts_list[0]}'
            last_account_data: str = accounts_list[-1]
            del accounts_list[-1]

            formatted_accounts_list: list[FormattedAccount] = []

            with Pool(processes=threads) as executor:
                checked_accounts_list: list[list[FormattedAccount]] = [current_account for current_account
                                                                       in executor.map(format_account, accounts_list)
                                                                       if current_account]

            for current_checked_account in checked_accounts_list:
                formatted_accounts_list.extend(current_checked_account)

            print()
            logger.info(f'Loaded Accounts: {len(accounts_list)}')

            try:
                import uvloop

                uvloop.run(main())

            except ModuleNotFoundError:
                asyncio.run(main())

    logger.success('Work has been successfully completed')
    input('\nPress Enter to Exit..')

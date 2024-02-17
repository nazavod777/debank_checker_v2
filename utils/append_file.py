import asyncio
from sys import platform

import aiofiles

if platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def append_file(file_path: str,
                      file_content: str) -> None:
    async with aiofiles.open(file=file_path,
                             mode='a',
                             encoding='utf-8-sig') as file:
        await file.write(file_content)

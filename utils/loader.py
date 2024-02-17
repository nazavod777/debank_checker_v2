import asyncio
from sys import platform

if platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

semaphore: asyncio.Semaphore

import aiofiles


async def append_file(file_path: str,
                      file_content: str) -> None:
    async with aiofiles.open(file=file_path,
                             mode='a',
                             encoding='utf-8-sig') as file:
        await file.write(file_content)

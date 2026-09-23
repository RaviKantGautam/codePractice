What are coroutine and Task in asyncio?
Answer: coroutine are functions what starts with "async def" keyword. There are special functions that we can pause the execution in an event loop. these are also sometimes called as coroutine functions. Then there are coroutine object which used the "await" keyword, and these are waitables which are returned when we call these coroutine functions. They can suspend execution and resume it later but they are design to work with event loop.

When to use asyncio.gather and asyncio.TaskGroup?
Answer: 
asyncio.gather can take coroutine functions or tasks as list as argument with the extra parameter of return_exception = true in such a way that it don't care about the exception. For example:
tasks = [asyncio.create_task(fetch(i)) for i in range(1,3)]
result = await asyncio.gather(*tasks, return_exception=true)

where as asyncio.Taskgroup does the same work but can exit if exception happens and it example is
async with asyncio.TaskGroup() as tg:
    results = [tg.create_task(fetch(i)) for i in range(1,3)]
print(f" result {[result.result() for result in results]}")

which is library use to process files asyncroniously?
answer: aiofiles

async with aiofiles.open(download_path, "wb") as f:
    async for chunk in response.aiter_bytes(chunk_size=8192):
        await f.write(chunk)


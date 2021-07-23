import asyncio


async def wrap_coro(coro):
    # skip event for next iter
    await asyncio.sleep(0)
    return await coro

from ohwait import ohwait


async def coro():
    print("coro enter")
    print("coro exit")
    return 123


def sync_func():
    print("sync_func enter")
    result = ohwait(coro())
    print("sync_func exit")
    return result


async def async_func():
    print("async_func enter")
    # await coro()
    # print(ohwait(coro()))
    print(sync_func())
    print("async_func exit")


import asyncio

asyncio.run(async_func())

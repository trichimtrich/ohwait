from ohwait import ohwait


async def coro(a):
    print("coro enter")
    print("coro exit")
    return a


def sync_func():
    print("sync_func enter")
    result = ohwait(coro(1))
    # result = ohwait(coro(2), globals())
    print("sync_func exit")
    return result


async def async_func():
    result = 1
    print("async_func enter")
    # await coro()
    # ohwait(coro(1), globals())
    # print(ohwait(coro(1), globals()))
    print(sync_func())
    # result = ohwait(coro(4))
    # print(result)
    print("async_func exit")
    return result


import asyncio

asyncio.run(async_func())

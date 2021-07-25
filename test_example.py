import asyncio
from ohwait import ohwait


async def coro(a):
    print("> coroutine is running")
    await asyncio.sleep(0.5)
    return "result-" + a


def sync_func():  # to be called in a async chain
    print("> sync_func enter")
    result = ohwait(coro("from-ohwait-in-sync-func"))
    print("> sync_func exit")
    return result


async def async_func():
    print("> async_func enter")

    print(await coro("from-normal-await-call"))
    print(ohwait(coro("from-ohwait-directly")))
    print(sync_func())

    print("> async_func exit")


print("=" * 50 + " FIRST RUN " + "=" * 50)
asyncio.run(async_func())

print("=" * 50 + " SECOND RUN " + "=" * 50)
asyncio.run(async_func())

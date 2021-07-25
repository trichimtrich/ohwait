def use_curio():
    import curio

    async def _wrap_coro(coro):
        await curio.sleep(0)
        return await coro

    global wrap_coro
    wrap_coro = _wrap_coro


def use_trio():
    import trio

    async def _wrap_coro(coro):
        await trio.sleep(0)
        return await coro

    global wrap_coro
    wrap_coro = _wrap_coro


def use_asyncio():
    import asyncio

    async def _wrap_coro(coro):
        await asyncio.sleep(0)
        return await coro

    global wrap_coro
    wrap_coro = _wrap_coro


use_asyncio()

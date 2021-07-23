import trio
import ohwait._asynclib as lib


async def wrap_coro(coro):
    await trio.sleep(0)
    await coro


lib.wrap_coro = wrap_coro

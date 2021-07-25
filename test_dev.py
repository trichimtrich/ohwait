from ohwait import ohwait

import asyncio
import random


async def coro(a):
    r1 = random.randint(0, 100)
    print("[coro-{}] enter".format(r1))
    r2 = random.random() * 0.25
    print("[coro-{}] doing io job for ... {:.2f}s".format(r1, r2))
    await asyncio.sleep(r2)
    print("[coro-{}] get result: {}".format(r1, a))
    print("[coro-{}] exit".format(r1))
    return a


def nop(*args, **kargs):
    pass


def sync_func_bad_inject():
    print("sync_func_bad_inject enter")
    if 1 == 1:
        # NOTE: POP_JUMP 250
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        nop(1)
        result = ohwait(coro(4))
        # NOTE: after ohwait
        # POP_JUMP 260
    else:
        print("your cpu is crazy, burn it!!!")
    print("sync_func_bad_inject exit")
    return result


def sync_func():
    print("sync_func enter")
    print(ohwait(coro(2)))
    print("sync_func exit")


def sync_func2():
    print("sync_func2 enter")
    print(ohwait(coro(3)))
    print("sync_func2 exit")


async def async_func():
    result = 1
    print("async_func enter")

    print(await coro(0))
    print(ohwait(coro(1)))
    sync_func()
    sync_func2()
    sync_func_bad_inject()

    print("async_func exit")
    return result


from dis import dis

import asyncio

print(">" * 50 + " FIRST RUN " + "<" * 50)
asyncio.run(async_func())

# NOTE: re-run, check if injected
print(">" * 50 + " SECOND RUN " + "<" * 50)
asyncio.run(async_func())

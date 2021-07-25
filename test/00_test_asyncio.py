from ohwait import ohwait
import asyncio

from common import log_enter, log_exit

# IO
async def async_func_io_bound():
    log_enter()
    await asyncio.sleep(1)
    log_exit()
    return "io"


def sync_func_io():
    log_enter()
    result = ohwait(async_func_io_bound())
    log_exit()
    return result


async def async_task_io():
    log_enter()
    result = sync_func_io()
    log_exit()
    return result


# CPU
async def async_func_cpu_bound():
    log_enter()
    for i in range(100):
        pass
    log_exit()
    return "cpu"


def sync_func_cpu():
    log_enter()
    result = ohwait(async_func_cpu_bound())
    log_exit()
    return result


async def async_task_cpu():
    log_enter()
    result = sync_func_cpu()
    log_exit()
    return result


if __name__ == "__main__":
    coro_io = async_task_io()
    coro_cpu = async_task_cpu()

    group = asyncio.gather(coro_io, coro_cpu)

    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(group)

    print(">>> Final result: {}".format(results))

    loop.close()

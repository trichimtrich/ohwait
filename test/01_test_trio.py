from ohwait import ohwait
import trio
import ohwait.trio

from common import log_enter, log_exit


async def async_func_io_bound():
    log_enter()
    await trio.sleep(0.1)
    log_exit()
    return "io"


async def async_func_cpu_bound():
    log_enter()
    for i in range(100):
        pass
    log_exit()
    return "cpu"


def sync_func_io():
    log_enter()
    result = ohwait(async_func_io_bound())
    log_exit()
    return result


def sync_func_noblock():
    log_enter()
    result = ohwait(async_func_cpu_bound())
    log_exit()
    return result


async def async_task_io():
    log_enter()
    result = sync_func_io()
    log_exit()
    return result


async def async_task_cpu():
    log_enter()
    result = sync_func_noblock()
    log_exit()
    return result


async def main():
    # print(await async_task_cpu())
    print(await async_task_io())


if __name__ == "__main__":
    trio.run(main)

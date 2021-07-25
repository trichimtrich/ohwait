from ohwait import ohwait, use_curio
import curio

from common import log_enter, log_exit

# IO
async def async_func_io_bound():
    log_enter()
    await curio.sleep(1)
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
    _ = result  # NOTE: magic
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
    _ = result  # NOTE: magic
    log_exit()
    return result


if __name__ == "__main__":
    use_curio()
    print(">>> CPU result:", curio.run(async_task_cpu))
    print(">>> IO result:", curio.run(async_task_io))

import inspect

from . import _ohno as ohno
from ._asm import do_inject, asm
from . import _asynclib as lib

i_magic = b""  # (data, gen)
i_magic += asm("UNPACK_SEQUENCE", 2)  # gen -> data
i_magic += asm("DUP_TOP")  # gen -> data -> data
i_magic += asm("POP_JUMP_IF_FALSE", 8)  # check data == None , jump
i_magic += asm("YIELD_VALUE")  # yield data back => recv data
i_magic += asm("YIELD_FROM")  # send data, yield from


def ohwait(coro, g_debug={}):
    assert inspect.iscoroutine(coro), "must be a coroutine"
    no_sync = ohno.count_sync_funcs()

    if no_sync < 0:
        raise Exception("must run in async event loop")

    f = inspect.currentframe()

    rets = [lib.wrap_coro(coro).__await__()]
    for i in range(no_sync + 1):
        if i > 0:
            gen = ohno.new_generator(f)
            rets.append(gen)

        f = f.f_back
        i_idx = f.f_lasti + 2
        f_code = f.f_code

        # TODO: some bytes are changed
        if ohno.is_injected(f_code, i_idx, i_magic):
            continue

        co_code = f_code.co_code

        # TODO: upper part of injected code might grow...
        new_co_code = do_inject(co_code, i_idx, i_magic)
        ohno.overwrite_bytes(
            co_code, i_idx, new_co_code[i_idx : len(co_code)]
        )  # NOTE: xxx
        ohno.replace_co_code(f_code, new_co_code, f_code.co_stacksize + 2)

    ret = None
    for gen in rets[::-1]:
        ret = (ret, gen)

    if g_debug:
        from dis import dis
        import code

        print(ret)
        code.interact(local={**globals(), **locals(), **g_debug})

    # return (((None, gen2), gen1), __await__)
    return ret

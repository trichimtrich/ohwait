import inspect
import re

from . import _ohno as ohno
from ._asm import do_inject, asm
from . import _asynclib as lib

I_MAGIC = b""  # (data, data, gen)
I_MAGIC += asm("UNPACK_SEQUENCE", 3)  # gen -> data -> data
I_MAGIC += asm("POP_JUMP_IF_FALSE", 6)  # check data == None , jump -> yield from
I_MAGIC += asm("YIELD_VALUE")  # yield data back => recv data
I_MAGIC += asm("YIELD_FROM")  # send data, yield from

# NOTE: custom payload to check if function is injected
# pay attention to the JUMP bytecode and its oparg
I_MAGIC_PAT = b""
I_MAGIC_PAT += re.escape(asm("UNPACK_SEQUENCE", 3))
I_MAGIC_PAT += (
    b"(?:" + re.escape(asm("EXTENDED_ARG", 0)[:1]) + b".)*"
)  # if oparg > 0xff
I_MAGIC_PAT += (
    re.escape(asm("POP_JUMP_IF_FALSE", 0)[:1]) + b"."
)  # oparg value is not constant
I_MAGIC_PAT += re.escape(asm("YIELD_VALUE") + asm("YIELD_FROM"))
I_MAGIC_PAT = re.compile(I_MAGIC_PAT)

assert I_MAGIC_PAT.match(I_MAGIC), "create issue please : )"


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
        co_code = f_code.co_code

        # check if func is injected
        if I_MAGIC_PAT.match(co_code[i_idx:]):
            continue

        co_code = f_code.co_code

        # TODO: upper part of injected code might grow...
        new_co_code = do_inject(co_code, i_idx, I_MAGIC)
        ohno.overwrite_bytes(
            co_code, i_idx, new_co_code[i_idx : len(co_code)]
        )  # NOTE: xxx
        ohno.replace_co_code(f_code, new_co_code, f_code.co_stacksize + 2)

    ret = None
    for gen in rets[::-1]:
        ret = (ret, ret, gen)

    if g_debug:
        from dis import dis
        import code

        print(ret)
        code.interact(local={**globals(), **locals(), **g_debug})

    # return (((None, gen2), gen1), __await__)
    return ret

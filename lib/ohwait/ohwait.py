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
        i_offset = f.f_lasti + 2  # f_lasti => CALL_FUNCTIOn
        f_code = f.f_code
        co_code = f_code.co_code

        # check if func is injected
        if I_MAGIC_PAT.match(co_code[i_offset:]):
            print("oh hey")
            continue

        # NOTE: upper part of injected code might grow bigger...
        # call sequence: 1 -> 2 ---------------> 3 ---------------> 4
        # original func: A -> B (ohwait call) -> C               -> D
        # injected func: A -> A'              -> B (ohwait caul) -> I_MAGIC -> C -> D
        # after "ohwait call" at 2, next instruction is 3
        # YIELD code resets the code layout of frame in the next execution,
        # so we will hit B again at 3 because of unexpected A'.
        # Solution is replacing NOP to the old co_code at 3 before do yielding.
        # Next execution after yielding uses new_co_code, we should be fine.

        new_co_code, new_i_offset, new_i_end = do_inject(co_code, i_offset, I_MAGIC)
        r_code = new_co_code[new_i_offset:new_i_end]

        if i_offset != new_i_offset:
            # count how many A' == number of NOP for replacing
            count_nop = (new_i_offset - i_offset) // 2
            r_code = count_nop * asm("NOP") + r_code

        ohno.overwrite_bytes(co_code, i_offset, r_code)
        ohno.replace_co_code(f_code, new_co_code, f_code.co_stacksize + 2)

    ret = None
    for gen in rets[::-1]:
        ret = (ret, ret, gen)

    if g_debug:
        import code

        code.interact(local={**globals(), **locals(), **g_debug})

    # return ((None, None, gen), (None, None, gen), __await__)
    return ret

import inspect

from ._asm import do_inject, asm
import ohwait._ohno as ohno
import ohwait._asynclib as lib

# TODO: expand stack size

# modify sync funcs
I_SYNC = b""  # ((__await__, gen1), gen2)
I_SYNC += asm("YIELD_VALUE")  # send tuple, recv (__await__, gen1)
I_SYNC += asm("UNPACK_SEQUENCE", 2)  # unpack => gen1, __await__
I_SYNC += asm("YIELD_FROM")  # send __await__, gen1 == receiver

# modify async func
I_ASYNC = b""  # recv => ((__await__, gen1), gen2)
I_ASYNC += asm("UNPACK_SEQUENCE", 2)  # unpack =>  gen2, (__await__, gen1)
I_ASYNC += asm("YIELD_FROM")  # send tuple, gen2 == receiver


def ohwait(coro):
    assert inspect.iscoroutine(coro), "must be a coroutine"
    no_sync = ohno.count_sync_funcs()

    if no_sync < 0:
        raise Exception("must run in async event loop")

    f = inspect.currentframe()

    ret = (None, lib.wrap_coro(coro).__await__())
    for i in range(no_sync + 1):
        if i > 0:
            gen = ohno.new_generator(f)
            ret = (ret, gen)
        f = f.f_back
        f_code = f.f_code

        # TODO: fix pls, this only allows 1 ohwait in sync func
        if ohno.is_injected(f_code):
            continue

        if i < no_sync:
            # NOTE: overwrite 2 bytes after CALL_FUNCTION, 100% good
            i_code = I_SYNC
            o_len = 2
        else:
            # NOTE: overwrite 4 bytes after CALL_FUNCTION
            # so if python code is like this `return sync/ohwait(..)`
            # => only 2 bytes left in the `co_code` buffer
            # `co_code` buffer is malloc(size) in heap
            # the overflow 2 bytes could cause trouble ...
            # but the situation is quite rare
            i_code = I_ASYNC
            o_len = 4

        i_idx = f.f_lasti + 2
        co_code = f_code.co_code
        new_co_code = do_inject(co_code, i_idx, i_code)
        ohno.overwrite_bytes(co_code, i_idx, i_code[:o_len])
        ohno.replace_co_code(f_code, new_co_code)

        # TODO: this coordinates with `is_injected`, find a better way
        ohno.mark_injected(f_code)

    # return ((__await__, gen1), gen2)
    return ret

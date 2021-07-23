import inspect

from ._asm import do_inject, asm
import ohwait._ohno as ohno
import ohwait._asynclib as lib

# TODO: expand stack size


def ohwait2(coro):
    no_sync = ohno.count_sync_funcs()

    f = inspect.currentframe()

    i_code1 = b""  # ((__await__, gen1), gen2)
    i_code1 += asm("YIELD_VALUE")  # send tuple, recv (__await__, gen1)
    i_code1 += asm("UNPACK_SEQUENCE")  # unpack => gen1, __await__
    i_code1 += asm("YIELD_FROM")  # send __await__, gen1 == receiver

    # async-call
    i_code2 = b""  # recv => ((__await__, gen1), gen2)
    i_code2 += asm("UNPACK_SEQUENCE")  # unpack =>  gen2, (__await__, gen1)
    i_code2 += asm("YIELD_FROM")  # send tuple, gen2 == receiver

    ret = coro.__await__()
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
            i_code = i_code1
            o_len = 2
        else:
            # NOTE: overwrite 4 bytes after CALL_FUNCTION
            # so if python code is like this `return sync/ohwait(..)`
            # => only 2 bytes left in the `co_code` buffer
            # `co_code` buffer is malloc(size) in heap
            # the overflow 2 bytes could cause trouble ...
            # but the situation is quite rare
            i_code = i_code2
            o_len = 4

        i_idx = f.f_lasti + 2
        co_code = f_code.co_code
        new_co_code = do_inject(co_code, i_idx, i_code)
        ohno.overwrite_bytes(co_code, i_idx, i_code[:o_len])
        ohno.replace_co_code(f_code, new_co_code)

        # TODO: this coordinates with `is_injected`, find a better way
        ohno.mark_injected(f_code)


def ohwait(coro):
    assert inspect.iscoroutine(coro), "must be a coroutine"
    no_sync = ohno.count_sync_funcs()

    if no_sync < 0:
        raise Exception("must run in async event loop")

    f = inspect.currentframe()

    # TODO: still requrie 4 bytes after CALL_FUNCTION
    # can improve by YIELD_VALUE directly and unpack later
    i_code = b""
    i_code += asm("UNPACK_SEQUENCE", 2)  # return (gen), coro =>
    i_code += asm("YIELD_VALUE")  # yield (gen)
    i_code += asm("POP_TOP")  # ignore yield sent
    i_code += asm("LOAD_CONST", 0)
    i_code += asm("YIELD_FROM")

    rets = [lib.wrap_coro(coro).__await__()]
    for i in range(no_sync + 1):
        if i > 0:
            gen = ohno.new_generator(f)
            rets.insert(0, gen)

        f = f.f_back
        f_code = f.f_code
        if ohno.is_injected(f_code):
            continue

        i_idx = f.f_lasti + 2

        co_code = f_code.co_code
        new_co_code = do_inject(co_code, i_idx, i_code)
        ohno.overwrite_bytes(co_code, i_idx, i_code[:4])
        ohno.replace_co_code(f_code, new_co_code)
        ohno.mark_injected(f_code)

    ret = None
    for gen in rets:
        ret = (ret, gen)

    # return ( (None, gen2), gen1), __await__()
    return ret

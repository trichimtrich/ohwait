import inspect

from ._asm import do_inject, asm
import ohwait._ohno as ohno
import ohwait._asynclib as lib


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

    # TODO: refernce count stuff here !!! SIGSEGV
    h = inspect.currentframe()

    ret = None
    for gen in rets:
        ret = (ret, gen)

    # return ( (None, gen2), gen1), __await__()
    return ret

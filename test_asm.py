from ohwait._asm import do_inject, asm
from dis import dis


def hihi():
    print("hih")
    print("hoho")


co = hihi.__code__.co_code

dis(co)

print("yeah")

co2 = b""
co2 += asm("UNPACK_SEQUENCE", 2)
co2 += asm("DUP_TOP")
co2 += asm("POP_JUMP_IF_FALSE", 8)
co2 += asm("YIELD_VALUE")
co2 += asm("YIELD_FROM")

dis(co2)


print("oh")

co3 = do_inject(co, 8, co2)

dis(co3)

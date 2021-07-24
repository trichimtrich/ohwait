from ohwait._asm import do_inject, asm
from dis import dis


def hihi():
    print("hih")
    print("hoho")


co = hihi.__code__.co_code
co = b"t\x00d\x01\x83\x01\x01\x00t\x01t\x02d\x02\x83\x01t\x03\x83\x00\x83\x02\x01\x00d\x03}\x00|\x00d\x027\x00}\x00|\x00d\x027\x00}\x00|\x00d\x027\x00}\x00t\x00d\x04\x83\x01\x01\x00d\x00S\x00"

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

co3 = do_inject(co, 22, co2)

dis(co3)

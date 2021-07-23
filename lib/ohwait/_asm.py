import dis
import opcode
from struct import pack
import io

# TODO: add test cases


def asm(op, arg=None):
    if isinstance(op, str):
        op = opcode.opmap[op]
    code = b""
    if arg is None:
        arg = 0
    most_arg, exts = calc_args(arg)
    for ext in exts:
        code += pack("BB", opcode.EXTENDED_ARG, ext)
    code += pack("BB", op, most_arg)
    return code


def calc_size(arg):
    return (1 + len(calc_args(arg)[1])) * 2


def calc_args(arg):
    most_arg = arg & 0xFF
    arg >>= 8
    exts = []
    while arg:
        exts.insert(0, arg & 0xFF)
        arg >>= 8
    return most_arg, exts


def do_inject(co_code, inject_offset, inject_code):
    assert len(inject_code) % 2 == 0

    # parse old code
    insts = []
    offset_map = {}
    off_ext = 0
    for inst in dis._get_instructions_bytes(co_code):
        if inst.opcode == opcode.EXTENDED_ARG:
            # ignore
            if off_ext == 0:
                off_ext = inst.offset
        else:
            arg = inst.arg if inst.arg else 0
            offset = off_ext if off_ext else inst.offset
            rec = {
                "opcode": inst.opcode,
                "offset": offset,
                "arg": arg,
                "size": calc_size(arg),
            }
            offset_map[offset] = len(insts)
            insts.append(rec)
            off_ext = 0

    for inst in insts:
        op = inst["opcode"]
        offset = inst["offset"]
        size = inst["size"]
        arg = inst["arg"]
        if op in opcode.hasjrel:
            inst["j_inst"] = offset_map[offset + size + arg]
        elif op in opcode.hasjabs:
            inst["j_inst"] = offset_map[arg]
            inst["is_abs"] = True

    # inject
    insts_order = [i for i in range(len(insts))]
    inject_idx = offset_map[inject_offset]

    new_inst_idx = len(insts)
    insts.append(
        {
            "code": inject_code,
            "size": len(inject_code),
        }
    )

    insts_order.insert(inject_idx, new_inst_idx)

    # calculate extended args
    has_changed = True
    while has_changed:
        has_changed = False

        # regenerate offset
        offset = 0
        for idx in insts_order:
            rec = insts[idx]
            rec["offset"] = offset
            offset += rec["size"]

        # verify no_ext
        for idx in insts_order:
            rec = insts[idx]
            if "j_inst" not in rec:
                continue

            j_inst = rec["j_inst"]
            j_offset = insts[j_inst]["offset"]
            if rec.get("is_abs"):
                arg = j_offset
            else:
                arg = j_offset - rec["offset"] - rec["size"]

            rec["arg"] = arg
            new_size = calc_size(arg)
            if new_size > rec["size"]:
                rec["size"] = new_size
                has_changed = True

    # generate code
    code = io.BytesIO()
    for idx in insts_order:
        rec = insts[idx]
        assert code.tell() == rec["offset"]
        if "code" in rec:
            code.write(rec["code"])
        else:
            code.write(asm(rec["opcode"], rec["arg"]))

    code.seek(0)
    return code.read()

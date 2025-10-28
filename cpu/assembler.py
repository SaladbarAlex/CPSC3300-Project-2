# Very small assembler for a minimal MIPS-like subset used in this simulator.
# This is only for convenience/testing; your Project 1 output can be used directly if you
# produce hex words per line.

from . import isa

reg_alias = {
    **{name: idx for idx, name in isa.REG_NAMES.items()},
    # extras
    "$r0":0, "$r1":1, "$r2":2, "$r3":3, "$r4":4, "$r5":5, "$r6":6, "$r7":7,
    "$r8":8, "$r9":9, "$r10":10, "$r11":11, "$r12":12, "$r13":13, "$r14":14, "$r15":15,
    "$r16":16, "$r17":17, "$r18":18, "$r19":19, "$r20":20, "$r21":21, "$r22":22, "$r23":23,
    "$r24":24, "$r25":25, "$r26":26, "$r27":27, "$r28":28, "$r29":29, "$r30":30, "$r31":31,
}

def parse_reg(tok: str) -> int:
    tok = tok.strip().rstrip(',')
    if tok not in reg_alias:
        raise ValueError(f"Unknown register '{tok}'")
    return reg_alias[tok]

def parse_imm(tok: str) -> int:
    tok = tok.strip().rstrip(',')
    if tok.lower().startswith("0x"):
        return int(tok, 16)
    return int(tok, 10)

def parse_offset_addr(tok: str) -> (int,int):
    # format: imm(rs)
    tok = tok.strip().rstrip(',')
    if '(' in tok and tok.endswith(')'):
        imm_s, rs_s = tok.split('(')
        rs_s = rs_s[:-1]
        return parse_imm(imm_s), parse_reg(rs_s)
    raise ValueError(f"Bad memory operand {tok} (want imm(rs))")

def assemble(lines):
    # Two-pass to resolve labels for beq/j
    cleaned = []
    labels = {}
    pc = 0
    for line in lines:
        s = line.split('#')[0].strip()
        if not s:
            continue
        if s.endswith(':'):
            label = s[:-1].strip()
            labels[label] = pc
        else:
            cleaned.append(s)
            pc += 4

    words = []
    pc = 0
    for s in cleaned:
        parts = [p.strip() for p in s.replace('\t', ' ').split()]
        mn = parts[0].lower()
        ops = " ".join(parts[1:])

        def split_ops(k=3):
            return [x.strip() for x in ops.split(',')]

        if mn in ('add','sub','and','or','slt'):
            rd, rs, rt = split_ops(3)
            rd, rs, rt = parse_reg(rd), parse_reg(rs), parse_reg(rt)
            funct = {'add': isa.FUNCT_ADD, 'sub': isa.FUNCT_SUB, 'and': isa.FUNCT_AND,
                     'or': isa.FUNCT_OR, 'slt': isa.FUNCT_SLT}[mn]
            w = isa.encode_r(rs, rt, rd, 0, funct)

        elif mn == 'addi':
            rt, rs, imm = split_ops(3)
            rt, rs, imm = parse_reg(rt), parse_reg(rs), parse_imm(imm)
            w = isa.encode_i(isa.OP_ADDI, rs, rt, imm)

        elif mn == 'lw':
            rt, memop = split_ops(2)
            rt = parse_reg(rt)
            imm, rs = parse_offset_addr(memop)
            w = isa.encode_i(isa.OP_LW, rs, rt, imm)

        elif mn == 'sw':
            rt, memop = split_ops(2)
            rt = parse_reg(rt)
            imm, rs = parse_offset_addr(memop)
            w = isa.encode_i(isa.OP_SW, rs, rt, imm)

        elif mn == 'beq':
            rs, rt, label = split_ops(3)
            rs, rt = parse_reg(rs), parse_reg(rt)
            if label not in labels:
                raise ValueError(f"Unknown label {label}")
            target = labels[label]
            # imm = (target - (pc+4)) >> 2
            imm = (target - (pc + 4)) // 4
            w = isa.encode_i(isa.OP_BEQ, rs, rt, imm & 0xFFFF)

        elif mn == 'j':
            label = split_ops(1)[0]
            if label not in labels:
                raise ValueError(f"Unknown label {label}")
            target = labels[label]
            addr = (target >> 2) & 0x3FFFFFF
            w = isa.encode_j(isa.OP_J, addr)

        elif mn == 'halt':
            w = isa.HALT_WORD

        else:
            raise ValueError(f"Unknown mnemonic {mn}")

        words.append(w)
        pc += 4
    return words

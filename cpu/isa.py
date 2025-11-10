from dataclasses import dataclass
from typing import Optional

# MIPS-like encodings (big-endian conceptual layout, but we store ints)
# R-type: opcode(6)=0 | rs(5) | rt(5) | rd(5) | shamt(5) | funct(6)
# I-type: opcode(6)   | rs(5) | rt(5) | imm(16)
# J-type: opcode(6)   | address(26)
#
# Supported mnemonics: add, sub, and, or, slt, lw, sw, beq, addi, j, halt (special 0xFFFFFFFF)

OP_RTYPE = 0x00
OP_J     = 0x02
OP_BEQ   = 0x04
OP_ADDI  = 0x08
OP_LW    = 0x23
OP_SW    = 0x2B

FUNCT_ADD = 0x20
FUNCT_SUB = 0x22
FUNCT_AND = 0x24
FUNCT_OR  = 0x25
FUNCT_SLT = 0x2A

HALT_WORD = 0xFFFFFFFF

REG_NAMES = {
    0: "$zero", 1:"$at",
    2:"$v0", 3:"$v1",
    4:"$a0", 5:"$a1", 6:"$a2", 7:"$a3",
    8:"$t0", 9:"$t1", 10:"$t2", 11:"$t3", 12:"$t4", 13:"$t5", 14:"$t6", 15:"$t7",
    16:"$s0", 17:"$s1", 18:"$s2", 19:"$s3", 20:"$s4", 21:"$s5", 22:"$s6", 23:"$s7",
    24:"$t8", 25:"$t9",
    26:"$k0", 27:"$k1",
    28:"$gp", 29:"$sp", 30:"$fp", 31:"$ra",
}

@dataclass
class DecodedInstr:
    raw: int
    opcode: int
    rs: int = 0
    rt: int = 0
    rd: int = 0
    shamt: int = 0
    funct: int = 0
    imm: int = 0
    addr: int = 0
    mnemonic: Optional[str] = None

def sign_extend_16(x: int) -> int:
    """Convert a 16-bit immediate into a Python int with sign extension."""
    x &= 0xFFFF
    if x & 0x8000:
        return x - 0x10000
    return x

def decode(word: int) -> DecodedInstr:
    """Break a 32-bit instruction word into its constituent fields."""
    if word == HALT_WORD:
        return DecodedInstr(raw=word, opcode=-1, mnemonic="halt")
    opcode = (word >> 26) & 0x3F
    if opcode == OP_RTYPE:
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        shamt = (word >> 6) & 0x1F
        funct = word & 0x3F
        mnem = {
            FUNCT_ADD:"add", FUNCT_SUB:"sub", FUNCT_AND:"and",
            FUNCT_OR:"or", FUNCT_SLT:"slt"
        }.get(funct, "unknown")
        return DecodedInstr(raw=word, opcode=opcode, rs=rs, rt=rt, rd=rd, shamt=shamt, funct=funct, mnemonic=mnem)
    elif opcode in (OP_LW, OP_SW, OP_BEQ, OP_ADDI):
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        imm = sign_extend_16(word & 0xFFFF)
        mnem = {OP_LW:"lw", OP_SW:"sw", OP_BEQ:"beq", OP_ADDI:"addi"}[opcode]
        return DecodedInstr(raw=word, opcode=opcode, rs=rs, rt=rt, imm=imm, mnemonic=mnem)
    elif opcode == OP_J:
        addr = word & 0x3FFFFFF
        return DecodedInstr(raw=word, opcode=opcode, addr=addr, mnemonic="j")
    else:
        return DecodedInstr(raw=word, opcode=opcode, mnemonic="unknown")

def encode_r(rs, rt, rd, shamt, funct):
    """Build an R-type instruction word from its fields."""
    return (OP_RTYPE << 26) | (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct

def encode_i(op, rs, rt, imm):
    """Build an I-type instruction word with a 16-bit immediate."""
    imm &= 0xFFFF
    return (op << 26) | (rs << 21) | (rt << 16) | imm

def encode_j(op, addr):
    """Build a J-type instruction word from opcode and 26-bit address."""
    addr &= 0x3FFFFFF
    return (op << 26) | addr

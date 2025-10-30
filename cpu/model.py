from dataclasses import dataclass, field
from typing import List, Callable, Optional
from .stats import Stats
from . import isa

WORD = 4

def mask32(x:int) -> int:
    return x & 0xFFFFFFFF

@dataclass
class Memory:
    size_bytes: int = 64 * 1024
    data: bytearray = field(default_factory=lambda: bytearray(64*1024))

    def read_word(self, addr: int) -> int:
        if addr % 4 != 0 or addr < 0 or addr+3 >= self.size_bytes:
            raise MemoryError(f"Unaligned or OOB word read @0x{addr:08X}")
        b = self.data[addr:addr+4]
        return int.from_bytes(b, byteorder="big", signed=False)

    def write_word(self, addr: int, value: int):
        if addr % 4 != 0 or addr < 0 or addr+3 >= self.size_bytes:
            raise MemoryError(f"Unaligned or OOB word write @0x{addr:08X}")
        self.data[addr:addr+4] = mask32(value).to_bytes(4, byteorder="big", signed=False)

    def read_byte(self, addr: int) -> int:
        if addr < 0 or addr >= self.size_bytes:
            raise MemoryError(f"OOB byte read @0x{addr:08X}")
        return self.data[addr]

    def write_byte(self, addr: int, value: int):
        if addr < 0 or addr >= self.size_bytes:
            raise MemoryError(f"OOB byte write @0x{addr:08X}")
        self.data[addr] = value & 0xFF

@dataclass
class RegisterFile:
    regs: List[int] = field(default_factory=lambda: [0]*32)

    def __getitem__(self, idx: int) -> int:
        return self.regs[idx] if idx != 0 else 0  # $zero stays 0

    def __setitem__(self, idx: int, value: int):
        if idx != 0:
            self.regs[idx] = mask32(value)

@dataclass
class ALU:
    def add(self, a:int, b:int) -> int:
        return mask32((a + b) & 0xFFFFFFFF)

    def sub(self, a:int, b:int) -> int:
        return mask32((a - b) & 0xFFFFFFFF)

    def bitand(self, a:int, b:int) -> int:
        return mask32(a & b)

    def bitor(self, a:int, b:int) -> int:
        return mask32(a | b)

    def slt(self, a:int, b:int) -> int:
        # signed compare
        sa = a if a < 0x80000000 else a - 0x100000000
        sb = b if b < 0x80000000 else b - 0x100000000
        return 1 if sa < sb else 0

Observer = Callable[["CPUModel"], None]

@dataclass
class CPUModel:
    mem: Memory = field(default_factory=Memory)
    regs: RegisterFile = field(default_factory=RegisterFile)
    alu: ALU = field(default_factory=ALU)
    stats: Stats = field(default_factory=Stats)
    pc: int = 0
    observers: List[Observer] = field(default_factory=list)
    running: bool = True
    instr_window: int = 64  # for view convenience

    def attach(self, obs: Observer):
        self.observers.append(obs)

    def notify(self):
        for obs in self.observers:
            obs(self)

    def load_words(self, words: List[int], base_addr: int = 0):
        addr = base_addr
        for w in words:
            self.mem.write_word(addr, w)
            addr += WORD

    def fetch(self) -> int:
        instr = self.mem.read_word(self.pc)
        self.stats.bump_instr_fetch()
        return instr

    def step(self):
        if not self.running:
            return
        raw = self.fetch()
        dec = isa.decode(raw)
        if dec.mnemonic == "halt":
            self.running = False
            self.stats.bump_instr("halt")
            self.stats.bump_cycle()
            self.notify()
            return

        next_pc = self.pc + WORD  # PC + 4 by default
        self.execute(dec, lambda new_pc: self._set_next_pc(new_pc, setter=locals()))
        self.stats.bump_instr(dec.mnemonic or "unknown")
        self.stats.bump_cycle()
        self.pc = next_pc
        self.notify()

    def _set_next_pc(self, new_pc: int, setter: dict):
        setter['next_pc'] = new_pc

    def run(self, max_cycles: Optional[int] = None):
        c = 0
        while self.running:
            self.step()
            c += 1
            if max_cycles is not None and c >= max_cycles:
                break

    def execute(self, d: isa.DecodedInstr, set_next_pc):
        r = self.regs
        a = self.alu

        if d.opcode == isa.OP_RTYPE:
            rs, rt, rd = r[d.rs], r[d.rt], d.rd
            if d.funct == isa.FUNCT_ADD:
                res = a.add(rs, rt)
                r[rd] = res
                self.stats.bump_alu("add")
            elif d.funct == isa.FUNCT_SUB:
                res = a.sub(rs, rt)
                r[rd] = res
                self.stats.bump_alu("sub")
            elif d.funct == isa.FUNCT_AND:
                res = a.bitand(rs, rt)
                r[rd] = res
                self.stats.bump_alu("and")
            elif d.funct == isa.FUNCT_OR:
                res = a.bitor(rs, rt)
                r[rd] = res
                self.stats.bump_alu("or")
            elif d.funct == isa.FUNCT_SLT:
                res = a.slt(rs, rt)
                r[rd] = res
                self.stats.bump_alu("slt")
            else:
                raise ValueError(f"Unknown R-type funct {d.funct:#x}")

        elif d.opcode == isa.OP_ADDI:
            # rt <- rs + imm
            val = self.alu.add(self.regs[d.rs], d.imm & 0xFFFFFFFF)
            self.regs[d.rt] = val
            self.stats.bump_alu("add")  # ALU add for addi

        elif d.opcode == isa.OP_LW:
            # rt <- MEM[rs + imm]
            addr = (self.alu.add(self.regs[d.rs], d.imm & 0xFFFFFFFF))  # address calc counts as add
            self.stats.bump_alu("add")
            val = self.mem.read_word(addr)
            self.stats.bump_data_read()
            self.regs[d.rt] = val

        elif d.opcode == isa.OP_SW:
            # MEM[rs + imm] <- rt
            addr = (self.alu.add(self.regs[d.rs], d.imm & 0xFFFFFFFF))
            self.stats.bump_alu("add")
            self.mem.write_word(addr, self.regs[d.rt])
            self.stats.bump_data_write()

        elif d.opcode == isa.OP_BEQ:
            # if rs == rt: PC <- PC+4 + (imm<<2)
            # We'll implement as (rs - rt) == 0 via ALU sub (counts as arithmetic op)
            diff = self.alu.sub(self.regs[d.rs], self.regs[d.rt])
            self.stats.bump_alu("sub")  # beq compare uses sub
            if diff == 0:
                offset = d.imm << 2
                set_next_pc(self.pc + 4 + offset)

        elif d.opcode == isa.OP_J:
            # jump: target = (PC+4)[31:28] | (addr << 2)
            target = ((self.pc + 4) & 0xF0000000) | (d.addr << 2)
            set_next_pc(target)

        else:
            raise ValueError(f"Unknown opcode {d.opcode:#x} ({d.mnemonic})")

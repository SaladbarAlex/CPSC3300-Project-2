from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class Stats:
    cycles: int = 0
    instr_reads: int = 0          # instruction fetches
    data_reads: int = 0
    data_writes: int = 0
    alu_ops: dict = field(default_factory=lambda: defaultdict(int))  # e.g., {"add": 3, "sub": 1, "cmp": 2}
    instr_counts: dict = field(default_factory=lambda: defaultdict(int))

    def bump_cycle(self):
        self.cycles += 1

    def bump_instr_fetch(self):
        self.instr_reads += 1

    def bump_data_read(self):
        self.data_reads += 1

    def bump_data_write(self):
        self.data_writes += 1

    def bump_alu(self, op_name: str):
        self.alu_ops[op_name] += 1

    def bump_instr(self, mnemonic: str):
        self.instr_counts[mnemonic] += 1

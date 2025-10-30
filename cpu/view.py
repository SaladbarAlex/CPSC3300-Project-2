from . import isa

class TextView:
    def __init__(self, mem_dump_words: int = 32, show_all_mem: bool = False):
        self.mem_dump_words = mem_dump_words
        self.show_all_mem = show_all_mem
        self.prev_mem = {}

    def __call__(self, model):
        self.render(model)

    def _dump_registers(self, regs):
        rows = []
        names = isa.REG_NAMES
        for i in range(0, 32, 4):
            row = []
            for j in range(4):
                idx = i + j
                row.append(f"{names.get(idx, f'$r{idx}'):<5}={regs[idx]:>#10x}")
            rows.append("  ".join(row))
        return "\n".join(rows)

    def _dump_memory(self, mem):
        # Show the first mem_dump_words words and any words written since last cycle
        words = []
        for addr in range(0, self.mem_dump_words * 4, 4):
            w = mem.read_word(addr)
            words.append((addr, w))

        # Find modified words (if any); for safety in unified memory, pack small window
        # (We don't track writes history here; just show the first block.)
        lines = [f"{addr:08x}: {val:08x}" for addr, val in words]
        return "\n".join(lines)

    def render(self, model):
        print("="*78)
        print(f"Cycle {model.stats.cycles:>6} | PC=0x{model.pc:08X} | Running={model.running}")
        print("-"*78)
        print("Registers:")
        print(self._dump_registers(model.regs))
        print("-"*78)
        print("Memory [0 .. {limit}):".format(limit=self.mem_dump_words*4))
        try:
            print(self._dump_memory(model.mem))
        except Exception as e:
            print(f"<memory view error: {e}>")
        print("-"*78)
        print("Stats:")
        alu = ", ".join([f"{k}:{v}" for k,v in sorted(model.stats.alu_ops.items())]) or "(none)"
        ic  = ", ".join([f"{k}:{v}" for k,v in sorted(model.stats.instr_counts.items())]) or "(none)"
        print(f"  cycles={model.stats.cycles}  instr_fetches={model.stats.instr_reads}  "
              f"data_reads={model.stats.data_reads}  data_writes={model.stats.data_writes}")
        print(f"  alu_ops={{ {alu} }}")
        print(f"  instr_counts={{ {ic} }}")
        print("="*78)

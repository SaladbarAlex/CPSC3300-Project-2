import sys
import argparse
from typing import List
from .model import CPUModel
from .view import TextView
from .controller import RunController
from .assembler import assemble

def load_bin_words(path: str) -> List[int]:
    """Read hex/decimal words from a text file into a list of ints."""
    words = []
    with open(path, 'r') as f:
        for line in f:
            s = line.strip()
            if not s: 
                continue
            if '#' in s:
                s = s[:s.index('#')].strip()
            if not s:
                continue
            if s.lower().startswith("0x"):
                w = int(s, 16)
            else:
                w = int(s, 16) if all(c in "0123456789abcdefABCDEFx" for c in s) else int(s)
            words.append(w & 0xFFFFFFFF)
    return words

def main():
    """Entry point that assembles or runs programs under the CPU model."""
    p = argparse.ArgumentParser(description="CPSC3300 CPU Simulator (MVC + Observer, single-cycle MIPS-like)")
    p.add_argument("program", help="Path to .bin (hex words per line) or .asm (mini-assembler)")
    p.add_argument("--step", action="store_true", help="Enable interactive single-step mode")
    p.add_argument("--max-cycles", type=int, default=None, help="Optional cycle cap")
    p.add_argument("--assemble", action="store_true", help="Treat input as .asm and assemble to .bin output")
    p.add_argument("--out", type=str, default=None, help="Output .bin when using --assemble")
    p.add_argument("--mem-bytes", type=int, default=64*1024, help="Total memory bytes")
    args = p.parse_args()

    if args.assemble:
        if not args.program.lower().endswith(".asm"):
            print("ERROR: --assemble expects an .asm file input", file=sys.stderr)
            sys.exit(2)
        with open(args.program, "r") as f:
            words = assemble(f.readlines())
        out = args.out or (args.program.rsplit('.',1)[0] + ".bin")
        with open(out, "w") as g:
            for w in words:
                g.write(f"0x{w:08X}\n")
        print(f"Wrote {out} ({len(words)} words).")
        return

    # Normal simulation
    model = CPUModel()
    model.mem.size_bytes = args.mem_bytes
    model.mem.data = bytearray(args.mem_bytes)

    # Load program
    if args.program.lower().endswith(".asm"):
        with open(args.program, "r") as f:
            words = assemble(f.readlines())
    else:
        words = load_bin_words(args.program)
    model.load_words(words, base_addr=0)

    # Attach view + controller
    view = TextView(mem_dump_words=32)
    ctl = RunController(model, view, step_mode=args.step)

    ctl.run_all(max_cycles=args.max_cycles)

if __name__ == "__main__":
    main()

# CPSC3300 Project 2 — Single-Cycle CPU Simulator

## Project summary
This submission implements the Project 2 requirements for a single-cycle, MIPS-style CPU written in Python. The simulator executes one full instruction per cycle, prints a scoreboard every cycle, and records detailed performance counters.

## How to run the simulator
```bash
# Default run of the provided sample program
make run BIN=programs/sample.bin

# Interactive single-step mode (press Enter per cycle, q to quit)
make step BIN=programs/sample.bin
```
Both targets invoke `python -m cpu.main` under the hood. Passing `--max-cycles=N` is useful when testing potentially infinite loops.

## Program formats
1. **Binary (`.bin`) programs**: one 32-bit word per line written in hexadecimal (e.g., `0x2010002A`). Comments after `#` are ignored.
2. **Assembly (`.asm`) programs**: a compact assembly syntax supported by the included mini-assembler. Convert to `.bin` via
   ```bash
   python -m cpu.main programs/sample.asm --assemble --out programs/sample.bin
   ```
   The assembler understands labels, register aliases (e.g., `$t0`), and the instruction subset listed below.

## Architecture overview (MVC + Observer in plain terms)
- **Model (`CPUModel` in `cpu/model.py`)**
  - Owns the register file, ALU, unified memory, program counter, and statistics tracker.
  - Provides `step()`/`run()` to fetch, decode, and execute instructions.
  - After each cycle, it notifies any observers that state has changed.
- **View (`TextView` in `cpu/view.py`)**
  - Subscribes to the model as an observer.
  - Renders a scoreboard each cycle: PC, register file, a small memory window, and the stats block.
- **Controller (`RunController` in `cpu/controller.py`)**
  - Wires the model to the view and decides whether to run continuously or in interactive step mode.

**Observer pattern refresher:** the model keeps a list of callbacks (observers). After each cycle it calls them, so the view updates automatically.

## Instruction set and semantics
| Type | Instruction | Behavior summary |
|------|-------------|------------------|
| R-type | `add`, `sub`, `and`, `or`, `slt` | Standard register-register ALU ops; `$zero` remains immutable. |
| I-type | `addi`, `lw`, `sw`, `beq` | Add immediate, load/store word using base+offset, branch if registers match. |
| J-type | `j` | Jump within the current 256 MB region (MIPS-style). |
| Special | `halt` | Encoded as `0xFFFFFFFF`; stops the simulation cleanly. |

Design choices worth noting:
- All immediates are sign-extended. Branch offsets follow the PC+4 convention and are word-based.
- Memory is unified (instructions + data) and byte addressable. Loads/stores must be word aligned; misaligned or out-of-bounds access raises `MemoryError` to expose bugs quickly.
- `addi` was included to keep test programs short and to match later pipeline labs.

## Statistics collected each cycle
- `cycles`: total instructions retired (including `halt`).
- `alu_ops`: per-mnemonic counts of actual ALU work, including implicit adds for address calculations and subtracts for `beq` comparisons.
- `instr_reads`, `data_reads`, `data_writes`: distinguish instruction fetch traffic from data-side loads/stores.
- `instr_counts`: retired instruction counts keyed by mnemonic.

These counters are surfaced in the view and will also support later cache/pipeline analysis without changing the ISA layer.

## Testing checklist
- Assemble and run `programs/sample.asm` end-to-end; confirm the scoreboard trace matches expectations (e.g., `$t0` increments, memory slot updates, stats show 9 cycles).
- Craft focused `.asm` snippets for corner cases:
  - Negative immediates (`addi` with -1).
  - Taken and not-taken `beq` paths.
  - Misaligned load/store to verify the memory guard rails.
- Maintain golden `.bin` fixtures plus saved stat summaries so regression tests can diff outputs after refactors.

## Future work hooks
- **Cache insertion**: swap `CPUModel.mem` for a proxy that first checks a simulated cache before hitting main memory, while recording hit/miss counts in `Stats`.
- **Pipeline**: refactor `CPUModel.step()` into IF/ID/EX/MEM/WB stage helpers with pipeline registers and simple hazard detection/forwarding. The observer interface already enables a stage-by-stage view.

## Design Notes 
- Team:
  - Alex Salazar
  - Joseph Pugmire 
- Deviations from spec and why:
  - Added `addi` (opcode `0x08`) even though the base COD 4.4 subset only required R-type, `lw/sw`, `beq`, and `j`; it keeps sample/test programs short by avoiding multi-instruction immediates.
  - `make run` accepts `--max-cycles` and the controller enforces bounds/misalignment checks (`cpu/model.py:33` onward). The spec only required graceful halting, but the guard prevents runaway loops and surfaces memory bugs immediately.
  - Stats go beyond the minimum counters by splitting instruction fetches vs. data traffic and counting hidden ALU work (address calc + branch compare). That extra detail is needed for the cache/pipeline work that follows in Project 3.
- Testing strategy:
  - Smoke-test the full stack by assembling `programs/sample.asm` and running `make run BIN=programs/sample.bin` (and `make step ...`) to ensure the scoreboard, stats, and HALT handling agree with the hand-traced execution.
  - Build tiny `.asm` snippets per instruction (e.g., negative immediates for `addi`, fall-through/ taken `beq`, misaligned `lw/sw`) and compare the register/memory dumps against expected traces; this also validates that `Memory` raises on misaligned or OOB addresses.
  - For regression coverage, keep golden `.bin` fixtures plus expected stat summaries and diff the `TextView` output, so ISA or stats refactors can be checked automatically.
- Cache insertion plan:
  - Wrap `Memory` behind a thin interface (same `read_word/write_word`) and add a `CacheMemory` proxy that first probes a configurable direct-mapped/LRU structure before falling back to main memory.
  - Count hits/misses inside the proxy and expose them through `Stats` (new fields) so the view can print cache metrics without touching controllers.
  - Because controllers already talk only to `CPUModel.mem`, swapping `CPUModel.mem = CacheMemory(base=Memory(...))` keeps the ISA and view untouched; only the constructor path in `cpu/main.py` needs a flag to opt into the cache.
- Pipeline plan:
  - Refactor `CPUModel.step()` into explicit IF/ID/EX/MEM/WB stage functions with pipeline-register dataclasses so each stage can run every tick while sharing the existing `Stats` bookkeeping.
  - Introduce a simple hazard unit (forwarding paths plus stall logic) inside the model; control hazards start with one-cycle flushes on taken branches/jumps, then can be optimized via predict-not-taken.
  - Extend `TextView` to show which instruction occupies each stage per cycle (leveraging the observer callbacks) so we can visually debug bubbles/flushes before automating checks.

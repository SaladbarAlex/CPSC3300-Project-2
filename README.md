# CPSC3300 Project 2 — Single-Cycle MVC MIPS CPU Simulator
## Design Notes 
- Team:
  - Alex Salazar
  - Joseph Pugmire 

## Project summary
This submission implements the Project 2 requirements for a single-cycle, MIPS-style CPU written in Python. The simulator executes one full instruction per cycle, prints a scoreboard every cycle.

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

## Testing checklist
- Assemble and run `programs/sample.asm`; confirm the scoreboard trace matches expectations (e.g., `$t0` increments, memory slot updates, stats show 9 cycles).
- Craft focused `.asm` snippets for corner cases:
  - Negative immediates (`addi` with -1).
  - Taken and not-taken `beq` paths.
  - Misaligned load/store to verify the memory guard rails.

## Future work hooks
- **Cache insertion**: swap `CPUModel.mem` for a proxy that first checks a simulated cache before hitting main memory, while recording hit/miss counts in `Stats`.
- **Pipeline**: refactor `CPUModel.step()` into IF/ID/EX/MEM/WB stage helpers with pipeline registers and simple hazard detection/forwarding. The observer interface already enables a stage-by-stage view.

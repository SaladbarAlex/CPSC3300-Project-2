# CPSC3300 Project 2 — Single-Cycle CPU Simulator (MVC + Observer)

This repository provides a **reference-quality starter** that follows **MVC** and uses the **Observer** pattern for a text scoreboard that updates **every cycle**.

It implements a classic single-cycle MIPS-like subset (COD 4.4 style) plus **`addi`**:
- R-type: `add, sub, and, or, slt`
- I-type: `lw, sw, beq, addi`
- J-type: `j` (optional but included)
- Special: `halt` (0xFFFFFFFF) to terminate

> Memory is unified for both instructions and data (as required). A future cache can be plugged behind the `Memory` class without changing controllers or views.

## Requirements covered
- **MVC architecture** (`cpu/model.py`, `cpu/controller.py`, `cpu/view.py`).
- **Observer pattern** for views (`TextView` subscribes to `CPUModel` and prints scoreboard **each cycle**).
- Tracks:
  - **Total cycles**
  - **ALU arithmetic ops** (counts `add/sub/and/or/slt` plus hidden ALU ops for `beq` compare and `lw/sw` address calc; **PC increment not counted**)
  - **Memory ops** (separate counts for **instruction fetch** and **data** reads/writes)
  - **Per-instruction counts**
- **Makefile** with `all`, `clean`, `run`, `step`.
- Command form: `./<program> myprog.bin` → `python -m cpu.main programs/sample.bin`

## Quick start

```bash
# Run the sample program (adds 42 to $t0, stores, loads, branches, jumps, halts)
make run BIN=programs/sample.bin

# Single-step mode (press Enter each cycle; or 'q' to quit)
make step BIN=programs/sample.bin
```

You should see a per-cycle scoreboard (PC, registers, memory window, stats).

## File formats

- **Binary program (`.bin`)**: Text file, one 32-bit word per line in **hex** (e.g., `0x2010002A`). Comments allowed after `#`.
- Optionally, you can assemble **simple assembly** with the included mini-assembler:

```bash
python -m cpu.main programs/sample.asm --assemble --out programs/sample.bin
make run BIN=programs/sample.bin
```

## Design overview

### MVC + Observer
- **Model** (`CPUModel`): Owns **RegisterFile**, **ALU**, **ControlUnit**, **Memory**, and **Stats**. Executes one full instruction per *cycle*, notifies observers.
- **View** (`TextView`): Subscribes to model; prints a **scoreboard each cycle**, including PC, register file, a compact memory dump, and live stats.
- **Controller** (`RunController`): Provides `run_all()` and `step_once()`; CLI exposes `--step` for single-step execution.

### Memory
- Single unified byte-addressable memory with word helpers.
- Clean seam for future cache: replace `Memory` with a proxy that forwards to a backing store, counting hits/misses.

### ISA (MIPS-like)
- R-type (opcode=0): `funct` selects operation (add=0x20, sub=0x22, and=0x24, or=0x25, slt=0x2A).
- I-type: `lw=0x23`, `sw=0x2B`, `beq=0x04`, `addi=0x08`.
- J-type: `j=0x02`.
- Special HALT: `0xFFFFFFFF`.
- Branch offsets are **word offsets relative to PC+4** (standard MIPS semantics). Immediates sign-extended.

### Stats
- `cycles`
- `alu_ops` (by mnemonic)
- `mem`:
  - `instr_reads`
  - `data_reads`
  - `data_writes`
- `instr_counts` by mnemonic

### Extending
- Add new instructions in `isa.py` (decode/execute hooks).
- Add GUI by publishing model updates to a GUI view (bonus).
- Add pipeline by composing stages and duplicating memories (bonus). Ensure the view prints stage-resident instructions each cycle.


## Design Notes 
- Team:
  - Alex Salazar
  - Joseph Pugmire 
- Deviations from spec and why:
- Testing strategy:
- Cache insertion plan:
- Pipeline plan:

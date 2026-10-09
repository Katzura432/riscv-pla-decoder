# Design notes and interview discussion

## What makes this a PLA

Each product term compares only the instruction bits marked by its mask:
`(instruction & mask) == match`. Unmasked bits are don't-cares. This represents
an AND of selected true/complemented inputs. Each control output is the OR of
the product terms asserting that output. FPGA LUTs implement these Boolean
functions; the FPGA's physical LUT fabric is not replaced by a physical PLA.

The exact variant assigns one product to each instruction. The shared variant
combines adjacent cubes for each control bit, then deduplicates products across
control outputs. A combination is permitted only when two equal masks differ
in exactly one constrained bit. Removing that constraint produces precisely
their union, so it introduces no new encodings. M-extension products retain
their separate enable condition throughout minimization.

The compiler rejects overlapping instruction encodings. In an unambiguous
decode table, bitwise OR of control constants has the same meaning as selecting
the matched instruction. The direct case decoder provides an independently
structured implementation comparison, while the handwritten Python oracle
provides an independent encoding/control check.

## Performance tradeoffs

- Parallel lanes scale decode throughput, but dependencies require triangular
  register comparisons. This grows quadratically in lane count.
- Immediate assembly, legality gating, and register-use gating are shared
  datapath concepts across architectures. Comparing only opcode matches would
  omit meaningful frontend work.
- Exact PLA decoding has broad fanout into control OR planes. Per-output cube
  merging can shorten equations but also introduce more distinct products.
- A case decoder may become equivalent logic after synthesis. Source-code
  structure and product counts do not establish a hardware advantage.
- The benchmark isolates registered internal paths. The measured design is
  constrained at 100 MHz, not tuned to demonstrate maximum possible frequency.

## Integration contract

The fetch stage supplies fixed-width 32-bit instructions in program order.
Lane-valid bits may contain holes. Each instruction's PC and any fetch fault
must travel through corresponding companion pipeline registers in a real CPU;
this project does not supply PC storage or instruction-address fault handling.
AUIPC, jumps, and branches use that PC downstream. JALR target-bit clearing,
branch comparisons, arithmetic, memory access, privilege transitions, and
execution exceptions are downstream responsibilities.

`writes_rd` excludes x0, but a load into x0 remains a LOAD operation and must
still perform the memory access and raise execution faults when appropriate.
Likewise, other instructions targeting x0 remain legal.

RAW and WAW outputs are dependency metadata, not a complete issue scheduler.
An out-of-order pipeline would additionally need renaming, readiness tracking,
precise exception machinery, and control-flow recovery. For multiple older
writers to the same source register, choose the youngest matching producer.

FENCE provides serialization metadata and retains fm/pred/succ. Reserved
fm encodings may conservatively execute as a full fence in an RV32I core.
Unrecognized extensions are intentionally illegal in this project's contract.
RISC-V leaves some reserved-encoding behavior to the platform, so this is a
defined decoder policy rather than a universal assertion about every platform.

## Verification boundaries

Structural sweeps cover all 131,072 opcode/funct3/funct7 combinations with one
representative operand pattern. Remaining operands are exercised by immediate,
register, directed-system, and randomized tests. Complete records are compared,
including side-effect suppression for illegal/invalid lanes.

The elastic stage is checked with a cycle scoreboard that models its single
storage slot. Every cycle verifies output contents and ready behavior, covering
stalls, concurrent replacement, bubbles, reset, and flush.

Simulation is not exhaustive formal equivalence. Neither functional simulation
nor routed FPGA reports establish physical board operation or ASIC results.

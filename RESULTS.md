# Verification and routed FPGA results

Decoder: `{"status": "PASS", "oracle_vectors": 244040, "bundles": 61010, "widths": [1, 2, 4], "architectures": 3, "extension_modes": 2}`

Pipeline: `{"status": "PASS", "cycles": 4000, "accepted": 2256, "stalls": 1108, "flushes": 57}`

Target: Alveo U50 xcu50-fsvh2104-2-e, RV32I, 10 ns clock; identical registered boundaries.
Routed out-of-context results include dependency logic; no board measurements.
Clock source/skew is idealized (HD.CLK_SRC unset); external IO routing is excluded.

| Lanes | Decoder | LUTs | Flip-flops | Worst slack (ns) | Critical datapath (ns) |
| --- | --- | --- | --- | --- | --- |
| 1 | Direct RTL | 197 | 120 | 7.485 | 2.397 |
| 1 | Exact PLA | 194 | 120 | 7.449 | 2.532 |
| 1 | Shared PLA | 192 | 120 | 7.652 | 2.229 |
| 2 | Direct RTL | 467 | 243 | 7.134 | 2.845 |
| 2 | Exact PLA | 390 | 243 | 6.762 | 3.121 |
| 2 | Shared PLA | 433 | 243 | 6.746 | 3.235 |
| 4 | Direct RTL | 706 | 498 | 6.678 | 3.205 |
| 4 | Exact PLA | 839 | 498 | 6.705 | 3.178 |
| 4 | Shared PLA | 723 | 498 | 6.569 | 3.413 |

Completed 9 of 9 configurations.
Positive slack meets the specified 100 MHz constraint under the OOC clock model.
Datapath delay alone is not measured Fmax. RTL term counts are not FPGA LUT counts.

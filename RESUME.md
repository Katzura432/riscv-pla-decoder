# Resume wording

Project title: **Superscalar RISC-V Instruction Decoder with Generated PLA Logic**

- Designed a four-lane RV32I instruction decoder in SystemVerilog with optional
  RV32M decoding, generated PLA control logic, RAW/WAW dependency detection,
  and a stallable ready/valid pipeline with flush support.
- Verified complete decode records against an independent software model using
  244,040 test vectors across three architectures and widths 1/2/4; checked
  pipeline reset, stalls, replacement, and flush over 4,000 simulated cycles.
- Compared direct RTL, exact PLA, and shared-product PLA implementations using
  nine routed out-of-context Vivado designs on an Alveo U50 target; the four-lane
  shared PLA used 615 CLB LUTs (723 LUT primitive cells) and 498 flip-flops with a 3.413 ns critical datapath
  in RV32I mode. Documented area/timing tradeoffs across architectures and widths.

For a shorter resume, combine the first two bullets and include one measured
four-lane result. Describe M support as instruction decoding, not an implemented
multiplier/divider. Describe timing as FPGA block timing under the documented
OOC clock model, not measured board Fmax.

## Be prepared to explain

1. How instruction masks become PLA product terms and why overlaps are rejected.
2. Why control-bit cube merging is functionally safe but not globally minimal.
3. Why an instruction writing x0 can still have memory or exception side effects.
4. How B/J immediates are assembled and sign-extended.
5. Why every older matching writer is flagged, and why forwarding selects the
   youngest older producer.
6. How a one-entry pipeline simultaneously consumes and replaces a bundle.
7. Why FPGA synthesis can make different RTL descriptions converge to similar
   logic, and why one placement run is not a universal performance guarantee.
8. Which CPU components remain downstream: execution, PC context, renaming,
   issue scheduling, branch recovery, memory, and architectural traps.

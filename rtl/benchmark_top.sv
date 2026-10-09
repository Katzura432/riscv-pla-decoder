// Identical registered boundaries for every architecture/width comparison.
module benchmark_top #(
  parameter int WIDTH = 4, IMPL = 2,
  parameter bit ENABLE_M = 0
) (
  input logic clk,
  input logic [WIDTH*32-1:0] instructions,
  input logic [WIDTH-1:0] lane_valid,
  output logic [WIDTH*decode_pkg::DECODE_W-1:0] decoded,
  output logic [WIDTH*WIDTH-1:0] raw_rs1, raw_rs2, waw
);
  logic [WIDTH*32-1:0] insn_q;
  logic [WIDTH-1:0] valid_q;
  logic [WIDTH*decode_pkg::DECODE_W-1:0] next_decoded;
  logic [WIDTH*WIDTH-1:0] next_rs1, next_rs2, next_waw;
  superscalar_decoder #(.WIDTH(WIDTH), .IMPL(IMPL), .ENABLE_M(ENABLE_M)) u
    (insn_q, valid_q, next_decoded, next_rs1, next_rs2, next_waw);
  always_ff @(posedge clk) begin
    insn_q <= instructions; valid_q <= lane_valid;
    decoded <= next_decoded;
    raw_rs1 <= next_rs1; raw_rs2 <= next_rs2; waw <= next_waw;
  end
endmodule

// One-entry elastic bundle register; flush discards pending and incoming work.
module decode_pipeline #(
  parameter int WIDTH = 4, IMPL = 2,
  parameter bit ENABLE_M = 0
) (
  input logic clk, reset, flush,
  input logic in_valid,
  output logic in_ready,
  input logic [WIDTH*32-1:0] instructions,
  input logic [WIDTH-1:0] lane_valid,
  output logic out_valid,
  input logic out_ready,
  output logic [WIDTH*decode_pkg::DECODE_W-1:0] decoded,
  output logic [WIDTH*WIDTH-1:0] raw_rs1, raw_rs2, waw
);
  logic [WIDTH*decode_pkg::DECODE_W-1:0] next_decoded;
  logic [WIDTH*WIDTH-1:0] next_rs1, next_rs2, next_waw;
  superscalar_decoder #(.WIDTH(WIDTH), .IMPL(IMPL), .ENABLE_M(ENABLE_M)) u
    (instructions, lane_valid, next_decoded, next_rs1, next_rs2, next_waw);
  assign in_ready = !reset && !flush && (!out_valid || out_ready);
  always_ff @(posedge clk) begin
    if (reset || flush) begin
      out_valid <= 0;
      decoded <= '0; raw_rs1 <= '0; raw_rs2 <= '0; waw <= '0;
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid) begin
        decoded <= next_decoded;
        raw_rs1 <= next_rs1; raw_rs2 <= next_rs2; waw <= next_waw;
      end else begin
        decoded <= '0; raw_rs1 <= '0; raw_rs2 <= '0; waw <= '0;
      end
    end
  end
endmodule

// Combinational, independently valid decode lanes. Lane 0 is oldest.
module superscalar_decoder #(
  parameter int WIDTH = 4,
  parameter int IMPL = 2, // 0: direct case, 1: exact PLA, 2: shared PLA
  parameter bit ENABLE_M = 0
) (
  input logic [WIDTH*32-1:0] instructions,
  input logic [WIDTH-1:0] lane_valid,
  output logic [WIDTH*decode_pkg::DECODE_W-1:0] decoded,
  output logic [WIDTH*WIDTH-1:0] raw_rs1, raw_rs2, waw
);
  import decode_pkg::*;
  decode_t lanes [WIDTH];
  for (genvar i = 0; i < WIDTH; i++) begin : lane
    ctrl_t ctrl;
    if (IMPL == 0) begin : direct
      control_direct #(.ENABLE_M(ENABLE_M)) u (instructions[i*32+:32], ctrl);
    end else if (IMPL == 1) begin : pla
      control_pla #(.ENABLE_M(ENABLE_M)) u (instructions[i*32+:32], ctrl);
    end else begin : shared
      control_shared #(.ENABLE_M(ENABLE_M)) u (instructions[i*32+:32], ctrl);
    end
    always_comb lanes[i] = payload(instructions[i*32+:32], lane_valid[i], ctrl);
    assign decoded[i*DECODE_W+:DECODE_W] = lanes[i];
  end
  // Bit younger*WIDTH+older records every in-bundle dependency.
  // A future rename/forwarding stage must select the youngest matching writer.
  always_comb begin
    raw_rs1 = '0; raw_rs2 = '0; waw = '0;
    for (int younger = 0; younger < WIDTH; younger++) begin
      for (int older = 0; older < younger; older++) begin
        if (lanes[younger].valid && !lanes[younger].illegal &&
            lanes[older].valid && !lanes[older].illegal &&
            lanes[older].ctrl.writes_rd) begin
          raw_rs1[younger*WIDTH+older] = lanes[younger].ctrl.uses_rs1 &&
            lanes[younger].rs1 == lanes[older].rd;
          raw_rs2[younger*WIDTH+older] = lanes[younger].ctrl.uses_rs2 &&
            lanes[younger].rs2 == lanes[older].rd;
          waw[younger*WIDTH+older] = lanes[younger].ctrl.writes_rd &&
            lanes[younger].rd == lanes[older].rd;
        end
      end
    end
  end
endmodule

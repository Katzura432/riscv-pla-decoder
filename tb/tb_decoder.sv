`timescale 1ns/1ps
module tb_decoder;
  import decode_pkg::*;
  logic [127:0] instructions;
  logic [3:0] lane_valid;
  wire [4*DECODE_W-1:0] outputs [3][6];
  wire [15:0] rs1_matrix [3][6], rs2_matrix [3][6], waw_matrix [3][6];
  decode_t golden_i [4], golden_m [4];
  integer fd, scan, rows, bundles, summary;
  integer valid_word;
  logic [31:0] word;
  logic [DECODE_W-1:0] expected_i, expected_m;
  logic [15:0] e1,e2,ew;
  decode_t older_d,younger_d;
  string vector_path;

  for (genvar w=0;w<3;w++) begin : width_test
    localparam int W=1<<w;
    for (genvar k=0;k<6;k++) begin : variant
      wire [W*DECODE_W-1:0] result;
      wire [W*W-1:0] r1,r2,ww;
      superscalar_decoder #(.WIDTH(W),.IMPL(k%3),.ENABLE_M(k>=3)) dut
        (instructions[W*32-1:0],lane_valid[W-1:0],result,r1,r2,ww);
      assign outputs[w][k] = {{(4-W)*DECODE_W{1'b0}},result};
      assign rs1_matrix[w][k] = {{16-W*W{1'b0}},r1};
      assign rs2_matrix[w][k] = {{16-W*W{1'b0}},r2};
      assign waw_matrix[w][k] = {{16-W*W{1'b0}},ww};
    end
  end

  initial begin
    if (DECODE_W != 89 || CTRL_W != 28) $fatal(1,"Oracle packing needs updating");
    if (!$value$plusargs("VECTORS=%s",vector_path)) vector_path="../vectors.txt";
    fd=$fopen(vector_path,"r");
    if (!fd) $fatal(1,"Cannot open oracle vectors");
    rows=0; bundles=0;
    while (!$feof(fd)) begin
      for (int lane=0;lane<4;lane++) begin
        scan=$fscanf(fd,"%h %h %h %h\n",valid_word,word,expected_i,expected_m);
        if (scan!=4) $fatal(1,"Truncated vector file at row %0d",rows);
        instructions[lane*32+:32]=word;
        lane_valid[lane]=valid_word[0];
        golden_i[lane]=expected_i; golden_m[lane]=expected_m;
        rows++;
      end
      #1;
      for (int w=0;w<3;w++) begin
        for (int k=0;k<6;k++) begin
          e1=0;e2=0;ew=0;
          for (int lane=0;lane<(1<<w);lane++) begin
            younger_d=(k>=3)?golden_m[lane]:golden_i[lane];
            if (outputs[w][k][lane*DECODE_W+:DECODE_W] !== younger_d)
              $fatal(1,"Decode mismatch row=%0d width=%0d variant=%0d lane=%0d insn=%h actual=%h expected=%h",
                rows-4+lane,1<<w,k,lane,instructions[lane*32+:32],outputs[w][k][lane*DECODE_W+:DECODE_W],younger_d);
            for (int old=0;old<lane;old++) begin
              older_d=(k>=3)?golden_m[old]:golden_i[old];
              if (younger_d.valid && !younger_d.illegal && older_d.valid && !older_d.illegal && older_d.ctrl.writes_rd) begin
                e1[lane*(1<<w)+old]=younger_d.ctrl.uses_rs1 && younger_d.rs1==older_d.rd;
                e2[lane*(1<<w)+old]=younger_d.ctrl.uses_rs2 && younger_d.rs2==older_d.rd;
                ew[lane*(1<<w)+old]=younger_d.ctrl.writes_rd && younger_d.rd==older_d.rd;
              end
            end
          end
          if (rs1_matrix[w][k]!==e1 || rs2_matrix[w][k]!==e2 || waw_matrix[w][k]!==ew)
            $fatal(1,"Dependency mismatch bundle=%0d width=%0d variant=%0d",bundles,1<<w,k);
        end
      end
      bundles++;
    end
    $fclose(fd);
    summary=$fopen("../decode_simulation.json","w");
    $fdisplay(summary,"{\"status\":\"PASS\",\"oracle_vectors\":%0d,\"bundles\":%0d,\"widths\":[1,2,4],\"architectures\":3,\"extension_modes\":2}",rows,bundles);
    $fclose(summary);
    $display("PASS: %0d oracle vectors; widths 1/2/4, all 3 architectures, RV32I and RV32IM, dependency matrices",rows);
    $finish;
  end
endmodule

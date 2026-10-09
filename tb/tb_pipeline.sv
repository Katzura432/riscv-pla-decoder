`timescale 1ns/1ps
module tb_pipeline;
  import decode_pkg::*;
  logic clk=0;
  always #5 clk=~clk;
  logic reset,flush,in_valid,in_ready,out_valid,out_ready;
  logic [127:0] instructions;
  logic [3:0] lane_valid;
  wire [4*DECODE_W-1:0] result,comb;
  wire [15:0] r1,r2,ww,c1,c2,cw;
  logic expected_valid=0;
  logic [4*DECODE_W-1:0] expected_data='0;
  logic [15:0] expected_r1=0,expected_r2=0,expected_waw=0;
  logic [31:0] rng=32'h1234abcd;
  integer accepted=0,stalls=0,flushes=0,summary;
  function automatic logic [31:0] random_word();
    rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);
    return rng;
  endfunction
  decode_pipeline #(.ENABLE_M(1)) dut
    (clk,reset,flush,in_valid,in_ready,instructions,lane_valid,out_valid,out_ready,result,r1,r2,ww);
  superscalar_decoder #(.ENABLE_M(1)) reference_comb
    (instructions,lane_valid,comb,c1,c2,cw);
  initial begin
    reset=1;flush=0;in_valid=0;out_ready=0;instructions=0;lane_valid=0;
    @(posedge clk); #1;
    if(out_valid!==0 || result!==0) $fatal(1,"Reset failed");
    for(int cycle=0;cycle<4000;cycle++) begin
      @(negedge clk);
      reset=(cycle%257==0);flush=(cycle%71==0);
      in_valid=(random_word()%5!=0);out_ready=(random_word()%3!=0);
      lane_valid=random_word();
      for(int lane=0;lane<4;lane++) instructions[lane*32+:32]=random_word();
      #1;
      if(in_ready !== (!reset && !flush && (!expected_valid || out_ready)))
        $fatal(1,"Ready mismatch cycle %0d",cycle);
      if(reset || flush) begin
        expected_valid=0;expected_data=0;expected_r1=0;expected_r2=0;expected_waw=0;
        if(flush) flushes++;
      end else if(in_ready) begin
        expected_valid=in_valid;
        expected_data=in_valid?comb:'0;
        expected_r1=in_valid?c1:'0;expected_r2=in_valid?c2:'0;expected_waw=in_valid?cw:'0;
        if(in_valid) accepted++;
      end else stalls++;
      @(posedge clk);#1;
      if(out_valid!==expected_valid || result!==expected_data || r1!==expected_r1 || r2!==expected_r2 || ww!==expected_waw)
        $fatal(1,"Pipeline scoreboard mismatch cycle %0d",cycle);
    end
    if(accepted<100 || stalls<100 || flushes<10) $fatal(1,"Insufficient handshake coverage");
    summary=$fopen("../pipeline_simulation.json","w");
    $fdisplay(summary,"{\"status\":\"PASS\",\"cycles\":4000,\"accepted\":%0d,\"stalls\":%0d,\"flushes\":%0d}",accepted,stalls,flushes);
    $fclose(summary);
    $display("PASS: pipeline 4000 cycles, %0d accepted, %0d stalled, %0d flushes",accepted,stalls,flushes);
    $finish;
  end
endmodule

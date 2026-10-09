# Run from build/sim after scripts/verify.ps1 has built tb_pipeline.
open_vcd ../pipeline_waveform.vcd
log_vcd /tb_pipeline/clk
log_vcd /tb_pipeline/reset
log_vcd /tb_pipeline/flush
log_vcd /tb_pipeline/in_valid
log_vcd /tb_pipeline/in_ready
log_vcd /tb_pipeline/out_valid
log_vcd /tb_pipeline/out_ready
run all
close_vcd
quit

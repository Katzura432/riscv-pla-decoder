create_clock -name decode_clk -period 10.0 [get_ports clk]
set_false_path -from [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_false_path -to [get_ports -filter {DIRECTION == OUT}]

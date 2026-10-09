# Usage: vivado -mode batch -source scripts/synthesize.tcl -tclargs [part] [width|all] [impl|all]
set root [file normalize [file join [file dirname [info script]] ..]]
set part xcu50-fsvh2104-2-e
if {[llength $argv] > 0} { set part [lindex $argv 0] }
set widths {1 2 4}
set variants {0 1 2}
if {[llength $argv] > 1 && [lindex $argv 1] ne "all"} { set widths [list [lindex $argv 1]] }
if {[llength $argv] > 2 && [lindex $argv 2] ne "all"} { set variants [list [lindex $argv 2]] }
set reportdir [file join $root build synthesis]
file mkdir $reportdir
foreach width $widths {
  foreach impl $variants {
    create_project -in_memory -part $part
    set_property target_language Verilog [current_project]
    foreach source {rtl/generated/decode_pkg.sv rtl/generated/control_direct.sv rtl/generated/control_pla.sv rtl/generated/control_shared.sv rtl/superscalar_decoder.sv rtl/benchmark_top.sv} {
      read_verilog -sv [file join $root $source]
    }
    synth_design -top benchmark_top -part $part -mode out_of_context -flatten_hierarchy rebuilt \
      -generic "WIDTH=$width IMPL=$impl ENABLE_M=0"
    create_clock -name decode_clk -period 10.0 [get_ports clk]
    # Registered IO boundary: only internal register-to-register paths measured.
    set_false_path -from [get_ports -filter {DIRECTION == IN && NAME != clk}]
    set_false_path -to [get_ports -filter {DIRECTION == OUT}]
    opt_design
    place_design
    phys_opt_design
    route_design
    set prefix [file join $reportdir w${width}_impl${impl}]
    report_utilization -file ${prefix}_utilization.rpt
    report_timing_summary -file ${prefix}_timing.rpt
    report_timing -max_paths 10 -file ${prefix}_critical_paths.rpt
    write_checkpoint -force ${prefix}.dcp
    set paths [get_timing_paths -from [all_registers] -to [all_registers] -max_paths 1]
    if {[llength $paths] == 0} { error "No register-to-register timing path" }
    set delay [get_property DATAPATH_DELAY [lindex $paths 0]]
    set slack [get_property SLACK [lindex $paths 0]]
    set lutcount [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]
    set ffcount [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
    set fh [open ${prefix}_metrics.json w]
    puts $fh "{\"part\":\"$part\",\"width\":$width,\"implementation\":$impl,\"enable_m\":false,\"period_ns\":10.0,\"worst_slack_ns\":$slack,\"critical_datapath_ns\":$delay,\"luts\":$lutcount,\"flip_flops\":$ffcount}"
    close $fh
    close_project
  }
}

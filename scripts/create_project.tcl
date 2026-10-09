set root [file normalize [file join [file dirname [info script]] ..]]
set projectdir [file join $root build vivado]
if {[file exists [file join $projectdir pla_decoder.xpr]]} {
  open_project [file join $projectdir pla_decoder.xpr]
} else {
  create_project pla_decoder $projectdir -part xcu50-fsvh2104-2-e
}
foreach source {rtl/generated/decode_pkg.sv rtl/generated/control_direct.sv rtl/generated/control_pla.sv rtl/generated/control_shared.sv rtl/superscalar_decoder.sv rtl/decode_pipeline.sv rtl/benchmark_top.sv} {
  add_files -norecurse [file join $root $source]
}
add_files -fileset sim_1 [file join $root tb tb_decoder.sv]
add_files -fileset sim_1 [file join $root tb tb_pipeline.sv]
set_property top benchmark_top [current_fileset]
set_property top tb_decoder [get_filesets sim_1]
add_files -fileset constrs_1 [file join $root scripts benchmark.xdc]
# For GUI simulation, pass an absolute vector path through a plusarg.
set_property -dict [list xsim.simulate.xsim.more_options "-testplusarg VECTORS=[file join $root build vectors.txt]"] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
close_project

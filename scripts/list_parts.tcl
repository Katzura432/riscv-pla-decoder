set root [file normalize [file join [file dirname [info script]] ..]]
set fh [open [file join $root build installed_parts.txt] w]
foreach part [get_parts] { puts $fh $part }
close $fh

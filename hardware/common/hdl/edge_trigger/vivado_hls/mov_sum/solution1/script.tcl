############################################################
## This file is generated automatically by Vivado HLS.
## Please DO NOT edit it.
## Copyright (C) 1986-2018 Xilinx, Inc. All Rights Reserved.
############################################################
open_project mov_sum
set_top mov_sum
add_files mov_sum.cpp
open_solution "solution1"
set_part {xa7a12tcsg325-1q}
create_clock -period 10 -name default
#source "./mov_sum/solution1/directives.tcl"
#csim_design
csynth_design
#cosim_design
export_design -format ip_catalog

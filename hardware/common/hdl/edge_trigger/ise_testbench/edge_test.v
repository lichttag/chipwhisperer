`timescale 1ns / 1ps

////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer:
//
// Create Date:   19:54:40 03/10/2021
// Design Name:   mov_sum
// Module Name:   /home/thilo/repos/chipwhisperer/hardware/common/hdl/edge_trigger/ise_testbench/mov_sum_new.v
// Project Name:  edge_trigger
// Target Device:  
// Tool versions:  
// Description: 
//
// Verilog Test Fixture created by ISE for module: mov_sum
//
// Dependencies:
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
////////////////////////////////////////////////////////////////////////////////

module edge_test;

	// Inputs
	reg ap_clk;
	reg ap_rst;
	reg ap_start;
	reg [7:0] window_width_V;
	
	reg [0:0] absolute_value_V;
	reg [7:0] downsample_num_V;
	reg [9:0] datain_V_dout;
	reg datain_V_empty_n;

	// Outputs
	wire ap_done;
	wire ap_idle;
	wire ap_ready;
	wire [31:0] sumout_V;
	wire sumout_V_ap_vld;
	
	// Outputs
	wire ap_done_downsample;
	wire ap_idle_downsample;
	wire ap_ready_downsample;
	wire [13:0] sumout_V_downsample;
	wire sumout_V_ap_vld_downsample;

	// Instantiate the Unit Under Test (UUT)
	downsample uut_down (
		.ap_clk(ap_clk), 
		.ap_rst(ap_rst), 
		.ap_start(ap_start), 
		.ap_done(ap_done_downsample), 
		.ap_idle(ap_idle_downsample), 
		.ap_ready(ap_ready_downsample), 
		.absolute_value_V(absolute_value_V), 
		.downsample_num_V(downsample_num_V), 
		.datain_V_dout(datain_V_dout), 
		.datain_V_empty_n(datain_V_empty_n), 
		.datain_V_read(datain_V_read), 
		.sumout_V(sumout_V_downsample), 
		.sumout_V_ap_vld(sumout_V_ap_vld_downsample)
	);

	reg sum_start;
	reg sum_started = 0;
	wire mov_sum_clk;
	assign mov_sum_clk = (downsample_num_V > 1) ? (sumout_V_ap_vld_downsample | ap_rst) : ap_clk;
	
	// Instantiate the Unit Under Test (UUT)
	mov_sum uut (
		.ap_clk(mov_sum_clk), 
		.ap_rst(ap_rst), 
		.ap_start(sumout_V_ap_vld_downsample), 
		.ap_done(ap_done), 
		.ap_idle(ap_idle), 
		.ap_ready(ap_ready), 
		.window_width_V(window_width_V), 
		.downsample_num_V(downsample_num_V), 
		.datain_V(sumout_V_downsample),
		//.datain_V_ap_vld(sumout_V_ap_vld_downsample),
		//.datain_valid_V(sumout_V_ap_vld_downsample), 		
		.sumout_V(sumout_V), 
		.sumout_V_ap_vld(sumout_V_ap_vld)
	);
	
	always  begin
		#1  
		ap_clk = ~ap_clk;
	end
	
	reg signed [10:0] temp;

	
integer numdata, indata, sout, count;
	initial begin
		// Initialize Inputs
		ap_clk = 0;
		ap_rst = 0;
		ap_start = 0;
		window_width_V = 3;
		absolute_value_V = 0;
		downsample_num_V = 2;
		datain_V_dout = 0;
		datain_V_empty_n = 0;
		sum_start <= 0;
		sum_started <= 0;
		
		indata = $fopen("data.txt","r");		
		count = $fscanf(indata, "%d\n", numdata);
		sout = $fopen("sout_verilog.txt","w");

		// Wait 100 ns for global reset to finish
		#100;
		ap_rst = 1;
		
		#100;
		ap_rst = 0;
		
		@(posedge ap_clk);
		@(posedge ap_clk);
		ap_start = 1;
		@(posedge ap_clk);
		ap_start = 0;
		
		datain_V_empty_n = 1;
		while ( numdata > 0) begin
		  @ (posedge ap_clk);
		  numdata = numdata - 1;     
		  count = $fscanf(indata,"%d\n",temp);
		  datain_V_dout = temp - 512;
		  $fwrite(sout,"%d\n",sumout_V);
	   end
		$fclose(sout);
		
		#100 $finish;

	end
      
endmodule
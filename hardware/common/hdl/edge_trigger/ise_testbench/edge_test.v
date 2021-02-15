`timescale 1ns / 1ps

////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer:
//
// Create Date:   10:23:55 02/15/2021
// Design Name:   mov_sum
// Module Name:   /home/thilo/repos/chipwhisperer/hardware/common/hdl/edge_trigger/ise_testbench/edge_test.v
// Project Name:  cwlite_ise
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
	reg [9:0] datain_V_dout;
	reg datain_V_empty_n;
	
	reg signed [10:0] temp;

	// Outputs
	wire ap_done;
	wire ap_idle;
	wire ap_ready;
	wire datain_V_read;
	wire [31:0] sumout_V;
	wire sumout_V_ap_vld;
	
	always  #1  ap_clk = ~ap_clk;

	// Instantiate the Unit Under Test (UUT)
	mov_sum uut (
		.ap_clk(ap_clk), 
		.ap_rst(ap_rst), 
		.ap_start(ap_start), 
		.ap_done(ap_done), 
		.ap_idle(ap_idle), 
		.ap_ready(ap_ready), 
		.window_width_V(window_width_V), 
		.absolute_value_V(absolute_value_V), 
		.datain_V_dout(datain_V_dout), 
		.datain_V_empty_n(datain_V_empty_n), 
		.datain_V_read(datain_V_read), 
		.sumout_V(sumout_V), 
		.sumout_V_ap_vld(sumout_V_ap_vld)
	);
	
	integer numdata, indata, sout, count;
	
	initial begin
		// Initialize Inputs
		ap_clk = 0;
		ap_rst = 0;
		ap_start = 0;
		window_width_V = 3;
		absolute_value_V = 0;
		datain_V_dout = 0;
		datain_V_empty_n = 0;
		
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


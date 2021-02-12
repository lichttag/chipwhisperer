`include "includes.v"
//`define CHIPSCOPE

/***********************************************************************
This file is part of the ChipWhisperer Project. See www.newae.com for more
details, or the codebase at http://www.chipwhisperer.com

Copyright (c) 2021, NewAE Technology Inc. All rights reserved.
Author: Thilo Krachenfels <tkrachenfels@sect.tu-berlin.de>

  chipwhisperer is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  chipwhisperer is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
*************************************************************************/
module reg_edge(
	input 				reset_i,
	input 				clk,
	input		[5:0]		reg_address,  // Address of register
	input		[15:0]	reg_bytecnt,  // Current byte count
	input		[7:0]		reg_datai,    // Data to write
	output	[7:0]		reg_datao,    // Data to read
	input		[15:0]	reg_size,     // Total size being read/write
	input					reg_read,     // Read flag
	input					reg_write,    // Write flag
	input					reg_addrvalid,// Address valid flag
	output				reg_stream,
	input		[5:0]		reg_hypaddress,
	output	[15:0]	reg_hyplen,
	input		[9:0]		ADC_data,
	input					ADC_clk,
	output reg			trig_out
   );
	 
	 wire reset;
	 assign reset = reset_i;
	 assign reg_stream = 1'b0;
 	  
	`define EDGE_STATUSCFG_ADDR 60
	`define EDGE_STATUSCFG_LEN 4
	`define EDGE_THRESHOLD_ADDR 61
	`define EDGE_THRESHOLD_LEN 4
	
	`define EDGE_TYPE_RISING 0
	`define EDGE_TYPE_FALLING 1
	
	 reg [15:0] reg_hyplen_reg;
	 assign reg_hyplen = reg_hyplen_reg;
	 
	 always @(reg_hypaddress) begin
		case (reg_hypaddress)
				`EDGE_STATUSCFG_ADDR: reg_hyplen_reg <= `EDGE_STATUSCFG_LEN;
				`EDGE_THRESHOLD_ADDR: reg_hyplen_reg <= `EDGE_THRESHOLD_LEN;
				default: reg_hyplen_reg<= 0;
		endcase
	 end    
	
	 reg [7:0] reg_datao_reg;
	 assign reg_datao = reg_datao_reg;
	 
	 reg [31:0] statuscfg_reg;
	 wire [31:0] statuscfg_reg_read;
	 
	 reg [31:0] threshold_reg;
	 
	 wire			rst_core;
	 assign rst_core = statuscfg_reg[0];
	 wire			start_core;
	 assign start_core = statuscfg_reg[1];
	 
	 assign statuscfg_reg_read[2:0] = statuscfg_reg[2:0];
	 assign statuscfg_reg_read[3] = sum_wr;
	 assign statuscfg_reg_read[31:4] = statuscfg_reg[31:4];
	  	 
	 always @(posedge clk) begin
		if (reg_read) begin
			case (reg_address)		
				`EDGE_STATUSCFG_ADDR: begin reg_datao_reg <= statuscfg_reg_read[reg_bytecnt*8 +: 8]; end
				`EDGE_THRESHOLD_ADDR: begin reg_datao_reg <= threshold_reg[reg_bytecnt*8 +: 8]; end
				default: begin reg_datao_reg <= 0; end
			endcase
		end
	 end
	 
	 always @(posedge clk) begin
		if (reset) begin
			statuscfg_reg <= 0;
			threshold_reg <= 0;
		end else if (reg_write) begin
			case (reg_address)
				`EDGE_STATUSCFG_ADDR: statuscfg_reg[reg_bytecnt*8 +: 8] <= reg_datai;
				`EDGE_THRESHOLD_ADDR: threshold_reg[reg_bytecnt*8 +: 8] <= reg_datai;
				default: ;
			endcase
		end
	 end	 	 

	 	 
	wire [31:0] sum_out;
	wire sum_wr;
	
	wire absolute_value;
	assign absolute_value = statuscfg_reg[6];
	wire edge_type;
	assign edge_type = statuscfg_reg[7];
	wire [7:0] settling_time;
	assign settling_time = statuscfg_reg[15:8];
	wire [7:0] edge_num;
	assign edge_num = statuscfg_reg[23:16];
	wire [7:0] pretrigger_num;
	assign pretrigger_num = statuscfg_reg[31:24];

	mov_sum mov_sum_inst (
	.ap_clk(ADC_clk),
	.ap_rst(rst_core|reset),
	.ap_start(start_core),
	.ap_done(),
	.ap_idle(),
	.ap_ready(),
	.window_width_V(settling_time), //7:0
	.absolute_value_V(absolute_value),
	.datain_V_dout(ADC_data), //9:0
	.datain_V_empty_n(1'b1),
	.datain_V_read(),
	.sumout_V_din(sum_out), //19:0
	.sumout_V_full_n(1'b1),
	.sumout_V_write(sum_wr)
	);

	reg [7:0] edge_ctr = 0;
	reg [7:0] pretrigger_ctr = 0;
	reg is_high = 0;

	always @(posedge ADC_clk) begin
		//Default assignment
		trig_out <= 0;
		
		if ((!start_core) || rst_core) begin //might be unnecessary
			edge_ctr <= 0;
			pretrigger_ctr <= 0;
			is_high <= 0;
		end else begin

			if (sum_wr) begin
				if (sum_out > threshold_reg) begin
					if (edge_type == `EDGE_TYPE_RISING) begin
						if ((!is_high) || (pretrigger_ctr > 0)) begin
							pretrigger_ctr <= pretrigger_ctr + 1;
						end
						else begin
							pretrigger_ctr <= 0;
						end
						if (pretrigger_ctr == (pretrigger_num-1)) begin
							edge_ctr <= edge_ctr + 1;
							pretrigger_ctr <= 0;
							if((edge_ctr+1) == edge_num) begin
								trig_out <= 1;
								edge_ctr <= 0;
							end
						end
					end //(edge_type == `EDGE_TYPE_RISING)
					is_high <= 1;
				end //if (sum_out > threshold)
				else begin
					if (edge_type == `EDGE_TYPE_FALLING) begin
						if (is_high || (pretrigger_ctr > 0)) begin
							pretrigger_ctr <= pretrigger_ctr + 1;
						end
						else begin
							pretrigger_ctr <= 0;
						end
						if (pretrigger_ctr == (pretrigger_num-1)) begin
							edge_ctr <= edge_ctr + 1;
							pretrigger_ctr <= 0;
							if((edge_ctr+1) == edge_num) begin
								trig_out <= 1;
								edge_ctr <= 0;
							end
						end
					end //(edge_type == `EDGE_TYPE_FALLING)
					is_high <= 0;
				end //else (sum_out > threshold)
			end //if (sum_wr)
		end //if (reset)
	end //always
	 
 `ifdef CHIPSCOPE
   wire [127:0] cs_data;   
   wire [35:0]  chipscope_control;
  coregen_icon icon (
    .CONTROL0(chipscope_control) // INOUT BUS [35:0]
   ); 

   coregen_ila ila (
    .CONTROL(chipscope_control), // INOUT BUS [35:0]
    .CLK(ADC_clk), // IN
    .TRIG0(cs_data) // IN BUS [127:0]
   );  
	 assign cs_data[2:0] = statuscfg_reg[2:0];	 
	 assign cs_data[3] = 0;
	 assign cs_data[4] = 0;	 
	 assign cs_data[5] = 0;
	 assign cs_data[18:9] = 0;	 
	 assign cs_data[27:20] = reg_datai;
	 assign cs_data[29] = sum_wr;
	 assign cs_data[49:30] = sum_out;	 	
	 assign cs_data[59:50] = ADC_data;
 `endif
 
endmodule

`undef CHIPSCOPE

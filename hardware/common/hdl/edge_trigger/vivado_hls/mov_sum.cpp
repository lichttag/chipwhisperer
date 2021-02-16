
#include "ap_int.h"

#define max_window_width 128

//Wrap array initialization into function to avoid many initialization cycles
void init_datamem(ap_uint<10> * datamem){
	ap_uint<9> i;
	for(i = 0; i < max_window_width; i++){
			datamem[i] = 0;
	}
}

void mov_sum(ap_uint<8> window_width, ap_uint<1> absolute_value, ap_uint<10> * datain, ap_uint<32> * sumout)
{
#pragma HLS INTERFACE ap_fifo port=datain
#pragma HLS INTERFACE ap_stable port=window_width
#pragma HLS INTERFACE ap_stable port=absolute_value

	ap_uint<10> datamem[max_window_width];
	ap_uint<32> totalsum;
	ap_uint<9> i;
	ap_uint<8> shift_cnt;
	ap_uint<10> tmp;

#pragma HLS ARRAY_PARTITION variable=datamem complete dim=1

	init_datamem(datamem);
	totalsum = 0;
	shift_cnt = 0;
	
	while(1){
	#pragma HLS PIPELINE II=1
		//Shift data, load new
		for(i = max_window_width-1; i > 0; i--){
			datamem[i] = datamem[i-1];
		}
		tmp = *(datain++);

		//Calculate absolute value if configured
		if(absolute_value && (tmp < 512))
			datamem[0] = 1023 - tmp;
		else
			datamem[0] = tmp;
		
		//Calculate current sum
		totalsum = totalsum + datamem[0] - datamem[window_width];

		//Start operation if one full window has been calculated
		if(shift_cnt >= (window_width-1))
			*sumout = totalsum;
		else
			shift_cnt += 1;
	}
}

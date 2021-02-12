
#include "ap_int.h"

#define max_window_width 128

void mov_sum(ap_uint<8> window_width, ap_uint<1> absolute_value, ap_uint<10> * datain, ap_uint<32> * sumout)
{
#pragma HLS INTERFACE ap_fifo port=datain
#pragma HLS INTERFACE ap_fifo port=sumout
#pragma HLS INTERFACE ap_stable port=window_width

	ap_uint<10> datamem[max_window_width];
	ap_uint<32> totalsum = 0;
	ap_uint<8> i;
	ap_uint<8> shift_cnt = 0;

#pragma HLS ARRAY_PARTITION variable=datamem complete dim=1

	for(i = 0; i < window_width; i++){
		datamem[i] = 0;
	}
	
	while(1){
	#pragma HLS PIPELINE II=1
		//Shift data, load new
		for(i = window_width-1; i > 0; i--){
			datamem[i] = datamem[i-1];
		}
		//Calculate absolute value if configured
		if(absolute_value && (*datain < 512))
			datamem[0] = *(datain++) + 512;
		else
			datamem[0] = *(datain++);
		
		//Calculate current sum
		totalsum = totalsum + datamem[0] - datamem[window_width-1];

		//Start operation if one full window has been calculated
		if(shift_cnt >= (window_width-1))
			*(sumout++) = totalsum;
		else
			shift_cnt += 1;
	}
}


#include "ap_int.h"

#define max_window_width 128

void mov_sum(ap_uint<8> window_width, ap_uint<10> * datain, ap_uint<32> * sumout)
{
#pragma HLS INTERFACE ap_fifo port=datain
#pragma HLS INTERFACE ap_fifo port=sumout
#pragma HLS INTERFACE ap_stable port=window_width

	ap_uint<10> datamem[max_window_width];
	ap_uint<32> totalsum = 0;
	int i, shift_cnt;

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
		datamem[0] = *(datain++);
		

		//Calculate current sum
		
		//Add new value
		/*
		if (datamem[0] > 0)
		*/
			totalsum += datamem[0];
		/*
		else
			totalsum -= datamem[0];
		*/
			
		//Delete oldest value
		/*
		if (datamem[window_width] > 0)
			totalsum += datamem[window_width];
		else
		*/
			totalsum -= datamem[window_width];

		if(shift_cnt >= max_window_width)
			*(sumout++) = totalsum;
		else
			shift_cnt += 1;
	}
}

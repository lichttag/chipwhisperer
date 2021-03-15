
#include "ap_int.h"
#include "ap_utils.h"
#include "definitions.h"

//Wrap array initialization into function to avoid many initialization cycles
void init_datamem(ap_uint<ADC_SUM_BITS> * datamem){
	ap_uint<9> i;
	for(i = 0; i < MAX_WINDOW_WIDTH; i++){
			datamem[i] = 0;
	}
}

void mov_sum(ap_uint<8> window_width, ap_uint<ADC_SUM_BITS> *datain, ap_uint<32> * sumout)
{
#pragma HLS INTERFACE ap_stable port=window_width
//#pragma HLS INTERFACE ap_vld port=datain

	ap_uint<ADC_SUM_BITS> datamem[MAX_WINDOW_WIDTH];
	ap_uint<32> totalsum;
	ap_uint<9> i;
	ap_uint<8> shift_cnt;
	ap_uint<ADC_SUM_BITS> tmp;

#pragma HLS ARRAY_PARTITION variable=datamem complete dim=1

	init_datamem(datamem);
	totalsum = 0;
	shift_cnt = 0;
	
	while(1){
	#pragma HLS PIPELINE II=1

		//Wait for new data (stall if not valid)
		tmp = *datain;

		//Calculate current sum
		totalsum = totalsum - datamem[window_width-1] + tmp;

		//Shift data
		for(i = MAX_WINDOW_WIDTH-1; i > 0; i--){
			datamem[i] = datamem[i-1];
		}
		datamem[0] = tmp;

		//Start operation if one full window has been calculated
		if(shift_cnt >= (window_width-1)){
			*sumout = totalsum;
		}
		else {
			shift_cnt += 1;
		}
	}
}

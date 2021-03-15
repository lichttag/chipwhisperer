
#include "ap_int.h"
#include "definitions.h"


void downsample(ap_uint<1> absolute_value, ap_uint<8> downsample_num, ap_uint<10> * datain, ap_uint<ADC_SUM_BITS> * sumout)
{
#pragma HLS INTERFACE ap_fifo port=datain
#pragma HLS INTERFACE ap_stable port=absolute_value
#pragma HLS INTERFACE ap_stable port=downsample_num

	ap_uint<ADC_SUM_BITS> totalsum;
	ap_uint<8> downsample_cnt;
	ap_uint<10> tmp;

	totalsum = 0;
	downsample_cnt = 0;
	
	while(1){
	#pragma HLS PIPELINE II=1

		tmp = *(datain++);
		//Calculate absolute value if configured
		if(absolute_value && (tmp < 512))
			totalsum += 1023 - tmp;
		else
			totalsum += tmp;

		if(downsample_cnt == (downsample_num-1)){
			*sumout = totalsum;
			totalsum = 0;
			downsample_cnt = 0;
		} else {
			downsample_cnt += 1;
		}
	}
}

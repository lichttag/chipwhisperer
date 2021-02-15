#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 NewAE Technology Inc
# All rights reserved.
#
# Authors: Otto Bittner, Thilo Krachenfels
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================
import logging
import struct
import base64
import copy

import numpy as np
from collections import OrderedDict
from chipwhisperer.common.utils import util

"""
ec_cfgaddr[0]: reset
ec_cfgaddr[1]: enable
ec_cfgaddr[3]: running
ec_cfgaddr[6]: absolute_values --> calculate absolute value before summing up
ec_cfgaddr[7]: edge_type --> 0 == "rising_edge", 1 == "falling_edge"
ec_cfgaddr[8:15]: window_size 
ec_cfgaddr[16:23]: edge_num
ec_cfgaddr[24:31]: hold_cycles
ec_dataaddr[0:31]: threshold
"""
ec_cfgaddr  = 60
ec_dataaddr = 61
CODE_READ   = 0x80
CODE_WRITE  = 0xC0


class ChipWhispererEdgeCounter(object):
    """Communicates with the EdgeCounter module inside the CW Pro/Lite

    """
    _name = 'EdgeCounter Trigger Module'
    STATUS_RUNNING_MASK = 1 << 3
    STATUS_RESET_MASK = 1 << 0
    STATUS_START_MASK = 1 << 1
    EDGE_TYPE_MASK = 0b01111111

    def __init__(self, oa):
        self.oa = oa

    # CW communication helper
    # new_data will be truncated to 8 bit!
    def __set_config_val(self, new_data, idx):
        # Fetch data from CW so we only update pretrigger_ctr
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)

        # Truncate by only using lowest 8 bit
        data[idx] = new_data & 0xff

        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data, Validate=False)
    
    def __get_config_val(self, addr, idx, fstr):
        data = self.oa.sendMessage(CODE_READ, addr, maxResp=4)

        # unpack() expects a buffer of bytes, but accessing elements of a bytearray returns ints.
        # Calling bytes() with an int produces 'int' number of 0x00 bytes.
        # Calling bytes() on an iterable (here: slide of len 1) produces a byte object including the iterables content.
        # Unpack always returns a tuple
        unpacked = struct.unpack(fstr, bytes(data[idx:idx+1]))[0]
        
        # most significant byte in the beginning of bytearray
        return int.from_bytes(unpacked, "big", signed=False)

    # Serialization helper
    def _dict_repr(self):
        dict = OrderedDict()
        dict['edge_type'] = self.edge_type
        dict['window_size'] = self.window_size
        dict['threshold'] = self.threshold
        dict['edge_num'] = self.edge_num
        dict['hold_cycles'] = self.hold_cycles
        return dict

    # Serialization helper
    def __repr__(self):
        return util.dict_to_str(self._dict_repr())

    def __str__(self):
        return self.__repr__()

    @property
    def absolute_values(self):
        return self._get_absolute_values()

    @absolute_values.setter
    def absolute_values(self, value):
        self._set_absolute_values(value)

    @property
    def edge_type(self):
        return self._get_edge_type()

    @edge_type.setter
    def edge_type(self, value):
        self._set_edge_type(value)

    @property
    def window_size(self):
        return self._get_window_size()

    @window_size.setter
    def window_size(self, value):
        self._set_window_size(value)

    @property
    def threshold(self):
        """ The threshold for the EdgeCounter trigger."""
        return self._get_threshold()

    @threshold.setter
    def threshold(self, value):
        self._set_threshold(value)

    @property
    def edge_num(self):
        return self._get_edge_num()

    @edge_num.setter
    def edge_num(self, value):
        self._set_edge_num(value)

    @property
    def hold_cycles(self):
        return self._get_hold_cycles()

    @hold_cycles.setter
    def hold_cycles(self, value):
        self._set_hold_cycles(value)

    def reset(self):
        """ Reset the EdgeCounter hardware block. The ADC clock must be running! """
        
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)
        data[0] = 0x01
        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data)
        
        if self.check_status():
            raise IOError("EdgeCounter Reset in progress, but EdgeCounter reports still running. Is ADC Clock stopped?")
        
        data[0] = 0x00
        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data)

    def start(self):
        """ Start the EdgeCounter algorithm, which causes the threshold to be loaded from the FIFO """
        
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)
        # Set enable        
        data[0] = 0x02
        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data, Validate=False)
        data[0] = 0x00
        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data, Validate=False)

    def check_status(self):
        """ Check if the EdgeCounter module is running & outputting valid data """
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)
        if not (data[0] & self.STATUS_RUNNING_MASK):
            return False
        else:
            return True

    def _get_absolute_values(self):
        """ Get if the absolute value of the signal should be calculated before averaging/summing"""
        # ec_cfgaddr[6]: absolute_values --> calculate absolute value before summing up
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)
        
        # isolate bit 6
        data = (data[0] >> 6) & 0x01
        
        if data == 0b0:
            return False
        if data == 0b1:
            return True

    def _set_absolute_values(self, absolute_values):
        """ Set if the absolute value of the signal should be calculated before averaging/summing"""
        if not isinstance(absolute_values, bool):
            raise ValueError(f"Value for absolute_values {edge_type} is not a boolean")
        
        # Fetch data from CW so we only update pretrigger_ctr
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)
        
        if absolute_values:
            # set bit 6 in byte 0
            data[0] |= 1 << 6
        else:
            # clear bit 6 in byte 0
            data[0] &= ~(1 << 6)
        
        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data, Validate=False)


    def _get_edge_type(self):
        """ Get the edge type"""
        # ec_cfgaddr[7]: edge_type --> 0 == "rising_edge", 1 == "falling_edge"
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)
        
        # isolate bit 7
        data = (data[0] >> 7) & 0x01
        
        if data == 0b0:
            return "rising_edge"
        if data == 0b1:
            return "falling_edge"

    def _set_edge_type(self, edge_type):
        """ Set the edge type"""
        if edge_type != "rising_edge" and edge_type != "falling_edge":
            raise ValueError(f"Invalid edge_type {edge_type}. Must be 'rising_edge' or 'falling_edge'")
    
        # Fetch data from CW so we only update pretrigger_ctr
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)


        if edge_type == "rising_edge":
            # clear bit 7 in byte 0
            data[0] &= ~(1 << 7)
        if edge_type == "falling_edge":
            # set bit 7 in byte 0
            data[0] |= 1 << 7
        
        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data, Validate=False)


    def _get_window_size(self):
        """ Get the moving average/sum width in ADC cycles"""
        # ec_cfgaddr[8:15]: window_size 
        return self.__get_config_val(ec_cfgaddr, 1, "c")

    def _set_window_size(self, window_size):
        """ Set the moving average/sum width in ADC cycles"""
        if (window_size > 255) or (window_size < 1):
            raise ValueError("Invalid settling_time {}. Must be in range (1, 255)".format(window_size))
        
        self.__set_config_val(window_size, 1)


    def _get_threshold(self):
        """ Get the threshold. When the trace level surpasses/falls below this threshold for long enough the system triggers (depending on the configured edge_type) """
        data = self.oa.sendMessage(CODE_READ, ec_dataaddr, maxResp=4)
        
        thr_raw = struct.unpack('<I', data)[0]
        thr_unpacked = ((thr_raw * self.window_size) // 1024) - 0.5
        return thr_unpacked


    def _set_threshold(self, threshold):
        """ Set the threshold. When the trace level surpasses/falls below this threshold for long enough the system triggers (depending on the configured edge_type) """
        print("[!] Make sure to set window_size before threshold")
        
        if self.window_size < 1:
            raise IOError("EdgeCounter window_size must be set before threshold can be set")
        
        threshold_s = int(((threshold + 0.5) * 1024) * self.window_size)
        threshold_packed = struct.pack("<I", threshold_s)
        
        self.oa.sendMessage(CODE_WRITE, ec_dataaddr, threshold_packed, Validate=False)
        self.start()


    def _get_edge_num(self):
        """ Get the number of edges which should be detected before triggering"""
        # ec_cfgaddr[16:23]: edge_num
        return self.__get_config_val(ec_cfgaddr, 2, "c")

    def _set_edge_num(self, edge_num):
        """ Set the number of edges which should be detected before triggering"""
        if (edge_num > 255) or (edge_num < 1):
            raise ValueError("Invalid edge_num {}. Must be in range (1, 255)".format(edge_num))
        
        self.__set_config_val(edge_num, 2)


    def _get_hold_cycles(self):
        """ Get the number of cycles the moving average/sum should stay above/below threshold before detecting an edge"""
        # ec_cfgaddr[24:31]: hold_cycles
        return self.__get_config_val(ec_cfgaddr, 3, "c")

    def _set_hold_cycles(self, hold_cycles):
        """ Set the number of cycles the moving average/sum should stay above/below threshold before detecting an edge"""
        if (hold_cycles > 255) or (hold_cycles < 1):
            raise ValueError("Invalid hold_cycles value {}. Must be in range (1, 255)".format(hold_cycles))
        
        self.__set_config_val(hold_cycles, 3)


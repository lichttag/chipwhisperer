#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014, NewAE Technology Inc
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
ec_cfgaddr[7]: edge_type --> 0 == "rising_edge", 1 == "falling_edge"
ec_cfgaddr[8:15]: settling_time 
ec_cfgaddr[16:23]: edge_num
ec_cfgaddr[24:31]: pretrigger_ctr
ec_dataaddr[0:31]: threshold
"""
ec_cfgaddr  = 60
ec_dataaddr = 61
CODE_READ   = 0x80
CODE_WRITE  = 0xC0


class ChipWhispererEdgeCounter(object):
    """Communicates with the EdgeCounter module inside the CW Pro

    """
    _name = 'EdgeCounter Trigger Module'
    STATUS_RUNNING_MASK = 1 << 3
    STATUS_RESET_MASK = 1 << 0
    STATUS_START_MASK = 1 << 1
    EDGE_TYPE_MASK = 0b01111111

    def __init__(self, oa):
        self.oa = oa

    # CW communication helper
    def __set_config_val(new_data, idx, fstr):
        # Fetch data from CW so we only update pretrigger_ctr
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)

        data[idx] = struct.pack(fstr, new_data)

        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data, Validate=False)
    
    def __get_config_val(addr, idx, fstr):
        data = self.oa.sendMessage(CODE_READ, addr, maxResp=4)

        return struct.unpack(fstr, data[idx])

    # Serialization helper
    def _dict_repr(self):
        dict = OrderedDict()
        dict['edge_type'] = self.edge_type
        dict['settling_time'] = self.settling_time
        dict['threshold'] = self.threshold
        dict['edge_num'] = self.edge_num
        dict['pretrigger_ctr'] = self.pretrigger_ctr
        return dict

    # Serialization helper
    def __repr__(self):
        return util.dict_to_str(self._dict_repr())

    def __str__(self):
        return self.__repr__()

    @property
    def edge_type(self):
        self._get_edge_type()

    @edge_type.setter
    def edge_type(self, value):
        self._set_edge_type(value)

    @property
    def settling_time(self):
        self._get_settling_time()

    @settling_time.setter
    def settling_time(self, value):
        self._set_settling_time(value)

    @property
    def threshold(self):
        """ The threshold for the EdgeCounter trigger.
        """
        return self._get_threshold()

    @threshold.setter
    def threshold(self, value):
        self._set_threshold(value)

    @property
    def edge_num(self):
        self._get_edge_num()

    @edge_num.setter
    def edge_num(self, value):
        self._set_edge_num(value)

    @property
    def pretrigger_ctr(self):
        self._get_pretrigger_ctr()

    @pretrigger_ctr.setter
    def pretrigger_ctr(self, value):
        self._set_pretrigger_ctr(value)

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
        # data is a bytearray
        # Set reset & enable        
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

    def _get_edge_type(self):
        # ec_cfgaddr[7]: edge_type --> 0 == "rising_edge", 1 == "falling_edge"
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)

        # isolate bit 7
        data = (data[0] >> 7) & 0x01

        if data == 0b0:
            return "rising_edge"
        if data == 0b1:
            return "falling_edge"

    def _set_edge_type(self, edge_type):
        if edge_type != "rising_edge" and edge_type != "falling_edge":
            raise ValueError(f"Invalid edge_type {edge_type}. Must be 'rising_edge' or 'falling_edge'")
    
        if edge_type == "rising_edge":
            _edge_type = 0
        if edge_type == "falling_edge":
            _edge_type = 1
        
        # Fetch data from CW so we only update pretrigger_ctr
        data = self.oa.sendMessage(CODE_READ, ec_cfgaddr, maxResp=4)

        # Put edge_type bit to bit 7 and fill bits below with '1' by ORing with EDGE_TYPE_MASK
        # Then pull bit 7 in data[0] to value of _edge_type
        data[0] &= ((_edge_type << 7) | EDGE_TYPE_MASK)

        self.oa.sendMessage(CODE_WRITE, ec_cfgaddr, data, Validate=False)

        if self.check_status() == False:
            raise IOError("EdgeCounter edge_type set, but EdgeCounter not running. No valid trigger will be present. Did you set a threshold?")

    def _get_settling_time(self):
        # ec_cfgaddr[8:15]: settling_time 
        return __get_config_val(ec_cfgaddr, 1, "c")

    def _set_settling_time(self, settling_time):
        if (threshold > 255) or (threshold < 0):
            raise ValueError("Invalid settling_time {}. Must be in range (0, 255)".format(threshold))
    
        __set_config_val(settling_time, 1, "c")

        if self.check_status() == False:
            raise IOError("EdgeCounter settling_time set, but EdgeCounter not running. No valid trigger will be present. Did you set a threshold?")

    def _get_threshold(self):
        """ Get the threshold. When the trace level surpasses/falls below this threshold for long enough the system triggers (depending on the configured edge_type) """
        data = self.oa.sendMessage(CODE_READ, ec_dataaddr, maxResp=4)

        return struct.unpack("f", data)

    def _set_threshold(self, threshold):
        """ Set the threshold. When the trace level surpasses/falls below this threshold for long enough the system triggers (depending on the configured edge_type) """
        self.reset()

        # Transform python 32bit float into c 32 bit float
        threshold_packed = struct.pack("f", threshold)

        self.oa.sendMessage(CODE_WRITE, ec_dataaddr, threshold_packed, Validate=False)
        self.start()


    def _get_edge_num(self):
        # ec_cfgaddr[16:23]: edge_num
        return __get_config_val(ec_cfgaddr, 2, "c")
        

    def _set_edge_num(self, edge_num):
        if (edge_num > 255) or (edge_num < 0):
            raise ValueError("Invalid edge_num {}. Must be in range (0, 255)".format(threshold))

        __set_config_val(edge_num, 2, "c")

        if self.check_status() == False:
            raise IOError("EdgeCounter edge_num set, but EdgeCounter not running. No valid trigger will be present. Did you set a threshold?")

    def _get_pretrigger_ctr(self):
        # ec_cfgaddr[24:31]: pretrigger_ctr
        return __get_config_val(ec_cfgaddr, 3, "c")

    def _set_pretrigger_ctr(self, pretrigger_ctr):
        if (pretrigger_ctr > 255) or (pretrigger_ctr < 0):
            raise ValueError("Invalid pretrigger_ctr {}. Must be in range (0, 255)".format(threshold))

        __set_config_val(pretrigger_ctr, 3, "c")

        if self.check_status() == False:
            raise IOError("EdgeCounter pretrigger_ctr set, but EdgeCounter not running. No valid trigger will be present. Did you set a threshold?")


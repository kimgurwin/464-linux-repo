#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday Sat 6 01:47:21 2025

@author: Henry Vergowven
"""

'''
Description:
This file test both motor modules on the robot to easily test mechanically functions or motor failures before debugging main file
'''

import ckbot.logical as L
import time

c = L.Cluster(count=2)

for i in range(10):
    '''c.at.Nx01.set_pos(-5000)
    time.sleep(1)
    c.at.Nx01.set_pos(5000)
    time.sleep(1)'''
    c.at.Nx33.set_pos(-5000)
    c.at.Nx05.set_pos(5000)
    time.sleep(1)
    c.at.Nx33.set_pos(5000)
    c.at.Nx05.set_pos(-5000)
    time.sleep(1)
    
    
    
    
    
    
    
    
    
    
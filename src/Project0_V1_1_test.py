#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sunday Sat 6 01:47:21 2025

@author: Henry Vergowven
"""

'''
Description:
This file allows for testing the modifications used in Project0_V1_1 when the robot mechanics were being modified.

Controls:
- W: Move the module forward and backward
- Q or Esc: Quit the program
'''

import os
os.environ["SDL_VIDEODRIVER"] = "x11"

import time
from joy.decl import *
from joy import JoyApp
from joy.misc import curry
from joy.plans import GaitCyclePlan
from joy.misc import loadCSV
class WalkerApp( JoyApp ):
    
    def __init__(self,*arg,**kw):
        # We expect a 2 module robot
        JoyApp.__init__(self,robot=dict(count=1),*arg,**kw)
      
    def onStart(self):
        # Create a temporal filter that is true once every 0.5 seconds
        self.oncePer = self.onceEvery(0.5)
        # Make sure all the motors are in servo mode
        for m in self.robot.itermodules():
          m.set_mode("SERVO")
          
        self.robot.at.Nx0F.set_pos(3000)
          
    def onStop( self ):
      # Make sure we go_slack on all servo modules when we exit
      self.robot.at.Nx0F.set_pos(3000)
      self.robot.off()
      
    def onEvent(self, evt):
      ### Main event handler
      # We have several broad classes of events, which are processed differently
      #  depending on our mode. In most cases, we return after handling the event.
      #
      # Allow operator to quit by closing window or hitting 'q' or <escape>
      #  (actually, the superclass call at the end of this method would do all
      #  of this, but it is good practice to clean our own mess if we can)
      if evt.type==QUIT or (evt.type==KEYDOWN and evt.key in [K_q,K_ESCAPE]):
        self.stop()
      #
      # Joystick buttons
      if evt.type==KEYDOWN:
          if evt.key == K_w:
              self.robot.at.Nx0F.set_pos(3000)
              time.sleep(.5)
              self.robot.at.Nx0F.set_pos(-5000)
              time.sleep(.5)
        

      return


    
    
if __name__=="__main__":
    print("starting")
    app=WalkerApp()
    app.run()
    
    
    
    
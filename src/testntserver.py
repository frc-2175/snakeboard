#!/usr/bin/env python3

import time
from _pyntcore import NetworkTables
from wpilib import SendableChooser, SmartDashboard, SendableRegistry

# To see messages from networktables, you must set up logging
import logging

logging.basicConfig(level=logging.DEBUG)

NetworkTables.startServer()
sd = NetworkTables.getTable("SmartDashboard")

sd.putNumber("aNumber", 0)

auto = SendableChooser()
auto.setDefaultOption('Do Nothing', 1)
auto.addOption('Move Forward', 2)
auto.addOption('Shoot Three', 3)
# SendableRegistry.add(auto, 'Auto Mode')

blap = SendableChooser()
blap.setDefaultOption('it bad', 1)
blap.addOption('it good', 2)
blap.addOption('it something', 3)
# SendableRegistry.add(blap, 'norp')

SmartDashboard.putData(auto)
SmartDashboard.putData(blap)

i = 0
b = True
while True:
    sd.putNumber("robotTime", i)
    sd.putString("robotTimeString", str(i) + " seconds")
    sd.putString("myTable/robotTimeString", str(i) + " seconds again")
    sd.putBoolean("lightOn", b)

    time.sleep(1)
    i += 1
    b = not b

    if i == 10:
    	sd.putBoolean("wow", True)

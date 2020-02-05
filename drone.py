import logging
import time
import csv
import unittest
import sys

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from unittest.mock import MagicMock
 
URI = 'radio://0/80/2M'
 
logging.basicConfig(level=logging.ERROR)
 
 
if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)
 
    lg_stab = LogConfig(name='stateEstimate', period_in_ms=10)
    lg_stab.add_variable('stateEstimate.x', 'float')
    lg_stab.add_variable('stateEstimate.y', 'float')
    
    if '-test' in sys.argv:
        sync = MagicMock(spec=SyncCrazyflie, name=URI)
        sync_logger = MagicMock(spec=SyncLogger, name='logger-'+URI)
    else:
        sync = SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache'))
        sync_logger = SyncLogger(sync, lg_stab)

    with sync as scf:
        with sync_logger as logger:
            cf = scf.cf
 
            cf.param.set_value('kalman.resetEstimation', '1')
            time.sleep(0.1)
            cf.param.set_value('kalman.resetEstimation', '0')
            time.sleep(2)
            angle = 90  #degrees/s changes turn angle
            speed = .2   #m/s changes drone speed
            looptime = 360//angle * 10
                #takeoff
                #send_hover_setpoint(vx(m/s),vy(m/s),yawrate(degrees/s),zdistance)
            for y in range(10):   #loop 1 second
                cf.commander.send_hover_setpoint(0,0,0, y / 25)
                time.sleep(0.1)
 
           
            for _ in range(20):     #loop 2 seconds
                cf.commander.send_hover_setpoint(0,0,0,0.4)
                time.sleep(0.1)
 
            for _ in range(looptime):    
                cf.commander.send_hover_setpoint(speed,0,angle,0.4)
                time.sleep(0.1)
 
            for _ in range(looptime):
                cf.commander.send_hover_setpoint(speed,0,-angle,0.4)
                time.sleep(0.1)
 
            for _ in range(20):
                cf.commander.send_hover_setpoint(0,0,0,0.4)
                time.sleep(0.1)
                   
            #landing
            for y in range(10):
                cf.commander.send_hover_setpoint(0,0,0, (10-y) / 25)
                time.sleep(0.1)
               
            with open('./data/flightCoordinates.csv', mode='w') as file:
                writer = csv.writer(file, delimiter=',')
                writer.writerow(['time','X','Y'])
                for entry in logger:
                    timestamp = entry[0]
                    data = entry[1]
                    logconf_name = entry[2]
                    #print('[%d][%s]: %s' % (timestamp, logconf_name, data))
                    writer.writerow([timestamp, data["stateEstimate.x"], data["stateEstimate.y"]])
 
    print("done")

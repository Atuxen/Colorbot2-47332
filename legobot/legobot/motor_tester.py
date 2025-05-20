#!/usr/bin/env python3
# import argparse
# from ev3dev2.sound import Sound
import time
#from ev3dev2.sensor import INPUT_1
#from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.motor import SpeedPercent, MediumMotor
from ev3dev2.motor import OUTPUT_B


def motor_test():
    """ Motor test function
    """
    # The Setup
    #cs = ColorSensor(INPUT_1)
    x = MediumMotor(OUTPUT_B)

    # # Load in the arguments
    #x.run_to_abs_pos(position_sp=200, speed_sp=200)
    # x.wait_while('running')
    # time.sleep(5)
    print('resetting')
    # x.reset()
    #x.run_to_abs_pos(position_sp=1000, speed_sp=100)
    for n in range(120):
        x.on_for_degrees(SpeedPercent(10), 3)
        time.sleep(0.05)
    #x.on_for_degrees(SpeedPercent(10), 1000)
    #x.on_to_position(SpeedPercent(10), 1000)

    # x.full_travel_count()

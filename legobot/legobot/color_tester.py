# import argparse
# from ev3dev2.sound import Sound
import time
from ev3dev2.sensor import INPUT_1
from ev3dev2.sensor.lego import ColorSensor

# The Setup
cs = ColorSensor(INPUT_1)

# # Load in the arguments
while True:
    print(cs.rgb)
    time.sleep(1)


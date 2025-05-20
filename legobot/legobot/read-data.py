# Test script for Zhenyun

import pandas as pd

df = pd.read_csv('/home/robot/47332_exercises/data/datafile.csv', sep=';')
with open('/home/robot/47332_exercises/data/read.txt', 'w') as f:
    f.write('%s' % df)

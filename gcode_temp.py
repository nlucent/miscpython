#!python

import sys
import os
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--infile', help="input gcode file")
parser.add_argument('-o', '--outfile', help="output gcode file to be written")
parser.add_argument(
    '-t', '--tempchange', help="temperature change per mm", type=int)
parser.add_argument(
    '-m', '--mmheight', help="height in mm tempchange should be applied", type=int)
args = parser.parse_args()
print(args)

testfile = 'c:/users/nlucent/documents/code/3dBenchy.gcode'
outfile = 'c:/users/nlucent/documents/code/out_test.gcode'
heightmm = args.mmheight
tempIncrease = args.tempchange

tempre = r'^M10[49] S(?P<temp>\d+)'

zchangere = r'^G1 Z(?P<level>\d+)\.\d+ F\d+'
results = []

f = open(args.infile, 'r')
o = open(outfile, 'w')

z = re.compile(zchangere)
t = re.compile(tempre)

for line in f.readlines():
    o.write(line)
    mt = t.match(line)

    if mt:
        try:
            curtemp
        except NameError:
            curtemp = int(mt.group('temp'))

    mz = z.match(line)
    if mz:
        if int(mz.group('level')) not in results
        and int(mz.group('level')) % heightmm == 0:
            o.write("M104 S" + str(curtemp) + " T0\n")
            results.append(int(mz.group('level')))
            print(mz.group('level'), curtemp)
            curtemp += tempIncrease

o.close()
f.close()

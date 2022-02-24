'''
Program template for printing operations with coordinates as the geometry input.

Inputs of the printing parameters are defined in lines 172 - 183.
'''

# Import modules
import os
import sys
import serial 
import time
import numpy as np
import transform_rot as transform
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from uarm.wrapper import SwiftAPI

# Import Syringe Pump Arduino
ArduinoSerial = serial.Serial('COM4',2400) #COM3 is the port of syringe pump
time.sleep(2)

# Import uArm
swift = SwiftAPI(filters={'hwid': 'USB VID:PID=2341:0042'})
swift.waiting_ready(timeout=3)
device_info = swift.get_device_info()
print(device_info)
firmware_version = device_info['firmware_version']
if firmware_version and not firmware_version.startswith(('0.', '1.', '2.', '3.')):
    swift.set_speed_factor(0.0005)
swift.set_mode(0)

# My function
def my_range(start, end, step):
    while start >= end:
        yield start
        start = start-step
        
def return_():
    a = swift.get_position(wait=True, timeout=None, callback=None)
    swift.set_position(x=a[0], y=a[1], z=10, speed=3000, wait=True)
    swift.set_position(x=150, y=0, z=10, wait=True)
    swift.set_position(x=105, wait=True)
    swift.set_position(z=20, wait=True)
    swift.set_position(x=115, wait=True)
    swift.set_position(x=105, wait=True)
    sys.exit()
     
def extrusion(printhead):
    if printhead == 3:
        o =  ArduinoSerial.write(b'3')
    if printhead == 2:
        o =  ArduinoSerial.write(b'2')
    if printhead == 1:
        o =  ArduinoSerial.write(b'1')
    return o

def convert_to_arduino(number):
    while number > 30000 or number <= 0:
        number = int(input('input the delaytime you want to set, maximum 30000, the larger the delaytime is the slower the pump will be, dont set it too small!'))
    else:
        length = len(str(number))
    
    if length == 1: #send first charater to the Arduino, let it know how many numbers it needs to wait before convert numbers in buffer into delaytime)
        ArduinoSerial.write(b'1')
    if length == 2:
        ArduinoSerial.write(b'2')
    if length == 3:
        ArduinoSerial.write(b'3')
    if length == 4:
        ArduinoSerial.write(b'4')
    if length == 5:
        ArduinoSerial.write(b'5')
    
    for i in str(number):#send numbers in the delaytime individually
        print(i)
        if int(i) == 0:
            ArduinoSerial.write(b'0')
        if int(i) == 1:
            ArduinoSerial.write(b'1')
        if int(i) == 2:
            ArduinoSerial.write(b'2')
        if int(i) == 3:
            ArduinoSerial.write(b'3')
        if int(i) == 4:
            ArduinoSerial.wrie(b'4')
        if int(i) == 5:
            ArduinoSerial.write(b'5')
        if int(i) == 6:
            ArduinoSerial.write(b'6')
        if int(i) == 7:
            ArduinoSerial.write(b'7')
        if int(i) == 8:
            ArduinoSerial.write(b'8')
        if int(i) == 9:
            ArduinoSerial.write(b'9')  
    print('Delaytime sent to Arduino!')
     
def calibration(Z0, a_gcode, b_gcode, r_stage):
    x_cal = [0]
    y_cal = [0]
    xyarm_cal = transform.coordinateTransfer(x_cal, y_cal, a_gcode, b_gcode, r_stage).T  
    z_check = False
    while z_check == False: 
        swift.flush_cmd(wait_stop=True)
        swift.set_position(xyarm_cal[0, 0], xyarm_cal[0, 1], 10, speed=3000, timeout=20)
        time.sleep(1)
        swift.set_position(xyarm_cal[0, 0], xyarm_cal[0, 1], Z0, wait=True)
        swift.flush_cmd(wait_stop=True)
        
        isPosition = input('Is the z-position correct? Please type any key to continue [Y/n/R (Return)]: ')
    
        if isPosition == 'R':
            return_()
        
        elif isPosition == 'n':
            shift_z = input('Enter the z shifting value: ')
            Z0 = float(Z0) + float(shift_z)
        
        else:
            z_check = True
            pass
        
        print('Calibrated z = ' + str(Z0)) 
        
        # Perform xy calibration 
        print('\nPerforming xy calibration')
        xy_check = False
        while xy_check == False: 
            print('Is the xy (central) position correct?')
            isPosition = input('Is the xy-position correct? Please type any key to continue [Y/n/R]: ')
            if isPosition == 'R':
                return_()
            elif isPosition == 'n':
                shift_a = input('Enter the x shifting value: ')
                shift_b = input('Enter the y shifting value: ')
                a_gcode = float(a_gcode) + float(shift_a)
                b_gcode = float(b_gcode) + float(shift_b)
                xy_check = False
                xyarm_cal = transform.coordinateTransfer(x_cal, y_cal, a_gcode, b_gcode, r_stage).T  
                swift.flush_cmd(wait_stop=True)
                swift.set_position(xyarm_cal[0, 0], xyarm_cal[0, 1], 10, speed=3000, timeout=20)
                time.sleep(1)
                swift.set_position(xyarm_cal[0, 0], xyarm_cal[0, 1], Z0, wait=True)
                swift.flush_cmd(wait_stop=True)
            
            else: 
                xy_check = True
                pass      
    print('x, y = ' + str(a_gcode) + ',' + str(b_gcode)) 
    return a_gcode, b_gcode

def discretisation(x_list, y_list, factor):
    x_line_mega = []
    y_line_mega = []
    
    for num, (x, y) in enumerate(zip(x_list, y_list)):
        print(num)
        if num < len(x_list) - 1:
            for n in range(factor):
                if n == 0:
                    x_line_mega.append(x)
                    y_line_mega.append(y)
                  
                elif n > 0 and n <= factor:
                    x_line_mega.append(x_list[num] + (x_list[num+1] - x_list[num])*n/factor)
                    y_line_mega.append(y_list[num] + (y_list[num+1] - y_list[num])*n/factor)
        if num == len(x_list) - 1:
            x_line_mega.append(x)
            y_line_mega.append(y)

    return x_line_mega, y_line_mega
      
# User-defined inputs
x_line = [-10, -10, -10]  # Enter x-coordinate in mm 
y_line = [-10, 0, 10]  # Enter y-coordinate in mm
spp = 30 # Printing speed 
Z0 = 67.5 # Starting z position
delaytime = 30000 # Delaytime in μs between steps of the stepper motor
printhead = 3 # Assigned number of the printhead in use, 1 - 4 (4 printheads)
stage = 1 # Assigned number of the stage
          # Petri dish '1': 35 mm, '2': 55 mm, '3': 90 mm, '4': 35 mm heating stage
          # Rectangular container '5': 33 mm, '6': 40 mm
          # '7': Standard glass slide
offset = [0, 0, Z0] # Setting as [0,0,Z0] means printing at the central point (a_gcode,b_gcde) of the stage at Z0


# Operation
d_f = 100 #By default, discretisation factor = 100
convert_to_arduino(delaytime) # Send delaytime to Arduino
x_line_mega, y_line_mega = discretisation(x_line, y_line, d_f) # Discretisation x, y coordinates

# Print to std out for checking!
isTerminate = input('Continue? Please type any key to continue [Y/n]: ')
if isTerminate == 'n':
    return_()

ab = [[282.5,146.5], [282,72.5], [285,-1], [280,-74]] #Approx. positions of printheads 1,2,3,4
stage_mega_r = [33, 44.5, 60, 36, 33, 38.2, 29.8]
a_coord = ab[printhead-1][0] # x coord of the printhead from uArm base, mm 
b_coord= ab[printhead-1][1] # y coord of the printhead from uArm base, mm
r_stage = stage_mega_r[stage-1]

a_coord, b_coord = calibration(Z0, a_coord, b_coord, r_stage)
xyarm_coord = transform.coordinateTransfer(x_line_mega, y_line_mega, a_coord, b_coord, r_stage).T     
print('Printing discretised coordinates: ')
for i in range(xyarm_coord.shape[0]):
    print(xyarm_coord[i])
print('')

# Print to std out for checking!
isTerminate = input('Continue? Please type any key to continue [Y/n]: ')
if isTerminate == 'n':
    return_()
       
# Start here-------
print('\nMove to the first position')
swift.flush_cmd(wait_stop=True)
swift.set_position(xyarm_coord[0, 0], xyarm_coord[0, 1], 10, speed=3000, timeout=20)
time.sleep(1)
swift.set_position(xyarm_coord[0, 0], xyarm_coord[0, 1], Z0, wait=True)
swift.flush_cmd(wait_stop=True)

# Print to std out for checking!
isTerminate = input('Continue? Please type any key to continue [Y/n]: ')
if isTerminate == 'n':
    return_()
    
print('\nStart printing')
swift.set_buzzer(frequency=3000, duration=0.1)
extrusion(printhead)
for x, y in xyarm_coord:
    swift.set_position(x, y, Z0,speed=spp, wait=True)
    swift.flush_cmd(wait_stop=True)
    extrusion(printhead)

time.sleep(1)
ArduinoSerial.write(b'5')
swift.flush_cmd(wait_stop=True)
time.sleep(1)        
swift.set_buzzer(frequency=3000, duration=0.1)
swift.flush_cmd(wait_stop=True)
print('\nPrinting finished')  

print('\nLowering nozzle to z = 10')
swift.set_position(z=10, speed=3000, wait=True)
print('......')


print('\nReturn to starting position.(around X95 Y0 Z20)')
swift.set_position(x=200, y=0, z=10, wait=True)
swift.flush_cmd()
swift.set_position(x=150, y=0, z=10, wait=True)
swift.flush_cmd()
swift.set_position(x=130, y=0, z=10, wait=True)
swift.set_position(z=20, wait=True)
swift.set_position(x=115, wait=True)
swift.set_position(x=105, wait=True)
swift.flush_cmd()
swift.flush_cmd()
swift.set_buzzer(frequency=1000, duration=0.1)
time.sleep(2)

print('Printing done!')
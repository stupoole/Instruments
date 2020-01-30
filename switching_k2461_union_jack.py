import numpy as np
import time
import matplotlib
import instruments
from tkinter import filedialog as dialog

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

pulse1_assignments = {"I+": "B", "I-": "F"}  # configuration for a pulse from B to F
pulse2_assignments = {"I+": "D", "I-": "H"}  # configuration for a pulse from D to H
measure_assignments = {"V1+": "C", "V1-": "G", "V2+": "B", "V2-": "D", "I+": "A", "I-": "E"}  # here V1 is Vxy
resistance_assignments = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0}


# Parameters to be changed
pulse_current = 10e-3  # set current
pulse_width = 1e-3  # set pulse duration
measure_current = 1e-4  # measurement current
measure_number = 100  # number of measurements to store in buffer when calling measure_n and read_buffer
num_loops = 2
measure_delay = measure_number * 0.18  # Not strictly necessary.



pos_time = np.array([])
neg_time = np.array([])
pos_rxx = np.array([])
neg_rxx = np.array([])
pos_rxy = np.array([])
neg_rxy = np.array([])

switch_box = instruments.SwitchBox()  # make a sb object
pulse_generator = instruments.K2461()  # make a k2461 object
keithley = instruments.K2000()  # make a k2000 object
balance_box = instruments.BalanceBox()
start_time = time.time()  # use this for the graphing only

# actually connect to the instruments
pulse_generator.connect()
switch_box.connect(4)
keithley.connect(3)
balance_box.connect(5)
balance_box.enable_all()
balance_box.reset_resistances()
balance_box.set_resistances(resistance_assignments)

for i in range(num_loops):
    # pulse in one direction
    switch_box.switch(pulse1_assignments)
    plt.pause(200e-3)  # pauses to allow changes to apply before telling them to do something else.
    pulse1_time = time.time()
    pulse_generator.pulse_current(pulse_current, pulse_width)  # sends a pulse with given params
    # print('Pulse current: ', pulse_current)  # just to show the set value.
    plt.pause(100e-3)
    switch_box.switch(measure_assignments)  # tells the switchbox to switch to a measurement assignment
    pulse_generator.measure_n(measure_current, measure_number)  # tells the k2461 to prepare a vxx measurement
    keithley.measure_n(measure_number)  # tells the k2000 to prepare a vxy measurement
    plt.pause(100e-3)
    keithley.trigger()  # actually starts measuring
    pulse_generator.trigger()  # actually starts the measuring
    # the instruments will wait for their "timeout" duration anyway but for large N manually waiting is necesasry
    plt.pause(measure_delay)
    # reads the values
    t, vxx = pulse_generator.read_buffer(measure_number)
    vxy = keithley.read_buffer()
    pos_time = np.append(pos_time, t + pulse1_time - start_time)
    pos_rxx = np.append(pos_rxx, vxx/measure_current)
    pos_rxy = np.append(pos_rxy, vxy/measure_current)

    # repeat of above with other pulse direction.
    switch_box.switch(pulse2_assignments)
    plt.pause(200e-3)
    pulse2_time = time.time()
    pulse_generator.pulse_current(pulse_current, pulse_width)
    plt.pause(200e-3)
    print('Pulse current: ', pulse_current)
    switch_box.switch(measure_assignments)
    pulse_generator.measure_n(measure_current, measure_number, 2)
    keithley.measure_n(measure_number, 0, 2)
    plt.pause(200e-3)
    keithley.trigger()
    pulse_generator.trigger()
    plt.pause(measure_delay)
    t, vxx = pulse_generator.read_buffer(measure_number)
    vxy = keithley.read_buffer()
    neg_time = np.append(neg_time, t + pulse2_time - start_time)
    neg_rxx = np.append(neg_rxx, vxx/measure_current)
    neg_rxy = np.append(neg_rxy, vxy/measure_current)

    # plotting
    plt.figure(1)
    plt.plot(pos_time, pos_rxx, 'k+')
    plt.plot(neg_time, neg_rxx, 'r+')
    plt.xlabel('Time (s)')
    plt.ylabel('R_xx (Ohms)')
    plt.draw()
    plt.figure(2)
    plt.plot(pos_time, pos_rxy, 'k+')
    plt.plot(neg_time, neg_rxy, 'r+')
    plt.xlabel('Time (s)')
    plt.ylabel('R_xy (Ohms)')
    plt.draw()


data = np.column_stack((pos_time, pos_rxx, pos_rxy, neg_time, neg_rxx, neg_rxy))
name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, data, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

plt.show()

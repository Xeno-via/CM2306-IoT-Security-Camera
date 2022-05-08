import os
import csv
import sys
import time
import json
from tkinter import simpledialog
import tkinter as tk

if sys.platform == 'uwp': #Check which part to import for the LCD
    import winrt_smbus as smbus
    bus = smbus.SMBus(1)
else:
    import smbus
    import RPi.GPIO as GPIO
    rev = GPIO.RPI_REVISION
    if rev == 2 or rev == 3:
        bus = smbus.SMBus(1)
    else:
        bus = smbus.SMBus(0)
        
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e
        
def setRGB(r,g,b): # A function for changing the colour of the backlight
    bus.write_byte_data(DISPLAY_RGB_ADDR,0,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,1,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR,4,r)
    bus.write_byte_data(DISPLAY_RGB_ADDR,3,g)
    bus.write_byte_data(DISPLAY_RGB_ADDR,2,b)


def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)


def setText(text): #A function for clearing the LCD and displaying new information on it
    textCommand(0x01) # clear display
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))


setRGB(0, 128, 64)
time.sleep(2)
Name = ""
lcd = json.dumps('Please input your name') # Asking the user to input their name
setText(lcd)
time.sleep(0.1)
ROOT = tk.Tk() # Creating a dialog box for the user to enter their name
ROOT.withdraw()

Name = simpledialog.askstring(title="New User", prompt="Enter your Name: ") # Getting the name from the user

f = open('Names.csv', 'a').write(',' + Name) # Addings their name to the Names.csv file


exec(open("datasetfacestuff.py").read()) # Run the datasetfacestuff.py file
exec(open("facetrainer.py").read()) # Run the facetrainer.py file
    
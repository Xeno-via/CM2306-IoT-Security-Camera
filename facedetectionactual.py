#!/usr/bin/env python3
import cv2
import numpy as np
import os
import sys
import json
import grovepi
import time
import math
import csv
import paho.mqtt.client as mqtt
import serial


try:
    bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=9600) # Try see if the bluetooth device is connected
except:
    print("Connect BlueTooth Device")


highestConfidence = 0 # Initialise variables / set the pin number of several components
os.environ['DISPLAY'] = ':0'
sensor = 4
blue = 0
buzzer = 8
grovepi.pinMode(buzzer, "OUTPUT")
names = []

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


DISPLAY_RGB_ADDR = 0x62 #Assign addresses to the LCD backlight and text
DISPLAY_TEXT_ADDR = 0x3e
recognizer = cv2.face.LBPHFaceRecognizer_create() # Create a face recogniser object
recognizer.read('trainer/trainer.yml') # Assign the trained file to the face recogniser
cascadePath = "Cascades/haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath);

font = cv2.FONT_HERSHEY_SIMPLEX # Set font

# A function for changing the colour of the backlight
def setRGB(r,g,b):
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


#iniciate id counter
id = 0
confidenceCounter = 0
UnknownCounter = 0


# Get the names from the Names.csv file
with open('Names.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in spamreader:
        names = names + row
    

# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video widht
cam.set(4, 480) # set video height

# Define min window size to be recognized as a facethings
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)
sys.stdout.write("Working")

setRGB(0, 128, 64)
time.sleep(2)

lcd = json.dumps('Please Look At The Camera') # Providing guidance to the user
setText(lcd)
time.sleep(0.1)

while True:
    ret, img =cam.read()  # Get an image from the camera
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) # convert the image to grayscale
    k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video

    faces = faceCascade.detectMultiScale( 
        gray,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
       )

    for(x,y,w,h) in faces:
        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2) # Draw a rectangle around the face(s)
        id, confidence = recognizer.predict(gray[y:y+h,x:x+w]) # Get the confidence and ID from the predictor

        # Check if confidence is less than 100 ==> "0" is perfect match 
        if (confidence < 100):
            id = names[id] #Get the name using the ID
            confidence = round(100 - confidence) # Change the confidence into a percentile
            if (confidence > 30) and (confidenceCounter < 30): # Check the classifier has a greater than 30 confidence that it is the user, 30 times
                if (highestConfidence < confidence): # Only record the highest confidence 
                    highestConfidence = confidence
                confidenceCounter = confidenceCounter + 1
            elif (confidence > 30) and (confidenceCounter >= 30): # Once the classifier is sure
                confidenceCounter = 0
                json_telemetry = json.dumps({"Sign In":"Success", "User ID":id, "Confidence":highestConfidence, "Sign In True/False": 1}) # Create telemetry json dump
                with open('json_telemetry.json', 'w') as outfile:
                    json.dump(json_telemetry, outfile) # Write the json to a file, to be read by another program which handles telemetry
                lcd = json.dumps('Welcome '+ id) # Feedback to user
                setText(lcd)
                time.sleep(0.1)
                b = bytes("1", 'utf-8') # Create a "1" as a byte
                bluetoothSerial.write(b) # Send the "1" over bluetooth to the arduino, to communicate to open the servo

                while (confidenceCounter < 30): # Beep the buzzer a few times for feedback to the user
                    grovepi.digitalWrite(buzzer,1)
                    time.sleep(0.05)
                    grovepi.digitalWrite(buzzer,0)
                    time.sleep(0.05)
                    confidenceCounter = confidenceCounter + 1

                k=27 # Break the program
                
                
            confidence = "  {0}%".format(confidence)
        else:
            id = "Unknown" # If classifier is not confident, then the ID is unknown
            
            if (UnknownCounter < 30):
                UnknownCounter = UnknownCounter + 1 # Make sure the classifier is sure it is unknown
            else:
                UnknownCounter = 0
                confidence = round(100 - confidence)
                json_telemetry = json.dumps({"Sign In": "Failure" ,"Confidence": confidence, "User ID": "Unknown", "Sign In True/False": 0})# Create telemetry data
                with open('json_telemetry.json', 'w') as outfile:
                    json.dump(json_telemetry, outfile) # Write the telemetry to the json file
                lcd = json.dumps(id) # Set LCD to "Unknown"
                setText(lcd)
                time.sleep(0.1)
                grovepi.digitalWrite(buzzer,1) # One long beep for feedback to user
                time.sleep(1)
                grovepi.digitalWrite(buzzer,0)
                k=27 # Break the program

            

        cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2) # Place text with the ID and confidence on the box around the face
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)

    cv2.imshow('camera',img) # Show the camera image with the drawings ontop


    if k == 27:
        break

# Do a bit of cleanup
print("\n [INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()
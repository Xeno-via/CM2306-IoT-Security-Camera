import cv2
import os
import glob
import grovepi

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
ultrasonic_ranger = 3 # Assing address for the ranger

setRGB(0, 128, 64) #Set the backlight for the lcd
time.sleep(2)

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


cam = cv2.VideoCapture(0) # Starting the cv2 video capture
cam.set(3, 640) # set video width
cam.set(4, 480) # set video height

face_detector = cv2.CascadeClassifier('Cascades/haarcascade_frontalface_default.xml') # Pointing the classifier to the classifier directory

# For each person, enter one numeric face
with open('latest_id.txt') as f: # getting the latest ID that was created, and writing the updated ID back to the txt file
    latest_id = f.readline()
face_id = int(latest_id) + 1
with open('latest_id.txt', 'w') as f:
    f.write(str(face_id))

lcd = json.dumps('Please look at camera and wait ') # Sending this text to the LCD
setText(lcd)
time.sleep(0.1)
# Initialize individual sampling face count
count = 0

while(True):
    distance = grovepi.ultrasonicRead(ultrasonic_ranger) # Startup of the rangefinder
    print(distance)
    time.sleep(0.1)
    ret, img = cam.read() # Get an image from the camera
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # convert the image to grayscale
    faces = face_detector.detectMultiScale(gray, 1.3, 5) # detect a face within the grayscale image

    for (x,y,w,h) in faces:
        cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2) # draw a rectangle around the face
        
        if distance < 100: # If the user is less than 1m away from the camera 
            count += 1
            # Save the captured image into the datasets folder
            cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w]) # Save the image to the dataset
            cv2.imshow('image', img)
            lcd = json.dumps('Good Distance, Stand Still') # Feedback for the user
            setText(lcd)
            time.sleep(0.1)
        else:
            lcd = json.dumps('Stand closer to the camera') # Feedback for the user
            setText(lcd)
            time.sleep(0.1)

    k = cv2.waitKey(100) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        break
    elif count >= 30: # Take 30 face sample and stop video
         break

# Do a bit of cleanup
lcd = json.dumps('Completed Face Capture')
setText(lcd)
cam.release()
cv2.destroyAllWindows()
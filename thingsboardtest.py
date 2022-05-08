import paho.mqtt.client as mqtt
import json
import os
import ssl, socket
import certifi

telemetry_data = json.dumps("{}")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc, *extra_params):
   print('Connected with result code '+str(rc))
   # Subscribing in on_connect() means that if we lose the connection and
   # reconnect then subscriptions will be renewed.
   client.subscribe('v1/devices/me/attributes')
   client.subscribe('v1/devices/me/attributes/response/+')
   client.subscribe('v1/devices/me/rpc/request/+')
   client.subscribe('v1/devices/me/telemetry')


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
   print('Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload))
   payload = json.loads(msg.payload) # Get the payload message from thingsboard
   
   if msg.topic.startswith( 'v1/devices/me/rpc/request/'): # The json payload has a few parameters, if this one is "request" it means a button has been pushed
       if payload['params'] == 'DetectFace': # Each button has a different parameter, therefore detect for either DetectFace or NewFace
           os.system("python3 facedetectionactual.py") # Run the facedetectionactual.py script

       elif payload['params'] == 'NewFace':
           os.system("python3 FaceDetectionRunner.py") # Run the FaceDetectionRunner.py script
       
       
       with open('json_telemetry.json') as json_file:
           telemetry_data = json.load(json_file) # Load the telemetry data from the json file
           
       print(telemetry_data)
       client.publish('v1/devices/me/telemetry', telemetry_data, 1) # Publish the telemetry data created
       requestId = msg.topic[len('v1/devices/me/rpc/request/'):len(msg.topic)] # Get the ID of the msg from the button
       print('This is a RPC call. RequestID: ' + requestId + '. Going to reply now!')
       client.publish('v1/devices/me/rpc/response/' + requestId, "{\"value1\":\"A\", \"value2\":\"B\"}", 1) # Respond to the button as to avoid a timeout
       



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.publish('v1/devices/me/attributes/request/1', "{\"clientKeys\":\"model\"}", 1)
client.username_pw_set('U1RfKYNvmDmBSpcQzR8F')
client.connect('demo.thingsboard.io', 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
client.loop_forever()
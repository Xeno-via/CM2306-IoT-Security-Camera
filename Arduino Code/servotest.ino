#include <Servo.h>
#include <SoftwareSerial.h>//Software Serial Port
#define RxD         8
#define TxD         9


const int buttonPin = 4;  // the number of the pushbutton pin, D4
int buttonState;          // the state of the button


Servo myservo;  // create servo object to control a servo
// twelve servo objects can be created on most boards

int pos = 0;    // variable to store the servo position
SoftwareSerial blueToothSerial(RxD, TxD);

void setup() {
  Serial.begin(9600);
  while(!Serial){
    ;
  }
  Serial.print("Started/n");
  pinMode(RxD, INPUT);
  pinMode(TxD, OUTPUT);
  setupBlueToothConnection();
  Serial.flush();
  blueToothSerial.flush();
}

void loop() {
  char recvChar;
  static unsigned char state = 0;
  if(blueToothSerial.available()>0){
    String a = String(blueToothSerial.read());
    Serial.print(a);
    if(a=="49"){
        myservo.attach(5);
        Serial.print("startturn");
        myservo.write(180);
        delay(1000);
        Serial.print("endturn");
        myservo.write(0);
        delay(1000);
        myservo.detach();
        //hi
    }
  }
  
  delay(200);
}

void setupBlueToothConnection()
{ 
  blueToothSerial.begin(9600);
  
  blueToothSerial.print("AT");
  delay(2000); 
  
  blueToothSerial.print("AT+BAUD4");
  delay(2000);
 
  blueToothSerial.print("AT+ROLES");
  delay(2000); 
  
  blueToothSerial.print("AT+NAMESlave");   // set the bluetooth name as "Slave" ,the length of bluetooth name must less than 12 characters.
  delay(2000);
  
  blueToothSerial.print("AT+AUTH1"); 
  delay(2000);
 
  blueToothSerial.flush();
  Serial.print("Finished\n");
}

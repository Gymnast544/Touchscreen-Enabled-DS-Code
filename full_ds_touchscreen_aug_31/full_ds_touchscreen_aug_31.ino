#define LEFT_SHOULDER_PIN 2
#define DPAD_RIGHT_PIN 3
#define DPAD_UP_PIN 4
#define DPAD_LEFT_PIN 5
#define DPAD_DOWN_PIN 6
#define X_PIN 7
#define Y_PIN 8
#define B_PIN 9

#define SELECT_PIN 16
#define A_PIN 17
#define RIGHT_SHOULDER_PIN 18
#define START_PIN 19
#define XPLUS A9
#define YPLUS A8
#define YMINUS A7
#define XMINUS A6


#define PWR 15

#define LID 24

#define SYNC 0


#define CS_PIN 10
#define MOSI_PIN 11
#define MISO_PIN 12
#define SCK_PIN 13
#define PEN 14

int mode = 0;

int pinstatus[12] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}; //Sets all button statuses to pressed, which is the default when the DS is off

int pins[12] = {A_PIN, B_PIN, X_PIN, Y_PIN, DPAD_LEFT_PIN, DPAD_RIGHT_PIN, DPAD_UP_PIN, DPAD_DOWN_PIN, LEFT_SHOULDER_PIN, RIGHT_SHOULDER_PIN, START_PIN, SELECT_PIN};

char pindown[12] = {10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21};//Bytes which are sent when a button is pressed
char pinup[12] = {30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41};//Bytes which are sent when a button is released



void resetbuttons() {
  //Setting all button modes to input
  for(byte i=0;i<12;i++){
    pinMode(pins[i], INPUT);
  }

  //Resets the status of each pin
  for (int i = 0; i < 12; i++) {
    pinstatus[i] = 1;
  }

}

void setup() {
  // put your setup code here, to run once:
  resetbuttons();
  Serial.begin(115200);

}

void loop() {
  // put your main code here, to run repeatedly:
  serialInterface();
  pinMode(DPAD_RIGHT_PIN, OUTPUT);
  digitalWrite(DPAD_RIGHT_PIN, LOW);
  delay(500);
  digitalWrite(DPAD_RIGHT_PIN, HIGH);
  delay(500);
  //Serial.println(digitalRead(DPAD_RIGHT_PIN));
  //delay(500);
}



void serialInterface() {
  for (int i = 0; i < Serial.available(); i++) {
    //Checks all incoming bytes
    int incomingbyte = Serial.read();
    checkMode(incomingbyte);
    //Serial.write(incomingbyte);
    if (incomingbyte < 25) {
      //Electronically pressing a button
      int buttonnum = incomingbyte - 10;
      pinstatus[buttonnum] = -1;//indicating to the input loop that the button is pressed
      pinMode(pins[buttonnum], OUTPUT);
      digitalWrite(pins[buttonnum], LOW);
    } else {
      //Stopping electronically pressing a button
      int buttonnum = incomingbyte - 30;
      pinstatus[buttonnum] = 1;//Setting the button status to released
      pinMode(pins[buttonnum], INPUT);
    }

  }
  for (int i = 0; i < 12; i++) {
    if (pinstatus[i] > -1) {
      //getting input
      int pinread = digitalRead(pins[i]);
      if (pinread != pinstatus[i]) {
        if (pinread) {
          Serial.write(pinup[i]);
        }
        else {
          Serial.write(pindown[i]);
        }
      }
      pinstatus[i] = pinread;
    }

  }
}



void checkMode(int incomingbyte) {
  //Checks any incoming bytes to see if they're a mode switching byte

  if (incomingbyte == 100) {
    //Performs the "handshake test"
    //If it receives byte 100, it will send byte 101 - this is the verification that the desktop program uses to verify that it's an Input Interface connected
    Serial.write(101);
  }
}

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



volatile short numclocks = 0;
volatile boolean bitbuffer[20];


volatile boolean xbits[16] = {0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean ybits[16] = {0, 1, 1, 1, 1, 1, 1, 1,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean bbits[16] = {0, 0, 0, 1, 0, 1, 1, 1,    1, 0, 0, 0, 0, 0, 0, 0};

volatile short xpos = 128; 
volatile short ypos = 128;


volatile boolean updatetouch = false;
boolean xbuffer[16] = {0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
boolean ybuffer[16] = {0, 1, 1, 1, 1, 1, 1, 1,    0, 0, 0, 0, 0, 0, 0, 0};

volatile boolean touchrunning = false;

  

void resetbuttons() {
  //Setting all button modes to input
  for(byte i=0;i<12;i++){
    pinMode(pins[i], INPUT_PULLUP);
  }

  //Resets the status of each pin
  for (int i = 0; i < 12; i++) {
    pinstatus[i] = 1;
  }

}

void setup() {
  // put your setup code here, to run once:
  resetbuttons();
  setupTouchscreenPins();
  attachTouchscreenInterrupts();
  Serial.begin(115200);

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


void setupTouchscreenPins() {
  // put your setup code here, to run once:


  pinMode(MOSI_PIN, INPUT);
  pinMode(MISO_PIN, INPUT);
  pinMode(PEN, OUTPUT);
  digitalWrite(PEN, LOW);
  pinMode(CS_PIN, INPUT);
  pinMode(SYNC, INPUT);
  Serial.begin(115200);
  Serial.println("Starting...");
  while(digitalReadFast(SYNC)==1){
    //wait until the next frame
  }
}


void attachTouchscreenInterrupts(){
  attachInterrupt(SYNC, syncinterrupt, FALLING);
  attachInterrupt(CS_PIN, CSfall, FALLING);
}



FASTRUN void CSfall() {
  attachInterrupt(CS_PIN, CSrise, RISING);
  attachInterrupt(SCK_PIN, clockchanging, RISING);
  pinMode(MISO_PIN, OUTPUT);
  digitalWriteFast(MISO_PIN, LOW);
  touchrunning = true;
  //Serial.println("F");
}


FASTRUN void CSrise() {
  attachInterrupt(CS_PIN, CSfall, FALLING);
  detachInterrupt(SCK_PIN);
  pinMode(MISO_PIN, INPUT);
  touchrunning = false;
  //Serial.println("R");
  /*
  for(int i=0;i<8;i++){
    Serial.print(bitbuffer[i]);
  }*/
  numclocks = 0;
}


FASTRUN void clockchanging() {
  bitbuffer[numclocks] = digitalReadFast(MOSI_PIN);
  //Serial.print();
  //digitalWriteFast(MISO_PIN, bitbuffer[numclocks]);
  numclocks++;
  if(numclocks>7){
    numclocks = 0;
    if(bitbuffer[3]){
      //it's an x or y pos thingy
      if(bitbuffer[1]){
        //x pos
        digitalWriteFast(MISO_PIN, xbits[0]);
        attachInterrupt(SCK_PIN, clockchangex, FALLING);
      }else{
        //y pos
        digitalWriteFast(MISO_PIN, ybits[0]);
        attachInterrupt(SCK_PIN, clockchangey, FALLING);
      }
    }else if(bitbuffer[5]){
      //it's a beginning or end CS cycle
      digitalWriteFast(MISO_PIN, bbits[0]);
      attachInterrupt(SCK_PIN, clockchangeb, FALLING);
    }else{
      //don't do anything
      detachInterrupt(SCK_PIN);
    }
  }
}



//the clockchange x, y, and b functions are pretty much the same, with the exception that they pull data from a different list, for efficiency
FASTRUN void clockchangex(){
  digitalWriteFast(MISO_PIN, xbits[numclocks]);
  numclocks++;
  if(numclocks>15){
    numclocks = 0;
  }
}


FASTRUN void clockchangey(){
  digitalWriteFast(MISO_PIN, ybits[numclocks]);
  numclocks++;
  if(numclocks>15){
    numclocks = 0;
  }
}


FASTRUN void clockchangeb(){
  digitalWriteFast(MISO_PIN, bbits[numclocks]);
  numclocks++;
  if(numclocks>15){
    numclocks = 0;
  }
}

volatile boolean waitforsync = false;

FASTRUN void syncinterrupt() {
  waitforsync = false;
}



FASTRUN void loop() {
  if(Serial.available()>0){
    waitforsync = true;
    while(waitforsync){
      //wait
    }
    while(Serial.available()>0){
    byte inbyte = Serial.read();
    if(inbyte == 32){
      //touchscreen click
      digitalWrite(PEN, LOW);
      Serial.print("wrote");
    }else if(inbyte == 33){
      //touchscreen release
      digitalWriteFast(PEN, HIGH);
    }else if(inbyte == 30){
      //adjusting x  pos
      //we need 16 bits - in order to get this to be more consistent I will just send 16 bytes over

      for (byte i=0;i<16;i++){
        xbuffer[i] = 0;//just resetting the list
      }
      byte numbytesreceived = 0;
      boolean receiving = true;
      byte index = 0;
      while(receiving){
        Serial.write(numbytesreceived);//letting the pc know how many bytes the DS has gotten - hopefully useful in case of a dropped bit somewhere
        while(Serial.available()==0){
          //pass - waiting until we're sure we have data in
        }
        inbyte = Serial.read();
        
        //digitalWrite(DPAD_DOWN_PIN, LOW);
        /*
        for(byte pos = 7;pos>=0;pos--){
          Serial.print("X");
          //incrementing backwards on the byte
          xbuffer[index] = bitRead(inbyte, pos);
          index++;
          Serial.print("B");
        }
        Serial.print("A");
        */
        numbytesreceived++;
        if(numbytesreceived==2){
          receiving = false;
        }
        
        
      }
      updatetouch = true;


      
    }else if(inbyte == 31){
      //adjusting y pos
      //we need 16 bits - in order to get this to be more consistent I will just send 16 bytes over

      for (byte i=0;i<16;i++){
        ybuffer[i] = 0;//just resetting the list
      }
      byte numbytesreceived = 0;
      boolean receiving = true;
      while(receiving){
        Serial.write(numbytesreceived);//letting the pc know how many bits the DS has gotten - hopefully useful in case of a dropped bit somewhere
        while(Serial.available()==0){
          //pass - waiting until we're sure we have data in
        }
        inbyte = Serial.read();
        if(inbyte==50){
          ybuffer[numbytesreceived] = 0;
          numbytesreceived++;
        }else if(inbyte==51){
          ybuffer[numbytesreceived] = 1;
          numbytesreceived++;
        }else if(inbyte == 68){
          //done with the transmission
          receiving = false;
        }
      }
      updatetouch = true;
    }
  }
  }
}

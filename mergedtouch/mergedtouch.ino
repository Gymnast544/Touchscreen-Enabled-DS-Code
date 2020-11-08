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





struct frameData{
  bool a;
  bool b;
  bool x;
  bool y;
  bool l;
  bool r;
  bool du;
  bool dd;
  bool dl;
  bool dr;
  bool startbutton;
  bool selectbutton;
  bool pen;
  bool lid;
  bool pwr;
  bool framexbits[16] = {0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
  bool frameybits[16] = {0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
};




int pins[12] = {A_PIN, B_PIN, X_PIN, Y_PIN, DPAD_LEFT_PIN, DPAD_RIGHT_PIN, DPAD_UP_PIN, DPAD_DOWN_PIN, LEFT_SHOULDER_PIN, RIGHT_SHOULDER_PIN, START_PIN, SELECT_PIN};


volatile short numclocks = 0;
volatile byte numpolls = 0;
volatile boolean bitbuffer[20];


volatile boolean xbits[16] = {0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean ybits[16] = {0, 1, 1, 1, 1, 1, 1, 1,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean bbits[16] = {0, 0, 0, 1, 0, 1, 1, 1,    1, 0, 0, 0, 0, 0, 0, 0};

void FASTRUN executeFrame(frameData Frame){
  memcpy(xbits, Frame.framexbits, 16);//Tested and works - reassigns the array correctly 
  memcpy(ybits, Frame.frameybits, 16);
}

void resetbuttons() {
  //Setting all button modes to input
  for(byte i=0;i<12;i++){
    pinMode(pins[i], INPUT_PULLUP);
  }
}

void setup() {
  // put your setup code here, to run once:
  resetbuttons();
  setupTouchscreenPins();
  attachTouchscreenInterrupts();
  Serial.begin(115200);

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
  pinMode(MOSI_PIN, INPUT);
  pinMode(MISO_PIN, INPUT);
  pinMode(PEN, OUTPUT);
  digitalWrite(PEN, HIGH);
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

FASTRUN void syncinterrupt(){
  numpolls=0;
}

FASTRUN void CSfall() {
  attachInterrupt(CS_PIN, CSrise, RISING);
  attachInterrupt(SCK_PIN, clockchanging, RISING);
  pinMode(MISO_PIN, OUTPUT);
  digitalWriteFast(MISO_PIN, LOW);
}


FASTRUN void CSrise() {
  attachInterrupt(CS_PIN, CSfall, FALLING);
  detachInterrupt(SCK_PIN);
  pinMode(MISO_PIN, INPUT);
  numclocks = 0;
  numpolls++;
}


FASTRUN void clockchanging() {
  bitbuffer[numclocks] = digitalReadFast(MOSI_PIN);
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


FASTRUN void loop() {
  if(Serial.available()>0){
    byte inbyte = Serial.read();
    if(inbyte == 30){
      frameData inputFrame;
      //adjusting x  pos
      //we need 16 bits - in order to get this to be more consistent I will just send 16 bytes over
      byte numbytesreceived = 0;
      boolean receiving = true;
      while(receiving){
        Serial.write(numbytesreceived);//letting the pc know how many bits the DS has gotten - hopefully useful in case of a dropped bit somewhere
        while(Serial.available()==0){
          //pass - waiting until we're sure we have data in
        }
        inbyte = Serial.read();
        if(inbyte==50){
          inputFrame.framexbits[numbytesreceived] = 0;
          numbytesreceived++;
        }else if(inbyte==51){
          inputFrame.framexbits[numbytesreceived] = 1;
          numbytesreceived++;
        }else if(inbyte == 68){
          //done with the transmission
          receiving = false;
        } 
      }
      while(Serial.read()!=31){}
      //adjusting y pos
      //we need 16 bits - in order to get this to be more consistent I will just send 16 bytes over
      numbytesreceived = 0;
      receiving = true;
      while(receiving){
        Serial.write(numbytesreceived);//letting the pc know how many bits the DS has gotten - hopefully useful in case of a dropped bit somewhere
        while(Serial.available()==0){
          //pass - waiting until we're sure we have data in
        }
        inbyte = Serial.read();
        if(inbyte==50){
          inputFrame.frameybits[numbytesreceived] = 0;
          numbytesreceived++;
        }else if(inbyte==51){
          inputFrame.frameybits[numbytesreceived] = 1;
          numbytesreceived++;
        }else if(inbyte == 68){
          //done with the transmission
          receiving = false;
        }
      }
      executeFrame(inputFrame);
    }else if(inbyte == 32){
      //touchscreen click
      digitalWriteFast(PEN, LOW);
    }else if(inbyte == 33){
      //touchscreen release
      digitalWriteFast(PEN, HIGH);
    }
  }
  
}

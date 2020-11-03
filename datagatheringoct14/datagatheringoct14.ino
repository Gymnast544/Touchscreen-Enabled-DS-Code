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

#define firstthreebitmask 7

int mode = 0;


int pins[12] = {A_PIN, B_PIN, X_PIN, Y_PIN, DPAD_LEFT_PIN, DPAD_RIGHT_PIN, DPAD_UP_PIN, DPAD_DOWN_PIN, LEFT_SHOULDER_PIN, RIGHT_SHOULDER_PIN, START_PIN, SELECT_PIN};


volatile byte numpolls = 0;

volatile short numclocks = 0;
volatile bool bitbuffer[20];

//This is what the touchscreen spoofing code reads from for the data
volatile bool xbits[16] = {0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
volatile bool ybits[16] = {0, 1, 1, 1, 1, 1, 1, 1,    0, 0, 0, 0, 0, 0, 0, 0};
volatile bool bbits[16] = {0, 0, 0, 1, 0, 1, 1, 1,    1, 0, 0, 0, 0, 0, 0, 0};



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

void FASTRUN executeFrame(frameData Frame){
  if(Frame.a){
    //button isn't pressed
    pinMode(A_PIN, INPUT);
  }else{
    pinMode(A_PIN, OUTPUT);
    digitalWrite(A_PIN, LOW);
  }
  /*
  digitalWriteFast(B_PIN, Frame.b);
  digitalWriteFast(X_PIN, Frame.x);
  digitalWriteFast(Y_PIN, Frame.y);
  digitalWriteFast(START_PIN, Frame.startbutton);
  digitalWriteFast(SELECT_PIN, Frame.selectbutton);
  digitalWriteFast(DPAD_UP_PIN, Frame.du);
  digitalWriteFast(DPAD_DOWN_PIN, Frame.dd);
  digitalWriteFast(DPAD_LEFT_PIN, Frame.dl);
  digitalWriteFast(DPAD_RIGHT_PIN, Frame.dr);
  digitalWriteFast(PEN, Frame.pen);
  digitalWriteFast(LID, Frame.lid);*/
  memcpy(xbits, Frame.framexbits, 16);//Tested and works - reassigns the array correctly 
  memcpy(ybits, Frame.frameybits, 16);
  //std::copy(Frame.framexbits + 0, Frame.framexbits+16, xbits);
  //bool* xbits[16] = Frame.framexbits;
  //ybits = Frame.frameybits;
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
  //attachTouchscreenInterrupts();
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
  // put your setup code here, to run once:


  pinMode(MOSI_PIN, INPUT);
  pinMode(MISO_PIN, INPUT);
  pinMode(PEN, OUTPUT);
  digitalWrite(PEN, LOW);
  pinMode(CS_PIN, INPUT);
  pinMode(SYNC, INPUT);
  Serial.begin(115200);
  Serial.println("Starting...");
  Serial.write(245);
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
  //Serial.println("F");
}


FASTRUN void CSrise() {
  attachInterrupt(CS_PIN, CSfall, FALLING);
  detachInterrupt(SCK_PIN);
  pinMode(MISO_PIN, INPUT);
  //Serial.println("R");

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


FASTRUN void syncinterrupt() {
  //update buttons
}



FASTRUN void loop() {
  if(Serial.available()>0){
    byte inByte = Serial.read();
    Serial.write("X");
    Serial.println(int(inByte));
    if (inByte==245){
      Serial.write("Y");
      frameData inputFrame;
      //starting with a data transfer, starting with buttons
      boolean transferring = true;
      while(transferring==true){
        if(Serial.available()>0){
          inByte = Serial.read();
          byte identifier = inByte & firstthreebitmask;
          if(identifier==7){
            //move onto the next section
            Serial.write("d");
            transferring=false;
          }else if(identifier == 0){
            //first data byte
            //ranges from 3 to 8
            inputFrame.a = bitRead(inByte, 3);
            Serial.write("a");
          }else if(identifier == 4){
            //second data byte
            Serial.write("b");
          }else if(identifier == 2){
            //third data byte
            Serial.write("c");
          }
        }
      }
      Serial.write("y");
      //moving onto touchscreen
      transferring = true;
      while(transferring==true){
        if(Serial.available()>0){
          inByte = Serial.read();
          byte identifier = inByte & firstthreebitmask;
          if(inByte==255){
            //finishing the transfer
            Serial.write("k");
            transferring=false;
          }else if(identifier == 0){
            //first data byte
            Serial.write("e");
          }else if(identifier == 4){
            //second data byte
            Serial.write("f");
          }else if(identifier == 2){
            //third data byte
            Serial.write("g");
          }else if(identifier == 6){
            //fourth data byte
            Serial.write("h");
          }else if(identifier == 1){
            //fifth data byte
            Serial.write("i");
          }else if(identifier == 5){
            //sixth data byte
            Serial.write("j");
          }
        }
      }
      Serial.write("x");
      executeFrame(inputFrame);
    }
  }
}

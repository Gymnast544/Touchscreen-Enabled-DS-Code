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

int pins[12] = {A_PIN, B_PIN, X_PIN, Y_PIN, DPAD_LEFT_PIN, DPAD_RIGHT_PIN, DPAD_UP_PIN, DPAD_DOWN_PIN, LEFT_SHOULDER_PIN, RIGHT_SHOULDER_PIN, START_PIN, SELECT_PIN};

#define firstthreebitmask 7

volatile short numclocks = 0;
volatile byte numpolls = 0;
volatile boolean bitbuffer[20];

volatile boolean xbits[16] = {0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean ybits[16] = {0, 1, 1, 1, 1, 1, 1, 1,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean bbits[16] = {0, 0, 0, 1, 0, 1, 1, 1,    1, 0, 0, 0, 0, 0, 0, 0};

struct frameData {
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

void FASTRUN executeFrame(frameData Frame) {
  digitalWriteFast(PEN, Frame.pen);
  if(Frame.pen==0){
    Serial.write(190);//letting it know that we're not spoofing touchscreen, so no tight timing
  }
  else{
    Serial.write(189);
  }
  //Can't just digitalWrite to the button pins, each line is required (can't use a loop because I'm using digitalWriteFast)
  if (Frame.a) {
    //button isn't pressed
    pinMode(A_PIN, INPUT);
  } else {
    pinMode(A_PIN, OUTPUT);
    digitalWriteFast(A_PIN, LOW);
  }
  if (Frame.b) {
    //button isn't pressed
    pinMode(B_PIN, INPUT);
  } else {
    pinMode(B_PIN, OUTPUT);
    digitalWriteFast(B_PIN, LOW);
  }
  if (Frame.x) {
    //button isn't pressed
    pinMode(X_PIN, INPUT);
  } else {
    pinMode(X_PIN, OUTPUT);
    digitalWriteFast(X_PIN, LOW);
  }
  if (Frame.y) {
    //button isn't pressed
    pinMode(Y_PIN, INPUT);
  } else {
    pinMode(Y_PIN, OUTPUT);
    digitalWriteFast(Y_PIN, LOW);
  }
  if (Frame.startbutton) {
    //button isn't pressed
    pinMode(START_PIN, INPUT);
  } else {
    pinMode(START_PIN, OUTPUT);
    digitalWriteFast(START_PIN, LOW);
  }
  if (Frame.selectbutton) {
    //button isn't pressed
    pinMode(SELECT_PIN, INPUT);
  } else {
    pinMode(SELECT_PIN, OUTPUT);
    digitalWriteFast(SELECT_PIN, LOW);
  }
  if (Frame.l) {
    //button isn't pressed
    pinMode(LEFT_SHOULDER_PIN, INPUT);
  } else {
    pinMode(LEFT_SHOULDER_PIN, OUTPUT);
    digitalWriteFast(LEFT_SHOULDER_PIN, LOW);
  }
  if (Frame.r) {
    //button isn't pressed
    pinMode(RIGHT_SHOULDER_PIN, INPUT);
  } else {
    pinMode(RIGHT_SHOULDER_PIN, OUTPUT);
    digitalWriteFast(RIGHT_SHOULDER_PIN, LOW);
  }
  if (Frame.du) {
    //button isn't pressed
    pinMode(DPAD_UP_PIN, INPUT);
  } else {
    pinMode(DPAD_UP_PIN, OUTPUT);
    digitalWriteFast(DPAD_UP_PIN, LOW);
  }
  if (Frame.dd) {
    //button isn't pressed
    pinMode(DPAD_DOWN_PIN, INPUT);
  } else {
    pinMode(DPAD_DOWN_PIN, OUTPUT);
    digitalWriteFast(DPAD_DOWN_PIN, LOW);
  }
  if (Frame.dl) {
    //button isn't pressed
    pinMode(DPAD_LEFT_PIN, INPUT);
  } else {
    pinMode(DPAD_LEFT_PIN, OUTPUT);
    digitalWriteFast(DPAD_LEFT_PIN, LOW);
  }
  if (Frame.dr) {
    //button isn't pressed
    pinMode(DPAD_RIGHT_PIN, INPUT);
  } else {
    pinMode(DPAD_RIGHT_PIN, OUTPUT);
    digitalWriteFast(DPAD_RIGHT_PIN, LOW);
  }
  /*
  if (Frame.lid) {
    //button isn't pressed
    pinMode(LID, INPUT);
  } else {
    pinMode(LID, OUTPUT);
    digitalWriteFast(A_PIN, LOW);
  }*/
  //TODO: IMPLEMENT POWER
  memcpy(xbits, Frame.framexbits, 16);//Tested and works - reassigns the array correctly
  memcpy(ybits, Frame.frameybits, 16);
}

void setup() {
  // put your setup code here, to run once:
  resetbuttons();
  setupTouchscreenPins();
  Serial.begin(115200);
}


volatile byte pollsperframe;
bool poweronstart;

#define queue_size 80
#include <LinkedList.h>
volatile LinkedList<frameData> framequeue = LinkedList<frameData>();

void FASTRUN TASsyncinterrupt(){
  numpolls=0;
  Serial.write("Y");
  executeFrame(framequeue.shift());//pulls the next frame out of the queue
  Serial.write("X");
}

void FASTRUN batteryPowerOn() {
  pinMode(PWR, INPUT);
  //Serial.write("G");
  if (digitalRead(PWR)) {
    while (digitalRead(PWR)) {
      //wait until it drops down
    }
  }
  while (!digitalRead(PWR)) {
    //Waiting until the Power button is pulled up (battery is inserted into console)
    //Serial.write(digitalRead(PWR)+50);
  }
  pinMode(PWR, OUTPUT);
  digitalWrite(PWR, LOW);
  delay(200);
}

void loop() {
  if (Serial.available() > 0) {
    byte inByte = Serial.read();
    if (inByte == 50) {
      Serial.write("X");
      //time to start a TAS playback
      while (Serial.available() == 0) {}
      pollsperframe = Serial.read();
      while (Serial.available() == 0) {}
      inByte = Serial.read();
      if (inByte == 65) {
        //Gonna start asap
        poweronstart = false;
      } else {
        //Gonna start on battery insertion
        poweronstart = true;
      }
      Serial.write(queue_size);
      while (framequeue.size() < queue_size) {
        Serial.write(framequeue.size());
        while (Serial.available() == 0) {}
        framequeue.add(frameTransfer());
      }
      Serial.write(180);//signals that it's ready to start
      while (Serial.available() == 0) {}//waiting for a single byte to start
      //starting TAS
      attachInterrupt(SYNC, TASsyncinterrupt, FALLING);
      attachInterrupt(CS_PIN, CSfall, FALLING);
      if(poweronstart){
        batteryPowerOn();
        Serial.write("z");
      }
      Serial.write("R");
      while(framequeue.size()>0){
        Serial.write("S");
        //continue running the TAS
        if(Serial.available()>0){
          framequeue.add(frameTransfer());
        }
      }
      Serial.write(230);//denoting the end of playback
    }
  }
}



void resetbuttons() {
  //Setting all button modes to input
  for (byte i = 0; i < 12; i++) {
    pinMode(pins[i], INPUT_PULLUP);
  }
}

void setupTouchscreenPins() {
  pinMode(MOSI_PIN, INPUT);
  pinMode(MISO_PIN, INPUT);
  pinMode(PEN, OUTPUT);
  digitalWrite(PEN, HIGH);
  pinMode(CS_PIN, INPUT);
  pinMode(SYNC, INPUT);
}

void detachTouchscreenInterrupts() {
  detachInterrupt(SYNC);
  detachInterrupt(CS_PIN);
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
  if(numpolls%5==0){
    Serial.write(191);//telling it that now is a good time to transfer a frame
  }
}


FASTRUN void clockchanging() {
  bitbuffer[numclocks] = digitalReadFast(MOSI_PIN);
  numclocks++;
  if (numclocks > 7) {
    numclocks = 0;
    if (bitbuffer[3]) {
      //it's an x or y pos thingy
      if (bitbuffer[1]) {
        //x pos
        digitalWriteFast(MISO_PIN, xbits[0]);
        attachInterrupt(SCK_PIN, clockchangex, FALLING);
      } else {
        //y pos
        digitalWriteFast(MISO_PIN, ybits[0]);
        attachInterrupt(SCK_PIN, clockchangey, FALLING);
      }
    } else if (bitbuffer[5]) {
      //it's a beginning or end CS cycle
      digitalWriteFast(MISO_PIN, bbits[0]);
      attachInterrupt(SCK_PIN, clockchangeb, FALLING);
    } else {
      //don't do anything
      detachInterrupt(SCK_PIN);
    }
  }
}



//the clockchange x, y, and b functions are pretty much the same, with the exception that they pull data from a different list, for efficiency
FASTRUN void clockchangex() {
  digitalWriteFast(MISO_PIN, xbits[numclocks]);
  numclocks++;
  if (numclocks > 15) {
    numclocks = 0;
  }
}


FASTRUN void clockchangey() {
  digitalWriteFast(MISO_PIN, ybits[numclocks]);
  numclocks++;
  if (numclocks > 15) {
    numclocks = 0;
  }
}


FASTRUN void clockchangeb() {
  digitalWriteFast(MISO_PIN, bbits[numclocks]);
  numclocks++;
  if (numclocks > 15) {
    numclocks = 0;
  }
}

FASTRUN frameData frameTransfer() {
  byte inByte = Serial.read();
  //Serial.write("X");
  frameData inputFrame;
  //Serial.println(int(inByte));
  if (inByte == 245) {
    //Serial.write("Y");
    //starting with a data transfer, starting with buttons
    boolean transferring = true;
    while (transferring == true) {
      if (Serial.available() > 0) {
        inByte = Serial.read();
        byte identifier = inByte & firstthreebitmask;
        if (identifier == 7) {
          //move onto the next section
          //Serial.write("d");
          transferring = false;
        } else if (identifier == 0) {
          //first data byte
          //ranges from 3 to 8
          inputFrame.a = bitRead(inByte, 3);
          inputFrame.b = bitRead(inByte, 4);
          inputFrame.x = bitRead(inByte, 5);
          inputFrame.y = bitRead(inByte, 6);
          inputFrame.dl = bitRead(inByte, 7);
          //Serial.write("a");
        } else if (identifier == 4) {
          //second data byte
          inputFrame.dr = bitRead(inByte, 3);
          inputFrame.du = bitRead(inByte, 4);
          inputFrame.dd = bitRead(inByte, 5);
          inputFrame.l = bitRead(inByte, 6);
          inputFrame.r = bitRead(inByte, 7);
          //Serial.write("b");
        } else if (identifier == 2) {
          //third data byte
          inputFrame.startbutton = bitRead(inByte, 3);
          inputFrame.selectbutton = bitRead(inByte, 4);
          inputFrame.lid = bitRead(inByte, 5);
          inputFrame.pen = bitRead(inByte, 6);
          inputFrame.pwr = bitRead(inByte, 7);
          //Serial.write("c");
        }
      }
    }
    //Serial.write("y");
    //moving onto touchscreen
    transferring = true;
    while (transferring == true) {
      if (Serial.available() > 0) {
        inByte = Serial.read();
        byte identifier = inByte & firstthreebitmask;
        if (inByte == 255) {
          //finishing the transfer
          //Serial.write("k");
          transferring = false;
        } else if (identifier == 0) {
          //first data byte
          inputFrame.framexbits[0] = bitRead(inByte, 3);
          inputFrame.framexbits[1] = bitRead(inByte, 4);
          inputFrame.framexbits[2] = bitRead(inByte, 5);
          inputFrame.framexbits[3] = bitRead(inByte, 6);
          inputFrame.framexbits[4] = bitRead(inByte, 7);
          //Serial.write("e");
        } else if (identifier == 4) {
          //second data byte
          inputFrame.framexbits[5] = bitRead(inByte, 3);
          inputFrame.framexbits[6] = bitRead(inByte, 4);
          inputFrame.framexbits[7] = bitRead(inByte, 5);
          inputFrame.framexbits[8] = bitRead(inByte, 6);
          inputFrame.framexbits[9] = bitRead(inByte, 7);
          //Serial.write("f");
        } else if (identifier == 2) {
          //third data byte
          inputFrame.framexbits[10] = bitRead(inByte, 3);
          inputFrame.framexbits[11] = bitRead(inByte, 4);
          inputFrame.framexbits[12] = bitRead(inByte, 5);
          inputFrame.framexbits[13] = bitRead(inByte, 6);
          inputFrame.framexbits[14] = bitRead(inByte, 7);
          //Serial.write("g");
        } else if (identifier == 6) {
          //fourth data byte
          inputFrame.frameybits[0] = bitRead(inByte, 3);
          inputFrame.frameybits[1] = bitRead(inByte, 4);
          inputFrame.frameybits[2] = bitRead(inByte, 5);
          inputFrame.frameybits[3] = bitRead(inByte, 6);
          inputFrame.frameybits[4] = bitRead(inByte, 7);
          //Serial.write("h");
        } else if (identifier == 1) {
          //fifth data byte
          inputFrame.frameybits[5] = bitRead(inByte, 3);
          inputFrame.frameybits[6] = bitRead(inByte, 4);
          inputFrame.frameybits[7] = bitRead(inByte, 5);
          inputFrame.frameybits[8] = bitRead(inByte, 6);
          inputFrame.frameybits[9] = bitRead(inByte, 7);
          //Serial.write("i");
        } else if (identifier == 5) {
          //sixth data byte
          inputFrame.frameybits[10] = bitRead(inByte, 3);
          inputFrame.frameybits[11] = bitRead(inByte, 4);
          inputFrame.frameybits[12] = bitRead(inByte, 5);
          inputFrame.frameybits[13] = bitRead(inByte, 6);
          inputFrame.frameybits[14] = bitRead(inByte, 7);
          //Serial.write("j");
        }
      }
    }
    //Serial.write("x");
  }
  return inputFrame;
}

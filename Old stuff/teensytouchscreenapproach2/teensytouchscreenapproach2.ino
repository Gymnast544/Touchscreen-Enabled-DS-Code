
#define CS_PIN 10
#define MOSI_PIN 11
#define MISO_PIN 12
#define SCK_PIN 13
#define PEN 0
#define SYNC 32

volatile short numclocks = 0;
volatile boolean bitbuffer[20];


// 0, 127, 55, 19, 1, 0
volatile boolean xbits[16] = {0, 1, 0, 0, 0, 0, 0, 0,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean ybits[16] = {0, 1, 1, 1, 1, 0, 1, 1,    0, 0, 0, 0, 0, 0, 0, 0};
volatile boolean bbits[16] = {0, 0, 0, 1, 0, 1, 1, 1,    1, 0, 0, 0, 0, 0, 0, 0};

volatile short xpos = 128;
volatile short ypos = 128;



void setup() {
  // put your setup code here, to run once:


  pinMode(MOSI_PIN, INPUT);
  pinMode(MISO_PIN, INPUT);
  pinMode(PEN, OUTPUT);
  digitalWrite(PEN, HIGH);
  pinMode(23, INPUT_PULLUP);
  pinMode(CS_PIN, INPUT);
  pinMode(SYNC, INPUT);
  Serial.begin(115200);
  Serial.println("Starting...");
  while(digitalReadFast(SYNC)==1){
    //wait until the next frame
  }
  attachInterrupt(SYNC, syncinterrupt, FALLING);
  attachInterrupt(CS_PIN, CSfall, FALLING);
}

FASTRUN void updatebits(){
  
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

void syncinterrupt() {
  if(Serial.available()>0){
    byte inbyte = Serial.read();
    if(inbyte == 30){
      //adjusting x pos
      //we need 16 bits - in order to get this to be more consistent I will just send 16 bytes over

      for (byte i=0;i<16;i++){
        xbits[i] = 0;//just resetting the list
      }
      byte numbytesreceived = 0;
      boolean receiving = true;
      while(receiving){
        while(Serial.available()==0){
          //pass - waiting until we're sure we have data in
        }
        inbyte = Serial.read();
        if(inbyte==50){
          xbits[numbytesreceived] = 0;
          numbytesreceived++;
        }else if(inbyte==51){
          xbits[numbytesreceived] = 1;
          numbytesreceived++;
        }else if(inbyte == 68){
          //done with the transmission
        }
        Serial.write(numbytesreceived);//letting the pc know how many bits the DS has gotten - hopefully useful in case of a dropped bit somewhere
        
      }
    }else if(inbyte == 31){
      //adjusting y pos
    }else if(inbyte == 32){
      //touchscreen click
      digitalWriteFast(PEN, LOW);
    }else if(inbyte == 33){
      //touchscreen release
      digitalWriteFast(PEN, HIGH);
    }
  }
  
}

FASTRUN void loop() {


}

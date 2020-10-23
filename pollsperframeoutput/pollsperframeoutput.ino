#define SYNC 0


#define CS_PIN 10
#define MOSI_PIN 11
#define MISO_PIN 12
#define SCK_PIN 13
#define PEN 14



void setup() {
  // put your setup code here, to run once:
  setupTouchscreenPins();
  //attachTouchscreenInterrupts();
  Serial.begin(115200);

}

int numpolls = 0;

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
}






FASTRUN void loop(){
  if(!digitalReadFast(CS_PIN)){
    numpolls++;
    while(!digitalReadFast(CS_PIN)){}
    delay(1);
  }else if(!digitalReadFast(SYNC)){
    Serial.println(numpolls);
    numpolls = 0;
    while(!digitalReadFast(SYNC)){}
  }
   
}

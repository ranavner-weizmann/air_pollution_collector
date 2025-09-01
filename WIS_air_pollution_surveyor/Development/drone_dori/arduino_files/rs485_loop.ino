const int SSERIAL_CTRL_PIN = 3;
const int RS485_TRANSMIT = HIGH;
const int RS485_RECEIVE = LOW;
long i = 0;
String m = "";

void setup() {
    // put your setup code here, to run once:
  Serial.begin(9600);
  Serial1.begin(9600);
  delay(30);
  pinMode(SSERIAL_CTRL_PIN, OUTPUT);    
  digitalWrite(SSERIAL_CTRL_PIN, RS485_TRANSMIT);

}

void loop() {
  i += 1000;
  i = i % 1000000;
  m += "1";
  String message = "#0215B6?VR042E01D043";
   //digitalWrite(SSERIAL_CTRL_PIN, RS485_TRANSMIT);
    Serial1.println(message);
    Serial.println(message);
    delay(10);
   //digitalWrite(SSERIAL_CTRL_PIN, RS485_RECEIVE);

}
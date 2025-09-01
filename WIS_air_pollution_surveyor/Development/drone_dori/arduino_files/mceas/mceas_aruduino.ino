/*
 * Copyright (c) 2023 Noam Inbari, weizmann institute of science
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without restriction,
 * including without limitation the rights to use, copy, modify, merge,
 * publish, distribute, sublicense, and/or sell copies of the Software,
 * and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
 * AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 *
 * Title:           Drone project - led, pump, flow and pressure control
 * Author:          Noam Inbari <noam.inbari@weizmann.ac.il>
 * Version:         v1.1.0
 */

/*----------------------------------------------------------------------------*/
/* Pin layout                                                                 */
/*----------------------------------------------------------------------------*/
/*
 * Pin 0 – serial TX
 * Pin 1 – serial RX
 * Pin 3 - Led control
 * Pin 5 - Pump control
 * A0 – Pressure sensor
 * A2 – Flow sensor
 * A1 - brightness sensor
 */

/*----------------------------------------------------------------------------*/
/* Globals                                                                    */
/*----------------------------------------------------------------------------*/

#include <Wire.h>
// #include "tec.h"
int pumpStrength = 0;
int ledStrength = 0;
// float temperature = -1.0;

#define LED_SET 'L'
#define PUMP_SET 'F'
#define PUMP_PIN 5
#define LED_PIN 3


// #define _DEBUG

#define fabs(x) ((x)>0?(x):-(x))

// Debugging prints
#ifdef _DEBUG
#define printFloat(x ,y) {Serial.print(x);Serial.println(y, 4);}
#define printInt(x,y) {Serial.print(x);Serial.println(y);}
#else
#define printFloat(x ,y) {}
#define printInt(x,y) {}
#endif

#define min(x,y) (((x) > (y)) ? (y) : (x))
#define sign(x) ((x) >= 0 ? 1 : -1)

int delayMilliTest = 1;
int delayMilliLoop = 10;
class PIDController{
  private:
    float kp;
    float ki;
    float kd;
    float last_error = 0;
    float integral = 0;
  public:
    PIDController(float kp, float ki, float kd){
      this->kp = kp;
      this->ki = ki;
      this->kd = kd;
    }

  float calculate(float setpoint, float measured_value){
      float error = setpoint - measured_value;

      // Proportional term
      float proportional = this->kp * error;

      // Integral term
      this->integral += this->ki * error;

      // Derivative term
      float derivative = this->kd * (error - this->last_error);
      this->last_error = error;
      return proportional + this->integral + derivative;
  }
};

PIDController pumpPid = PIDController(1, 0.5, 2);
float flow = 1.2;
bool stopped = false;
int ledTarget = 255;


void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(57600);
  // Serial1.begin(57600);
  delay(1000);
  // Serial1.print(OUTPUT_TEMPERATURE_COMMAND);
  // Serial1.flush();
  // delay(1000);
}

void ledTest(void)
{
  // increase the LED brightness
  for(int dutyCycle = 0; dutyCycle <= 255; dutyCycle++){   
    // changing the LED brightness with PWM
    analogWrite(LED_PIN, dutyCycle);
    delay(200);
  }

  // decrease the LED brightness
  for(int dutyCycle = 255; dutyCycle >= 0; dutyCycle--){
    // changing the LED brightness with PWM
    analogWrite(LED_PIN, dutyCycle);
    delay(200);
  }
}

float calcFlow(float voltage)
{
    //y = 0.0103x^4 - 0.102x^3 + 0.4306x^2 - 0.5288x + 0.19
    float calc = 0;
    float x4 = (float)pow(voltage, 4);
    float x3 = (float)pow(voltage, 3); 
    float x2 = (float)pow(voltage, 2);

    calc = (float)(0.0103 * x4 - 0.102 * x3 + 0.4306 * x2 - 0.5288 * voltage + 0.19);
    return calc;
}


int setControl(void){
  char controlByte;
  int power = 0;
  int bRead;
  if (Serial.available() > 0){
    // Control byte and strength byte
    bRead = Serial.readBytes((char *)&controlByte, sizeof(controlByte));
    if (bRead != 1) {return -1;}
    // Serial.print("Read: ");
    // Serial.println(controlByte);
    if (controlByte == LED_SET){
      power = Serial.parseInt();
      if (0 > power || power >= 256){return -1;}
      ledTarget = power;
      ledStrength = power;
      analogWrite(LED_PIN, ledTarget);
    }
    else if(controlByte == PUMP_SET){
      read_flowrate();
    }
  }
  return 0;
}


void check_pump(void){
  int i;
  for ( i = 0 ; i < 200; i += 10){
    printInt("Writing: ", i);
    analogWrite(PUMP_PIN, i);
    delay(1000);
  }
  for ( i = 200 ; i >= 0; i -= 10){
    printInt("Writing: ", i);
    analogWrite(PUMP_PIN, i);
    delay(1000);
  }
}









float read_flowrate(void){
  extern float flow;
  float flowRate = -1;
  if (Serial.available() > 0 ){
    flowRate = Serial.parseFloat();
    // Serial.print("Got flowrate of: ");
    // Serial.println(flowRate, 4);
    if (flowRate < 0 || flowRate > 2){return -1;}
    flow = flowRate;
  }
  
}

void control_flow(){
  extern float flow;
  extern PIDController pumpPid;
  extern int pumpStrength;
  float flowVolate = analogRead(A2) * (5.0 / 1023.0);
  float current_flow_rate = calcFlow(flowVolate);
  float target = pumpPid.calculate(flow, current_flow_rate);
  // Serial.print("Calculated from pid: ");
  // Serial.println(target, 10);
  int new_pump_voltage = floor(target * (256.0 / 2));
  new_pump_voltage = (new_pump_voltage < 256) ? new_pump_voltage : 255;
  new_pump_voltage = (new_pump_voltage >= 0) ? new_pump_voltage : 0;
  analogWrite(PUMP_PIN, new_pump_voltage);
  pumpStrength = new_pump_voltage;
}



/*
 * Main loop
 */
void loop() 
{
  extern bool stopped;
  extern float flow;
  extern float temperature;
  setControl();
  if (flow != 0){
    control_flow();
  }
  else{
    analogWrite(PUMP_PIN, 0);
    // analogWrite(LED_PIN, 0);
    pumpStrength = 0;
    ledStrength = 0;
    ledTarget = 0;
    // stopped = true;
  }
  // Read analog inputs
  int pressureSensorValue = analogRead(A0); 
  int flowSensorValue = analogRead(A2); 
 
  // Convert the analog reading (which goes from 0 - 1023) to a voltage (0 - 5V):
  float pressureVoltage = pressureSensorValue * (5.0 / 1023.0);
  float flowVoltage = flowSensorValue * (5.0 / 1023.0);

  // Calc pressure and Flow inputs
  float pressureOnePSI = 0.125; // in voltage => full range voltage calc :: 3.75 / 30 = 0.125 
  float pressureCalcPSI = pressureVoltage/pressureOnePSI;
  float pressureCalcMB = pressureCalcPSI * 68.9476;
 
  float flowLM = calcFlow(flowVoltage);


  Serial.print("FLM: ");
  Serial.print(flowLM);
  Serial.print(" ,FTARGET: ");
  Serial.print(flow);
  Serial.print(" ,CPSI: ");
  Serial.print(pressureCalcPSI);
  Serial.print(" ,CMB:");
  Serial.println(pressureCalcMB);

  



    // Status printout:
  // Serial.print("F:[");
  // Serial.print(flowVoltage, 3);
  // Serial.print(",");
  // Serial.print(flowLM, 3);
  // Serial.print("],");

  // Serial.print("P:["); 
  // Serial.print(pressureVoltage, 3);
  // Serial.print(",");
  // Serial.print(pressureCalcPSI, 3);
  // Serial.print(",");
  // Serial.print(pressureCalcMB, 3);
  // Serial.print("],");

  // Serial.print("LED:");
  // Serial.print(ledStrength);

  // Serial.print(",PUMP:");
  // Serial.println(pumpStrength);

  // if (Serial1.available() > 0){
  //   unsigned int const responseBufferLen = 30;
  //   char responseBuffer[responseBufferLen] = {0};
  //   Serial1.readString().toCharArray(responseBuffer, responseBufferLen);
  //   temperature = calculateObjectValueFromReponse(responseBuffer);
  // }


  // if (temperature != -1.0){
  //   Serial.print("{");
  //   Serial.print("flow: ");
  //   Serial.print(flowLM, 4);
  //   Serial.print(", led_strength: ");
  //   Serial.print(ledStrength);
  //   Serial.print(", led_temperature: ");
  //   Serial.print(temperature);
  //   Serial.print(", pressurePSI: ");
  //   Serial.print(pressureCalcPSI, 4);
  //   Serial.print(", pressureMB: ");
  //   Serial.print(pressureCalcMB, 4);
  //   Serial.print(", pump_strength: ");
  //   Serial.print(pumpStrength);
  //   Serial.println("}");
  //   temperature = -1.0;
  //   Serial1.print(OUTPUT_TEMPERATURE_COMMAND);
  //   Serial1.flush();
  // }
  delay(delayMilliLoop);
}


// void serialEvent1(){
//   unsigned int const responseBufferLen = 30;
//   char responseBuffer[responseBufferLen] = {0};
//   // temperature = calculateObjectValueFromReponse(responseBuffer);
//   Serial.println("Serial event 1 triggered");
//   Serial1.readString().toCharArray(responseBuffer, responseBufferLen);
//   Serial.println(calculateObjectValueFromReponse(responseBuffer));
//   Serial.flush();
// }

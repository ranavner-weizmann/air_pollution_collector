// tec and ldd libraries
#include "MePort.h"
#include "MeCom.h"
#include "MeFrame.h"
#include "MeCRC16.h"
#include "MeVarConv.h"
#include "MeInt.h"
#include "ArduinoMecomAdapters.h"
// HDC temperature sensor library
#include <HDC2080.h>
// tec and ldd constants
const int SSERIAL_CTRL_PIN = 3;
const int RS485_TRANSMIT = HIGH;
const int RS485_RECEIVE = LOW;
const bool DEBUG = true;
const int LDD_ADDRESS = 1;
const int TEC_ADDRESS = 2;
// HDC temperatur sensor constants
#define HDC_ADDR 0x41
HDC2080 sensorHDC(HDC_ADDR);
#define COMFORT_ZONE_TEMPERATURE_HIGH 28
#define COMFORT_ZONE_TEMPERATURE_LOW 22
#define COMFORT_ZONE_HUMIDITY_HIGH 55
#define COMFORT_ZONE_HUMIDITY_LOW 40
// tec and ldd externs
extern int8_t *MeInt_QueryRcvPayload;

String data;
#define DELIMITER ","
const bool DEBUG_MEPORT = false;

// MeCom.cpp ===> start
uint8_t MeCom_GetIdentString(uint8_t Address, int8_t *arr)
{
  uint8_t Succeeded = MeInt_Query('#', Address, 3, (int8_t *)"?IF");
  if (Succeeded == 0)
  {
    Serial.println("error in GetIdentString");
    *arr = 0;
    return Succeeded;
  }

  for (int32_t i = 0; i < 20; i++)
  {
    *arr = MeInt_QueryRcvPayload[i];
    arr++;
  }
  *arr = 0;
  return Succeeded;
}
uint8_t MeCom_ParValuel(uint8_t Address, uint16_t ParId, uint8_t Inst, MeParLongFields *Fields, MeParCmd Cmd)
{
  if (Cmd == MeGet)
  {
    int8_t TxData[20];
    TxData[0] = '?';
    TxData[1] = 'V';
    TxData[2] = 'R';
    MeVarConv_AddUsHex(&TxData[3], ParId);
    MeVarConv_AddUcHex(&TxData[7], Inst);
    uint8_t Succeeded = MeInt_Query('#', Address, 9, TxData);

    if (Succeeded == 0)
    {
      Fields->Value = 0;
      return Succeeded;
    }

    Fields->Value = MeVarConv_HexToSl(&MeInt_QueryRcvPayload[0]);

    return Succeeded;
  }
  else if (Cmd == MeSet)
  {
    int8_t TxData[20];
    TxData[0] = 'V';
    TxData[1] = 'S';
    MeVarConv_AddUsHex(&TxData[2], ParId);
    MeVarConv_AddUcHex(&TxData[6], Inst);
    MeVarConv_AddSlHex(&TxData[8], Fields->Value);

    return MeInt_Set('#', Address, 16, TxData);
  }
  else if (Cmd == MeGetLimits)
  {
    int8_t TxData[20];
    TxData[0] = '?';
    TxData[1] = 'V';
    TxData[2] = 'L';
    MeVarConv_AddUsHex(&TxData[3], ParId);
    MeVarConv_AddUcHex(&TxData[7], Inst);

    uint8_t Succeeded = MeInt_Query('#', Address, 9, TxData);
    if (Succeeded == 0)
    {
      Fields->Min = 0;
      Fields->Max = 0;
      return Succeeded;
    }

    Fields->Min = MeVarConv_HexToSl(&MeInt_QueryRcvPayload[2]);
    Fields->Max = MeVarConv_HexToSl(&MeInt_QueryRcvPayload[10]);

    return Succeeded;
  }
  return 0;
}
uint8_t MeCom_ParValuef(uint8_t Address, uint16_t ParId, uint8_t Inst, MeParFloatFields *Fields, MeParCmd Cmd)
{
  return MeCom_ParValuel(Address, ParId, Inst, (MeParLongFields *)Fields, Cmd);
}
// MeCom.cpp ===> end

void arduinoMemset(void *dest, int ch, int count)
{
  memset(dest, ch, count);
}

void arduinoWaitSecondsMili(int miliSeconds)
{
  delay(miliSeconds);
}

void writeToSerial(char *toWrite)
{
  Serial.write(toWrite);
}

void writeToSerial1(char *in)
{
  int length = strlen(in);
  bool DEBUG_WRITING = false;
  if (DEBUG_WRITING)
  {
    Serial.write("Writing to Serial1: ");
    Serial.write(in);
    Serial.write(" length is ");
    Serial.println(length);
  }

  digitalWrite(SSERIAL_CTRL_PIN, RS485_TRANSMIT);
  for (int i = 0; i < length; i++)
  {
    Serial1.write(in[i]);
    delay(1);
  }
  Serial1.write('\r');
  // OG, works for IF but not for VR queries: delayMicroseconds(1300);                           // Wait before going back to Receive mode
  delayMicroseconds(1500);
  digitalWrite(SSERIAL_CTRL_PIN, RS485_RECEIVE);
}

void tryToReceiveSerial1(int destination)
{
  // OG, works for IF but missing first byte of VR queries: delayMicroseconds(1500);
  digitalWrite(SSERIAL_CTRL_PIN, RS485_RECEIVE);
  char RcvBuffer[100] = ""; // Initialize an empty string
  arduinoMemset(RcvBuffer, 0, 100);
  int index = 0;
  // delay(1000); commented because trying to run sensor
  while (!Serial1.available())
    ;
  while (Serial1.available())
  {
    RcvBuffer[index] = Serial1.read();
    index++;
    delay(1);
  }
  if (index > 0)
  {
    bool DEBUG_READING = false;
    if (DEBUG_READING)
    {
      Serial.write("received");
      Serial.println(RcvBuffer);
    }
    // check that the message is for a meerstetter device
    if (destination == MEERSTETER_DESTINATION)
    {
      MePort_ReceiveByte((int8_t *)RcvBuffer);
    }
  }
  else
  {
    Serial.println("didn't receive any data");
  }
}

// #0115AA?IF257D - ldd get model
// #0215AA?IFED08 - tec something
void printInt8_t(int8_t *buf, int length)
{
  for (int i = 0; i < length; i++)
  {
    int8_t c = buf[i];
    Serial.print((char)c);
  }
  Serial.println();
}

void setupRS485()
{
  pinMode(SSERIAL_CTRL_PIN, OUTPUT);
  digitalWrite(SSERIAL_CTRL_PIN, RS485_RECEIVE);
}

void setupHDC2022()
{
  // Initialize I2C communication
  sensorHDC.begin();

  // Begin with a device reset
  sensorHDC.reset();

  // Set up the comfort zone
  sensorHDC.setHighTemp(COMFORT_ZONE_TEMPERATURE_HIGH);
  sensorHDC.setLowTemp(COMFORT_ZONE_TEMPERATURE_LOW);
  sensorHDC.setHighHumidity(COMFORT_ZONE_HUMIDITY_HIGH);
  sensorHDC.setLowHumidity(COMFORT_ZONE_HUMIDITY_LOW);

  // Configure Measurements
  sensorHDC.setMeasurementMode(TEMP_AND_HUMID); // Set measurements to temperature and humidity
  sensorHDC.setRate(FIVE_HZ);
  sensorHDC.setTempRes(FOURTEEN_BIT);
  sensorHDC.setHumidRes(FOURTEEN_BIT);

  // begin measuring
  sensorHDC.triggerMeasurement();
}

void temperatureAppendDataToString(String &data)
{
  data += String(sensorHDC.readTemp());
  data += DELIMITER;
  data += String(sensorHDC.readHumidity());
}
void tecAppendDataToString(String &data)
{
  MeParFloatFields Fields;
  int instance = 1;
  const int NUMBER_OF_INSTANCES_TEC = 2;
  for (instance = 1; instance <= NUMBER_OF_INSTANCES_TEC; instance++)
  {
    MeCom_TEC_Mon_ObjectTemperature(TEC_ADDRESS, instance, &Fields, MeGet);
    data += Fields.Value;
    // errors
    MeCom_TEC_Mon_ErrorNumber(TEC_ADDRESS, instance, &lFields, MeGet);
    data += lFields.Value;
    data += DELIMITER;
    MeCom_TEC_Mon_ErrorInstance(TEC_ADDRESS, instance, &lFields, MeGet);
    data += fFields.Value;
    data += DELIMITER;
    MeCom_TEC_Mon_ErrorParameter(TEC_ADDRESS, instance, &lFields, MeGet);
    data += fFields.Value;
    if (instance < NUMBER_OF_INSTANCES_TEC)
    {
      data += DELIMITER;
    }
  }
}
void lddAppendDataToString(String &data)
{
  MeParFloatFields fFields;
  MeParLongFields lFields;
  // output current
  MeCom_LDD_Mon_LaserDiodeCurrentActual(LDD_ADDRESS, &fFields, MeGet);
  data += fFields.Value;
  data += DELIMITER;
  // output voltage
  MeCom_LDD_Mon_LaserDiodeVoltageActual(LDD_ADDRESS, &fFields, MeGet);
  data += fFields.Value;
  data += DELIMITER;
  // Anode Voltage
  data += "anodeVoltage";
  data += DELIMITER;
  // Cathode Voltage
  data += "cathodeVoltage";
  data += DELIMITER;
  // laser power
  MeCom_LDD_Mon_LaserPower(LDD_ADDRESS, &fFields, MeGet);
  data += fFields.Value;
  data += DELIMITER;
  // laser temperature
  MeCom_LDD_Mon_LaserDiodeTemperature(LDD_ADDRESS, &fFields, MeGet);
  data += fFields.Value;
  data += DELIMITER;
  // base plate temperature
  MeCom_LDD_Mon_BasePlateTemperature(LDD_ADDRESS, &fFields, MeGet);
  data += fFields.Value;
  data += DELIMITER;
  // photodiode input
  data += "photodiodeInput";
  data += DELIMITER;
  // errors
  MeCom_LDD_Mon_ErrorNumber(LDD_ADDRESS, &lFields, MeGet);
  data += lFields.Value;
  data += DELIMITER;
  MeCom_LDD_Mon_ErrorInstance(LDD_ADDRESS, &lFields, MeGet);
  data += fFields.Value;
  data += DELIMITER;
  MeCom_LDD_Mon_ErrorParameter(LDD_ADDRESS, &lFields, MeGet);
  data += fFields.Value;
}

void updateDataString(String &data)
{
  data = "";
  temperatureAppendDataToString(data);
  data += DELIMITER;
  lddAppendDataToString(data);
  data += DELIMITER;
  tecAppendDataToString(data);
}

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial1.begin(9600);
  delay(30);
  if (!data.reserve(1000))
  { // check the last largest reserve
    while (1)
    { // stop here and print repeating msg
      Serial.println(F("Strings out-of-memory"));
      delay(3000); // repeat msg every 3 sec
    }
  }
  setupRS485();
  setupHDC2022();
}

void loop()
{
  int8_t buf[25];
  // MeCom_GetIdentString(1, buf);
  // Serial.write("ldd identity string: ");
  // printInt8_t(buf, 25);

  // if(Serial.available()){
  //   while(Serial.available()){
  //     Serial.read();
  //   }
  //       MeParFloatFields Fields;
  //   int switchTemp = random(0,2);
  //   Fields.Value = switchTemp ? 21.75 : 25;
  //   int instance = 1;
  //   MeCom_TEC_Tem_TargetObjectTemp(TEC_ADDRESS, instance, &Fields, MeSet);
  // }

  // memset(buf, '\0', 25);
  // MeCom_GetIdentString(TEC_ADDRESS, buf);
  // Serial.write("tec identity string: ");
  // printInt8_t(buf, 25);
  updateDataString(data);

  Serial.println(data);
}
// #0215CA?IFA98B
// #0215CB?VR03E801946B

//tec and ldd libraries
#include "MePort.h"
#include "MeCom.h"
#include "MeFrame.h"
#include "MeCRC16.h"
#include "MeVarConv.h"
#include "MeInt.h"
#include "ArduinoMecomAdapters.h"
//HDC temperature sensor library
#include <HDC2080.h>
#include <TimeProfiler.h>
//Honeywell pressure library
#include <HoneywellTruStabilitySPI.h>
//tec and ldd constants
const int SSERIAL_CTRL_PIN = 4;
const int RS485_RECEIVE_CTRL_PIN = 2;
const int RS485_TRANSMIT = HIGH;
const int RS485_RECEIVE = LOW;
const bool DEBUG = true;
const int LDD_ADDRESS = 1;
const int TEC_ADDRESS = 2;
//HDC temperatur sensor constants
#define HDC_ADDR 0x41
HDC2080 sensorHDC(HDC_ADDR);
#define COMFORT_ZONE_TEMPERATURE_HIGH 28
#define COMFORT_ZONE_TEMPERATURE_LOW 22
#define COMFORT_ZONE_HUMIDITY_HIGH 55
#define COMFORT_ZONE_HUMIDITY_LOW 40
//pressure constants
const float pmin = 0;
const float pmax = 1.600;
#define SLAVE_SELECT_PIN SS
TruStabilityPressureSensor sensorPressure( SLAVE_SELECT_PIN, pmin, pmax );
//tec and ldd externs
extern int8_t* MeInt_QueryRcvPayload;

String data;
#define DELIMITER ","
const bool DEBUG_MEPORT = false;
const unsigned long READ_TIMEOUT = 10;
const int BAD_PARAMETER_VALUE = -999;

typedef struct MceasMecomIntegratorParams {
  int address;
  int instance;
  void* fields;
} MceasMecomIntegratorParams;

typedef uint8_t (*MceasMecomIntegrator) (MceasMecomIntegratorParams);

//MeCom.cpp ===> start
uint8_t MeCom_GetIdentString(uint8_t Address, int8_t* arr)
{
    uint8_t Succeeded = MeInt_Query('#', Address, 3, (int8_t*)"?IF");
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
uint8_t MeCom_ParValuel(uint8_t Address, uint16_t ParId, uint8_t Inst, MeParLongFields* Fields, MeParCmd Cmd)
{
    if (Cmd == MeGet)
    {
        int8_t TxData[20];
        TxData[0] = '?'; TxData[1] = 'V'; TxData[2] = 'R';
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
        TxData[0] = 'V'; TxData[1] = 'S';
        MeVarConv_AddUsHex(&TxData[2], ParId);
        MeVarConv_AddUcHex(&TxData[6], Inst);
        MeVarConv_AddSlHex(&TxData[8], Fields->Value);

        return MeInt_Set('#', Address, 16, TxData);
    }
    else if (Cmd == MeGetLimits)
    {
        int8_t TxData[20];
        TxData[0] = '?'; TxData[1] = 'V'; TxData[2] = 'L';
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
uint8_t MeCom_ParValuef(uint8_t Address, uint16_t ParId, uint8_t Inst, MeParFloatFields* Fields, MeParCmd Cmd)
{
    return MeCom_ParValuel(Address, ParId, Inst, (MeParLongFields*)Fields, Cmd);
}
//MeCom.cpp ===> end

bool timeoutPassed(int startMicros, int endMicros){
  /*
  */
  if(endMicros < startMicros){
    return true;
  }
  return endMicros - startMicros >= READ_TIMEOUT * 1000;
}

bool readnUntilTimeoutSerial1(char charToWait, char* destinationString, int n){
  /*
    params:
    charToWait - the character that will cause the reading to stop
  */
  int charsRead = 0;
  int start = micros();
  char characterRead;
  bool DEBUG_READ_TIMEOUT = false;
  while(!timeoutPassed(start, micros()) && charsRead < n){
    if(Serial1.available()){
      characterRead = Serial1.read();
      if(NULL != destinationString){
        destinationString[charsRead] = characterRead;
      }
      charsRead ++;
      if(characterRead == charToWait){
        //return true if we read the character we wanted
        return true;
      }
    }
  }
  if(charsRead == n){
    //return true if n characers were
    return true;
  }
  if(DEBUG_READ_TIMEOUT){
    Serial.println("Timeout reached");
  }
  return false; 
}

void arduinoMemset(void *dest, int ch, int count){
  memset(dest, ch, count);
}

void arduinoWaitSecondsMili(int miliSeconds){
  delay(miliSeconds);
}

void writeToSerial(char* toWrite){
  Serial.write(toWrite);
}

void clearBufferSerial1(){
  while(Serial1.available()){
    Serial1.read();
  }
}

void writeToSerial1(char* in){
  TIMEPROFILE_BEGIN(WRITE_SERIAL);
  int length = strlen(in);
  bool DEBUG_WRITING = false;
  if (DEBUG_WRITING){
    Serial.write("Writing to Serial1: ");
    Serial.write(in);
    Serial.write(" length is ");
    Serial.println(length);
  }
  Serial1.print(in);
  Serial1.print('\r');
  TIMEPROFILE_END(WRITE_SERIAL);
  //Serial.print("Time to write Serial1: ");  Serial.println(TimeProfiler.getProfile("WRITE_SERIAL"));
}

void meersteterReceive(){
  TIMEPROFILE_BEGIN(RECEIVE_SERIAL);
  const int BUFFER_SIZE = 100;
  const bool DEBUG_READING = false;
  unsigned long start, end = 0;
  char RcvBuffer[BUFFER_SIZE + 1] = {0}; // Initialize an empty string
  arduinoMemset(RcvBuffer, 0, BUFFER_SIZE);
  int index = 0;

  if(readnUntilTimeoutSerial1('\r', NULL, BUFFER_SIZE)){
    if(DEBUG_READING){
      Serial.println("Success reading echo rs485 message");
    }
  }else{
    if(DEBUG_READING){
      Serial.println("FAILED!!! timeout reading echo rs485 message, stopping receive");
    }
    delay(READ_TIMEOUT);
    clearBufferSerial1();
    return;
  }
  if(readnUntilTimeoutSerial1('\r', RcvBuffer, BUFFER_SIZE)){
    if(DEBUG_READING){
      Serial.print("Success reading response from meer device. managed to read: "); Serial.println(RcvBuffer);
    }
    TIMEPROFILE_BEGIN(RECEIVE_BYTE);
    MePort_ReceiveByte((int8_t*)RcvBuffer);
    TIMEPROFILE_END(RECEIVE_BYTE);
  }else{
    if(DEBUG_READING){
      Serial.print("FAILED!!! timeout while waiting for response from meer device. managed to read: "); Serial.println(RcvBuffer);
    }
    delay(READ_TIMEOUT);
    clearBufferSerial1();
  }
  TIMEPROFILE_END(RECEIVE_SERIAL);
  //Serial.print("Time to receive Serial1: ");  Serial.print(TimeProfiler.getProfile("RECEIVE_SERIAL")); Serial.print(" from it, time spent in receive byte: "); Serial.println(TimeProfiler.getProfile("RECEIVE_BYTE"));
}

void tryToReceiveSerial1(int destination)
{
  switch(destination){
    case MEERSTETER_DESTINATION:
      meersteterReceive();
      break;
    default:
      Serial.println("invalid destination in tryToReceiveSerial1");
      break;
  }
}

//#0115AA?IF257D - ldd get model
//#0215AA?IFED08 - tec something
void printInt8_t(int8_t* buf, int length){
  for(int i = 0; i < length; i++){
    int8_t c = buf[i];
    Serial.print((char)c);
  }
  Serial.println();
}

void setupRS485(){
  pinMode(SSERIAL_CTRL_PIN, OUTPUT);    
  digitalWrite(SSERIAL_CTRL_PIN, RS485_TRANSMIT);
  pinMode(RS485_RECEIVE_CTRL_PIN, OUTPUT);    
  digitalWrite(RS485_RECEIVE_CTRL_PIN, RS485_RECEIVE);
}

void setupHDC2022(){
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
  sensorHDC.setMeasurementMode(TEMP_AND_HUMID);  // Set measurements to temperature and humidity
  sensorHDC.setRate(FIVE_HZ);
  sensorHDC.setTempRes(FOURTEEN_BIT);
  sensorHDC.setHumidRes(FOURTEEN_BIT);
  
  //begin measuring
  sensorHDC.triggerMeasurement();
}

void setupPressure(){
  SPI.begin(); // start SPI communication
  sensorPressure.begin(); // run sensor initialization
}

bool messageValid(char* message){
  int messageLength = strlen(message);
  if(message[0] != '^' || message[1] != '^'){
    return false;
  }
  if(message[messageLength - 1] != ';' || message[messageLength - 2] != ';'){
    return false;
  }
  return true;
}

void handleMessage(char* message){
  const int TEC_CHANGE_TARGET_TEMP_COMMAND = 1;
  const int PWR_CHANGE_TARGET_TEMP_COMMAND = 2;
  const int MAX_ADDITIONAL_PARAMETRS = 10;

  if(!messageValid(message)){
    Serial.println("Error handling message");
    return;
  }
  //slice relevant message into croppedMessage
  char croppedMessage[100] = {0};  
  strncpy(croppedMessage, message + 2, strlen(message) - 4);
  char* delim = "|";

  int commandNumber = atoi(strtok(croppedMessage, delim));
  char* additionalParameters = strtok(NULL, delim);
  //assuming there won't be more than MAX_ADDITIONAL_PARAMETRS parameters.
  char* parameters[MAX_ADDITIONAL_PARAMETRS] = {0};
  for (int i = 0; i < MAX_ADDITIONAL_PARAMETRS; i++){
    char* delimParameters = ",";
    if(i == 0){
      parameters[i] = strtok(additionalParameters, delimParameters);
    } else {
      parameters[i] = strtok(NULL, delimParameters);
    }
    //strtok has returned nothing
    if(NULL == parameters[i]){
      break;
    }
  }
  MeParFloatFields Fields;
  int result = -1;
  if(TEC_CHANGE_TARGET_TEMP_COMMAND == commandNumber){
    Fields.Value = atof(parameters[0]);
    int instance = atoi(parameters[1]);
    
    result = MeCom_TEC_Tem_TargetObjectTemp(TEC_ADDRESS, instance, &Fields, MeSet); 
  }
  else if(PWR_CHANGE_TARGET_TEMP_COMMAND == commandNumber){
      Fields.Value = atof(parameters[0]);
      result = MeCom_ParValuef(LDD_ADDRESS, 4000, 1, &Fields, MeSet);

  }
  else{
    //unknown command
  } 

  
}

void temperatureAppendDataToString(String& data){
  data += String(sensorHDC.readTemp());
  data += DELIMITER;
  data += String(sensorHDC.readHumidity());
}

float calculatedPressure(float rawPressure)
{
  float arduino_bias = 5.010471343994140625;
  return (rawPressure/pow(2,14)-0.1)*1600/0.8 + arduino_bias;
}

void pressureAppendDataToString(String& data){
  if( sensorPressure.readSensor() == 0 ){
    data += sensorPressure.rawPressure();
    data += DELIMITER;
    data += calculatedPressure(float(sensorPressure.rawPressure()));
  } else {
    data += BAD_PARAMETER_VALUE;
    data += DELIMITER;
    data += BAD_PARAMETER_VALUE;
  }

}

uint8_t mceas_TEC_Mon_ObjectTemperature(MceasMecomIntegratorParams params){
  return MeCom_TEC_Mon_ObjectTemperature(params.address, params.instance, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_TEC_Mon_TargetObjectTemperature(MceasMecomIntegratorParams params){
  return MeCom_TEC_Mon_TargetObjectTemperature(params.address, params.instance, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_COM_ErrorNumber(MceasMecomIntegratorParams params){
  return MeCom_COM_ErrorNumber(params.address, (MeParLongFields*)params.fields, MeGet);
}
uint8_t mceas_COM_ErrorInstance(MceasMecomIntegratorParams params){
  return MeCom_COM_ErrorInstance(params.address, (MeParLongFields*)params.fields, MeGet);
}
uint8_t mceas_COM_ErrorParameter(MceasMecomIntegratorParams params){
  return MeCom_COM_ErrorParameter(params.address, (MeParLongFields*)params.fields, MeGet);
}

void tecAppendDataToString(String& data){
  MeParFloatFields fFields;
  MeParLongFields lFields;
  int instance = 1;
  const int NUMBER_OF_INSTANCES_TEC = 2, NUMBER_OF_FUNCTIONS = 5;
  bool queryFailed = false;
  MceasMecomIntegrator tecFunctions[NUMBER_OF_FUNCTIONS] = {
    mceas_TEC_Mon_ObjectTemperature,
    mceas_TEC_Mon_TargetObjectTemperature,
    mceas_COM_ErrorNumber,
    mceas_COM_ErrorInstance,
    mceas_COM_ErrorParameter
  };
  for (instance = 1; instance <= NUMBER_OF_INSTANCES_TEC; instance++){
    MceasMecomIntegratorParams paramsFloat = {TEC_ADDRESS, instance, &fFields};
    MceasMecomIntegratorParams paramsLong = {TEC_ADDRESS, instance, &lFields};
    MceasMecomIntegratorParams *tecParams[NUMBER_OF_FUNCTIONS] = {
      &paramsFloat,
      &paramsFloat,
      &paramsLong,
      &paramsLong,
      &paramsLong
    };
    for(int i = 0; i < NUMBER_OF_FUNCTIONS; i++){
      if(queryFailed){
        data += BAD_PARAMETER_VALUE;
      }else{
        clearBufferSerial1();
        if(!tecFunctions[i](*tecParams[i])){
          queryFailed = true;
          data += BAD_PARAMETER_VALUE;
        }else{
          if(tecParams[i] == &paramsFloat){
            data += ((MeParFloatFields*)tecParams[i]->fields)->Value;
          } else if(tecParams[i] == &paramsLong){
            data += ((MeParLongFields*)tecParams[i]->fields)->Value;
          }else{
            Serial.println("Wrong type passed to tecParams");
          }  
        }
      }    
      if(instance < NUMBER_OF_INSTANCES_TEC || i < NUMBER_OF_FUNCTIONS - 1){
        data += DELIMITER;
      }
    }
  }  
}

uint8_t mceas_LDD_Mon_LaserDiodeCurrentActual(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1100, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_LaserDiodeVoltageActual(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1101, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_AnodeVoltage(MceasMecomIntegratorParams params){
  return MeCom_LDD_Mon_AnodeVoltage(params.address, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_CathodeVoltage(MceasMecomIntegratorParams params){
  return MeCom_LDD_Mon_CathodeVoltage(params.address, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_LaserPower(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1600, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_deviceTemperature(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1065, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_temperatureLDDriver(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1066, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_PhotoDiode(MceasMecomIntegratorParams params){
  return MeCom_LDD_Mon_PhotoDiode(params.address, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_ObjectActualTemperature(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1000, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_SinkActualTemperature(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1001, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_targetObjectTemperature(MceasMecomIntegratorParams params){
  return MeCom_ParValuef(params.address, 1010, 1, (MeParFloatFields*)params.fields, MeGet);
}
uint8_t mceas_LDD_Mon_temperatureStable(MceasMecomIntegratorParams params){
  return MeCom_ParValuel(params.address, 1050, 1, (MeParLongFields*)params.fields, MeGet);
}


void lddAppendDataToString(String& data){
  MeParFloatFields fFields;
  MeParLongFields lFields;
  const int NUMBER_OF_FUNCTIONS = 15;
  bool queryFailed = false;
  MceasMecomIntegratorParams paramsFloat = {LDD_ADDRESS, 1, &fFields};
  MceasMecomIntegratorParams paramsLong = {LDD_ADDRESS, 1, &lFields};
  MceasMecomIntegrator lddFunctions[NUMBER_OF_FUNCTIONS] = {
    mceas_LDD_Mon_LaserDiodeCurrentActual,
    mceas_LDD_Mon_LaserDiodeVoltageActual,
    mceas_LDD_Mon_AnodeVoltage,
    mceas_LDD_Mon_CathodeVoltage,
    mceas_LDD_Mon_LaserPower,
    mceas_LDD_Mon_deviceTemperature,
    mceas_LDD_Mon_temperatureLDDriver,
    mceas_LDD_Mon_PhotoDiode,
    mceas_COM_ErrorNumber,
    mceas_COM_ErrorInstance,
    mceas_COM_ErrorParameter,
    mceas_LDD_Mon_ObjectActualTemperature,
    mceas_LDD_Mon_SinkActualTemperature,
    mceas_LDD_Mon_targetObjectTemperature,
    mceas_LDD_Mon_temperatureStable
  };
  MceasMecomIntegratorParams *lddParams[NUMBER_OF_FUNCTIONS] = {
    &paramsFloat,
    &paramsFloat,
    &paramsFloat,
    &paramsFloat,
    &paramsFloat,
    &paramsFloat,
    &paramsFloat,
    &paramsFloat,
    &paramsLong,
    &paramsLong,
    &paramsLong,
    &paramsFloat,
    &paramsFloat,
    &paramsFloat,
    &paramsLong
  };
  for(int i = 0; i < NUMBER_OF_FUNCTIONS; i++){
    if(queryFailed){
      data += BAD_PARAMETER_VALUE;
    }else{
      clearBufferSerial1();
      if(!lddFunctions[i](*lddParams[i])){
        queryFailed = true;
        data += BAD_PARAMETER_VALUE;
      }else{
        if(lddParams[i] == &paramsFloat){
          data += ((MeParFloatFields*)lddParams[i]->fields)->Value;
        } else if(lddParams[i] == &paramsLong){
          data += ((MeParLongFields*)lddParams[i]->fields)->Value;
        }else{
          Serial.println("Wrong type passed to lddParams");
        }   
      }
    }     
    if(i < NUMBER_OF_FUNCTIONS - 1){
      data += DELIMITER;
    }
  }
}

void updateDataString(String& data){
  data = "";
  TIMEPROFILE_BEGIN(TEMP);  
  temperatureAppendDataToString(data);
  TIMEPROFILE_END(TEMP);
  TIMEPROFILE_BEGIN(LDD);
  data += DELIMITER;
  lddAppendDataToString(data);
  TIMEPROFILE_END(LDD);
  TIMEPROFILE_BEGIN(TEC);
  data += DELIMITER;
  tecAppendDataToString(data);
  TIMEPROFILE_END(TEC);
  TIMEPROFILE_BEGIN(PRESSURE);
  data += DELIMITER;
  pressureAppendDataToString(data);
  TIMEPROFILE_END(PRESSURE);
}

void printProfiling(){

  Serial.print("TEMP Total[ms]: ");  Serial.println(TimeProfiler.getProfile("TEMP"));
  Serial.print("LDD Total[ms]: ");   Serial.println(TimeProfiler.getProfile("LDD"));
  Serial.print("TEC Total[ms]: ");   Serial.println(TimeProfiler.getProfile("TEC"));  
  Serial.print("PRESSURE Total[ms]: ");   Serial.println(TimeProfiler.getProfile("PRESSURE")); 
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial1.begin(115200);
  delay(30);
  if (!data.reserve(1000)) { // check the last largest reserve
    while (1) { // stop here and print repeating 
      Serial.println("Strings out-of-memory");
      delay(3000); // repeat msg every 3 sec
    }
  }
  setupRS485();
  setupHDC2022();
  setupPressure();
}

void loop() {
  int8_t buf[25];
  // MeCom_GetIdentString(1, buf);
  // Serial.write("ldd identity string: ");
  //printInt8_t(buf, 25);
  char message[100] = {0};
  if(Serial.available()){
    int i = 0;
    while(Serial.available()){
      message[i] = Serial.read();
      i++;
      //delay is 2 because if it's less the message gets interuppted.
      delay(2);
    }
    message[strcspn(message, "\n")] = 0;
    handleMessage(message);
    MeParFloatFields fFields;  
    // int switchTemp = random(0,2);
    // Fields.Value = switchTemp ? 21.75 : 25;
    // int instance = 1;
    // MeCom_TEC_Tem_TargetObjectTemp(TEC_ADDRESS, instance, &Fields, MeSet);  
  }

  // memset(buf, '\0', 25);
  // MeCom_GetIdentString(TEC_ADDRESS, buf);   
  // Serial.write("tec identity string: ");
  // printInt8_t(buf, 25); 


  updateDataString(data);
  Serial.println(data);


  //printProfiling();
  clearBufferSerial1();

  //delay(1000);

  
}
//#0215CA?IFA98B
//#0215CB?VR03E801946B
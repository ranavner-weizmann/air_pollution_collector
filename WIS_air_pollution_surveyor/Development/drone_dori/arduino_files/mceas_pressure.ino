#include <HDC2080.h>
#include <HoneywellTruStabilitySPI.h>


float pmin = 0;
float pmax = 1.600;
float temperature = 0, humidity = 0;

#define SLAVE_SELECT_PIN SS
#define ADDR 0x41
HDC2080 sensorHDC(ADDR);
TruStabilityPressureSensor sensorPressure( SLAVE_SELECT_PIN, pmin, pmax );

float pressure_formula(float p);

void setup() {

  Serial.begin(9600);
  while(!Serial);

  // Initialize I2C communication
  sensorHDC.begin();
    
  // Begin with a device reset
  sensorHDC.reset();
  
  // Set up the comfort zone
  sensorHDC.setHighTemp(28);         // High temperature of 28C
  sensorHDC.setLowTemp(22);          // Low temperature of 22C
  sensorHDC.setHighHumidity(55);     // High humidity of 55%
  sensorHDC.setLowHumidity(40);      // Low humidity of 40%
  
  // Configure Measurements
  sensorHDC.setMeasurementMode(TEMP_AND_HUMID);  // Set measurements to temperature and humidity
  sensorHDC.setRate(FIVE_HZ);                     // Set measurement frequency to 1 Hz
  sensorHDC.setTempRes(FOURTEEN_BIT);
  sensorHDC.setHumidRes(FOURTEEN_BIT);
  
  //begin measuring
  sensorHDC.triggerMeasurement();

  SPI.begin(); // start SPI communication
  sensorPressure.begin(); // run sensor initialization
}

void loop() {
  if( sensorPressure.readSensor() == 0 ) {
    Serial.print( sensorPressure.rawPressure() );                           Serial.print(",");
    Serial.print( calculatedPressure(float(sensorPressure.rawPressure())));   Serial.print(",");
  }
  Serial.print(sensorHDC.readHumidity());                                   Serial.print(",");
  Serial.println(sensorHDC.readTemp());  
  // Wait 0.2 second for the next reading because maximum reading is 5Hz
  delay(200);
  
}

float calculatedPressure(float rawPressure)
{
  float arduino_bias = 5.010471343994140625;
  return (rawPressure/pow(2,14)-0.1)*1600/0.8 + arduino_bias;
}


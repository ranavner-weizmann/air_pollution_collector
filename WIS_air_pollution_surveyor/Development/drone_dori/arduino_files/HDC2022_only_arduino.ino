#include <HDC2080.h>

#define ADDR 0x41
HDC2080 sensor(ADDR);

float temperature = 0, humidity = 0;

void setup() {

  Serial.begin(115200);
  while(!Serial);

  // Initialize I2C communication
  sensor.begin();
    
  // Begin with a device reset
  sensor.reset();
  
  // Set up the comfort zone
  sensor.setHighTemp(28);         // High temperature of 28C
  sensor.setLowTemp(22);          // Low temperature of 22C
  sensor.setHighHumidity(55);     // High humidity of 55%
  sensor.setLowHumidity(40);      // Low humidity of 40%
  
  // Configure Measurements
  sensor.setMeasurementMode(TEMP_AND_HUMID);  // Set measurements to temperature and humidity
  sensor.setRate(FIVE_HZ);                     // Set measurement frequency to 1 Hz
  sensor.setTempRes(FOURTEEN_BIT);
  sensor.setHumidRes(FOURTEEN_BIT);
  
  //begin measuring
  sensor.triggerMeasurement();
}

void loop() {
  Serial.println(sensor.readTemp());  
  // Wait 0.2 second for the next reading because maximum reading is 5Hz
  delay(200);
  
}

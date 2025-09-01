/*
* Program to fetch data from the IMU, GPS and RTC
* Made by: Nitzan Yizhar
*/
#include <Wire.h>
#include <SparkFun_RV1805.h>
#include "SparkFun_ISM330DHCX.h"
#include "LSM6DS3.h"

// New imu
LSM6DS3 theIMU(I2C_MODE, 0x6A);
// RTC
RV1805 rtc;
// Old imu
SparkFun_ISM330DHCX myISM; 
// Structs for X,Y,Z data
sfe_ism_data_t accelData; 
sfe_ism_data_t gyroData;

unsigned long lastTime = 0;
unsigned long startTime = 0;
unsigned long updateCount = 0;

int beginRTC(){
	/*
		Function to begin the connection to the RTC
	*/
	extern RV1805 rtc;
	if (rtc.begin() == false){
		Serial.println("Please check connection to the RTC. Freezing...");
		while(1){}
	}
	rtc.set24Hour();
	Serial.println("RTC on");
	return 0;
}

int beginIMU(){
	/*
		Function to begin the connection to the IMU
	*/
	if (theIMU.begin() != 0) {
		Serial.print("Please check connection to the IMU. Freezing");
		while(1){}
    }
	Serial.println("IMU on");
	return 0;
}

int beginIMUSpark(){

	if (myISM.begin() == false){
		Serial.println("Did not begin.");
		return -1;
	}

	// Reset the device to default settings. This if helpful is you're doing multiple
	// uploads testing different settings. 
	// myISM.deviceReset();

	// Wait for it to finish reseting
	// while( !myISM.getDeviceReset() ){
	// 	Serial.println("Reset imu");
	// }

	delay(100);
	
	myISM.setDeviceConfig();
	myISM.setBlockDataUpdate();
	
	// Set the output data rate and precision of the accelerometer
	myISM.setAccelDataRate(ISM_XL_ODR_104Hz);
	myISM.setAccelFullScale(ISM_4g); 

	// Set the output data rate and precision of the gyroscope
	myISM.setGyroDataRate(ISM_GY_ODR_104Hz);
	myISM.setGyroFullScale(ISM_500dps); 

	// Turn on the accelerometer's filter and apply settings. 
	myISM.setAccelFilterLP2();
	myISM.setAccelSlopeFilter(ISM_LP_ODR_DIV_100);

	// Turn on the gyroscope's filter and apply settings. 
	myISM.setGyroFilterLP1();
	myISM.setGyroLP1Bandwidth(ISM_MEDIUM);
	return 0;
}



void blink_led(){
	/*
	* Causes the led to blink a few times. This is just for sanity to see the restart
	*/
	// the loop function runs over and over again forever
	unsigned int time_between = 100;
	delay(time_between);
	digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
	delay(time_between);              // wait for a second
	digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
	delay(time_between);              // wait for a second

	digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
	delay(time_between);              // wait for a second
	digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
	delay(time_between);              // wait for a second

	digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
	delay(time_between);              // wait for a second
	digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
	delay(time_between);
	digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
}



void setup(){
	pinMode(LED_BUILTIN, OUTPUT);
	blink_led();
	Wire.begin();
	Serial.begin(115200);
	blink_led();
	beginRTC();
	Serial.println("RTC Began");
	blink_led();
	beginIMU();
	Serial.println("IMU 1 Began");
	blink_led();
	beginIMUSpark();
	Serial.println("IMU 2 Began");
	blink_led();
}

void outputData(){
	extern RV1805 rtc;
	extern LSM6DS3 theIMU;
	if (rtc.updateTime() == true) //Updates the time variables from RTC
	{
		char *currentDate, *currentTime;
		currentDate = rtc.stringDate(); //Get the current date in dd/mm/yyyy format
		currentTime = rtc.stringTime(); //Get the time
		Serial.print("{\"time\": \"");
		Serial.print(currentDate);
		Serial.print(" ");
		Serial.print(currentTime);
		Serial.print("\", ");
	}

	Serial.print(" \"acc_direction_x\": ");
	Serial.print(theIMU.readFloatAccelX(), 4);
	Serial.print(", \"acc_direction_y\": ");
	Serial.print(theIMU.readFloatAccelY(), 4);
	Serial.print(", \"acc_direction_z\": ");
	Serial.print(theIMU.readFloatAccelZ(), 4);
	Serial.print(", \"gyro_rotation_x\": ");
	Serial.print(theIMU.readFloatGyroX(), 4);
	Serial.print(", \"gyro_rotation_y\": ");
	Serial.print(theIMU.readFloatGyroY(), 4);
	Serial.print(", \"gyro_rotation_z\": ");
	Serial.print(theIMU.readFloatGyroZ(), 4);


	if( myISM.checkStatus() ){
		myISM.getAccel(&accelData);
		myISM.getGyro(&gyroData);
		Serial.print(", \"sparkfun_acc_direction_x\": ");
		Serial.print(accelData.xData);
		Serial.print(", \"sparkfun_acc_direction_y\": ");
		Serial.print(accelData.yData);
		Serial.print(", \"sparkfun_acc_direction_z\": ");
		Serial.print(accelData.zData);
		Serial.print(", \"sparkfun_gyro_rotation_x\": ");
		Serial.print(gyroData.xData);
		Serial.print(", \"sparkfun_gyro_rotation_y\": ");
		Serial.print(gyroData.yData);
		Serial.print(", \"sparkfun_gyro_rotation_z\": ");
		Serial.print(gyroData.zData);
	}
	Serial.println("}");
}


void loop(){
	if ((millis() - lastTime) > 50){
		lastTime = millis();
		outputData();
	}
}

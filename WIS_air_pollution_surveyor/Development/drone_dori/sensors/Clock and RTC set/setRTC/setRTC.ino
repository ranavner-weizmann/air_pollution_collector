/*
* Arduino program to set the rtc time
* The idea is to quickly load and run the program so it sets the RTC time
* to the currect time.
* Made by: Nitzan Yizhar
*/




#include <SparkFun_RV1805.h>
RV1805 rtc;

void setup(){
    Wire.begin();
    rtc.begin();
    if (rtc.setToCompilerTime() == false) {
   		Serial.println("Something went wrong setting the time");
  	}
}


void loop(){}
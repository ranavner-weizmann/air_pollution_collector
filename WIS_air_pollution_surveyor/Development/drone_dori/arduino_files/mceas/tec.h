#ifndef TEC_FUNCTIONS_H
#define TEC_FUNCTIONS_H
#include <Arduino.h>

#define OUTPUT_TEMPERATURE_COMMAND "#020029?VR03E8019877\r"
#define OUTPUT_CURRENT_COMMAND "#020029?VR03FC012B52\r"
#define OUTPUT_VOLTAGE_COMMAND "#024823?VR03FD012406\r"

float getResponseFromCommand(const char *command);
float calculateObjectValueFromReponse(const char *respose);


#endif
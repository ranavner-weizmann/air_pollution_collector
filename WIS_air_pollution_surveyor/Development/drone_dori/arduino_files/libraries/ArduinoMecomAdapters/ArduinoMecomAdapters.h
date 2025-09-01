#ifndef ARDUINO_ADAPTER_H
#define ARDUINO_ADAPTER_H
#include "../MeCom/MeCom.h"

void arduinoWaitSecondsMili(int miliSeconds);
void arduinoWaitSecondsMicro(int microSeconds);
void tryToReceiveSerial1(int destination);
void writeToSerial1(char *in);
void writeToSerial(char *toWrite);
void arduinoMemset(void *dest, int ch, int count);

extern const bool DEBUG_MEPORT;

#define MEERSTETER_DESTINATION 1

#endif

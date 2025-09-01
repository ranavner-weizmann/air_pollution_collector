#include "../ArduinoMecomAdapters/ArduinoMecomAdapters.h"

void ComPort_Send(char *in)
{
  writeToSerial1(in);
  tryToReceiveSerial1(MEERSTETER_DESTINATION);
}
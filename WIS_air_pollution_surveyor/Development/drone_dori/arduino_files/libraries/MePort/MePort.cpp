#include <stdint.h>
#include "MePort.h"
#include "../ArduinoMecomAdapters/ArduinoMecomAdapters.h"
#include "../MeCom/MeCom.h"
#include "../MeFrame/MeFrame.h"

static volatile uint8_t SemaphorHandler = 0;
void MePort_SendByte(int8_t in, MePort_SB FirstLast)
{
  static char Buffer[MEPORT_MAX_TX_BUF_SIZE];
  static int Ctr;

  switch (FirstLast)
  {
  case MePort_SB_IsFirstByte:
    // This is the first Byte of the Message String
    // add memset because of bug:
    /*
    bug was that somehow, the 0 terminating that happend in the LAST_BYTE didn't work,
    causing the last few bytes from the VR query to stay in the buffer, because this query is larger than the if one
    */
    arduinoMemset(Buffer, 0, MEPORT_MAX_TX_BUF_SIZE);
    Ctr = 0;
    Buffer[Ctr] = in;
    Ctr++;
    break;
  case MePort_SB_Normal:
    // These are some middle Bytes
    if (Ctr < MEPORT_MAX_TX_BUF_SIZE - 1)
    {
      Buffer[Ctr] = in;
      Ctr++;
    }
    break;
  case MePort_SB_IsLastByte:
    // This is the last Byte of the Message String
    if (Ctr < MEPORT_MAX_TX_BUF_SIZE - 1)
    {
      ComPort_Send(Buffer);
    }
    break;
  }
}
void MePort_ReceiveByte(int8_t *arr)
{
  while (*arr)
  {
    if (*arr == '\n')
      *arr = '\r';
    MeFrame_Receive(*arr);
    arr++;
  }
}
void MePort_SemaphorTake(uint32_t TimeoutMs)
{
  while (SemaphorHandler == 0)
  {    
    if (TimeoutMs > 0)
      TimeoutMs -= 10;
    else
      return;
    arduinoWaitSecondsMili(10);
  }
  SemaphorHandler = 0;
}
void MePort_SemaphorGive(void)
{
  SemaphorHandler = 1;
}
void MePort_ErrorThrow(int32_t ErrorNr)
{
  if (!DEBUG_MEPORT)
  {
    return;
  }
  switch (ErrorNr)
  {
  case MEPORT_ERROR_CMD_NOT_AVAILABLE:
    writeToSerial("MePort Error: Command not available\n");
    break;

  case MEPORT_ERROR_DEVICE_BUSY:
    writeToSerial("MePort Error: Device is Busy\n");
    break;

  case MEPORT_ERROR_GENERAL_COM:
    writeToSerial("MePort Error: General Error\n");
    break;

  case MEPORT_ERROR_FORMAT:
    writeToSerial("MePort Error: Format Error\n");
    break;

  case MEPORT_ERROR_PAR_NOT_AVAILABLE:
    writeToSerial("MePort Error: Parameter not available\n");
    break;

  case MEPORT_ERROR_PAR_NOT_WRITABLE:
    writeToSerial("MePort Error: Parameter not writable\n");
    break;

  case MEPORT_ERROR_PAR_OUT_OF_RANGE:
    writeToSerial("MePort Error: Parameter out of Range\n");
    break;

  case MEPORT_ERROR_PAR_INST_NOT_AVAILABLE:
    writeToSerial("MePort Error: Parameter Instance not available\n");
    break;

  case MEPORT_ERROR_SET_TIMEOUT:
    writeToSerial("MePort Error: Set Timeout\n");
    break;

  case MEPORT_ERROR_QUERY_TIMEOUT:
    writeToSerial("MePort Error: Query Timeout\n");
    break;
  }
}
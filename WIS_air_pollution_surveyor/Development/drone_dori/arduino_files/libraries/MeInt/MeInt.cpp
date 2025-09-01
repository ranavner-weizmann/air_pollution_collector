#include <stdint.h>
#include <stdio.h>
#include "../MeFrame/MeFrame.h"
#include "../ArduinoMecomAdapters/ArduinoMecomAdapters.h"
#include "../MeVarConv/MeVarConv.h"

int8_t *MeInt_QueryRcvPayload = MeFrame_RcvFrame.Payload;
static uint16_t SequenceNr = 5545;
uint8_t MeInt_Query(int8_t Control, uint8_t Address, uint32_t Length, int8_t *Payload)
{
    const bool DEBUG_QUERY = false;
    SequenceNr++;

    int32_t Trials = 3;
    while (Trials > 0)
    {

        Trials--;
        MeFrame_RcvFrame.DataReceived = 0;
        MeFrame_RcvFrame.AckReceived = 0;
        // if(Trials % 2 == 1) {
        //     if(DEBUG_QUERY){
        //         writeToSerial("send\n");
        //     }
        //     MeFrame_Send(Control, Address, Length, SequenceNr, Payload);
        // } else {
        //     if(DEBUG_QUERY){
        //         writeToSerial("only try\n");
        //     }            
        //     tryToReceiveSerial1(MEERSTETER_DESTINATION);
        // } 
        MeFrame_Send(Control, Address, Length, SequenceNr, Payload);       
        //MePort_SemaphorTake(MEPORT_SET_AND_QUERY_TIMEOUT);
        //arduinoWaitSecondsMili(100);
        char debugMessage[100] = {0};
        if(DEBUG_QUERY){
            sprintf(debugMessage, "condition 1: %d, condition 2: %d, condition 3: %d\n", MeFrame_RcvFrame.DataReceived == 1, MeFrame_RcvFrame.Address == Address, MeFrame_RcvFrame.SeqNr == SequenceNr);
            writeToSerial(debugMessage);
            sprintf(debugMessage, "expected sequence %d but got %d\n", SequenceNr, MeFrame_RcvFrame.SeqNr);
            writeToSerial(debugMessage);
        }
        if (MeFrame_RcvFrame.DataReceived == 1 && MeFrame_RcvFrame.Address == Address && MeFrame_RcvFrame.SeqNr == SequenceNr)
        {
            // Correct Data Received -->Check for Error Code
            if (MeFrame_RcvFrame.Payload[0] == '+')
            {
                // Server Error code Received
                MePort_ErrorThrow(MeVarConv_HexToUc(&MeFrame_RcvFrame.Payload[1]));
                return 0;
            }
            return 1;
        }
    }
    MePort_ErrorThrow(MEPORT_ERROR_QUERY_TIMEOUT);
    return 0;
}
uint8_t MeInt_Set(int8_t Control, uint8_t Address, uint32_t Length, int8_t *Payload)
{
    SequenceNr++;

    int32_t Trials = 3;
    while (Trials > 0)
    {
        Trials--;
        MeFrame_RcvFrame.DataReceived = 0;
        MeFrame_RcvFrame.AckReceived = 0;
        MeFrame_Send(Control, Address, Length, SequenceNr, Payload);
        if (Address == 255)
            return 1;
        MePort_SemaphorTake(MEPORT_SET_AND_QUERY_TIMEOUT);
        arduinoWaitSecondsMili(1);
        if (MeFrame_RcvFrame.DataReceived == 1 && MeFrame_RcvFrame.Address == Address && MeFrame_RcvFrame.SeqNr == SequenceNr &&
            MeFrame_RcvFrame.Payload[0] == '+')
        {
            // Server Error code Received
            MePort_ErrorThrow(MeVarConv_HexToUc(&MeFrame_RcvFrame.Payload[1]));
            return 0;
        }
        else if (MeFrame_RcvFrame.AckReceived == 1 && MeFrame_RcvFrame.Address == Address && MeFrame_RcvFrame.SeqNr == SequenceNr)
        {
            // Correct ADC received
            return 1;
        }
    }
    MePort_ErrorThrow(MEPORT_ERROR_SET_TIMEOUT);
    return 0;
}
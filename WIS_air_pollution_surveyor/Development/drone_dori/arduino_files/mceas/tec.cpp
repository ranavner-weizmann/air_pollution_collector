#include "tec.h"
#include <SoftwareSerial.h>

#define rxPIN 0
#define txPIN 1
void hexCharacterStringToBytes(byte *byteArray, const char *hexString);
void getSubstring(const char *source, int start, int end, char *destination);
void reverseByteArray(uint8_t *array, int length);
byte nibble(char c);
void dumpByteArray(const byte *byteArray, const byte arraySize);
void hexCharacterStringToBytes(byte *byteArray, const char *hexString);

/*
    Once you fix the serial and can send serial messages from the arduino the TEC
    you can use this command to get the reponse this program parses:
    #020029?VR03E8019877
    If this doesn't work you can use the main.c program with address 2, instance 2
    and paramter id to be 1000.
    You can see other parmaters id for different queries in the memcom/commands.py
*/
union floatUnpack{
    float packedFloat;
    byte packedBytes[sizeof(float)];
};

float calculateObjectValueFromReponse(const char *respose){
    floatUnpack packedValue;
    char floatPart[sizeof(float) * 2] = {0};
    getSubstring(respose, 7, 15, floatPart);
    // Serial.print("Substring is: ");
    // Serial.println(floatPart);
    hexCharacterStringToBytes(packedValue.packedBytes, floatPart);
    reverseByteArray(packedValue.packedBytes, sizeof(float));
    return packedValue.packedFloat;
}

float getResponseFromCommand(const char *command){
    unsigned int const responseBufferLen = 30;
    unsigned long maxTime = 5000;
    unsigned long startTime = millis();
    char responseBuffer[responseBufferLen] = {0};
    Serial1.print(command);
    Serial1.flush();
    while(Serial1.available() == 0){ if ((millis() - startTime) > maxTime){return 0.0;}};
    Serial1.readString().toCharArray(responseBuffer, responseBufferLen);
    return calculateObjectValueFromReponse(responseBuffer);
}


/*
    Code taken from: https://forum.arduino.cc/t/hex-string-to-byte-array/563827/3
    Written by: johnwasser

*/
void hexCharacterStringToBytes(byte *byteArray, const char *hexString)
{
    bool oddLength = strlen(hexString) & 1;

    byte currentByte = 0;
    byte byteIndex = 0;

    for (byte charIndex = 0; charIndex < strlen(hexString); charIndex++)
    {
      bool oddCharIndex = charIndex & 1;

      if (oddLength)
      {
        // If the length is odd
        if (oddCharIndex)
        {
          // odd characters go in high nibble
          currentByte = nibble(hexString[charIndex]) << 4;
        }
        else
        {
          // Even characters go into low nibble
          currentByte |= nibble(hexString[charIndex]);
          byteArray[byteIndex++] = currentByte;
          currentByte = 0;
        }
      }
      else
      {
        // If the length is even
        if (!oddCharIndex)
        {
          // Odd characters go into the high nibble
          currentByte = nibble(hexString[charIndex]) << 4;
        }
        else
        {
          // Odd characters go into low nibble
          currentByte |= nibble(hexString[charIndex]);
          byteArray[byteIndex++] = currentByte;
          currentByte = 0;
        }
      }
    }
}
void dumpByteArray(const byte *byteArray, const byte arraySize)
{

    for (int i = 0; i < arraySize; i++)
    {
      Serial.print("0x");
      if (byteArray[i] < 0x10)
        Serial.print("0");
      Serial.print(byteArray[i], HEX);
      Serial.print(", ");
    }
    Serial.println();
}
byte nibble(char c)
{
    if (c >= '0' && c <= '9')
      return c - '0';

    if (c >= 'a' && c <= 'f')
      return c - 'a' + 10;

    if (c >= 'A' && c <= 'F')
      return c - 'A' + 10;

    return 0; // Not a valid hexadecimal character
}
void reverseByteArray(uint8_t *array, int length)
{
    int start = 0;
    int end = length - 1;

    while (start < end)
    {
      uint8_t temp = array[start];
      array[start] = array[end];
      array[end] = temp;
      start++;
      end--;
    }
}
void getSubstring(const char *source, int start, int end, char *destination)
{
    int sourceLength = strlen(source);

    // Adjust start and end indices if they are out of bounds
    if (start < 0)
      start = 0;
    if (end >= sourceLength)
      end = sourceLength - 1;

    int destinationLength = end - start;

    // Copy the substring from source to destination
    strncpy(destination, source + start, destinationLength);
    destination[destinationLength] = '\0';
}
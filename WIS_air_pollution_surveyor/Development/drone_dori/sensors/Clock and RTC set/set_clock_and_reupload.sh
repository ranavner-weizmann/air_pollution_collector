#!/bin/sh

if [ $# -ne 2 ]
then
    echo "Usage: $0 <fqbn of RTC> <Port>"
    exit 1
fi

arduino-cli compile -u -p $2 --fqbn $1 ./setRTC
if [ $? -eq 1 ]
then
    echo "Failed uploading clock set"
    exit 1
fi
echo "Upload of clock set done"

arduino-cli compile -u -p $2 --fqbn $1 ./imu_gps_rtc
if [ $? -eq 1 ]
then
    echo "Failed uploading deploy"
    exit 1
fi
echo "Fininshed Setting RTC"


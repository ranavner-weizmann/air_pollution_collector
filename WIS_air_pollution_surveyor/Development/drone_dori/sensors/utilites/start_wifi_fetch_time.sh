sudo ifconfig wlan0 up
sudo iwconfig wlan0 essid WIS_Hotspot
sudo dhclient wlan0
# Fetching the current date and time from an online HTTP server
# Note: This uses the date from HTTP headers, which may not be very accurate
time_from_server=$(curl -s --head http://worldtimeapi.org/api/timezone/Etc/UTC | grep date: | sed 's/date: //i')

# Converting HTTP date to a format suitable for 'date' command
formatted_date=$(date -d "$time_from_server" '+%m%d%H%M%Y.%S')

# Setting the system date and time
sudo date $formatted_date
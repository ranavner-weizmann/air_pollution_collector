sudo ifconfig $1 up
sudo iwconfig $1 essid WIS_Hotspot
sudo dhclient $1

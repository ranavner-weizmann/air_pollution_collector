### Preliminary Notes
1. pi time sync: only with wifi: (install first jq) bash: curl -s http://worldtimeapi.org/api/timezone/Etc/UTC | jq -r '.unixtime'
2. connecting to pi using SSH (user: rpi, password: 123qweASD)
3. installed packages that DJI PSDK require: bash install_dependencies.sh (will take some time, also there is some manual downloading needed): 

https://developer.dji.com/doc/payload-sdk-tutorial/en/quick-start/quick-guide/raspberry-pi.html


4. Verify the packages were installed.
5. delete the installing files using: bash cleanup.sh
6. raspi-usb-device-start.sh is a file that determine the USB connection of the pi so it'll work with the PSDK. move it to /use/local/sbin/
7. run: sudo chmod +x /usr/local/sbin/raspi-usb-device-start.sh
8. run: sudo sed -i 's/enable_bulk=.*/enable_bulk=1/' /usr/local/sbin/raspi-usb-device-start.sh
        sudo sed -i 's/enable_vcom=.*/enable_vcom=0/' /usr/local/sbin/raspi-usb-device-start.sh
        sudo sed -i 's/enable_rndis=.*/enable_rndis=0/' /usr/local/sbin/raspi-usb-device-start.sh

        that's for choosing BULK mod for the USB connection. 

9. run: sudo /usr/local/sbin/raspi-usb-device-start.sh
    the pi will reboot

10. find a image that is already created by other people and use it instead of doing steps 3 - 9. (hint: https://sdk-forum.dji.net/hc/zh-cn/articles/10232604141465-%E6%A0%91%E8%8E%93%E6%B4%BE4B%E9%85%8D%E7%BD%AEUSB-device-RNDIS-%E5%92%8C-BULK)
11. change password! defult is 'rsp'
12. find a way to sync the f time
13. clone the psdk repo by running psdk_install.sh
14. create an app in the psdk developer center (DJI)
15. change the necessary files (with app id, name... usb configurations, etc.) (more info: https://developer.dji.com/doc/payload-sdk-tutorial/en/quick-start/E-Port%20Quick%20Start/raspberry-pi.html?utm_source=chatgpt.com)
16. 
17. 




### Preliminary Notes
1. pi time sync: only with wifi: bash: curl -s http://worldtimeapi.org/api/timezone/Etc/UTC | jq -r '.unixtime'
2. connecting to pi using SSH (user: ranavner, password: 123qweASD)
3. installed packages that DJI PSDK require: bash install_dependencies.sh (will take some time, also there is some manual downloading needed): 

https://developer.dji.com/doc/payload-sdk-tutorial/en/quick-start/quick-guide/raspberry-pi.html


4. Verify the packages were installed.
5. delete the installing files using: bash cleanup.sh
6. 
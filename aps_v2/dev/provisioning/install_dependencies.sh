/* Update software repository */
sudo apt-get update
sudo apt-get upgrade

 /* Install libaio */
sudo apt-get install automake
sudo apt-get install libaio-dev

/* Download opus-1.3.1 source code from https://opus-codec.org/ and install it */
tar -xzvf opus-1.3.1.tar.gz
cd opus-1.3.1/
autoreconf -f -i
./configure
 make -j4 && sudo make install

/* Download ffmpeg 4.3 source code from github and install it */
tar -zxvf ffmpeg-4.3.2.tar.gz
./configure --enable-shared
make -j4
sudo make install

/* Download opecv 3.4.15 source code from https://opencv.org/releases/ and install it */
unzip opencv-3.4.15.zip
cd opencv-3.4.15/
mkdir build && cd build/
cmake ../
make -j4 && sudo make install
/* Check opencv version*/
opencv_version

/* Install libusb */
sudo apt-get install libusb-1.0-0-dev
sudo apt install -y build-essential cmake git pkg-config \
                    libssl-dev libusb-1.0-0-dev libudev-dev
mkdir -p ~/djipsdk && cd ~/djipsdk
git clone https://github.com/dji-sdk/Payload-SDK.git
cd Payload-SDK/samples
mkdir -p build && cd build
cmake ../..
make -j"$(nproc)"

#!/bin/bash
# Cleanup script after building Opus, FFmpeg, and OpenCV from source

echo "Starting cleanup..."

# Remove source + build directories (adjust paths if needed)
rm -rf ~/opus-1.5.2
rm -rf ~/ffmpeg-8.0
rm -rf ~/opencv-4.12.0

# Clear apt cache to free space
sudo apt-get clean
sudo apt-get autoremove -y

# Optional: remove leftover tarballs/zip if still around
rm -f ~/opus-1.5.2.tar.gz
rm -f ~/ffmpeg-8.0.tar.gz
rm -f ~/opencv-4.12.0.zip

# Show free disk space after cleanup
echo "Cleanup complete. Disk usage now:"
df -h /

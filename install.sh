#!/bin/bash

echo "Hey! Setting up ArchBuddy on Arch live USB! 🐧"
if [ "$EUID" -ne 0 ]; then
    echo "Run with sudo: sudo ./install.sh"
    exit 1
fi
echo "Updating system..."
pacman -Syu --noconfirm
echo "Installing Python and PyQt5..."
pacman -S --noconfirm python python-pyqt5
echo "Installing pacstrap and parted..."
pacman -S --noconfirm arch-install-scripts parted
echo "Downloading archbuddy.py..."
wget -O archbuddy.py https://raw.githubusercontent.com/klovych/archbuddy/main/archbuddy.py
chmod +x archbuddy.py

echo "Ready! Run: sudo ./archbuddy.py"
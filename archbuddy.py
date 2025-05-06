#!/usr/bin/env python3

import sys
import subprocess
import parted
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QProgressBar, QCheckBox
from PyQt5.QtCore import Qt

class ArchBuddyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ArchBuddy 🐧 - Arch Linux Installer")
        self.setGeometry(100, 100, 500, 600)
        self.setup_ui()

    def setup_ui(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
        widget.setLayout(layout)
        welcome = QLabel("Welcome to ArchBuddy! Let’s install Arch Linux! 😄")
        welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome)
        layout.addWidget(QLabel("Choose language:"))
        self.language = QComboBox()
        self.language.addItems(["English", "Russian"])
        layout.addWidget(self.language)
        layout.addWidget(QLabel("Select disk for installation:"))
        self.disk = QComboBox()
        self.disks = self.get_disks()
        self.disk.addItems(self.disks)
        layout.addWidget(self.disk)
        self.luks = QCheckBox("Enable LUKS encryption")
        layout.addWidget(self.luks)
        layout.addWidget(QLabel("Pick a desktop:"))
        self.desktop = QComboBox()
        self.desktop.addItems(["None", "KDE", "GNOME", "XFCE", "i3"])
        layout.addWidget(self.desktop)
        layout.addWidget(QLabel("Extra apps (e.g., neofetch, vim):"))
        self.apps = QLineEdit()
        self.apps.setPlaceholderText("Type apps, split by commas")
        layout.addWidget(self.apps)
        self.install_btn = QPushButton("Install Arch! 🚀")
        self.install_btn.clicked.connect(self.start_install)
        layout.addWidget(self.install_btn)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status = QLabel("Ready to start!")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

    def get_disks(self):
        try:
            result = subprocess.run(["lsblk", "-d", "-n", "-o", "NAME"], capture_output=True, text=True)
            return [f"/dev/{line}" for line in result.stdout.splitlines()]
        except:
            return ["/dev/sda"]

    def start_install(self):
        self.install_btn.setEnabled(False)
        self.status.setText("Starting installation... 🛠️")
        self.progress.setValue(5)

        disk = self.disk.currentText()
        luks = self.luks.isChecked()
        desktop = self.desktop.currentText()
        apps = self.apps.text().strip()

        try:
            self.status.setText("Partitioning disk...")
            disk_dev = parted.getDevice(disk)
            disk = parted.Disk(disk_dev)
            disk.deleteAllPartitions()
            esp = disk.partitionNew(parted.PARTITION_NORMAL, "fat32", 1, 512)
            root = disk.partitionNew(parted.PARTITION_NORMAL, "ext4", 512, disk_dev.getLength())
            esp.setFlag(parted.PARTITION_ESP)
            disk.commit()
            subprocess.run(["mkfs.fat", "-F32", f"{disk}.1"], check=True)
            subprocess.run(["mkfs.ext4", f"{disk}.2"], check=True)
            if luks:
                subprocess.run(["cryptsetup", "luksFormat", f"{disk}.2"], input="password\n", text=True, check=True)
                subprocess.run(["cryptsetup", "open", f"{disk}.2", "root"], input="password\n", text=True, check=True)
                subprocess.run(["mkfs.ext4", "/dev/mapper/root"], check=True)
            self.progress.setValue(20)
            self.status.setText("Installing base system...")
            mount_point = "/mnt"
            if luks:
                subprocess.run(["mount", "/dev/mapper/root", mount_point], check=True)
            else:
                subprocess.run(["mount", f"{disk}.2", mount_point], check=True)
            subprocess.run(["mkdir", f"{mount_point}/boot"], check=True)
            subprocess.run(["mount", f"{disk}.1", f"{mount_point}/boot"], check=True)
            subprocess.run(["pacstrap", mount_point, "base", "linux", "linux-firmware"], check=True)
            self.progress.setValue(50)
            self.status.setText("Setting up system files...")
            subprocess.run(["genfstab", "-U", mount_point], stdout=open(f"{mount_point}/etc/fstab", "w"))
            self.progress.setValue(60)
            self.status.setText("Configuring system...")
            with open(f"{mount_point}/setup.sh", "w") as f:
                f.write("#!/bin/bash\n")
                f.write("pacman -Syu --noconfirm\n")
                f.write("pacman -S --noconfirm networkmanager\n")
                f.write("systemctl enable NetworkManager\n")
                if desktop != "None":
                    pkgs = {"KDE": "plasma", "GNOME": "gnome", "XFCE": "xfce4", "i3": "i3"}[desktop]
                    f.write(f"pacman -S --noconfirm {pkgs} xorg\n")
                    f.write(f"systemctl enable {'sddm' if desktop == 'KDE' else 'gdm' if desktop == 'GNOME' else 'lightdm'}\n")
                if apps:
                    f.write(f"pacman -S --noconfirm {apps.replace(',', ' ')}\n")
                f.write("echo 'root:password' | chpasswd\n")
                f.write("bootctl --path=/boot install\n")
                f.write(f"echo 'LANG={self.language.currentText().lower()}.UTF-8' > /etc/locale.conf\n")
                f.write("locale-gen\n")
            subprocess.run(["chmod", "+x", f"{mount_point}/setup.sh"], check=True)
            subprocess.run(["arch-chroot", mount_point, "/bin/bash", "/setup.sh"], check=True)
            self.progress.setValue(90)
            self.status.setText("All done! Reboot to use Arch! 🎉")
            self.progress.setValue(100)
        except Exception as e:
            self.status.setText(f"Oops, something broke: {e}")
            self.install_btn.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArchBuddyWindow()
    window.show()
    sys.exit(app.exec_())
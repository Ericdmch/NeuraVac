# Immediate TODO: Ubuntu and ROS2 Installation

Install **Ubuntu Server 24.04 LTS, 64-bit + ROS2 Jazzy** on the Raspberry Pi 4 or 5. Use Ubuntu 24.04 specifically to match Jazzy's supported release. [ROS2 installation instructions](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/Ubuntu-Install-Debs.rst)

## 1. Flash Ubuntu from your computer

Use a spare **32 GB or larger microSD card** if possible to preserve the existing installation. Flashing erases the selected card.

- [ ] Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
- [ ] Select the Pi model and **Ubuntu Server 24.04 LTS (64-bit)**.
- [ ] If absent from the menu, download the **Raspberry Pi preinstalled server image** from [Ubuntu's 24.04 downloads](https://cdimage.ubuntu.com/releases/24.04/release/) and select **Use custom** in Imager.
- [ ] Configure a username, password, hostname such as `neuravac`, Wi-Fi, and **SSH** when offered. Ethernet is also suitable for initial setup.
- [ ] Select the correct microSD card and write the image.
- [ ] Insert the card into the Pi, power on, and wait for first-boot configuration to finish before logging in.

Reference: [Ubuntu's Pi setup guide](https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi).

## 2. Connect and update

- [ ] From your computer's terminal, connect using your actual username and Pi IP address:

```sh
ssh your_username@PI_IP_ADDRESS
```

**Run all remaining commands on the Pi through SSH.**

- [ ] Verify the OS and architecture:

```sh
cat /etc/os-release
dpkg --print-architecture
```

Expected: Ubuntu **24.04** and **arm64**. Stop and correct the image selection if these differ.

- [ ] Update and reboot:

```sh
sudo apt update
sudo apt upgrade -y
sudo reboot
```

- [ ] Reconnect over SSH after reboot.

## 3. Configure the ROS2 package repository

- [ ] Configure a UTF-8 locale and enable Ubuntu Universe:

```sh
sudo apt install -y locales software-properties-common curl
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8
export LANG=en_US.UTF-8
sudo add-apt-repository -y universe
```

References: official [locale setup](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/_Ubuntu-Set-Locale.rst) and [repository setup](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/_Apt-Repositories.rst).

- [ ] Install the ROS repository configuration package, using the verified `1.3.0` release:

```sh
ROS_APT_SOURCE_VERSION=1.3.0

curl -fL \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.noble_all.deb" \
  -o /tmp/ros2-apt-source.deb

sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
```

Reference: [official ROS apt-source release](https://github.com/ros-infrastructure/ros-apt-source/releases/tag/1.3.0).

## 4. Install ROS2 and SLAM tools

- [ ] Install ROS Base, development tools, SLAM Toolbox, recording tools, and test nodes:

```sh
sudo apt install -y \
  ros-jazzy-ros-base \
  ros-dev-tools \
  ros-jazzy-slam-toolbox \
  ros-jazzy-rosbag2 \
  ros-jazzy-demo-nodes-cpp \
  ros-jazzy-demo-nodes-py
```

ROS Base provides the communication libraries and command-line tools without a desktop installation. [ROS2 package options](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/Ubuntu-Install-Debs.rst) · [SLAM Toolbox package](https://index.ros.org/p/slam_toolbox/)

- [ ] Enable ROS in the current terminal and future Bash sessions; append the startup line once:

```sh
source /opt/ros/jazzy/setup.bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
```

## 5. Verify ROS2 works

- [ ] In the first SSH terminal, start the publisher:

```sh
ros2 run demo_nodes_cpp talker
```

- [ ] Open a second SSH terminal to the Pi and start the subscriber:

```sh
ros2 run demo_nodes_py listener
```

- [ ] Confirm the listener prints messages beginning with **“I heard”**.
- [ ] Stop both processes with `Ctrl+C`.

Reference: [official talker/listener verification](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/Ubuntu-Install-Debs.rst).

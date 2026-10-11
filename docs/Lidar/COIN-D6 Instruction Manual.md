# COIN-D6 Instruction Manual

Source: [COIN-D6 Instruction Manual.pdf](_originals/COIN-D6%20Instruction%20Manual.pdf).

Complete extracted text is included page by page, with spacing preserved for tables. Each page image preserves diagrams, screenshots, formatting, and any content that cannot be represented as text. Original language and wording are retained.

## Page 1

```text
          COIN-D6 Instruction Manual




Product Specification Sheet:

Model: COIN-D6 (Guoke Optoelectronics)

Description: LiDAR
```

![Complete source page 1](_assets/COIN-D6%20Instruction%20Manual/page-01.png)

## Page 2

```text
                                                              Contents
1. Product Overview ........................................................................................................................ 3

2. Parameter Indicators ................................................................................................................. 4

      2.1 Performance Parameters ............................................................................................... 4

      2.2 Mechanical Parameters ...................................................................................................5

      2.3 Optical Window .................................................................................................................. 6

      2.4 Installation and External Dimensions ....................................................................... 7

      2.5 Definition of Scan Data Coordinate System ........................................................... 7

3. Hardware Connection .................................................................................................................8

4. Instructions for Use .................................................................................................................... 9

      4.1 Windows System ...............................................................................................................9

             4.1.1 Installing the driver ..............................................................................................9

             4.1.2 PC Software Usage ............................................................................................. 10

      4.1.3. Serial Port Start Radar ............................................................................................ 12

      4.2 ROS2 .................................................................................................................................... 12
```

![Complete source page 2](_assets/COIN-D6%20Instruction%20Manual/page-02.png)

## Page 3

```text
1. Product Overview
The COIN-D6 is a new generation coaxial 360° scanning ranging lidar
developed by Guoke Optoelectronics. The product is based on direct
flight...

the time-to-time (dToF) ranging principle, with its internal rotating
components employing wireless power supply and optoelectronic
communication technology. Combined with optical, electrical , and
algorithmic design, it achieves high-frequency, high-precision distance
measurement with a maximum measurement radius of 12 meters. This
product is suitable for practical applications such as map surveying,
intelligent device navigation and obstacle avoidance, and environmental
modeling.

Product Features:

   Maximum measurement range: 0.05m~12m.

   The direct time-of-flight (dToF) ranging principle is adopted.

   Scanning range 360°, angular resolution 0.9°.

   Coaxial design, compact size, can be built-in installation.

It uses a brushless motor with a long service life of over 10,000 hours.

Product information package:
https://drive.google.com/drive/folders/1_XfZTemyIBoZssQmFW5Jx17jxx3
hn337?usp=drive_link
```

![Complete source page 3](_assets/COIN-D6%20Instruction%20Manual/page-03.png)

## Page 4

```text
2. Parameter Indicators

2.1 Performance Parameters

                Minimum   Typical   Maximum
   project                                    unit    Remark
                 value    value      value


    laser
                  890      905        920     nm          -
 wavelength


 Laser safety      -      Class1       -       -     (IEC-60825)


Measurement                                          90% diffuse
                 0.05       10        12       m
    range                                            reflectance


Measurement                                          10% diffuse
                 0.05       8         10       m
    range                                            reflectance


 Accuracy ①       ±10        -         -      mm      0.05-1m


 Accuracy ①       ±30      ±40         -      mm        >1m


Field of view      -         -        360      °          -


 Pitch angle       0         -         2       °          -


   Angular
                   -        0.9        -       °          -
  resolution


 Frequency         -       4000        -      Hz          -


Anti-ambient       -         -        60K      lx    Referencing
```

![Complete source page 4](_assets/COIN-D6%20Instruction%20Manual/page-04.png)

## Page 5

```text
     light                                                   the Guoke
                                                           Optoelectronic
                                                            Core Testing
                                                               Method


  rotational
                     -          10           15      Hz            -
    speed


Rated power          -          1.2          1.6      W            -


  Operating
                    -10         25           50       ℃            -
 temperature


   Storage
                    -30         25           70       ℃            -
 temperature


   Overall
                     -      10000             -       H            -
   lifespan


2.2 Mechanical Parameters

project                          parameter


Waterproof rating                IPX4


weight                           40g (excluding external wiring)


External dimensions (length *
                                 52.7mm*45.2mm*34.4mm
width * height)
```

![Complete source page 5](_assets/COIN-D6%20Instruction%20Manual/page-05.png)

## Page 6

```text
2.3 Optical Window

To prevent dust from affecting radar ranging performance, please keep
the product's optical window clean. To ensure normal radar operation, the
external radar system design must avoid obstructing the radar's optical
window. For special installation requirements or if the radar needs to be
encased in a translucent material, please contact Guoke Optoelectronics
technical personnel to discuss feasibility. Using the sensor base plane as a
reference, the height of the COIN-D6 laser emission point from the base
plane is 26.9mm.
```

![Complete source page 6](_assets/COIN-D6%20Instruction%20Manual/page-06.png)

## Page 7

```text
2.4 Installation and External Dimensions




2.5 Definition of Scan Data Coordinate
System

COIN-D6 uses a coordinate system that follows the left-hand rule. The
origin of the coordinate system is the center of rotation of the distance
measurement core, and the rotation angle increases with clockwise
rotation. The coordinate system definition is shown in the figure below:
```

![Complete source page 7](_assets/COIN-D6%20Instruction%20Manual/page-07.png)

## Page 8

```text
3. Hardware Connection
According to wire colors: yellow to 5V, white to GND, red to TXD, black to RXT.
```

![Complete source page 8](_assets/COIN-D6%20Instruction%20Manual/page-08.png)

## Page 9

```text
4. Instructions for Use

4.1 Windows System

4.1.1 Installing the driver

CH340 Download Link:https://drive.google.com/drive/folders/15z3-9ImOwGho-
p0NmA83ccnkjxUcmqtM?usp=drive_link




Double-click the SETUP.EXT program to begin installing the driver.




Click "Install" to begin driver installation.
```

![Complete source page 9](_assets/COIN-D6%20Instruction%20Manual/page-09.png)

## Page 10

```text
Install the USB serial port driver; if you already have one, you can skip
this step. After installing the driver, plug the USB into your computer and
it will display "USB-SERIAL".

CH340 (COMX) indicates that the driver installation was successful, as
shown in the figure.




4.1.2 PC Software Usage

PC software download link:
https://drive.google.com/file/d/1SBqWE_DmlgveFHY05U8B0erPRvElEP9v/
view?usp=drive_link

the PC software package provided by CSPC and run the PC software .
Confirm that the serial port is as previously displayed.
```

![Complete source page 10](_assets/COIN-D6%20Instruction%20Manual/page-10.png)

## Page 11

```text
After confirming the serial port connection is correct, click the OPEN
button and then click the radar icon to open the PC software.




Click the Running button on the PC software , and the radar will start
running and generate a point cloud map.




Clicking on a point cloud with the mouse will display information about
the angle, distance, and intensity of the point cloud at that point. (See the
image below.)
```

![Complete source page 11](_assets/COIN-D6%20Instruction%20Manual/page-11.png)

## Page 12

```text
4.1.3. Serial Port Start Radar
Serial Port Assistant Download: https://drive.google.com/file/d/1ps2fXKrsGR0NaRgpN-
Z9eFOhibTPjdsD/view?usp=drive_link

1. Open the Serial Port Assistant, select the 230400 baud rate and the corresponding port, and start
the port:

Start Radar Command: AA 55 F0 0F

Close Radar Command: AA 55 F5 0A


4.2 ROS2

ROS2 program download link:
https://drive.google.com/drive/folders/1yiiONkmzb4KWPYYFDwfQyIUfweCqo4F7?
usp=drive_link

Import the SDK into the virtual machine with the ROS2 environment configured,
and place it in ro2_ws/src;

Modify cspc_lidar_sdk_ros2/params/cspc_lidar.yaml and change the port to the
actual serial port;

Check serial port permissions and grant them.
```

![Complete source page 12](_assets/COIN-D6%20Instruction%20Manual/page-12.png)

## Page 13

```text
To compile within the ros2_ws working environment, enter the command "
colcon build " in the terminal.

After compilation, enter the command " source install/setup.bash " in the
terminal to add environment variables.

Enter the command " ros2 launch cspc_lidar lidar_launch.py " in the terminal to
turn on the LiDAR and receive data.




ros2 launch cspc_lidar lidar_rviz.py " in the terminal to open rviz2.
```

![Complete source page 13](_assets/COIN-D6%20Instruction%20Manual/page-13.png)

## Page 14

```text
The point cloud effect can be observed.
```

![Complete source page 14](_assets/COIN-D6%20Instruction%20Manual/page-14.png)


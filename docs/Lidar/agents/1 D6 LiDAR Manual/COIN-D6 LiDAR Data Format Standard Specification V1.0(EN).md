# COIN-D6 LiDAR Data Format Standard Specification V1.0(EN)

Source: [COIN-D6 LiDAR Data Format Standard Specification V1.0(EN).pdf](../_originals/1%20D6%20LiDAR%20Manual/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29.pdf).

Complete extracted text is included page by page, with spacing preserved for tables. Each page image preserves diagrams, screenshots, formatting, and any content that cannot be represented as text. Original language and wording are retained.

## Page 1

```text
 COIN-D6
Development
   Manual




    V1.0
```

![Complete source page 1](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29/page-1.png)

## Page 2

```text
                                               Catalogue
Data format standard specification .................................................................... 2

      1、Radar operating mode............................................................................ 2

      2、Radar command format ........................................................................... 2

            2.1、Radar equipment information command ............................................. 3

            2.2、Radar data command....................................................................4

revise ............................................................................................................... 6




                                                  第 1 页 共 6 页
```

![Complete source page 2](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29/page-2.png)

## Page 3

```text
Data format standard specification

1、Radar operating mode

      ⚫ The COIN-D6 LiDAR supports command-controlled start and stop functions.
           After power-on, the radar is in a state of stopping scanning and ranging,
           and can be started and stopped through commands at this time
           Start：

                 Send:0xAA 0x55 0xF0 0x0F

                 Ok Ack:0xA5,0x5A,0x50,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xA8

                 Error Ack: 0xA5,0x5A,0x55,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xE9
           Stop：

                 Send: 0xAA 0x55 0xF5 0x0A

                 Ok Ack: 0xA5,0x5A,0x55,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0Xad

                 Error Ack: 0xA5,0x5A,0x55,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xE9

⚫ The COIN-D6 LiDAR only outputs data after its rotational speed stabilizes.

     During the speed adjustment process, it emits double-byte speed adjustment

     commands accompanied by some 0xFE or 0xFF。

⚫ The COIN-D6 LiDAR undergoes closed-loop adjustment through an internal
  speed regulation module, maintaining a fixed rotation speed of 10Hz.

2、Radar command format

A5    5A    XX     XX    YY   YY    ZZ


A5    5A     ：Frame Header


XX    XX     ：Length, little-endian, e.g., 05 00 represents length 5.


YY    YY     ：Checksum, the sum of all other bytes


ZZ     ：Packet type: 0x81 = Upload LiDAR data; 0x01 = Upload LiDAR information.

                                                     ：Data field




                                         第 2 页 共 6 页
```

![Complete source page 3](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29/page-3.png)

## Page 4

```text
2.1、LiDAR device information command

LiDAR information upload. This command is the first command sent by the LiDAR after power-on, and
it provides a detailed description of the information of the COIN-D6 LiDAR device.

   A5    5A    14        00       E3    02   01              Data field

   The data field length is 20 bytes, and the specific data is as follows.：

   Byte offset：
   1          3               5          7         9           11         13        15        17        19
   43   4F    49    4E    2D       44   34   00    00   00    00    00    00   00   00   00   00   00   00   01


   Bytes 1-12 are the LiDAR model. Among them, bytes 1-7 are the ASCII code for
   COIN-D6; bytes 8-12 are reserved.
   Bytes 13-14 are 00 00, representing the deviation between the LiDAR data zero
   angle and the identification zero angle. The COIN-D6 has already completed
   angle compensation structurally, so ignore this compensation value.
   Byte 15 is 0x00, indicating that the LiDAR rotation direction is clockwise.
   Byte 16 is 0x01, indicating that angle correction needs to be implemented in the
   robot's driver code.
   Bytes 17-19 are reserved and default to 0.
   Byte 20 is 0x01, indicating that the current software version number is Rev 1.


                                                  Zero position direction




                                                    第 3 页 共 6 页
```

![Complete source page 4](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29/page-4.png)

## Page 5

```text
2.2、LiDAR data command

Start scan. This command is sent fixedly before starting the scan,

and it is the second command sent by the LiDAR after powering on.


A5    5A    00    00      80     01     81             Data field

Where 0x80 0x01 is the checksum, and 0x81 is the type code.
The data field is the point cloud data scanned by the system, and the unified data format is
as follows.
PHL   PHH   M&T   LSN     FSAL   FSAH   LSAL    LSAH   CSL   CSH    S1_L   S1_2nd   S1_H   S2_L   S2_2nd   S2_H   .. .. ..

AA    55



                                   Point cloud data format parsing
Identifier Definition                          Description
 PH(2B)                 Header                 Fixed as 0x55AA, little-endian mode.
                                               M-bit1:bit7: indicates the current scan frequency of the radar,
             Scan frequency and                valid in the start data packet, defaults to 0 in point cloud
M&T(1B)      data packet type                  data packets;
                                               T-bit0: indicates the type of the current data packet; 0x00:
                                               point cloud data packet, 0x01: start data packet.
                                               Indicates the number of sampling points contained in the
             Number of sampling
 LSN(1B)     points
                                               current data packet; there is only 1 start point data in the
                                               start data packet, and this value is 1.
 FSA(2B)          Start angle                  Angle data of the first sample, little-endian.
 LSA(2B)           End angle                   Angle data of the end sample, little-endian.
                                               Checksum of the current data packet, verified by
  CS(2B)            Checksum                   performing a two-byte XOR on the current data packet.

  Si(3B)          Sampling data                System test sampling data, consisting of distance
                                               and intensity values of sampling points.




M&T Parsing:

M: Indicates the current scanning frequency, M = M & [binary] >> 1;

10

T: Indicates the data packet type; T = (M & T) & 0x01; When T=1 is detected,

it indicates that this packet is the start data packet, representing the

beginning of a full scan of point cloud data. In this data packet, LSN = 1,

which means the quantity of Si is 1;




                                               第 4 页 共 6 页
```

![Complete source page 5](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29/page-5.png)

## Page 6

```text
Si Parsing:

Si information includes distance values, intensity values, and other information of the sampling

points. The specific format definition is shown in the figure below. The specific action is defined

as:




Intensity Parsing:

Intensity represents the effective intensity of the sampling spot corresponding to the

sampling point, used to indicate the echo intensity of that point. It is expressed as

Intensity, with a length of one byte (8 bits).

Intensity = (Si_2nd & 0x03) * 64 + (Si_L >> 2);

Distance Parsing:

Distance represents the ranging information corresponding to the sampling point, with a

length of 14 bits and a unit of mm.

Distance = Si_H * 64 + (Si_2nd >> 2);

Angle Parsing:

Angle data is stored in FSA and LSA, representing the start angle and end angle

respectively. Each angle data has the following data structure and uses little-endian mode.




      AngleL[7:1]        C[0]         AngleH[7:0]



Where C is the check bit with a fixed value of 1. The specific angle parsing process is as follows:

Start angle FSA calculation formula: Angle_fsa = (FSA >> 1) / 64;

End angle LSA calculation formula: Angle_lsa = (LSA >> 1) / 64;


Intermediate angle calculation formula: Angle(i) =

(FSA>>1)/64+(LSA>>1)/64-(FSA>>1)/64*(i-1);
                       LSN-1
                                                 [i=2,3...LSN-1]
                                             第 5 页 共 6 页
```

![Complete source page 6](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29/page-6.png)

## Page 7

```text
 Definition of high-reflectivity material flag bit：

 The high-reflectivity flag indicates whether the current sampling point is made of

 a high-reflectivity material, represented as High Reflection. Bit[0] is the high-

 reflectivity material flag position, and Bit[1] is a reserved bit.



 [0X01] indicates that the current sampling point is a high-reflectivity material,

 such as 3M reflective tape, metal, or other materials with a reflectivity

 exceeding 300%. [0X00] indicates materials with a reflectivity below 100%.

 Checksum parsing：

 The checksum uses a dual-byte XOR to verify the current data packet. It does
not participate in the XOR operation itself, and the XOR order does not
strictly follow the byte sequence; the XOR order is as shown in the diagram. It
is important to note that since the sampling data Si consists of 3 bytes, the
high 8 bits of the 3rd byte of Si must be padded with zeros before XORing, as
shown in D5 and D6 in the figure below, where the MSB of D6 is padded with 0.
 Therefore, the checksum calculation formula is:



This           This is the cumulative XOR formula, indicating that the elements D1,
               D4... Dn are XORed together. The XOR operation is independent of the
               order of elements.




 revise
       Date        Version                           Revised content
  2024-11-08        1.0                                First Draft




                                      第 6 页 共 6 页
```

![Complete source page 7](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29/page-7.png)


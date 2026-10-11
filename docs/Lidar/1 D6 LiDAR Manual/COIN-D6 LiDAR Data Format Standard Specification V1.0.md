# COIN-D6 LiDAR Data Format Standard Specification V1.0

Source: [COIN-D6 LiDAR Data Format Standard Specification V1.0.pdf](../_originals/1%20D6%20LiDAR%20Manual/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0.pdf).

Complete extracted text is included page by page, with spacing preserved for tables. Each page image preserves diagrams, screenshots, formatting, and any content that cannot be represented as text. Original language and wording are retained.

## Page 1

```text
COIN-D6
开发手册




  V1.0
```

![Complete source page 1](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0/page-1.png)

## Page 2

```text
                                                    目 录
数据格式标准说明 ....................................................................................... 2

     1、雷达工作方式 .................................................................................. 2

     2、雷达指令格式 .................................................................................. 2

           2.1、雷达设备信息指令 ................................................................ 3

           2.2、雷达数据指令 .........................................................................4

修订 ................................................................................................................ 6




                                                 第 1 页 共 6 页
```

![Complete source page 2](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0/page-2.png)

## Page 3

```text
数据格式标准说明

1、雷达工作方式


         COIN-D6 激光雷达支持指令控制启停功能。上电后雷达处于停止扫描测距状态，此时

          可通过指令进行启动和停止控制



          启动：

               Send:0xAA 0x55 0xF0 0x0F

               Ok Ack:0xA5,0x5A,0x50,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xA8

               Error Ack: 0xA5,0x5A,0x55,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xE9

          停止：

               Send: 0xAA 0x55 0xF5 0x0A

               Ok Ack: 0xA5,0x5A,0x55,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0Xad

               Error Ack: 0xA5,0x5A,0x55,0x07,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xE9

    COIN-D6 激光雷达在转速稳定后才输出数据，在转速调整过程中，伴随部分 0xFE 或 0xFF

     的双字节速度调整指令。

    COIN-D6 激光雷达通过内部调速模组进行闭环调节，固定转速为 10Hz。


2、雷达指令格式

A5   5A   XX     XX    YY   YY    ZZ


A5   5A    ：包头


XX   XX    ：长度，低位在前，如 05 00 代表长度 5


YY   YY    ：校验和，除了此字段外所有字节和


ZZ    ：包类型，0x81=上传雷达数据；0x01=上传雷达信息

                                                   ：数据区




                                       第 2 页 共 6 页
```

![Complete source page 3](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0/page-3.png)

## Page 4

```text
2.1、雷达设备信息指令

雷达信息上传，本条指令为雷达上电的发出的第一条指令，上传指令详细描述了 COIN-D6

激光雷达设备的信息。

A5   5A    14        00       E3    02   01             数据区

其中数据区长度为 20 个字节,以下为具体数据：

字节偏移：
1    3                    5          7        9          11        13        15        17        19
43   4F   49    4E    2D       44   34   00   00   00   00    00   00   00   00   00   00   00   00   01


第 1-12 字节为激光雷达型号。其中，第 1-7 字节为 COIN-D6 的 ASCII 码；第 8-12 字节为保

留。

第 13-14 字节为 00 00，代表雷达数据零度角与标识零度角的偏差，COIN-D6 结构上已完成

角度补偿，忽略此补偿值。

第 15 字节为 0x00，代表雷达旋转方向为顺时针。

第 16 字节为 0x01，表示需要在扫地机的驱动代码中实现角度矫正。

第 17-19 字节预留，默认为 0。

第 20 字节为 0x01，表示当前的软件版本号为 Rev 1。




                                              第 3 页 共 6 页
```

![Complete source page 4](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0/page-4.png)

## Page 5

```text
2.2、雷达数据指令

开始扫描，在开始扫描前固定发送，本条指令为雷达上电后发出的第二条指令。
A5    5A    00    00     80     01     81               数据区

其中，0x80 0x01 为检验和，0x81 为类型码。




数据区为系统扫描的点云数据，统一数据格式如下。

PHL   PHH   M&T   LSN    FSAL   FSAH    LSAL     LSAH   CSL   CSH   S1_L   S1_2nd   S1_H   S2_L   S2_2nd   S2_H   .. .. ..

AA    55



                                             点云数据格式解析
标识          定义                                 描述
 PH(2B)                 数据包头                   固定为 0x55AA,小端模式。
                                               M-bit1:bit7；表示当前雷达的扫描频率，起始数据包中该
                                               值为有效标识，点云数据包中，默认为 0；
M&T(1B)      扫描频率及数据包类型
                                               T-bit0:表示当前数据包的类型; 0x00:点云数据包 0x01:
                                               起始数据包。
                                               表示当前数据包中包含的采样点数量；起始数据包中只
 LSN(1B)           采样点数量
                                               有 1 个起始点的数据，该值为 1。
 FSA(2B)                起始角度                   采样数据中第一个采样点对应的角度数据，小端模式。
 LSA(2B)                结束角度                   采样数据中最后一个采样点对应的角度数据,小端模式。
                                               当前数据包的校验码，采用双字节异或对当前数据包进
 CS(2B)                 校验码
                                               行校验
  Si(3B)                采样数据                   系统测试的采样数据，为采样点的距离值、强度值




M&T 解析：

                                     M&�≫1
M:表示当前的扫描频率，M=                               ；
                                       10


T:表示数据包类型；T=(M&T)&0x01；当检测到 T=1 时，表明该包数据为起始数据包，表

示激光雷达一圈点云数据的开头，该数据包中 LSN = 1， 即 Si 的数量为 1；




                                               第 4 页 共 6 页
```

![Complete source page 5](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0/page-5.png)

## Page 6

```text
Si 解析：

Si 信息包含采样点的距离值、强度值等信息。具体格式定义如右下图所示。

具体动作定义为：




强度解析：

强度表示为采样点对应采样光斑的有效强度，用于提示该采样点的回波强度，表达为

Intensity，长度为一个字节（8bit）。

Intensity=( Si_2nd &0x03)*64+( Si_L>>2);




距离解析：

距离表示为采样点对应的测距信息，长度为 14bit，单位为 mm。

Distance = Si_H*64+(Si_2nd >>2);

角度解析：

角度数据保存在 FSA 和 LSA 中，分别表示起始角度和结束角度，每一个角度数据有如下

的数据结构，采用小端模式。


     AngleL[7:1]         C[0]            AngleH[7:0]


其中，C 是校验位，其值固定为 1。角度解析具体过程如下：

起始角 FSA 解算公式: Angle_fsa = (FSA>>1)/64;

结束角 LSA 解算公式:              Angle_lsa = (LSA>>1)/64;

中间角解算公式: Angle(i) =

               (LSA>>1)/64-(FSA>>1)/64
(FSA>>1)/64+           LSN-1
                                         *(i-1);   [i=2,3...LSN-1]


                                              第 5 页 共 6 页
```

![Complete source page 6](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0/page-6.png)

## Page 7

```text
㐙发棒忘低谣框＞

高反标志位表示当前采样点是否为高反材质，表达为 High Reflection。Bit[0] 为高反材质

标记位置，Bit[1] 为预留位。

[0X01] 代表当前采样点为高反材料，例如 3M 反光贴，金属或者其他反射率超过 300%的

材料。 [0X00] 代表反射率低于 100%的材料。

校验码解析：

校验码采用双字节异或，对当前数据包进行校验，其本身不参与异或运算，且异或顺序不是

严格按照字节顺序，其异或顺序如图所示，需要注意的是，由于采样数据 Si 有 3 个字节，

需要将 Si 第 3 个字节的高 8 位补零再异或，如右下图所示 D5、D6，D6 中 MSB 补 0。

因此，校验码解算公式为：

         �
CS=���       ��     i=1,2,…n
         1

     �
��� �� 为异或累计公式，表示将 D1,D4…Dn 的元素进行异或。异或运算与元素顺序无
     1


关。




修订
  日期              版本                         修订内容
2024-11-08        1.0                         初撰




                               第 6 页 共 6 页
```

![Complete source page 7](_assets/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0/page-7.png)


# Tucker Innovations  Guoke Optoelectronics D6 ROS Driver Package User Guide V1.0

Source: [Tucker Innovations  Guoke Optoelectronics D6 ROS Driver Package User Guide V1.0.pdf](../_originals/2%20ROS%20and%20ROS2%20feature%20pack%20information/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0.pdf).

Complete extracted text is included page by page, with spacing preserved for tables. Each page image preserves diagrams, screenshots, formatting, and any content that cannot be represented as text. Original language and wording are retained.

## Page 1

```text
                            D6 雷达 ROS 驱动包使用指导手册




COIN-D6 激光雷达
   ROS 驱动包使用指导手册
               V1.0




         烟台塔克电子科技有限公司

塔克创新官网       www.xtark.cn                1 / 8
```

![Complete source page 1](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-1.png)

## Page 2

```text
                                                   D6 雷达 ROS 驱动包使用指导手册


 版权申明



  本手册版权归属塔克创新所有，并保留一切权力，受法律保护。非经(书面形式)同意，任何单
位及个人不得擅自摘录或修改本手册部分或全部内容，违者我们将追究其法律责任。




  版本说明



   版本         日期                              内容说明

   V1.0     2025/2/18    第一次发布




 塔克媒体



          塔克官网          www.xtark.cn

          淘宝店铺          https://xtark.taobao.com

          塔克哔哩          https://space.bilibili.com/511052131

          销售邮箱          sales@xtark.cn




 塔克创新官网                       www.xtark.cn                      2 / 8
```

![Complete source page 2](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-2.png)

## Page 3

```text
                                                        D6 雷达 ROS 驱动包使用指导手册


1. 在 ROS1 中使用 D6 雷达
     ROS 环境搭建已经完成，且已经搭建好工作空间的情况下即可按照下列步骤进行操作。

1.1 确定雷达设备号
     在 D6 雷达插入 USB 口之前，运行一下命令：

     ls /dev/ttyUSB*

     将会看到所有的设备。

     再将 D6 雷达插入 USB 口，运行上述命令，多出来的设备号是 D6 雷达，我们需要再驱动包
中做修改。




     找到资料中的 D6 雷达 ROS1 驱动包 launch 文件下的 start.launch 文件，打开后做如下修
改：




     将划线位置的 sc_mini 修改为 D6 雷达的设备号 ttyUSB0（此处不同的用户情况不同，以自己
具体的设备号为准）。

     查看串口权限并赋权
      xtark@tarkbot-pc: ~$ ls -l /dev/ttyUSB0

      crw-rw-rw- 1 root dialout 188, 0 Feb 19 15:12 /dev/ttyUSB0

      xtark@tarkbot-pc: ~$ sudo chmod 777 /dev/ttyUSB0


1.2 拷贝编译 D6 雷达 ROS1 驱动包
     将修改后的 D6 雷达驱动包 cspc_lidar_sdk_ros1 拷贝到 src 文件夹下，然后将整个工作空间
进行 catkin_make 编译。

     xtark@tarkbot-pc:~ /lidar/catkin_ws$ catkin_make


     如图所示为编译成功。


   塔克创新官网                          www.xtark.cn                      3 / 8
```

![Complete source page 3](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-3.png)

## Page 4

```text
                                                     D6 雷达 ROS 驱动包使用指导手册


  设置环境变量

   xtark@tarkbot-pc:~ $ source devel/setup.bash

1.3 启动 launch 文件
  完成上述操作配置后运行以下命令，启动 launch 文件。

   xtark@tarkbot-pc:~ /lidar/catkin_ws$ roslaunch cspc_lidar start.launch
  运行效果如下图。




  如图所示节点运行成功，雷达开始转动。

1.4 在 rviz 中查看雷达数据
  按照上述节点启动 launch 文件后，再新建终端打开 rviz。

   xtark@tarkbot-pc:~ $ rosrun rviz rviz

  运行效果如下图。




  塔克创新官网                           www.xtark.cn                             4 / 8
```

![Complete source page 4](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-4.png)

## Page 5

```text
                                   D6 雷达 ROS 驱动包使用指导手册




即可在 rviz 中查看雷达数据。




塔克创新官网              www.xtark.cn                5 / 8
```

![Complete source page 5](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-5.png)

## Page 6

```text
                                                 D6 雷达 ROS 驱动包使用指导手册


2. 在 ROS2 中使用 D6 雷达
   ROS 环境搭建已经完成，且已经搭建好工作空间的情况下即可按照下列步骤进行操作。

2.1 确定雷达设备号
   在 D6 雷达插入 USB 口之前，运行一下命令：

   ls /dev /ttyUSB*

   将会看到所有已经插入的设备。

   再将 D6 雷达插入 USB 口，运行上述命令，多出来的设备号是 D6 雷达，我们需要再驱动包
中做修改。




   找到资料中的 D6 雷达 ROS2 驱动包 params 文件下的- m1ct_d2 文件，打开后做如下修改：




   将划线位置的 sc_mini 修改为 D6 雷达的设备号 ttyUSB0（此处不同的用户情况不同，以自己
具体的设备号为准）。

   查看串口权限并赋权
     xtark@tarkbot-pc: ~$ ls -l /dev/ttyUSB0

     crw-rw-rw- 1 root dialout 188, 0 Feb 19 15:12 /dev/ttyUSB0

     xtark@tarkbot-pc: ~$ sudo chmod 777 /dev/ttyUSB0


2.2 拷贝编译 D6 雷达 ROS2 驱动包
   将修改后的 D6 雷达驱动包 m1ct_d2 功能包拷贝到 src 文件夹下，然后将整个工作空间进行
colcon build 编译。




   如图所示为编译成功。


   塔克创新官网                        www.xtark.cn                     6 / 8
```

![Complete source page 6](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-6.png)

## Page 7

```text
                                                   D6 雷达 ROS 驱动包使用指导手册


  设置环境变量。新建一个终端运行：
 xtark@tarkbot-pc: ~ $ source /opt/ros/foxy（自己的 ROS 版本）/setup.bash

  更新上层工作空间：
 xtark@tarkbot-pc:~ ~ /lidar2/dev_ws$ . install/local_setup.bash


2.3 启动 launch 文件
  完成上述操作配置后运行以下命令，启动 launch 文件。

  xtark@tarkbot-pc:~ /lidar2/dev_ws$ ros2 run m1ct_d2 m1ct_d2




  如图所示节点运行成功，雷达开始转动。

2.4 在 rviz 中查看雷达数据
  按照上述节点启动 launch 文件，再新建终端打开 rviz。
   xtark@tarkbot-pc:~ $ ros2 run rviz2 rviz2




  塔克创新官网                          www.xtark.cn                     7 / 8
```

![Complete source page 7](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-7.png)

## Page 8

```text
                                   D6 雷达 ROS 驱动包使用指导手册




即可在 rviz 中查看雷达数据。




塔克创新官网              www.xtark.cn                8 / 8
```

![Complete source page 8](_assets/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0/page-8.png)


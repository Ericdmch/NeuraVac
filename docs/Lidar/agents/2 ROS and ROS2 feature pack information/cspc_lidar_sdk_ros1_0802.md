# cspc_lidar_sdk_ros1_0802.tar.gz

Original archive: [cspc_lidar_sdk_ros1_0802.tar.gz](../_originals/2%20ROS%20and%20ROS2%20feature%20pack%20information/cspc_lidar_sdk_ros1_0802.tar.gz). All original bytes, including compiled drivers and executables, are preserved in that archive.

Text files are transcribed below. Embedded PDF manuals have their own Markdown conversions. Binary files remain available in the original archive. No software was executed.

## Archive contents

| Entry | Bytes | Representation |
| --- | ---: | --- |
| cspc_lidar_sdk_ros1 | 0 | Directory or non-regular entry |
| cspc_lidar_sdk_ros1/readme.txt | 72 | Full text below |
| cspc_lidar_sdk_ros1/rviz | 0 | Directory or non-regular entry |
| cspc_lidar_sdk_ros1/rviz/sc_m.rviz | 4917 | Full text below |
| cspc_lidar_sdk_ros1/launch | 0 | Directory or non-regular entry |
| cspc_lidar_sdk_ros1/launch/rviz.launch | 151 | Full text below |
| cspc_lidar_sdk_ros1/launch/start.launch | 334 | Full text below |
| cspc_lidar_sdk_ros1/sc_mini.rules | 205 | Full text below |
| cspc_lidar_sdk_ros1/package.xml | 3531 | Full text below |
| cspc_lidar_sdk_ros1/include | 0 | Directory or non-regular entry |
| cspc_lidar_sdk_ros1/include/cspc_lidar | 0 | Directory or non-regular entry |
| cspc_lidar_sdk_ros1/include/cspc_lidar/lidar_information.h | 5184 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/timer.h | 113 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/msg_recept.h | 113 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/locker.h | 6505 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/serial_port.h | 3535 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/calibration.h | 4270 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/lidar_data_processing.h | 1989 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/mtime.h | 1059 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/point_cloud_optimize.h | 1001 | Full text below |
| cspc_lidar_sdk_ros1/include/cspc_lidar/node_lidar.h | 3826 | Full text below |
| cspc_lidar_sdk_ros1/CMakeLists.txt | 7802 | Full text below |
| cspc_lidar_sdk_ros1/src | 0 | Directory or non-regular entry |
| cspc_lidar_sdk_ros1/src/calibration.cpp | 20462 | Full text below |
| cspc_lidar_sdk_ros1/src/node_lidar.cpp | 16133 | Full text below |
| cspc_lidar_sdk_ros1/src/main.cpp | 2529 | Full text below |
| cspc_lidar_sdk_ros1/src/mtime.cpp | 2159 | Full text below |
| cspc_lidar_sdk_ros1/src/serial_port.cpp | 15617 | Full text below |
| cspc_lidar_sdk_ros1/src/lidar_data_processing.cpp | 31474 | Full text below |
| cspc_lidar_sdk_ros1/src/timer.cpp | 1033 | Full text below |
| cspc_lidar_sdk_ros1/src/lidar_information.cpp | 481 | Full text below |
| cspc_lidar_sdk_ros1/src/point_cloud_optimize.cpp | 12595 | Full text below |
| cspc_lidar_sdk_ros1/.vscode | 0 | Directory or non-regular entry |
| cspc_lidar_sdk_ros1/.vscode/c_cpp_properties.json | 371 | Full text below |
| cspc_lidar_sdk_ros1/.vscode/settings.json | 1714 | Full text below |

## `cspc_lidar_sdk_ros1/readme.txt`

```
sudo cp sc_mini.rules /etc/udev/rules.d

ros2 run cspc_lidar cspc_lidar
```
## `cspc_lidar_sdk_ros1/rviz/sc_m.rviz`

```
Panels:
  - Class: rviz/Displays
    Help Height: 78
    Name: Displays
    Property Tree Widget:
      Expanded:
        - /Global Options1
        - /Status1
        - /Grid1
        - /LaserScan1
        - /Axes1
      Splitter Ratio: 0.5
    Tree Height: 435
  - Class: rviz/Selection
    Name: Selection
  - Class: rviz/Tool Properties
    Expanded:
      - /2D Pose Estimate1
      - /2D Nav Goal1
      - /Publish Point1
    Name: Tool Properties
    Splitter Ratio: 0.588679016
  - Class: rviz/Views
    Expanded:
      - /Current View1
    Name: Views
    Splitter Ratio: 0.5
  - Class: rviz/Time
    Experimental: false
    Name: Time
    SyncMode: 0
    SyncSource: LaserScan
Toolbars:
  toolButtonStyle: 2
Visualization Manager:
  Class: ""
  Displays:
    - Alpha: 0.5
      Cell Size: 1
      Class: rviz/Grid
      Color: 160; 160; 164
      Enabled: true
      Line Style:
        Line Width: 0.0299999993
        Value: Lines
      Name: Grid
      Normal Cell Count: 0
      Offset:
        X: 0
        Y: 0
        Z: 0
      Plane: XY
      Plane Cell Count: 10
      Reference Frame: <Fixed Frame>
      Value: true
    - Alpha: 1
      Autocompute Intensity Bounds: true
      Autocompute Value Bounds:
        Max Value: 10
        Min Value: -10
        Value: true
      Axis: Z
      Channel Name: intensity
      Class: rviz/LaserScan
      Color: 255; 255; 255
      Color Transformer: Intensity
      Decay Time: 0
      Enabled: true
      Invert Rainbow: false
      Max Color: 255; 255; 255
      Max Intensity: 255
      Min Color: 0; 0; 0
      Min Intensity: 0
      Name: LaserScan
      Position Transformer: XYZ
      Queue Size: 10
      Selectable: true
      Size (Pixels): 3
      Size (m): 0.0299999993
      Style: Flat Squares
      Topic: /scan
      Unreliable: false
      Use Fixed Frame: true
      Use rainbow: true
      Value: true
    - Class: rviz/Axes
      Enabled: true
      Length: 0.5
      Name: Axes
      Radius: 0.0299999993
      Reference Frame: <Fixed Frame>
      Value: true
  Enabled: true
  Global Options:
    Background Color: 108; 108; 108
    Default Light: true
    Fixed Frame: laser_link
    Frame Rate: 30
  Name: root
  Tools:
    - Class: rviz/Interact
      Hide Inactive Objects: true
    - Class: rviz/MoveCamera
    - Class: rviz/Select
    - Class: rviz/FocusCamera
    - Class: rviz/Measure
    - Class: rviz/SetInitialPose
      Topic: /initialpose
    - Class: rviz/SetGoal
      Topic: /move_base_simple/goal
    - Class: rviz/PublishPoint
      Single click: true
      Topic: /clicked_point
  Value: true
  Views:
    Current:
      Class: rviz/Orbit
      Distance: 3.12298799
      Enable Stereo Rendering:
        Stereo Eye Separation: 0.0599999987
        Stereo Focal Distance: 1
        Swap Stereo Eyes: false
        Value: false
      Focal Point:
        X: 0
        Y: 0
        Z: 0
      Focal Shape Fixed Size: true
      Focal Shape Size: 0.0500000007
      Invert Z Axis: false
      Name: Current View
      Near Clip Distance: 0.00999999978
      Pitch: 1.39479649
      Target Frame: <Fixed Frame>
      Value: Orbit (rviz)
      Yaw: 2.3903966
    Saved: ~
Window Geometry:
  Displays:
    collapsed: false
  Height: 716
  Hide Left Dock: false
  Hide Right Dock: false
  QMainWindow State: 000000ff00000000fd0000000400000000000001d600000242fc0200000008fb0000001200530065006c0065006300740069006f006e00000001e10000009b0000006100fffffffb0000001e0054006f006f006c002000500072006f007000650072007400690065007302000001ed000001df00000185000000a3fb000000120056006900650077007300200054006f006f02000001df000002110000018500000122fb000000200054006f006f006c002000500072006f0070006500720074006900650073003203000002880000011d000002210000017afb000000100044006900730070006c006100790073010000002800000242000000d700fffffffb0000002000730065006c0065006300740069006f006e00200062007500660066006500720200000138000000aa0000023a00000294fb00000014005700690064006500530074006500720065006f02000000e6000000d2000003ee0000030bfb0000000c004b0069006e0065006300740200000186000001060000030c00000261000000010000010f00000242fc0200000003fb0000001e0054006f006f006c002000500072006f00700065007200740069006500730100000041000000780000000000000000fb0000000a00560069006500770073000000002800000242000000ad00fffffffb0000001200530065006c0065006300740069006f006e010000025a000000b200000000000000000000000200000490000000a9fc0100000001fb0000000a00560069006500770073030000004e00000080000002e10000019700000003000004b00000003efc0100000002fb0000000800540069006d00650100000000000004b00000030000fffffffb0000000800540069006d00650100000000000004500000000000000000000002d40000024200000004000000040000000800000008fc0000000100000002000000010000000a0054006f006f006c00730100000000ffffffff0000000000000000
  Selection:
    collapsed: false
  Time:
    collapsed: false
  Tool Properties:
    collapsed: false
  Views:
    collapsed: false
  Width: 1200
  X: 67
  Y: 24
```
## `cspc_lidar_sdk_ros1/launch/rviz.launch`

```
<launch>
  <node name="rviz" pkg="rviz" type="rviz" args="-d $(find cspc_lidar)/rviz/sc_m.rviz"/>                                          
</launch>

```
## `cspc_lidar_sdk_ros1/launch/start.launch`

```
<launch>
  <node pkg="cspc_lidar" type="cspc_lidar" name="cspc_lidar" output="screen">
    <param name="frame_id" type="string" value="laser_link"/>
    <param name="port" type="string" value="/dev/sc_mini"/>
    <param name="baud_rate" type="int" value="230400"/>
    <param name="version" type="int" value="4"/>
  </node>
</launch>
```
## `cspc_lidar_sdk_ros1/sc_mini.rules`

```
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE:="0666", SYMLINK+="sc_mini"
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE:="0777", SYMLINK+="sc_m_c"
```
## `cspc_lidar_sdk_ros1/package.xml`

```
<?xml version="1.0"?>
<package format="2">
  <name>cspc_lidar</name>
  <version>0.0.0</version>
  <description>The cspc_lidar package</description>

  <!-- One maintainer tag required, multiple allowed, one person per tag -->
  <!-- Example:  -->
  <!-- <maintainer email="jane.doe@example.com">Jane Doe</maintainer> -->
  <maintainer email="pi@todo.todo">pi</maintainer>


  <!-- One license tag required, multiple allowed, one license per tag -->
  <!-- Commonly used license strings: -->
  <!--   BSD, MIT, Boost Software License, GPLv2, GPLv3, LGPLv2.1, LGPLv3 -->
  <license>TODO</license>


  <!-- Url tags are optional, but multiple are allowed, one per tag -->
  <!-- Optional attribute type can be: website, bugtracker, or repository -->
  <!-- Example: -->
  <!-- <url type="website">http://wiki.ros.org/sc_mini</url> -->


  <!-- Author tags are optional, multiple are allowed, one per tag -->
  <!-- Authors do not have to be maintainers, but could be -->
  <!-- Example: -->
  <!-- <author email="jane.doe@example.com">Jane Doe</author> -->


  <!-- The *depend tags are used to specify dependencies -->
  <!-- Dependencies can be catkin packages or system dependencies -->
  <!-- Examples: -->
  <!-- Use depend as a shortcut for packages that are both build and exec dependencies -->
  <!--   <depend>roscpp</depend> -->
  <!--   Note that this is equivalent to the following: -->
  <!--   <build_depend>roscpp</build_depend> -->
  <!--   <exec_depend>roscpp</exec_depend> -->
  <!-- Use build_depend for packages you need at compile time: -->
  <!--   <build_depend>message_generation</build_depend> -->
  <!-- Use build_export_depend for packages you need in order to build against this package: -->
  <!--   <build_export_depend>message_generation</build_export_depend> -->
  <!-- Use buildtool_depend for build tool packages: -->
  <!--   <buildtool_depend>catkin</buildtool_depend> -->
  <!-- Use exec_depend for packages you need at runtime: -->
  <!--   <exec_depend>message_runtime</exec_depend> -->
  <!-- Use test_depend for packages you need only for testing: -->
  <!--   <test_depend>gtest</test_depend> -->
  <!-- Use doc_depend for packages you need only for building documentation: -->
  <!--   <doc_depend>doxygen</doc_depend> -->
  <buildtool_depend>catkin</buildtool_depend>
  <build_depend>boost</build_depend>
  <build_depend>geometry_msgs</build_depend>
  <build_depend>nav_msgs</build_depend>
  <build_depend>pluginlib</build_depend>
  <build_depend>roscpp</build_depend>
  <build_depend>sensor_msgs</build_depend>
  <build_depend>std_msgs</build_depend>
  <build_depend>tf</build_depend>
  <build_export_depend>boost</build_export_depend>
  <build_export_depend>geometry_msgs</build_export_depend>
  <build_export_depend>nav_msgs</build_export_depend>
  <build_export_depend>pluginlib</build_export_depend>
  <build_export_depend>roscpp</build_export_depend>
  <build_export_depend>sensor_msgs</build_export_depend>
  <build_export_depend>std_msgs</build_export_depend>
  <build_export_depend>tf</build_export_depend>
  <exec_depend>boost</exec_depend>
  <exec_depend>geometry_msgs</exec_depend>
  <exec_depend>nav_msgs</exec_depend>
  <exec_depend>pluginlib</exec_depend>
  <exec_depend>roscpp</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>std_msgs</exec_depend>
  <exec_depend>tf</exec_depend>


  <!-- The export tag contains other, unspecified, tags -->
  <export>
    <!-- Other tools can request additional information be placed here -->

  </export>
</package>
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/lidar_information.h`

```
#ifndef LIDAR_INFORMATION_H
#define LIDAR_INFORMATION_H

#include <stdint.h>
#include <vector>

#define FRAME_ANGLE_RANGE (90*256)
#define FRAME_ANGLE_BASE (0xA000)

#define PI 3.141592654
#define ULTRASONIC_ANGLE_INC_DEG 0.5

constexpr uint8_t start_lidar[4]={0xAA,0x55,0xF0,0x0F};
constexpr uint8_t end_lidar[4]={0xAA,0x55,0xF5,0x0A};
constexpr uint8_t low_exposure[4]={0xAA,0x55,0xF1,0x0E};
constexpr uint8_t high_exposure[4]={0xAA,0x55,0xF2,0x0D};
constexpr uint8_t get_version[4]={0xAA,0x55,0xFC,0x03};

constexpr uint8_t high_speed[4]={0xAA,0x55,0xF2,0x0D};
constexpr uint8_t low_speed[4]={0xAA,0x55,0xF1,0x0E};

typedef struct
{
  float f_begin;
  float f_end;
} LidarCoverAngleStr;

typedef struct
{
  uint64_t timeStamp;
  float GyroYaw;
} GyroYawStr;

struct LaserConfig
{
  float min_angle;
  float max_angle;
  float angle_increment;
  float time_increment;
  float scan_time;
  float min_range;
  float max_range;
  LaserConfig &operator=(const LaserConfig &data)
  {
    min_angle = data.min_angle;
    max_angle = data.max_angle;
    angle_increment = data.angle_increment;
    time_increment = data.time_increment;
    scan_time = data.scan_time;
    min_range = data.min_range;
    max_range = data.max_range;
    return *this;
  }
};



struct node_info
{
  uint8_t sync_flag;          //sync flag
  uint16_t sync_quality;      //! 信号质量
  uint16_t angle_q6_checkbit; //! 测距点角度
  uint16_t distance_q2;       //! 当前测距点距离
  uint64_t stamp;             //! 时间戳
  uint8_t scan_frequence;     //! 特定版本此值才有效,无效值是0
  uint8_t exp_m;              //! 当前的曝光模式
  uint8_t debug_info[12];
  uint8_t index;
};

typedef enum
{
  DEFAULT_TIMEOUT = 2000,    /**< 默认超时时间. */
  DEFAULT_HEART_BEAT = 1000, /**< 默认检测掉电功能时间. */
  MAX_SCAN_NODES = 800,     /**< 最大扫描点数. */
  DEFAULT_TIMEOUT_COUNT = 10,
}TIME_CHECK;

typedef enum
{
  LIDAR_FOR_MOTION = 0,
  LIDAR_FOR_BLOCKED = 1,
}MOTION_AND_BLOCKED;

#define RESULT_OK 0
#define RESULT_TIMEOUT -1
#define RESULT_FAIL -2

#define IS_OK(x) ((x) == RESULT_OK)
#define IS_TIMEOUT(x) ((x) == RESULT_TIMEOUT)
#define IS_FAIL(x) ((x) == RESULT_FAIL)

//#define timeout 2000

typedef int32_t result_t;

struct PackageNode
{
  uint8_t PakageSampleQuality;
  uint16_t PakageSampleDistance;
} __attribute__((packed));

#define PackageSampleMaxLngth 0x100
typedef enum
{
  CT_Normal = 0,
  CT_RingStart = 1,
  CT_Tail,
} CT;

/*激光雷达对应的版本*/
typedef enum{
  M1C1_Mini_v1 = 1,
  M1C1_Mini_v2,
  M1CT_Coin_Plus,
  M1CT_TOF,
}LIDAR_VERSION;



#define Node_Default_Quality (10)
#define Node_Sync 1
#define Node_NotSync 2
#define PackagePaidBytes 10
#define PH 0x55AA
#define NORMAL_PACKAGE_SIZE 90
#define INTENSITY_NORMAL_PACKAGE_SIZE 130

/*对应M1C1_Mini v2版本*/
struct node_package
{
  uint16_t package_Head;
  uint8_t package_CT;
  uint8_t nowPackageNum;
  uint16_t packageFirstSampleAngle;
  uint16_t packageLastSampleAngle;
  uint16_t checkSum;
  uint8_t packageSampleDistance[PackageSampleMaxLngth];
} __attribute__((packed));

/*对应M1C1_Mini v1版本*/
struct node_packages
{
  uint16_t package_Head;
  uint8_t package_CT;
  uint8_t nowPackageNum;
  uint16_t packageFirstSampleAngle;
  uint16_t packageLastSampleAngle;
  uint16_t checkSum;
  uint16_t packageSampleDistance[PackageSampleMaxLngth];
} __attribute__((packed));

/*对应M1CT_Coin_Plus 版本*/
struct node_package_coin
{
  uint8_t headL;
  uint8_t headH;
  uint8_t info;
  uint8_t sampleinfo;
  uint8_t speedL;
  uint8_t speedH;
  uint8_t startAngleL;
  uint8_t startAngleH;
  struct{
    uint8_t d0;
    uint8_t d1;
    uint8_t d2;
  }data[8];
  uint8_t stopAngleL;
  uint8_t stopAngleH;
  uint8_t csL;
  uint8_t csH;
} __attribute__((packed));


#define ANGLESTRLENMAX 32
#define LIDAR_CMD_SYNC_BYTE 0xA5
#define LIDAR_CMDFLAG_HAS_PAYLOAD 0x80
#define LIDAR_ANS_SYNC_BYTE1 0xA5
#define LIDAR_ANS_SYNC_BYTE2 0x5A
#define LIDAR_RESP_MEASUREMENT_CHECKBIT (0x1 << 0)
#define LIDAR_RESP_MEASUREMENT_ANGLE_SAMPLE_SHIFT 8
#define LIDAR_RESP_MEASUREMENT_SYNCBIT (0x1 << 0)
#define LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT 1
#define _countof(_Array) (int)(sizeof(_Array) / sizeof(_Array[0]))

struct node_Gyro
{
  float angle;
  int count;
  uint64_t time;
};


struct cmd_packet {
  uint8_t syncByte;
  uint8_t cmd_flag;
  uint8_t size;
  uint8_t data;
} __attribute__((packed)) ;

struct lidar_ans_header {
  uint8_t  syncByte1;
  uint8_t  syncByte2;
  uint32_t size: 30;
  uint32_t subType: 2;
  uint8_t  type;
} __attribute__((packed));

struct LaserPoint
{
  float angle;
  float range;
  uint16_t intensity;
  short range_check;
  LaserPoint &operator=(const LaserPoint &data)
  {
    this->angle = data.angle;
    this->range = data.range;
    this->intensity = data.intensity;
    this->range_check = data.range_check;
    return *this;
  }
};

struct LaserScan
{
  uint64_t stamp;
  std::vector<LaserPoint> points;
  LaserConfig config;
  LaserScan &operator=(const LaserScan &data)
  {
    this->points = data.points;
    this->stamp = data.stamp;
    this->config = data.config;
    return *this;
  }
};


bool get_version_t();



#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/timer.h`

```
#ifndef NODE_TIMER_H
#define NODE_TIMER_H

uint32_t getms();
uint64_t getTime();
void delay(uint32_t ms);

#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/msg_recept.h`

```
#ifndef __H_MESSAGE_RECEPT_H__
#define __H_MESSAGE_RECEPT_H__

bool get_version_t();
bool encry_doing();


#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/locker.h`

```
#pragma once
#ifdef _WIN32
#include <conio.h>
#include <windows.h>
#include <process.h>
#include <tlhelp32.h>
#include <sys/utime.h>
#include <io.h>
#include <direct.h>
#else
#include <assert.h>
#include <pthread.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#endif

class Locker
{
public:
  enum LOCK_STATUS
  {
    LOCK_OK = 0,
    LOCK_TIMEOUT = -1,
    LOCK_FAILED = -2
  };

  Locker()
  {
#ifdef _WIN32
    _lock = NULL;
#endif
    init();
  }

  ~Locker()
  {
    release();
  }

  Locker::LOCK_STATUS lock(unsigned long timeout = 0xFFFFFFFF)
  {
#ifdef _WIN32

    switch (WaitForSingleObject(_lock,
                                timeout == 0xFFFFFFF ? INFINITE : (DWORD)timeout))
    {
    case WAIT_ABANDONED:
      return LOCK_FAILED;

    case WAIT_OBJECT_0:
      return LOCK_OK;

    case WAIT_TIMEOUT:
      return LOCK_TIMEOUT;
    }

#else
#ifdef _MACOS

    if (timeout != 0)
    {
      if (pthread_mutex_lock(&_lock) == 0)
      {
        return LOCK_OK;
      }
    }

#else

    if (timeout == 0xFFFFFFFF)
    {
      if (pthread_mutex_lock(&_lock) == 0)
      {
        return LOCK_OK;
      }
    }

#endif
    else if (timeout == 0)
    {
      if (pthread_mutex_trylock(&_lock) == 0)
      {
        return LOCK_OK;
      }
    }

#ifndef _MACOS
    else
    {
      timespec wait_time;
      timeval now;
      gettimeofday(&now, NULL);

      wait_time.tv_sec = timeout / 1000 + now.tv_sec;
      wait_time.tv_nsec = (timeout % 1000) * 1000000 + now.tv_usec * 1000;

      if (wait_time.tv_nsec >= 1000000000)
      {
        ++wait_time.tv_sec;
        wait_time.tv_nsec -= 1000000000;
      }

#if !defined(__ANDROID__)

      switch (pthread_mutex_timedlock(&_lock, &wait_time))
      {
      case 0:
        return LOCK_OK;

      case ETIMEDOUT:
        return LOCK_TIMEOUT;
      }

#else
      struct timeval timenow;
      struct timespec sleepytime;
      /* This is just to avoid a completely busy wait */
      sleepytime.tv_sec = 0;
      sleepytime.tv_nsec = 10000000; /* 10ms */

      while (pthread_mutex_trylock(&_lock) == EBUSY)
      {
        gettimeofday(&timenow, NULL);

        if (timenow.tv_sec >= wait_time.tv_sec &&
            (timenow.tv_usec * 1000) >= wait_time.tv_nsec)
        {
          return LOCK_TIMEOUT;
        }

        nanosleep(&sleepytime, NULL);
      }

      return LOCK_OK;

#endif
    }

#endif
#endif

    return LOCK_FAILED;
  }

  void unlock()
  {
#ifdef _WIN32
    ReleaseMutex(_lock);
#else
    pthread_mutex_unlock(&_lock);
#endif
  }

#ifdef _WIN32
  HANDLE getLockHandle()
  {
    return _lock;
  }
#else
  pthread_mutex_t *getLockHandle()
  {
    return &_lock;
  }
#endif

protected:
  void init()
  {
#ifdef _WIN32
    _lock = CreateMutex(NULL, FALSE, NULL);
#else
    pthread_mutex_init(&_lock, NULL);
#endif
  }

  void release()
  {
    unlock();
#ifdef _WIN32

    if (_lock)
    {
      CloseHandle(_lock);
    }

    _lock = NULL;
#else
    pthread_mutex_destroy(&_lock);
#endif
  }

#ifdef _WIN32
  HANDLE _lock;
#else
  pthread_mutex_t _lock;
#endif
};

class Event
{
public:
  enum
  {
    EVENT_OK = 1,
    EVENT_TIMEOUT = 2,
    EVENT_FAILED = 0,
  };

  explicit Event(bool isAutoReset = true, bool isSignal = false)
#ifdef _WIN32
      : _event(NULL)
#else
      : _is_signalled(isSignal), _isAutoReset(isAutoReset)
#endif
  {
#ifdef _WIN32
    _event = CreateEvent(NULL, isAutoReset ? FALSE : TRUE, isSignal ? TRUE : FALSE,
                         NULL);
#else
    int ret = pthread_condattr_init(&_cond_cattr);

    if (ret != 0)
    {
      fprintf(stderr, "Failed to init condattr...\n");
      fflush(stderr);
    }

    ret = pthread_condattr_setclock(&_cond_cattr, CLOCK_MONOTONIC);
    pthread_mutex_init(&_cond_locker, NULL);
    ret = pthread_cond_init(&_cond_var, &_cond_cattr);
#endif
  }

  ~Event()
  {
    release();
  }

  void set(bool isSignal = true)
  {
    if (isSignal)
    {
#ifdef _WIN32
      SetEvent(_event);
#else
      pthread_mutex_lock(&_cond_locker);

      if (_is_signalled == false)
      {
        _is_signalled = true;
        pthread_cond_signal(&_cond_var);
      }

      pthread_mutex_unlock(&_cond_locker);
#endif
    }
    else
    {
#ifdef _WIN32
      ResetEvent(_event);
#else
      pthread_mutex_lock(&_cond_locker);
      _is_signalled = false;
      pthread_mutex_unlock(&_cond_locker);
#endif
    }
  }

  unsigned long wait(unsigned long timeout = 0xFFFFFFFF)
  {
#ifdef _WIN32

    switch (WaitForSingleObject(_event,
                                timeout == 0xFFFFFFF ? INFINITE : (DWORD)timeout))
    {
    case WAIT_FAILED:
      return EVENT_FAILED;

    case WAIT_OBJECT_0:
      return EVENT_OK;

    case WAIT_TIMEOUT:
      return EVENT_TIMEOUT;
    }

    return EVENT_OK;
#else
    unsigned long ans = EVENT_OK;
    pthread_mutex_lock(&_cond_locker);

    if (!_is_signalled)
    {
      if (timeout == 0xFFFFFFFF)
      {
        pthread_cond_wait(&_cond_var, &_cond_locker);
      }
      else
      {
        struct timespec wait_time;
        clock_gettime(CLOCK_MONOTONIC, &wait_time);

        wait_time.tv_sec += timeout / 1000;
        wait_time.tv_nsec += (timeout % 1000) * 1000000ULL;

        if (wait_time.tv_nsec >= 1000000000)
        {
          ++wait_time.tv_sec;
          wait_time.tv_nsec -= 1000000000;
        }

        switch (pthread_cond_timedwait(&_cond_var, &_cond_locker, &wait_time))
        {
        case 0:
          // signalled
          break;

        case ETIMEDOUT:
          // time up
          ans = EVENT_TIMEOUT;
          goto _final;
          break;

        default:
          ans = EVENT_FAILED;
          goto _final;
        }
      }
    }

    assert(_is_signalled);

    if (_isAutoReset)
    {
      _is_signalled = false;
    }

  _final:
    pthread_mutex_unlock(&_cond_locker);

    return ans;
#endif
  }

protected:
  void release()
  {
#ifdef _WIN32
    CloseHandle(_event);
#else
    pthread_condattr_destroy(&_cond_cattr);
    pthread_mutex_destroy(&_cond_locker);
    pthread_cond_destroy(&_cond_var);
#endif
  }

#ifdef _WIN32
  HANDLE _event;
#else
  pthread_condattr_t _cond_cattr;
  pthread_cond_t _cond_var;
  pthread_mutex_t _cond_locker;
  bool _is_signalled;
  bool _isAutoReset;
#endif
};

class ScopedLocker
{
public:
  explicit ScopedLocker(Locker &l) : _binded(l)
  {
    _binded.lock();
  }

  void forceUnlock()
  {
    _binded.unlock();
  }
  ~ScopedLocker()
  {
    _binded.unlock();
  }
  Locker &_binded;
};
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/serial_port.h`

```
#ifndef NODE_SERIAL_H
#define NODE_SERIAL_H

#include "lidar_information.h"
#include <stdint.h>
#include <vector>

#include <string>
#include <atomic>
#include <limits>
#include <termios.h>

using namespace std;

class MillisecondTimer
{
public:
  explicit MillisecondTimer(const uint64_t millis);
  int64_t remaining();

private:
  static timespec timespec_now();
  timespec expiry;
};

struct Timeout
{
  static uint32_t max()
  {
    return std::numeric_limits<uint32_t>::max();
  }
  
  static Timeout simpleTimeout(uint32_t timeout_t)
  {
    return Timeout(max(), timeout_t, 0, timeout_t, 0);
  }

  uint32_t inter_byte_timeout;
  uint32_t read_timeout_constant;

  uint32_t read_timeout_multiplier;
  uint32_t write_timeout_constant;
 
  uint32_t write_timeout_multiplier;

  explicit Timeout(uint32_t inter_byte_timeout_ = 0,
                   uint32_t read_timeout_constant_ = 0,
                   uint32_t read_timeout_multiplier_ = 0,
                   uint32_t write_timeout_constant_ = 0,
                   uint32_t write_timeout_multiplier_ = 0)
      : inter_byte_timeout(inter_byte_timeout_),
        read_timeout_constant(read_timeout_constant_),
        read_timeout_multiplier(read_timeout_multiplier_),
        write_timeout_constant(write_timeout_constant_),
        write_timeout_multiplier(write_timeout_multiplier_)
  {
  }
};


typedef enum {
  fivebits = 5,
  sixbits = 6,
  sevenbits = 7,
  eightbits = 8
} bytesize_t;

typedef enum {
  stopbits_one = 1,
  stopbits_two = 2,
  stopbits_one_point_five
} stopbits_t;

typedef enum {
  flowcontrol_none = 0,
  flowcontrol_software,
  flowcontrol_hardware
} flowcontrol_t;

typedef enum {
  parity_none = 0,
  parity_odd = 1,
  parity_even = 2,
  parity_mark = 3,
  parity_space = 4
} parity_t;

class Serial_Port
{
private:
  string port_;
  
  unsigned long baudrate_;    // Baudrate
  int fd_;
  pid_t pid;
  bool is_open_ = false;
  uint32_t byte_time_ns_; // Nanoseconds to transmit/receive a single byte

  Timeout timeout_;           // Timeout for read operations

  parity_t parity_;           // Parity
  bytesize_t bytesize_;       // Size of the bytes
  stopbits_t stopbits_;       // Stop Bits
  flowcontrol_t flowcontrol_; // Flow Control

public:
  Serial_Port(const std::string &port = "",
                  uint32_t baudrate = 115200,
                  Timeout timeout = Timeout(),
                  bytesize_t bytesize = eightbits,
                  parity_t parity = parity_none,
                  stopbits_t stopbits = stopbits_one,
                  flowcontrol_t flowcontrol = flowcontrol_none);

  ~Serial_Port();
  bool open();
  void close();
  bool getTermios(termios *tio);

  /*设置数据位数*/
  void set_databits(termios *tio, bytesize_t databits);

  /*设置奇偶性*/
  void set_parity(termios *tio, parity_t parity);

  /*设置停止位*/
  void set_stopbits(termios *tio, stopbits_t stopbits);

  /*流量控制*/
  void set_flowcontrol(termios *tio,flowcontrol_t flowcontrol);

  void set_common_props(termios *tio);

  
  result_t read_data(uint8_t *buf, size_t size);
  size_t write_data(const uint8_t *data, size_t length);
  result_t waitForData(size_t data_count, uint64_t timeout, size_t *returned_size);
  size_t available();
  bool setDTR(bool level);

  /*获取串口传输一个byte时间*/
  uint32_t getByteTime();

  bool setBaudrate(unsigned long baudrate);
  bool setTermios(const termios *tio);
  bool setCustomBaudRate(unsigned long baudrate);
  bool waitReadable(uint32_t timeout_t);



};

#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/calibration.h`

```
#ifndef LIDAR_CALIBRATION
#define LIDAR_CALIBRATION

#include "lidar_information.h"
#include <vector>

#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/core/core.hpp>

using namespace std;

const int map_ratio = 40;

// 定义二维向量结构体
struct Vector2D {
    double x;
    double y;

    // 计算向量的模长
    double Length() {
        return sqrt(x * x + y * y);
    }

    // 计算向量的点积
    double Dot(Vector2D v) {
        return x * v.x + y * v.y;
    }

    // 计算向量的叉积
    double Cross(Vector2D v) {
        return x * v.y - y * v.x;
    }

    // 计算向量的夹角（单位：弧度）
    double Angle(Vector2D v) {
        double dot = Dot(v);
        double cross = Cross(v);
        return atan2(cross, dot);
    }
};

// 定义线段结构体
struct LineSegment {
    Vector2D p1;
    Vector2D p2;
};


typedef struct 
{
    float x,y;
    float theta;
}pos_t;

typedef struct _point_
{
    float x , y , q ;
    int index ;
    float angle;
    float range;
    bool change = false;
    uint16_t intensity;
}point_t;

typedef struct _point_cloud_
{
    std::vector<point_t> data;
    pos_t origin;
    point_t origin_point;
}pcloud_t;

struct point_lines{
  point_t line_start;
  point_t line_end;
};

typedef struct _border_frame_
{
    int top,bottom;
    int left,right;
}border_frame_t;

class coord_tt
{
    public:
    int x,y;
    float theta;
    coord_tt(int x = 0, int y = 0, float theta = 0.0)
        :x(x), y(y), theta(theta){}
    void move(coord_tt);
    pos_t pos();
};

struct Line_new {
    double slope;
    double intercept;
};

//栅格坐标
typedef struct grid
{
    int x,y;
    bool operator==(const grid &b)const{return x == b.x && y == b.y;}
    bool operator!=(const grid &b)const{return x != b.x || y != b.y;}
    bool operator<(const grid &b)const {if(x == b.x) return y < b.y; return x < b.x;}
    bool operator>(const grid &b)const {if(x == b.x) return y > b.y; return x > b.x;}
    grid operator+(const grid &b) {return {x + b.x, y + b.y};}
    grid operator-(const grid &b) {return {x - b.x, y - b.y};}
    
    grid () {x = y = 0;}
    grid (int x_, int y_) {x = x_; y = y_;}
    grid (coord_tt coord){x = coord.x; y = coord.y;}
    
    bool near(grid &b)  {return abs(x - b.x) <= 1 && abs(y - b.y) <= 1;}
    //bool vaild() {return x >= 0 && y >= 0 && x < map_width_limit && y < map_width_limit;}
    void move(grid b) {x += b.x; y += b.y;} 
}grid_t;

typedef struct
{
    float dist;
    float ratio;
    grid_t point;
}p2seg_ret_t;


typedef struct _calibration_params_
{
  float distortion_processing_distance = 500;
 
  point_t origin_point;

  int calibration_type = 0;   //0:剔除畸变 1：拉直畸变

  int line_judgment_point_num;//判断提取一条直线的最小点数
}calibration_params_t;

extern calibration_params_t calibration_params;

/*畸变处理入口函数*/
void lidar_calibration(LaserScan &outscan);

/*获取直线的斜率和截距*/
void getLineKB(point_t start_point, point_t end_point, double &k, double &b);

/*点到直线的距离*/
double pointToLineDist(point_t point, double k, double b);

/*雷达数据转换为点云数据*/
void pcloud_build_by_pos_scan(LaserScan &outscan ,pcloud_t &pcloud);

/*拟合直线进行畸变处理的入口*/
void fitting_line(pcloud_t &pcloud);


/*直线的过程判断*/
bool line_judgment(std::vector<point_t> line, point_t point);

/*求相邻线段的夹角*/
void neighbor_lines_new(std::vector<point_t> line_first, std::vector<point_t> line_second, pcloud_t &pcloud);

/*进行直角畸变处理*/
void Point_cloud_straightening_new(std::vector<point_t> line_first, std::vector<point_t> line_second, pcloud_t &pcloud);

/*求两点间距离*/
float pointTopointDist(point_t a, point_t b);

/*判断点是否在直线的左侧*/
int isLeft(point_t p, point_t a, point_t b);

/*针对直线进行拉直处理*/
void straightening_process_new(std::vector<point_t> line_point, point_t a, point_t b, pcloud_t &pcloud);

/*求两个直线是否相交，并计算交点*/
bool intersect(LineSegment line1, LineSegment line2, Vector2D &intersection);

/*求两条直线的交点*/
point_t calculateIntersection(Line_new line1, Line_new line2);



#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/lidar_data_processing.h`

```
#ifndef LIDAR_DATA_PROCESSING
#define LIDAR_DATA_PROCESSING

#include <stdint.h>
#include "lidar_information.h"

class Lidar_Data_Processing
{

private:
  uint16_t CheckSumCal;
  uint16_t CheckSum;		         //校验和
  uint16_t SampleNumlAndCTCal;
  uint16_t LastSampleAngleCal;
  uint16_t Valu8Tou16;
  uint16_t package_Sample_Index; //包采样点索引
  uint16_t FirstSampleAngle;     //起始采样角
  uint16_t LastSampleAngle;      //结束采样角
  uint8_t scan_frequence;	       //协议中雷达转速
  bool CheckSumResult;
  bool has_package_error;
  float IntervalSampleAngle;
  float IntervalSampleAngle_LastPackage;
  int package_index;

  float start_t =0;
  float stop_t = 0;
  float angle_new = 0;
  float angle_bak = 0;
  size_t recvNodeCount;

  uint64_t m_node_time_ns;			 //< time stamp
  uint64_t m_node_last_time_ns;  //< time stamp
  uint32_t m_pointTime;				   //< two laser point time intervals
  size_t buffer_size = 0;

public:

  Lidar_Data_Processing();
  ~Lidar_Data_Processing();

  int PackageSampleBytes;   //一个包包含的激光点数

  /*向激光雷达发布指令*/
  //result_t sendCommand(uint8_t cmd,const void *payload = NULL,size_t payloadsize = 0);
  result_t sendCommand(uint8_t cmd);
  /*向激光雷达写数据*/
  result_t sendData(const uint8_t *data, size_t size);

  /*接收激光雷达回复的消息*/
  result_t waitResponseHeader(uint8_t cmd,uint64_t timeout = DEFAULT_TIMEOUT);

  /*等待激光雷达调速完成*/
  result_t waitSpeedRight(uint8_t cmd,uint64_t timeout = DEFAULT_TIMEOUT);

  /*接收串口上传的雷达数据*/
  result_t waitScanData(node_info *nodebuffer, size_t &count,uint32_t timeout = DEFAULT_TIMEOUT);

  /*解析接收到的雷达数据点（v1及v2版本）*/
  result_t waitPackage(node_info *node,uint32_t timeout = DEFAULT_TIMEOUT);

  /*解析接收到的雷达数据点（M1CT_coin_plus）*/
  result_t waitPackage_coin(node_info *node,uint32_t timeout = DEFAULT_TIMEOUT);
};

#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/mtime.h`

```
#ifndef __H_MTIME_H__
#define __H_MTIME_H__

#include <chrono>
#include <unistd.h>
#include <time.h>

enum TIME_PRECISION
{
	TIME_NANOSECOND = 0,	//纳秒
	TIME_MICROSECOND,		//微秒
	TIME_MILLISECOND,		//毫秒
	TIME_SECOND,
	TIME_MINUTE,
	TIME_HOUR
};

//计算用时
extern std::chrono::time_point<std::chrono::steady_clock> time_start;
inline void timestart()
{
	time_start = std::chrono::steady_clock::now();
}
inline int64_t timeused()
{
	return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - time_start).count();
}
inline int64_t timeused(std::chrono::time_point<std::chrono::steady_clock>& time_last)
{
	return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - time_last).count();
}

//休眠多少毫秒
void sleep_ms(int ms);

//获取tm (只更新年月日时分秒)
struct tm localdate(int time_zone = 8);

//获取时间[整数]
int64_t current_times(int precision = TIME_MILLISECOND);

//获取时间[字符串]
char *time_str(const char *fmt = "%F %T");

#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/point_cloud_optimize.h`

```
#ifndef POINT_CLOUD_OPTIMIZE_H
#define POINT_CLOUD_OPTIMIZE_H

//#include "node_lidar.h"
#include "lidar_data_processing.h"
#include <vector>
#include "lidar_information.h"

using namespace std;
class Point_cloud_optimize
{
private:
    int cnt=0;
    int cnt_all=0;
    int cnt_judge=0;
    int cnt_record=0;
    bool cumulation = false;
    short Lidar_Blocked[800];
    
public:

    /*点云滤波*/
    void PointCloudFilter(LaserScan *Scan);

    /*当前点的距离减去相同角度下雷达到扫地机边缘的距离*/
    int UltrasonicSimRanging(LaserPoint &pScan);

    /*获取需要剔除的角度信息*/
    void getLidarCoverAngle(char *charbuf);

    /*雷达被遮挡的判断*/
    void lidar_blocked_judge(int count);

    /*雷达被遮挡计数*/
    void lidar_blocked_count(LaserPoint &pScan,int count_lidar);

    /*点云缺口剔除*/
    void lidar_cover_cut(float &,float &);

    /*数据重置*/
    void datas_clear();

    void lidar_blocked_init();
    
};

#endif
```
## `cspc_lidar_sdk_ros1/include/cspc_lidar/node_lidar.h`

```
#ifndef NODE_LIDAR_H
#define NODE_LIDAR_H

#include <stdint.h>
#include <vector>
#include <string>
#include <atomic>
#include "point_cloud_optimize.h"
#include "lidar_data_processing.h"
#include "serial_port.h"
#include "locker.h"
#include "timer.h"
#include <memory>
#include <iostream>


#include <ros/ros.h>
#include <sensor_msgs/LaserScan.h>

#include <iostream>

using namespace std;

/*雷达基本信息*/
typedef struct{
  int version = 1; //雷达版本
  string port = "/dev/sc_mini";     //串口名称
  int m_SerialBaudrate = 115200;   //波特率
  bool m_intensities = false;
  uint64_t m_PointTime = 1e9/3800; 
  uint32_t trans_delay = 0;
  string frame_id = "laser_link";
}lidar_general_info_t;

/*雷达被遮挡判断结构体*/
typedef struct{
  uint16_t point_check = 0;
  uint16_t point_check_part = 0;
  uint16_t point_check_all = 0;
  int blocked_size = 0;
  int lidar_zero_count = 0;
  bool blocked_judge = true;
}lidar_block_t;

/*雷达原始数据包*/
typedef struct{
  node_package package;
  node_packages packages;
  node_package_coin package_coin;
}lidar_package_t;

/*雷达的时间*/
typedef struct{
  uint32_t scan_time_t = 0;      
  uint64_t scan_time_current = 0;
  uint64_t scan_time_record = 0;
  uint64_t system_start_time = 0;
  uint64_t last_encry_time = 0;
  uint64_t tim_scan_start = 0;
  uint64_t tim_scan_end = 0;
  uint64_t lidar_frequence_abnormal_time = 0;
}lidar_time_t;

/*机器人结构信息*/
typedef struct{
  float install_to_zero = 90.0;
  int ROBOT_DIAMETER_mm;               //扫地机直径
  int LIDAR_ROBOT_CENTER_DISTANCE_mm;  //扫地机雷达安装位置到中心的距离
  int LidarCoverBarNumber = 0;//雷达缺口剔除数值
  vector<LidarCoverAngleStr> LidarCoverAngle;
}lidar_robot_info_t;

/*雷达节点的运行状态*/
typedef struct{
  bool FilterEnable = true;           //是否需要滤波
  bool GyroCompensateEnable = false; //是否要做旋转角度补偿
  bool isConnected = false;          //串口连接状体
  bool slam_user = false;
  bool encry_lidar = false;
  bool optimize_enable = true;
  bool lidar_cover = false;
  bool disable_encry = false;
  bool able_exposure = false;
  bool low_exposure = false;
  bool lidar_ready = false;
  bool lidar_last_status =false;
  bool close_lidar = true;
  bool lidar_trap_restart = false;    //雷达卡住重启状态

  bool lidar_restart_try = false;


  uint8_t lidar_abnormal_state = 0; 
}lidar_status_t;

struct node_lidar_t
{

  node_info *scan_node_buf;      //存储激光雷达点的信息
  uint8_t *globalRecvBuffer;     //存储接收到的雷达数据
  lidar_block_t lidar_block;     //雷达被遮挡判断

  lidar_package_t scan_packages; //不同版本的雷达数据包

  lidar_time_t lidar_time;       //雷达的时间

  lidar_general_info_t lidar_general_info; //雷达基本信息

  lidar_robot_info_t lidar_robot_info;     //雷达相对机器人安装位置的信息

  lidar_status_t lidar_status;             //雷达运行状态

  size_t scan_node_count = 0;	//激光点数
  
  uint8_t recv_encryp[8];
  uint8_t lidar_version[8];

  Point_cloud_optimize optimize_lidar;
  Lidar_Data_Processing lidar_data_processing;
  //Serial_Port *serial_port;
  std::shared_ptr<Serial_Port> serial_port;
  Event _dataEvent;
  Locker _lock;

  bool data_calibration = false;
  float range_max;

  ~node_lidar_t();
};

extern node_lidar_t node_lidar;


bool initialize(); 
int node_start(int argc, char **argv);
void send_lidar_data(LaserScan &outscan);
void flushSerial();
result_t grabScanData(uint32_t timeout = DEFAULT_TIMEOUT);
result_t connect(const char *port_path, uint32_t baudrate,node_lidar_t &lidar_arg);


#endif
```
## `cspc_lidar_sdk_ros1/CMakeLists.txt`

```
cmake_minimum_required(VERSION 2.8.3)
project(cspc_lidar)

#SET(CMAKE_C_COMPILER arm-openwrt-linux-gcc)
#SET(CMAKE_CXX_COMPILER arm-openwrt-linux-g++)
set(CMAKE_CXX_FLAGS "-std=c++11 ${CMAKE_CXX_FLAGS}")

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}  -fsanitize=address -fsanitize=leak -g1 -fno-stack-protector -fno-omit-frame-pointer -fno-var-tracking")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}  -fsanitize=address -fsanitize=leak -g1 -fno-stack-protector -fno-omit-frame-pointer -fno-var-tracking")

#set(CMAKE_CXX_FLAGS, "-Os -pipe -march=armv7-a -mtune=cortex-a7 -mfpu=neon
#-fno-caller-saves -fno-plt -mfloat-abi=hard  -Wformat -Werror=format-security
#-fstack-protector -D_FORTIFY_SOURCE=1 -Wl,-z,now -Wl,-z,relro -Wno-virtual-dtor
#-std=c++11 -D__ANDROID__")

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  nav_msgs
  pluginlib
  roscpp
  sensor_msgs
  std_msgs
  tf
)

## System dependencies are found with CMake's conventions
find_package(Boost REQUIRED )
find_package(OpenCV REQUIRED)


## Uncomment this if the package has a setup.py. This macro ensures
## modules and global scripts declared therein get installed
## See http://ros.org/doc/api/catkin/html/user_guide/setup_dot_py.html
# catkin_python_setup()

################################################
## Declare ROS messages, services and actions ##
################################################

## To declare and build messages, services or actions from within this
## package, follow these steps:
## * Let MSG_DEP_SET be the set of packages whose message types you use in
##   your messages/services/actions (e.g. std_msgs, actionlib_msgs, ...).
## * In the file package.xml:
##   * add a build_depend tag for "message_generation"
##   * add a build_depend and a exec_depend tag for each package in MSG_DEP_SET
##   * If MSG_DEP_SET isn't empty the following dependency has been pulled in
##     but can be declared for certainty nonetheless:
##     * add a exec_depend tag for "message_runtime"
## * In this file (CMakeLists.txt):
##   * add "message_generation" and every package in MSG_DEP_SET to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * add "message_runtime" and every package in MSG_DEP_SET to
##     catkin_package(CATKIN_DEPENDS ...)
##   * uncomment the add_*_files sections below as needed
##     and list every .msg/.srv/.action file to be processed
##   * uncomment the generate_messages entry below
##   * add every package in MSG_DEP_SET to generate_messages(DEPENDENCIES ...)

## Generate messages in the 'msg' folder
# add_message_files(
#   FILES
#   Message1.msg
#   Message2.msg
# )

## Generate services in the 'srv' folder
# add_service_files(
#   FILES
#   Service1.srv
#   Service2.srv
# )

## Generate actions in the 'action' folder
# add_action_files(
#   FILES
#   Action1.action
#   Action2.action
# )

## Generate added messages and services with any dependencies listed here
# generate_messages(
#   DEPENDENCIES
#   geometry_msgs#   nav_msgs#   sensor_msgs#   std_msgs
# )

################################################
## Declare ROS dynamic reconfigure parameters ##
################################################

## To declare and build dynamic reconfigure parameters within this
## package, follow these steps:
## * In the file package.xml:
##   * add a build_depend and a exec_depend tag for "dynamic_reconfigure"
## * In this file (CMakeLists.txt):
##   * add "dynamic_reconfigure" to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * uncomment the "generate_dynamic_reconfigure_options" section below
##     and list every .cfg file to be processed

## Generate dynamic reconfigure parameters in the 'cfg' folder
# generate_dynamic_reconfigure_options(
#   cfg/DynReconf1.cfg
#   cfg/DynReconf2.cfg
# )

###################################
## catkin specific configuration ##
###################################
## The catkin_package macro generates cmake config files for your package
## Declare things to be passed to dependent projects
## INCLUDE_DIRS: uncomment this if your package contains header files
## LIBRARIES: libraries you create in this project that dependent projects also need
## CATKIN_DEPENDS: catkin_packages dependent projects also need
## DEPENDS: system dependencies of this project that dependent projects also need
catkin_package(
# include
# ${catkin_INCLUDE_DIRS}
# ${Boost_INCLUDE_DIRS}

)

###########
## Build ##
###########

## Specify additional locations of header files
## Your package locations should be listed before other locations
include_directories(
  include/cspc_lidar/
  ${catkin_INCLUDE_DIRS}
   ${Boost_INCLUDE_DIRS}
)

## Declare a C++ library
# add_library(${PROJECT_NAME}
#   src/${PROJECT_NAME}/main.cpp
# )

## Add cmake target dependencies of the library
## as an example, code may need to be generated before libraries
## either from message generation or dynamic reconfigure
# add_dependencies(${PROJECT_NAME} ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Declare a C++ executable
## With catkin_make all packages are built within a single CMake context
## The recommended prefix ensures that target names across packages don't collide

## Rename C++ executable without prefix
## The above recommended prefix causes long target names, the following renames the
## target back to the shorter version for ease of user use
## e.g. "rosrun someones_pkg node" instead of "rosrun someones_pkg someones_pkg_node"
# set_target_properties(${PROJECT_NAME}_node PROPERTIES OUTPUT_NAME node PREFIX "")

## Add cmake target dependencies of the executable
## same as for the library above
# add_dependencies(${PROJECT_NAME}_node ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Specify libraries to link a library or executable target against
# target_link_libraries(${PROJECT_NAME}_node
#   ${catkin_LIBRARIES}
# )

#############
## Install ##
#############

# all install targets should use catkin DESTINATION variables
# See http://ros.org/doc/api/catkin/html/adv_user_guide/variables.html

## Mark executable scripts (Python etc.) for installation
## in contrast to setup.py, you can choose the destination
# install(PROGRAMS
#   scripts/my_python_script
#   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
# )

## Mark executables and/or libraries for installation
# install(TARGETS ${PROJECT_NAME} ${PROJECT_NAME}_node
#   ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
# )

## Mark cpp header files for installation
# install(DIRECTORY include/${PROJECT_NAME}/
#   DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
#   FILES_MATCHING PATTERN "*.h"
#   PATTERN ".svn" EXCLUDE
# )

## Mark other files for installation (e.g. launch and bag files, etc.)
# install(FILES
#   # myfile1
#   # myfile2
#   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
# )

#############
## Testing ##
#############

## Add gtest based cpp test target and link libraries
# if(TARGET ${PROJECT_NAME}-test)
#   target_link_libraries(${PROJECT_NAME}-test ${PROJECT_NAME})
# endif()

## Add folders to be run by python nosetests
# catkin_add_nosetests(test)

add_executable(cspc_lidar src/mtime.cpp src/main.cpp src/node_lidar.cpp src/serial_port.cpp src/timer.cpp src/lidar_data_processing.cpp src/point_cloud_optimize.cpp src/calibration.cpp)
add_dependencies(cspc_lidar ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})
target_link_libraries(cspc_lidar ${catkin_LIBRARIES} ${Boost_LIBRARIES} ${OpenCV_LIBRARIES})
```
## `cspc_lidar_sdk_ros1/src/calibration.cpp`

```
#include <calibration.h>
#include <iostream>
#include <cstring>
#include <math.h>
#include <algorithm>
#include <iostream>
#include <cmath>

using namespace std;

calibration_params_t calibration_params;

#define RADIAN360 6.28318530717948
#define RADIAN180 3.14159265358974

/*弧度转角度*/
float RADIAN2ANGLE(float x)
{
  return 57.29577951308232 * x;
}
/*角度转弧度*/
float ANGLE2RADIAN(float x)
{
  return 0.017453292519943 * x;
}

/*点到点的距离*/
float pointTopointDist(point_t a, point_t b)
{
  return sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
}

/*清空点云数据*/
void pcloud_clear(pcloud_t &pcloud)
{
  pcloud.data.clear();
}

/*将雷达数据转换为点云数据*/
void pcloud_build_by_scan(LaserScan &outscan, pcloud_t &pcloud)
{
  point_t point;
  for (int i = 0; i < outscan.points.size(); i++)
  {
    memset(&point, 0, sizeof(point_t));
    // 阈值滤波
    // if (scan->lasers[i].dis < lidar_min_range || scan->lasers[i].dis > lidar_max_range || scan->lasers[i].quality)
    if (outscan.points[i].range * 1000 <= 0 || outscan.points[i].range * 1000 > 10 * 1000)
    {
      outscan.points[i].range = 0;
    }
    // 距离/角度转换点
    point.index = i;
    point.x = cosf(ANGLE2RADIAN(-outscan.points[i].angle)) * outscan.points[i].range * 1000;
    point.y = sinf(ANGLE2RADIAN(-outscan.points[i].angle)) * outscan.points[i].range * 1000;

    point.angle = outscan.points[i].angle;
    point.intensity = outscan.points[i].intensity;
    point.range = outscan.points[i].range;

    pcloud.data.emplace_back(point);
  }
}

/*将极坐标系下的点云转换到世界坐标系下*/
void pcloud_offset_by_pos(pcloud_t &pcloud)
{
  pos_t lidar_pos = pcloud.origin;

  point_t *point;
  float x, y;
  int size = (int)pcloud.data.size();
  for (int i = 0; i < size; i++)
  {
    point = &pcloud.data[i];
    x = point->x;
    y = point->y;

    point->x = lidar_pos.x + cosf(lidar_pos.theta) * x - sinf(lidar_pos.theta) * y;
    point->y = lidar_pos.y + cosf(lidar_pos.theta) * y + sinf(lidar_pos.theta) * x;
  }
}

/*点云转换函数*/
void pcloud_build_by_pos_scan(LaserScan &outscan, pcloud_t &pcloud)
{
  pcloud_clear(pcloud);

  pcloud.origin.x = calibration_params.origin_point.x;
  pcloud.origin.y = calibration_params.origin_point.y;
  pcloud.origin.theta = 0;

  // 将雷达原始数据转换成极坐标点云
  pcloud_build_by_scan(outscan, pcloud);

  // 将极坐标点云转换成真实坐标系下的点云
  pcloud_offset_by_pos(pcloud);
}

/*查找对应点*/
int find_index(point_t point, pcloud_t &pcloud)
{
  point_t point_min;
  memset(&point_min, 0, sizeof(point_t));
  float legth = 15000;
  for (auto p_point : pcloud.data)
  {
    double distance = sqrt(pow(p_point.x - point.x, 2) + pow(p_point.y - point.y, 2));

    if (distance < legth)
    {
      legth = distance;
      point_min = p_point;
    }
    /*
    if(p_point.x == point.x && p_point.y == point.y)
    {
      return p_point.index;
    }*/
  }
  // std::cout <<"p-x:"<< point.x << "p-y:" << point.y << std::endl;
  // std::cout <<"min-x:"<< point_min.x << "min-y:" << point_min.y << std::endl;
  if (point_min.index > pcloud.data.size())
  {
    return 0;
  }
  else
  {
    return point_min.index;
  }
}

/*移除噪点*/
void remove_noise_point(cv::Vec4i line_f, cv::Vec4i line_s, pcloud_t &pcloud)
{
  point_t point_f_1, point_f_2;
  point_t point_e_1, point_e_2;

  point_f_1.x = (float)line_f[0];
  point_f_1.y = (float)line_f[1];

  int index = find_index(point_f_1, pcloud);
  for (int i = 0; i < 3; i++)
  {
    if ((index - 1) >= 0)
    {
      pcloud.data[index - i].range = 0;
    }
    else
    {
      break;
    }
  }

  point_f_2.x = (float)line_f[2];
  point_f_2.y = (float)line_f[3];

  index = find_index(point_f_2, pcloud);
  for (int i = 0; i < 3; i++)
  {
    if ((index + i) < pcloud.data.size())
    {
      pcloud.data[index + i].range = 0;
    }
    else
    {
      break;
    }
  }

  point_e_1.x = (float)line_s[0];
  point_e_1.y = (float)line_s[1];

  index = find_index(point_e_1, pcloud);
  for (int i = 0; i < 3; i++)
  {
    if ((index - 1) >= 0)
    {
      pcloud.data[index - i].range = 0;
    }
    else
    {
      break;
    }
  }

  point_e_2.x = (float)line_s[2];
  point_e_2.y = (float)line_s[3];

  index = find_index(point_e_2, pcloud);
  for (int i = 0; i < 3; i++)
  {
    if ((index + i) < pcloud.data.size())
    {
      pcloud.data[index + i].range = 0;
    }
    else
    {
      break;
    }
  }
}

// 判断点是否在线段左侧
int isLeft(point_t p, point_t a, point_t b)
{
  double cross_product = a.x * b.y + b.x * p.y + p.x * a.y - a.x * p.y - b.x * a.y - p.x * b.y;
  if (cross_product > 0)
    return 1;
  else if (cross_product < 0)
    return 2;
  else
    return 0;
}

// 判断两个线段是否相交，并计算交点
bool intersect(LineSegment line1, LineSegment line2, Vector2D &intersection)
{
  // 计算两个方向向量
  Vector2D direction1 = {line1.p2.x - line1.p1.x, line1.p2.y - line1.p1.y};
  Vector2D direction2 = {line2.p2.x - line2.p1.x, line2.p2.y - line2.p1.y};

  // 计算向量叉积
  double cross = direction1.x * direction2.y - direction1.y * direction2.x;

  // 如果叉积为0，说明两个线段共线
  if (cross == 0)
  {
    return false;
  }

  // 计算线段起点位置向量
  Vector2D position1 = {line2.p1.x - line1.p1.x, line2.p1.y - line1.p1.y};
  Vector2D position2 = {line1.p1.x - line2.p1.x, line1.p1.y - line2.p1.y};

  // 计算向量叉积
  double cross1 = position1.x * direction1.y - position1.y * direction1.x;
  double cross2 = position2.x * direction2.y - position2.y * direction2.x;

  // 计算交点坐标
  intersection.x = line1.p1.x + direction1.x * cross2 / cross;
  intersection.y = line1.p1.y + direction1.y * cross2 / cross;

  // 判断交点是否在两个线段上
  /*
  if (intersection.x < min(line1.p1.x, line1.p2.x) || intersection.x > max(line1.p1.x, line1.p2.x) ||
      intersection.x < min(line2.p1.x, line2.p2.x) || intersection.x > max(line2.p1.x, line2.p2.x)) {
      return false;
  }

  if (intersection.y < min(line1.p1.y, line1.p2.y) || intersection.y > max(line1.p1.y, line1.p2.y) ||
      intersection.y < min(line2.p1.y, line2.p2.y) || intersection.y > max(line2.p1.y, line2.p2.y)) {
      return false;
  }*/

  // 两个线段相交，返回true
  return true;
}

void straightening_process(point_lines line_point, point_t a, point_t b, pcloud_t &pcloud)
{
  LineSegment line1 = {{line_point.line_start.x, line_point.line_start.y}, {line_point.line_end.x, line_point.line_end.y}};
  LineSegment line2 = {{(double)b.x, (double)b.y}, {(double)a.x, (double)a.y}};
  Vector2D intersection;
  if (intersect(line1, line2, intersection))
  {
    cout << "线段交点坐标为：(" << intersection.x << ", " << intersection.y << ")" << endl;
  }
  else
  {
    cout << "线段不相交" << endl;
  }
  float dist = sqrt((a.x - intersection.x) * (a.x - intersection.x) + (a.y - intersection.y) * (a.y - intersection.y));

  if (dist < 100)
  {
    pcloud.data[a.index].x = intersection.x;
    pcloud.data[a.index].y = intersection.y;
    pcloud.data[a.index].range = sqrt((b.x - intersection.x) * (b.x - intersection.x) + (b.y - intersection.y) * (b.y - intersection.y));
  }
}

void straightening_process_new(std::vector<point_t> line_point, point_t p_point, point_t origin_point, pcloud_t &pcloud)
{
  
  point_t line_start_point = line_point.front();
  point_t line_end_point = line_point.back();

  /*
  LineSegment line1 = {{line_start_point.x, line_start_point.y}, {line_end_point.x, line_end_point.y}};
  LineSegment line2 = {{(double)b.x, (double)b.y}, {(double)a.x, (double)a.y}};
  Vector2D intersection;
  if (intersect(line1, line2, intersection))
  {
    cout << "线段交点坐标为：(" << intersection.x << ", " << intersection.y << ")" << endl;
  }
  else
  {
    cout << "线段不相交" << endl;
  }*/
  Line_new line1, line2;

  double k, b;
  getLineKB(line_start_point, line_end_point, k, b);
  line1.slope = k;
  line1.intercept = b;

  getLineKB(p_point, origin_point, k, b);

  line2.slope = k;
  line2.intercept = b;

  point_t intersection = calculateIntersection(line1, line2);

  float dist = sqrt((p_point.x - intersection.x) * (p_point.x - intersection.x) + (p_point.y - intersection.y) * (p_point.y - intersection.y));
  cout << "拉直处理" << dist << endl;
  if (fabs(dist) < 200)
  {

    pcloud.data[p_point.index].x = intersection.x;
    pcloud.data[p_point.index].y = intersection.y;
    pcloud.data[p_point.index].range = sqrt((origin_point.x - intersection.x) * (origin_point.x - intersection.x) + (origin_point.y - intersection.y) * (origin_point.y - intersection.y));
  }
}

point_t calculateIntersection(Line_new line1, Line_new line2)
{
  point_t intersection;
  intersection.x = (line2.intercept - line1.intercept) / (line1.slope - line2.slope);
  intersection.y = line1.slope * intersection.x + line1.intercept;
  return intersection;
}

void Point_cloud_straightening_new(std::vector<point_t> line_first, std::vector<point_t> line_second, pcloud_t &pcloud)
{
  point_t line_first_point1 = line_first.front();
  point_t line_first_point2 = line_first.back();

  point_t line_second_point1 = line_second.front();
  point_t line_second_point2 = line_second.back();

  // LineSegment line1 = { {line_first_point1.x, line_first_point1.y}, {line_first_point2.x, line_first_point2.y} };
  // LineSegment line2 = { {line_second_point1.x, line_second_point1.y}, {line_second_point2.x, line_second_point2.y} };

  // Vector2D intersection;
  Line_new line1, line2;

  double k, b;
  getLineKB(line_first_point1, line_first_point2, k, b);
  line1.slope = k;
  line1.intercept = b;

  getLineKB(line_second_point1, line_second_point2, k, b);

  line2.slope = k;
  line2.intercept = b;

  point_t intersection = calculateIntersection(line1, line2);

  getLineKB(calibration_params.origin_point, intersection, k, b);

  // pointToLineDist

  /*
  if (intersect(line1, line2, intersection)) {
      //cout << "线段交点坐标为：(" << intersection.x << ", " << intersection.y << ")" << endl;
  }
  else {
      cout << "线段不相交" << endl;
      return;
  }*/

  point_t cross_point;
  cross_point.x = intersection.x;
  cross_point.y = intersection.y;
  
  if (pointTopointDist(cross_point, calibration_params.origin_point) > calibration_params.distortion_processing_distance)
  {
    std::cout << "距离判断" << pointTopointDist(cross_point, calibration_params.origin_point)
         << "," << calibration_params.distortion_processing_distance << std::endl;
    return;
  }

  double legth = 50000;
  point_t point_min;
  point_min.index = -1;
  // int index = find_index(cross_point,pcloud);
  for (auto p_point : pcloud.data)
  {
    // double distance = sqrt(pow(p_point.x - point.x, 2) + pow(p_point.y - point.y, 2));
    if(p_point.x == 10000 && p_point.y ==10000)
    {
      continue;
    }
    float distance = pointToLineDist(p_point, k, b);
    if (fabs(distance) < fabs(legth))
    {
      legth = distance;
      point_min = p_point;
    }
    /*
    if(p_point.x == point.x && p_point.y == point.y)
    {
      return p_point.index;
    }*/
  }
  if(point_min.index == -1)
  {
    return;
  }
  int index = point_min.index;

  std::cout << "距离最近点的坐标 " << pcloud.data[index].x << "," << pcloud.data[index].y << std::endl;

  int start_index = (index - 3) > 0 ? (index - 3) : 0;

  if (calibration_params.calibration_type == 0)
  {
    for (int i = start_index; i < index + 3; i++)
    {
      pcloud.data[i].range = 0;
      pcloud.data[i].intensity = 0;
      pcloud.data[i].x = pcloud.origin.x;
      pcloud.data[i].y = pcloud.origin.y;
      pcloud.data[i].change = true;
    }
  }
  else if (calibration_params.calibration_type == 1)
  {
    for (int i = start_index; i < index + 3; i++)
    {
      int judge = isLeft(pcloud.data[i], calibration_params.origin_point, cross_point);
      if (judge == 1)
      {
        straightening_process_new(line_first, pcloud.data[i], calibration_params.origin_point, pcloud);
      }
      else if (judge == 2)
      {
        straightening_process_new(line_second, pcloud.data[i], calibration_params.origin_point, pcloud);
      }
      pcloud.data[i].change = true;
    }
  }
}

void neighbor_lines_new(std::vector<point_t> line_first, std::vector<point_t> line_second, pcloud_t &pcloud)
{
  point_t line_first_point1 = line_first.front();
  point_t line_first_point2 = line_first.back();

  point_t line_second_point1 = line_second.front();
  point_t line_second_point2 = line_second.back();

  LineSegment line1 = {{line_first_point1.x, line_first_point1.y}, {line_first_point2.x, line_first_point2.y}};
  LineSegment line2 = {{line_second_point1.x, line_second_point1.y}, {line_second_point2.x, line_second_point2.y}};

  // 计算两个线段的方向向量
  Vector2D direction1 = {line1.p2.x - line1.p1.x, line1.p2.y - line1.p1.y};
  Vector2D direction2 = {line2.p2.x - line2.p1.x, line2.p2.y - line2.p1.y};

  // 求解两个方向向量的夹角
  double angle = direction1.Angle(direction2);

  // 将弧度转换为角度
  double degree = angle * 180 / M_PI;
  cout << "两条线段的夹角为：" << degree << "度" << endl;

  if (fabs(degree) > 110 && fabs(degree) < 70)
  {
    // remove_noise_point(line_f,line_s,pcloud);
  }
  else
  {
    Point_cloud_straightening_new(line_first, line_second, pcloud);
  }
}

void getLineKB(point_t start_point, point_t end_point, double &k, double &b)
{
  if (start_point.x == end_point.x)
  {
    // 直线垂直于x轴，斜率不存在
    k = NAN;
  }
  else if (start_point.y == end_point.y)
  {
    // 直线平行于x轴，斜率为0
    k = 0.0;
  }
  else
  {
    // 计算斜率和截距
    k = (end_point.y - start_point.y) / (end_point.x - start_point.x);
  }
  b = start_point.y - k * start_point.x;
}

// 求某点到直线的垂线距离
double pointToLineDist(point_t point, double k, double b)
{
  // 判断直线是否垂直于x轴
  if (fabs(k) < 1e-6)
  {
    return fabs(point.y - b);
  }

  // 计算直线上一个任意点的坐标
  double x0 = 0.0;
  double y0 = k * x0 + b;

  // 计算垂线斜率和截距
  double kt = -1.0 / k;
  double bt = point.y - kt * point.x;

  // 计算垂线与直线的交点坐标
  double ix = (bt - b) / (k - kt);
  double iy = k * ix + b;

  // 计算点到直线的距离
  return sqrt(pow(point.x - ix, 2.0) + pow(point.y - iy, 2.0));
}

bool line_judgment(std::vector<point_t> line, point_t point)
{
  point_t start_point = line.front();
  point_t end_point = line.back();
  double k, b;
  int reference = 10;
  static point_t reference_point;
  double d = 0;

  if (line.size() <= reference)
  {
    reference_point = end_point;
  }

  if (line.size() <= reference)
  {
    getLineKB(start_point, end_point, k, b);
    
    for (int i = 1; i < line.size() - 1; i++)
    {
      if(isnan(k))
      {
        d = line[i].x - start_point.x;
      }else if (k == 0.0){
        d = line[i].y - start_point.y;
      }else{
        d = pointToLineDist(line[i], k, b);
      }
      if (fabs(d) > 50)
      {
        return false;
      }
    }
    return true;
  }
  else
  {
    getLineKB(start_point, reference_point, k, b);

    /*求线段夹角*/
    LineSegment line1 = {{start_point.x, start_point.y}, {reference_point.x, reference_point.y}};
    LineSegment line2 = {{start_point.x, start_point.y}, {point.x, point.y}};
    Vector2D direction1 = {line1.p2.x - line1.p1.x, line1.p2.y - line1.p1.y};
    Vector2D direction2 = {line2.p2.x - line2.p1.x, line2.p2.y - line2.p1.y};
    double angle = direction1.Angle(direction2);
    double degree = angle * 180 / M_PI;

    if(isnan(k))
    {
      d = point.x - start_point.x;
    }else if (k == 0.0){
      d = point.y - start_point.y;
    }else{
      d = pointToLineDist(point, k, b);
    }

    // std::cout << "a坐标x：" << start_point.x << "坐标y：" << start_point.y <<std::endl;
    // std::cout << "b坐标x：" << reference_point.x << "坐标y：" <<reference_point.y <<std::endl;
    // std::cout << "c坐标x：" << point.x << "坐标y：" << point.y <<std::endl;
    // std::cout << "距离：" << dd << "角度：" << degree <<"line size"<<line.size() <<std::endl;

    if (fabs(d) < 30 && fabs(degree) < 30)
    {
      return true;
    }else{
      return false;
    }
  }
}

void fitting_line(pcloud_t &pcloud)
{
  std::vector<point_t> line;               // 当前线段
  std::vector<point_t> line_append;        // 可能遗漏的线段
  std::vector<std::vector<point_t>> lines; // 全部线段

  point_t point_record1;
  point_t point_record2;
  point_t point_last_one = pcloud.data.back();

  // 遍历点云
  for (auto &point : pcloud.data)
  {
    // 超过3个点进入直线拟合流程
    if (line.size() >= 3)
    {
      // 直线拟合判断
      if (line_judgment(line, point) == false)
      {
        if (line.size() >= calibration_params.line_judgment_point_num)
        {
          if (lines.empty())
          {
            point_record1 = line.front();
          }
          else
          {
            point_record2 = line.back();
          }
          lines.emplace_back(line);
          line.clear();
        }
        else
        {
          line.clear();
        }
      }else{
        if(point.index == point_last_one.index && line.size() >= calibration_params.line_judgment_point_num)
        {
          lines.emplace_back(line);
        }
      }
    }
    line.emplace_back(point);
  }
  line.clear();

  point_t point_append,point_append_last;
  if(point_record2.index < pcloud.data.size() 
  &&  point_last_one.index < pcloud.data.size()
  &&  point_record1.index < pcloud.data.size())
  {
     if (point_record2.index + 1 < point_last_one.index)
    {
      for (int i = point_record2.index + 1; i < point_last_one.index; i++)
      {
        point_append = pcloud.data[i];
        line_append.emplace_back(point_append);
      }
    }
    if (point_record1.index != 0)
    {
      for (int i = 0; i < point_record1.index; i++)
      {
        point_append = pcloud.data[i];
        line_append.emplace_back(point_append);
      }
    }                                                                    
  }
 
  if(!line_append.empty())
  {
    point_append_last = line_append.back();

    if (line_append.size() >= calibration_params.line_judgment_point_num)
    {
      for (auto &point : line_append)
      {
        if (line.size() >= 3)
        {
          // 直线拟合判断
          if (line_judgment(line, point) == false)
          {
            if (line.size() >= calibration_params.line_judgment_point_num)
            {
              lines.emplace_back(line);
              line.clear();
            }
            else
            {
              line.clear();
            }
          }
        }else{
          if(point.index == point_append_last.index && line.size() >= calibration_params.line_judgment_point_num)
          {
            lines.emplace_back(line);
          }
        }
        line.emplace_back(point);
      }
    }
  }

  std::cout << "------###----line_size:" << lines.size() << std::endl;

  if (lines.size() >= 2)
  {
    neighbor_lines_new(lines.back(), lines.front(), pcloud);
    for (int i = 0; i < lines.size() - 1; i++)
    {
      neighbor_lines_new(lines[i], lines[i + 1], pcloud);
    }
  }
}

void lidar_calibration(LaserScan &outscan)
{
  pcloud_t pcloud;

  // 将雷达原始数据转换成点云格式
  pcloud_build_by_pos_scan(outscan, pcloud);

  std::cout << "********size*********"<< pcloud.data.size() << std::endl;

  for(auto point : pcloud.data)
  {
    if(point.index > 500)
    {
       std::cout << "********index*********"<< point.index << std::endl;
    }
  }

  // 拟合直线进行畸变处理
  fitting_line(pcloud);

  // 清空带发布的点云
  for (auto &outscan_point : outscan.points)
  {
    memset(&outscan_point, 0, sizeof(LaserPoint));
  }

  for (auto point : pcloud.data)
  {
    if (point.change)
    {
      float distance = sqrt((point.x - pcloud.origin.x) * (point.x - pcloud.origin.x) + (point.y - pcloud.origin.y) * (point.y - pcloud.origin.y));
      outscan.points[point.index].range = distance / 1000.0f;
    }
    else
    {
      outscan.points[point.index].range = point.range;
    }

    outscan.points[point.index].angle = point.angle;
    outscan.points[point.index].intensity = point.intensity;
  }
}
```
## `cspc_lidar_sdk_ros1/src/node_lidar.cpp`

```
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <vector>
#include <thread>

#include "node_lidar.h"
#include "msg_recept.h"
#include "serial_port.h"
#include "lidar_data_processing.h"
#include "point_cloud_optimize.h"
#include "lidar_information.h"
#include "mtime.h"
#include "calibration.h"


using namespace std;

node_lidar_t node_lidar;

//#define ENCRYPTION_T

using std::placeholders::_1;
/*
class MinimalSubscriber : public rclcpp::Node
{
  public:
    MinimalSubscriber()
    : Node("cspc_lidar")
    {
      subscription_ = this->create_subscription<std_msgs::msg::UInt16>(
      "lidar_status", 10, std::bind(&MinimalSubscriber::topic_callback, this, _1));
    }

  private:
    void topic_callback(const std_msgs::msg::UInt16::SharedPtr msg) const
    {
		switch (msg->data)
		{
			//启动雷达
			case 1:
				node_lidar.lidar_status.lidar_ready = true;
				node_lidar.lidar_status.lidar_abnormal_state = 0;
				printf("#start lidar\n");
				break;
			//关闭雷达
			case 2:
				node_lidar.lidar_status.lidar_ready = false;
				node_lidar.lidar_status.close_lidar = true;
				node_lidar.serial_port->write_data(end_lidar,4);
				printf("#stop lidar\n");
				break;
			//high_exposure
			case 3:
				node_lidar.serial_port->write_data(high_exposure,4);
				break;
			//low_exposure
			case 4:
				node_lidar.serial_port->write_data(low_exposure,4);
				break;
			//清空异常状态
			case 5:
				node_lidar.lidar_status.lidar_abnormal_state = 0;
				break;
			
			default:
				break;
		}
     // RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg->data.c_str());
    }
    rclcpp::Subscription<std_msgs::msg::UInt16>::SharedPtr subscription_;
};
*/
node_lidar_t::~node_lidar_t(){
  	if(scan_node_buf)
	{
		delete[] scan_node_buf;
		scan_node_buf = NULL;
	}
	if (globalRecvBuffer)
	{
		delete[] globalRecvBuffer;
		globalRecvBuffer = NULL;
	}
	printf("关闭雷达");
	node_lidar.serial_port->close();
	node_lidar.lidar_status.lidar_ready = false;
	node_lidar.lidar_status.close_lidar = true;
	flushSerial();

}

/*清空缓存区数据*/
void flushSerial()
{
	if (!node_lidar.lidar_status.isConnected){
		return;
	}
	
	size_t len = node_lidar.serial_port->available();
	
	if (len)
	{
		uint8_t *buffer = static_cast<uint8_t *>(alloca(len * sizeof(uint8_t)));
		size_t bytes_read = node_lidar.serial_port->read_data(buffer, len);
	}

	sleep_ms(20);
}

/*激光雷达启动状态判断函数*/
bool lidar_state_judgment()
{
	static bool status_judge = false;     //整体状态判断
	static bool lidar_flush = false;      //是否已经下发雷达启动指令
	static bool wait_speed_right = false; //是否获取到调速信息
	static bool lidar_start_flag = false; //下发雷达启动指令后的雷达反馈标志

	static uint64_t lidar_status_time = 0; //收到启动指令或者重启指令的时间


	if(node_lidar.lidar_status.lidar_ready != node_lidar.lidar_status.lidar_last_status || node_lidar.lidar_status.close_lidar)
	{
		printf("状态切换\n");

		node_lidar.lidar_status.close_lidar = false;
		node_lidar.lidar_status.lidar_last_status = node_lidar.lidar_status.lidar_ready;

		lidar_flush = false;
		wait_speed_right = false;
		lidar_start_flag = false;

		lidar_status_time = current_times();
		flushSerial();
	}
	if(node_lidar.lidar_status.lidar_trap_restart)
	{
		printf("状态异常重新启动 %lld\n",lidar_status_time);
		
		node_lidar.lidar_status.lidar_trap_restart = false;

		
		wait_speed_right = false;
		lidar_flush = false;
		lidar_start_flag = false;

		lidar_status_time = current_times();
		node_lidar.serial_port->write_data(end_lidar,4);
	}
	if(node_lidar.lidar_status.lidar_ready && !wait_speed_right)
	{
		
		if(current_times() - lidar_status_time > 1000 && !lidar_flush)
		{
			switch (node_lidar.lidar_general_info.version)
			{
				case M1C1_Mini_v1:
					printf("V1版本启动雷达\n");
					node_lidar.serial_port->write_data(start_lidar,4);
					wait_speed_right = true;
					break;
				
				case M1C1_Mini_v2:
					printf("V2 X2版本启动雷达\n");
					node_lidar.serial_port->write_data(start_lidar,4);
					wait_speed_right = true;
					break;
				
				case M1CT_TOF:
					printf("TOF雷达启动\n");
					node_lidar.serial_port->write_data(start_lidar,4);
					wait_speed_right = true;
					break;
				
				default:
					break;
			}
		}
		node_lidar.lidar_time.lidar_frequence_abnormal_time = current_times();
		node_lidar.lidar_time.system_start_time = current_times();
	}
	return wait_speed_right;
}

/************************************************************************/
/*  激光数据解析线程　Laser data analysis thread                           */
/************************************************************************/
int read_forever()
{	
	node_info  local_buf[128];
	size_t     count = 128;
	node_info  local_scan[1000];
	size_t     scan_count = 0;
	result_t   ans = RESULT_FAIL;
	
	memset(local_scan, 0, sizeof(local_scan));

	node_lidar.lidar_time.scan_time_record = current_times();

	while (1)
	{
		bool state_jugde = lidar_state_judgment();
		if(state_jugde)
		{
			count = 128;
			ans = node_lidar.lidar_data_processing.waitScanData(local_buf, count);
			if(!IS_OK(ans))
			{
				if(current_times()-node_lidar.lidar_time.system_start_time > 3000 )
				{
					if(!node_lidar.lidar_status.lidar_restart_try)
					{
						printf("尝试重启雷达\n");
						node_lidar.lidar_status.lidar_restart_try = true;
						node_lidar.lidar_status.lidar_trap_restart = true;
					}else{
						printf("@@@雷达被卡住\n");
						node_lidar.lidar_status.lidar_abnormal_state |= 0x01;
						usleep(100);
					}
				}	
			}else{
				node_lidar.lidar_status.lidar_restart_try = false;
				node_lidar.lidar_time.system_start_time = current_times();
			}
			for (size_t pos = 0; pos < count; ++pos)
			{
				if (local_buf[pos].sync_flag & LIDAR_RESP_MEASUREMENT_SYNCBIT)
				{
					if ((local_scan[0].sync_flag & LIDAR_RESP_MEASUREMENT_SYNCBIT))
					{
						local_scan[0].stamp = local_buf[pos].stamp;
						local_scan[0].scan_frequence = local_buf[pos].scan_frequence;
		
						/*频率异常超过30秒，触发异常状态*/
						if(local_scan[0].scan_frequence > 200 || local_scan[0].scan_frequence < 10)
						{
							if(current_times()-node_lidar.lidar_time.lidar_frequence_abnormal_time > 30000)
							{
								node_lidar.lidar_status.lidar_abnormal_state |= 0x02;
							}
						}else{
							node_lidar.lidar_time.lidar_frequence_abnormal_time = current_times();
						}
						
						
						node_lidar._lock.lock();
						if((node_lidar.lidar_time.scan_time_current - node_lidar.lidar_time.scan_time_record) > 2000)
						{
							printf("full----- count=%d,time=%lld\n",scan_count,current_times());
							node_lidar.lidar_time.scan_time_record = node_lidar.lidar_time.scan_time_current;
						}
						memcpy(node_lidar.scan_node_buf, local_scan, scan_count * sizeof(node_info));
						node_lidar.scan_node_count = scan_count;
						node_lidar.lidar_time.scan_time_current = current_times();
						node_lidar._dataEvent.set();
						node_lidar._lock.unlock();
					}
					scan_count = 0;
				}
				local_scan[scan_count++] = local_buf[pos];
				if (scan_count == _countof(local_scan))
				{
					scan_count -= 1;
				}
			}
		}
		else{
			flushSerial();
			delay(100);
		}
		
	}
	return RESULT_OK;
}

/*线程事件同步函数*/
result_t grabScanData(uint32_t timeout) {
	switch (node_lidar._dataEvent.wait(timeout)) {
		case Event::EVENT_TIMEOUT:
			return RESULT_TIMEOUT;

		case Event::EVENT_OK: 
			{
				node_lidar._lock.lock();
				if (node_lidar.scan_node_count == 0) {
					return RESULT_FAIL;
				}
				node_lidar._lock.unlock();
			}
			return RESULT_OK;

		default:
			return RESULT_FAIL;
	}
}

/*处理雷达的线程*/
bool data_handling(LaserScan &outscan)
{

	//node_lidar.lidar_time.tim_scan_start = getTime();	
	if(grabScanData(2000)==RESULT_OK)
	{
		send_lidar_data(outscan);
		return true;
	}else{
		return false;
	}
	
}


/*处理最新一圈雷达的数据*/
void send_lidar_data(LaserScan &outscan)
{
	node_lidar._lock.lock();

	size_t count = node_lidar.scan_node_count;

	if(count < MAX_SCAN_NODES && count > 0)
	{	
		node_lidar.lidar_time.tim_scan_end = getTime();
		uint64_t scan_time = node_lidar.lidar_general_info.m_PointTime * (count - 1);
		node_lidar.lidar_time.tim_scan_start = node_lidar.lidar_time.tim_scan_end -  scan_time ;

		node_lidar.lidar_block.lidar_zero_count = 0;


		outscan.config.angle_increment = (2.0*M_PI/count);
		outscan.config.min_angle = 0;
		outscan.config.max_angle = 2*M_PI;
		outscan.config.min_range = 0.10;
		outscan.config.max_range = 10.0; //测量的最远距离是10m
		outscan.config.scan_time =  static_cast<float>(scan_time * 1.0 / 1e9);
    	outscan.config.time_increment = outscan.config.scan_time / (double)(count - 1);
		outscan.stamp = node_lidar.lidar_time.tim_scan_start;
		//scan_msg->header.frame_id = node_lidar.lidar_general_info.frame_id;
		//scan_msg->header.stamp = ros::Time::now();

		if(node_lidar.lidar_status.isConnected)
		{
			//outscan.points.clear();
			float range = 0;
			float angle = 0.0;
			uint16_t intensity = 0;
			for (int i = 0; i < count; i++)
			{
				LaserPoint point;
				LaserPoint point_check;
				angle = static_cast<float>((node_lidar.scan_node_buf[i].angle_q6_checkbit >>
											LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) /64.0f);
				range = (node_lidar.scan_node_buf[i].distance_q2/1000.0f);
				
				intensity = node_lidar.scan_node_buf[i].sync_quality;

				point_check.angle = angle;
				point_check.range = range;
				point_check.intensity = intensity;
				
				if(0 <= angle && angle <= 360){
					point.range = range;
					point.angle = angle;
					point.intensity = intensity;
				}else{
					point.range = 0.0;
					point.intensity = 0;
					point.angle = 0.0;
				}

				if(range > node_lidar.range_max || range < 0)
				{
					point.range = 0.0;
				}

				if(range < 0.1)
				{
					node_lidar.lidar_block.lidar_zero_count++;
				}
				
				outscan.points.push_back(point);
			}
			if(node_lidar.data_calibration)
			{
				//lidar_calibration(outscan);
			}

			node_lidar._lock.unlock();

			/*雷达被遮挡判断*/
			
			node_lidar.optimize_lidar.lidar_blocked_judge(count);


			if (node_lidar.lidar_status.FilterEnable)
			{
				node_lidar.optimize_lidar.PointCloudFilter(&outscan);
			}


		}
	}
	node_lidar._lock.unlock();
}

/*设置串口信息的函数*/
bool lidar_set_port()
{
	if (node_lidar.lidar_status.isConnected)
	{
		return true;
	}

	std::cout << "***" << node_lidar.lidar_general_info.port << std::endl;
	node_lidar.serial_port=make_shared<Serial_Port>(node_lidar.lidar_general_info.port,
							node_lidar.lidar_general_info.m_SerialBaudrate,Timeout::simpleTimeout(DEFAULT_TIMEOUT));
	if (!node_lidar.serial_port->open())
	{
		return false;
	}
	node_lidar.lidar_status.isConnected=true;
	sleep_ms(100);
    node_lidar.serial_port->setDTR(0);
	return true;
}

/*初始化函数*/
bool initialize()
{
	if(node_lidar.lidar_status.optimize_enable)
	{
		//求雷达安装位置到扫地机边缘的距离
		node_lidar.optimize_lidar.lidar_blocked_init();
	}

	switch (node_lidar.lidar_general_info.version)
	{
	case M1C1_Mini_v1:
		printf("version M1C1_Mini_v1\n");
		node_lidar.lidar_general_info.m_SerialBaudrate = 115200;
		node_lidar.lidar_data_processing.PackageSampleBytes = 2;
		break;

	case M1C1_Mini_v2:
		printf("version M1C1_Mini_v2\n");
		node_lidar.lidar_general_info.m_SerialBaudrate = 150000;
		node_lidar.lidar_data_processing.PackageSampleBytes = 3;
		node_lidar.lidar_general_info.m_intensities = true;
		break;

	case M1CT_Coin_Plus:
		printf("version M1CT_Coin_Plus\n");
		node_lidar.lidar_general_info.m_SerialBaudrate = 115200;
		node_lidar.lidar_data_processing.PackageSampleBytes = 3;
		break;
	
	case M1CT_TOF:
		printf("version M1CT_TOF\n");
		node_lidar.lidar_general_info.m_SerialBaudrate = 230400;
		node_lidar.lidar_data_processing.PackageSampleBytes = 3;
		node_lidar.lidar_general_info.m_intensities = true;
		break;
	
	default:
		break;
	}

	//设置通信串口
	if(!lidar_set_port()){
		printf("lidar_set_port wrong\n");
		return false;
	}

	//获取串口获取每个byte所用的时间
	node_lidar.lidar_general_info.trans_delay = node_lidar.serial_port->getByteTime();
	node_lidar.scan_node_buf = new node_info[1000];
	node_lidar.globalRecvBuffer = new uint8_t[sizeof(node_packages)];
	return true;
}


#ifdef ROS_2
int topic_thread()
{
	rclcpp::spin(std::make_shared<MinimalSubscriber>());
}
#endif

int node_start(int argc, char **argv)
{

	ros::init(argc, argv, "M1CT_Coin_Plus");
	ros::NodeHandle n;
	ros::NodeHandle priv_nh("~");

	priv_nh.param("baud_rate", node_lidar.lidar_general_info.m_SerialBaudrate, 115200);
	priv_nh.param("frame_id", node_lidar.lidar_general_info.frame_id, std::string("base_link"));
	priv_nh.param("port", node_lidar.lidar_general_info.port, std::string("/dev/sc_mini"));
	priv_nh.param("version", node_lidar.lidar_general_info.version, 2);
	priv_nh.param("calib", node_lidar.data_calibration, false);
	priv_nh.param("rangemax", node_lidar.range_max, 10000.0f);
	calibration_params.origin_point.x = node_lidar.range_max;
	calibration_params.origin_point.y = node_lidar.range_max;

	priv_nh.param("dpd", calibration_params.distortion_processing_distance, 1000.0f);
	priv_nh.param("calib_type", calibration_params.calibration_type, 0);
	priv_nh.param("ljpn", calibration_params.line_judgment_point_num, 15);

	

	/*
	auto subscription_ = node->create_subscription<std_msgs::msg::UInt16>(
      "lidar_status", 10, topic_callback);*/
	
	
	bool ret_init = initialize();

	if(!ret_init){
		printf("node_lidar init error\n");
		return -1;
	}
	/*读取激光雷达数据的线程*/
	thread t1(read_forever);
	t1.detach();


	/*处理雷达数据的线程*/
	/*
	thread t2(data_handling(node));
	t2.detach();*/
	
	node_lidar.lidar_status.lidar_ready = true;
	ros::Publisher laser_pub = n.advertise<sensor_msgs::LaserScan>("scan", 1);

	while(ros::ok())
	{
#ifdef ROS_2
		if(node_lidar.lidar_status.lidar_abnormal_state != 0)
		{
			if(node_lidar.lidar_status.lidar_abnormal_state & 0x01)
			{
				pubdata.data="node_lidar is trapped\n";
				error_pub->publish(pubdata);
				printf("异常状态1---trapped\n");
			}
			if(node_lidar.lidar_status.lidar_abnormal_state & 0x02)
			{
				pubdata.data="node_lidar frequence abnormal\n";
				error_pub->publish(pubdata);
				printf("异常状态2---frequence abnormal\n");
			}
			if(node_lidar.lidar_status.lidar_abnormal_state & 0x04)
			{
				pubdata.data="node_lidar is blocked\n";
				error_pub->publish(pubdata);
				printf("异常状态3---blocked\n");
			}
			node_lidar.serial_port->write_data(end_lidar,4);
			node_lidar.lidar_status.lidar_ready = false;

			sleep(1);
		}
#endif
		LaserScan scan;
		if(data_handling(scan))
		{
			sensor_msgs::LaserScan scan_pub;
			scan_pub.ranges.resize(scan.points.size());
			scan_pub.intensities.resize(scan.points.size());
			scan_pub.angle_increment = (2.0*M_PI/scan.points.size());
			scan_pub.angle_min = 0;
			scan_pub.angle_max = 2*M_PI;
			scan_pub.range_min = 0.10;
			scan_pub.range_max = 10.0; //测量的最远距离是10m
			scan_pub.header.frame_id = node_lidar.lidar_general_info.frame_id;
			scan_pub.header.stamp = ros::Time::now();
			for(int i=0; i < scan.points.size(); i++) {
				scan_pub.ranges[i] = scan.points[i].range;
				scan_pub.intensities[i] = scan.points[i].intensity;
			}
			laser_pub.publish(scan_pub);
			
      	}
	}
	node_lidar.serial_port->write_data(end_lidar,4);
	return 0;
}

```
## `cspc_lidar_sdk_ros1/src/main.cpp`

```
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include "node_lidar.h"


int parse_args(int argc, char **argv)
{
	struct option opts[] = {
		{"cover", 1, 0, 256}, //剔除雷达上盖结构的缺口
		{"diameter",1,0,257}, //扫地机机身直径
		{"center",1,0,258},   //扫地机中心到雷达中心的距离（雷达处于扫地机前半边数值为正，雷达中心处于扫地机后半边数值为负）
		{"gyr",1,0,259},      //是否在雷达节点做旋转补偿
		{"slam",0,0,260},     //是否在待机状态让雷达节点解析数据
		{"angle",1,0,261},    //雷达的安装角度（顺时针偏转）
		{"version",1,0,262},  //雷达的版本（1:M1C1_Mini_v1;2:M1C1_Mini_V2;3:M1CT_Coin_plus）
		{"baudrate",1,0,263}, //雷达的波特率
		{"encry",0,0,264},   
		{"exp",0,0,265},   
		{0, 0, 0, 0} 
	};
	int ch;
	while ((ch = getopt_long_only(argc, argv, "hcfs", opts, NULL)) != -1)
	{
		switch (ch)
		{
		case 'h':
			printf("lidar node Help:\n");
			printf("./node_lidar /dev/ttyS2 -c -d.\n");
			printf("node lidar -c : no rotate compensate.\n");
			printf("node lidar -f : no lidar data filter.\n");
			printf("node lidar -cover [57,70][101,117][184,196][228,241][291,305][335,350] :note, no blank between []\n");
			exit(0);
			break;
		case 'c':
			break;
		case 'f':
			break;
		case 's':
			break;
		case 256:
			node_lidar.lidar_status.lidar_cover = true;
			node_lidar.optimize_lidar.getLidarCoverAngle(optarg);
			break;
		case 257:
			node_lidar.lidar_robot_info.ROBOT_DIAMETER_mm=atoi(optarg);
			break;
		case 258:
			node_lidar.lidar_robot_info.LIDAR_ROBOT_CENTER_DISTANCE_mm=atoi(optarg);
			break;
		case 259:
			node_lidar.lidar_status.GyroCompensateEnable = true;
			break;
		case 260:
			node_lidar.lidar_status.slam_user = true;
			break;
		case 261:
			node_lidar.lidar_robot_info.install_to_zero = atof(optarg);
			break;
		case 262:
			node_lidar.lidar_general_info.version = atoi(optarg);
			break;
		case 263:
			node_lidar.lidar_general_info.m_SerialBaudrate = atoi(optarg);
			break;
		case 264:
			node_lidar.lidar_status.disable_encry = true;
			break;
		case 265:
			node_lidar.lidar_status.able_exposure = true;
			break;

		default:
			printf("error: unknow arg in ths args\n");
			break;
		}
	}
	return 0;
}


int main(int argc, char **argv)
{
	/*
	if(argc < 2)
	{
		printf("args error\n");
		return 0;
	}*/
	
	fflush(stdout);

	node_start(argc, argv);
}                                                                                                           
```
## `cspc_lidar_sdk_ros1/src/mtime.cpp`

```
#include "mtime.h"

using namespace std;
using namespace chrono;

time_point<steady_clock> time_start;

int64_t current_times(int precision)
{
	auto durations = std::chrono::steady_clock::now().time_since_epoch();
	switch(precision)
	{
        case TIME_NANOSECOND:
            return durations.count();
        case TIME_MICROSECOND:
            return duration_cast<microseconds>(durations).count();
        case TIME_MILLISECOND:
            return duration_cast<milliseconds>(durations).count();
        case TIME_SECOND:
            return duration_cast<seconds>(durations).count();
        case TIME_MINUTE:
            return duration_cast<minutes>(durations).count();
        case TIME_HOUR:
            return duration_cast<hours>(durations).count();
	}
    return 0;
}

struct tm localdate(int time_zone)
{
    time_t unix_sec = time(NULL);
    struct tm tms;

    static const int kHoursInDay = 24;
    static const int kMinutesInHour = 60;
    static const int kDaysFromUnixTime = 2472632;
    static const int kDaysFromYear = 153;
    static const int kMagicUnkonwnFirst = 146097;
    static const int kMagicUnkonwnSec = 1461;
    tms.tm_sec  =  unix_sec % kMinutesInHour;
    int i      = (unix_sec/kMinutesInHour);
    tms.tm_min  = i % kMinutesInHour; //nn
    i /= kMinutesInHour;
    tms.tm_hour = (i + time_zone) % kHoursInDay; // hh
    tms.tm_mday = (i + time_zone) / kHoursInDay;
    int a = tms.tm_mday + kDaysFromUnixTime;
    int b = (a*4  + 3)/kMagicUnkonwnFirst;
    int c = (-b*kMagicUnkonwnFirst)/4 + a;
    int d =((c*4 + 3) / kMagicUnkonwnSec);
    int e = -d * kMagicUnkonwnSec;
    e = e/4 + c;
    int m = (5*e + 2)/kDaysFromYear;
    tms.tm_mday = -(kDaysFromYear * m + 2)/5 + e + 1;
    tms.tm_mon = (-m/10)*12 + m + 2;
    tms.tm_year = b*100 + d  - 6700 + (m/10);
    return tms;
}


//休眠多少毫秒
void sleep_ms(int ms)
{
    int ts = ms / 1000;
    int ns = ms % 1000;
    struct timespec r {ts, ns * 1000 * 1000};
    nanosleep(&r, NULL);
}

//返回时间字符串
char *time_str(const char *fmt)
{
    static char str[256];
    struct tm tms = localdate();
    strftime(str, 255, fmt, &tms);
    return str;
}
```
## `cspc_lidar_sdk_ros1/src/serial_port.cpp`

```
#include <stdio.h>
#include <termios.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>

#include <sys/select.h>
#include <linux/serial.h>
#include <sys/ioctl.h>

#include "serial_port.h"
#include "node_lidar.h"

using namespace std;


#define SNCCS 19
#define BOTHER 0010000
struct termios2 {
  tcflag_t c_iflag;       /* input mode flags */
  tcflag_t c_oflag;       /* output mode flags */
  tcflag_t c_cflag;       /* control mode flags */
  tcflag_t c_lflag;       /* local mode flags */
  cc_t c_line;            /* line discipline */
  cc_t c_cc[SNCCS];       /* control characters */
  speed_t c_ispeed;       /* input speed */
  speed_t c_ospeed;       /* output speed */
};

Serial_Port::Serial_Port(const string &port, uint32_t baudrate, Timeout timeout,
               bytesize_t bytesize, parity_t parity, stopbits_t stopbits,
               flowcontrol_t flowcontrol)
	:port_(port),baudrate_(baudrate),timeout_(timeout),bytesize_(bytesize),parity_(parity),stopbits_(stopbits),flowcontrol_(flowcontrol){

}

Serial_Port::~Serial_Port(){
  
}

MillisecondTimer::MillisecondTimer(const uint64_t millis) : expiry(timespec_now())
{
	int64_t tv_nsec = expiry.tv_nsec + (millis * 1e6);

	if (tv_nsec >= 1e9)
	{
		int64_t sec_diff = tv_nsec / static_cast<int>(1e9);
		expiry.tv_nsec = tv_nsec % static_cast<int>(1e9);
		expiry.tv_sec += sec_diff;
	}
	else
	{
		expiry.tv_nsec = tv_nsec;
	}
}

int64_t MillisecondTimer::remaining()
{
	timespec now(timespec_now());
	int64_t millis = (expiry.tv_sec - now.tv_sec) * 1e3;
	millis += (expiry.tv_nsec - now.tv_nsec) / 1e6;
	return millis;
}

timespec MillisecondTimer::timespec_now()
{
	timespec time;
	clock_gettime(CLOCK_MONOTONIC, &time);
	return time;
}

timespec timespec_from_ms(const uint32_t millis)
{
	timespec time;
	time.tv_sec = millis / 1e3;
	time.tv_nsec = (millis - (time.tv_sec * 1e3)) * 1e6;
	return time;
}

result_t Serial_Port::waitForData(size_t data_count, uint64_t timeout, size_t *returned_size)
{
	if(!is_open_)
	{
		return RESULT_FAIL;
	}

	size_t length = 0;

	if (returned_size == NULL)
	{
		returned_size = (size_t *)&length;
	}

	*returned_size = 0;

	if (is_open_)
	{
    	/*得到缓冲区里有多少字节*/
		if (ioctl(fd_, FIONREAD, returned_size) == -1)
		{
			return RESULT_FAIL;
		}
		if (*returned_size >= data_count)
		{
			return RESULT_OK;
		}
	}
	
	fd_set readfds;
	/*将set清零使集合中不含任何fd*/
	FD_ZERO(&readfds);
	/*将fd_加入set集合*/
	FD_SET(fd_, &readfds);

	MillisecondTimer total_timeout(timeout);

	while (is_open_)
	{
		int64_t timeout_remaining_ms = total_timeout.remaining();

		if ((timeout_remaining_ms <= 0))
		{
			return RESULT_TIMEOUT;
		}
		
		timespec timeout_val(timespec_from_ms(timeout_remaining_ms));

		/*检查文件描述符是否就绪*/
		int n = pselect(fd_+1, &readfds, NULL, NULL, &timeout_val,NULL);

		if (n < 0)
		{
			if (errno == EINTR)
			{
				return RESULT_TIMEOUT;
			}
			return RESULT_FAIL;
		}
		else if (n == 0)
		{
			return RESULT_TIMEOUT;
		}
		else
		{
			/*调用select后，检查fd_是否在set集合中*/
			if(FD_ISSET(fd_, &readfds)){
				if(ioctl(fd_, FIONREAD, returned_size)<0){
					return RESULT_FAIL;
				}
			
				if (*returned_size >= data_count)
				{
					return RESULT_OK;
				}else{
					int remain_timeout = timeout_val.tv_sec * 1000000 + timeout_val.tv_nsec /1000;
					int expect_remain_time = (data_count - *returned_size) * 1000000 * 8 / baudrate_;
					if (remain_timeout > expect_remain_time)
					{
						usleep(expect_remain_time);
					}
				}
			}else{
				usleep(30);
			}
		}
	}
	return RESULT_FAIL;
}

bool Serial_Port::waitReadable(uint32_t timeout_t)
{
	// Setup a select call to block for serial data or a timeout
	fd_set readfds;
	FD_ZERO(&readfds);
	FD_SET(fd_, &readfds);
	timespec timeout_ts(timespec_from_ms(timeout_t));
	int r = pselect(fd_ + 1, &readfds, NULL, NULL, &timeout_ts, NULL);

	if (r < 0)
	{
		// Select was interrupted
		if (errno == EINTR)
		{
			return false;
		}

		// Otherwise there was some error
		return false;
	}

	// Timeout occurred
	if (r == 0)
	{
		return false;
	}

	// This shouldn't happen, if r > 0 our fd has to be in the list!
	if (!FD_ISSET(fd_, &readfds))
	{
		return false;
	}

	// Data available to read.
	return true;
}

size_t Serial_Port::available()
{
	if (!is_open_)
	{
		return 0;
	}

	int count = 0;

	if (-1 == ioctl(fd_, TIOCINQ, &count))
	{
		return 0;
	}else{
		return static_cast<size_t>(count);
	}
}

uint32_t byte_time_ns_;

void waitByteTimes(size_t count)
{
	timespec wait_time = {0, static_cast<long>(byte_time_ns_ * count)};
	pselect(0, NULL, NULL, NULL, &wait_time, NULL);
}

result_t Serial_Port::read_data(uint8_t *buf, size_t size)
{
	// If the port is not open, throw
	if (!is_open_)
	{
		return 0;
	}

	Timeout timeout_;

	size_t bytes_read = 0;

	// Calculate total timeout in milliseconds t_c + (t_m * N)
	long total_timeout_ms = timeout_.read_timeout_constant;
	total_timeout_ms += timeout_.read_timeout_multiplier * static_cast<long>(size);
	MillisecondTimer total_timeout(total_timeout_ms);

	// Pre-fill buffer with available bytes
	{
		ssize_t bytes_read_now = ::read(fd_, buf, size);

		if (bytes_read_now > 0)
		{
			bytes_read = bytes_read_now;
		}
	}

	while (bytes_read < size)
	{
		int64_t timeout_remaining_ms = total_timeout.remaining();

		if (timeout_remaining_ms <= 0)
		{
			// Timed out
			break;
		}

		// Timeout for the next select is whichever is less of the remaining
		// total read timeout and the inter-byte timeout.
		uint32_t timeout_t = std::min(static_cast<uint32_t>(timeout_remaining_ms),
									  timeout_.inter_byte_timeout);

		// Wait for the device to be readable, and then attempt to read.
		if (waitReadable(timeout_t))
		{
			// If it's a fixed-length multi-byte read, insert a wait here so that
			// we can attempt to grab the whole thing in a single IO call. Skip
			// this wait if a non-max inter_byte_timeout is specified.
			if (size > 1 && timeout_.inter_byte_timeout == Timeout::max())
			{
				size_t bytes_available = available();

				if (bytes_available + bytes_read < size)
				{
					waitByteTimes(size - (bytes_available + bytes_read));
				}
			}

			// This should be non-blocking returning only what is available now
			//  Then returning so that select can block again.
			ssize_t bytes_read_now = ::read(fd_, buf + bytes_read, size - bytes_read);

			// read should always return some data as select reported it was
			// ready to read when we get to this point.
			if (bytes_read_now < 1)
			{
				// Disconnected devices, at least on Linux, show the
				// behavior that they are always ready to read immediately
				// but reading returns nothing.
				continue;
			}

			// Update bytes_read
			bytes_read += static_cast<size_t>(bytes_read_now);

			// If bytes_read == size then we have read everything we need
			if (bytes_read == size)
			{
				break;
			}

			// If bytes_read < size then we have more to read
			if (bytes_read < size)
			{
				continue;
			}

			// If bytes_read > size then we have over read, which shouldn't happen
			if (bytes_read > size)
			{
				break;
			}
		}
	}

	return bytes_read;
}

size_t Serial_Port::write_data(const uint8_t *data, size_t length) {
  if (is_open_ == false) {
    return 0;
  }

  Timeout timeout_;
  fd_set writefds;
  size_t bytes_written = 0;

  // Calculate total timeout in milliseconds t_c + (t_m * N)
  long total_timeout_ms = timeout_.write_timeout_constant;
  total_timeout_ms += timeout_.write_timeout_multiplier * static_cast<long>
                      (length);
  MillisecondTimer total_timeout(total_timeout_ms);

  bool first_iteration = true;

  while (bytes_written < length) {
    int64_t timeout_remaining_ms = total_timeout.remaining();

    // Only consider the timeout if it's not the first iteration of the loop
    // otherwise a timeout of 0 won't be allowed through
    if (!first_iteration && (timeout_remaining_ms <= 0)) {
      // Timed out
      break;
    }

    first_iteration = false;

    timespec timeout(timespec_from_ms(timeout_remaining_ms));

    FD_ZERO(&writefds);
    FD_SET(fd_, &writefds);

    // Do the select
    int r = pselect(fd_ + 1, NULL, &writefds, NULL, &timeout, NULL);

    // Figure out what happened by looking at select's response 'r'
    /** Error **/
    if (r < 0) {
      // Select was interrupted, try again
      if (errno == EINTR) {
        continue;
      }

      // Otherwise there was some error
      continue;
    }

    /** Timeout **/
    if (r == 0) {
      break;
    }

    /** Port ready to write **/
    if (r > 0) {
      // Make sure our file descriptor is in the ready to write list
      if (FD_ISSET(fd_, &writefds)) {
        // This will write some
        ssize_t bytes_written_now = ::write(fd_, data + bytes_written,
                                            length - bytes_written);

        // write should always return some data as select reported it was
        // ready to write when we get to this point.
        if (bytes_written_now < 1) {
          // Disconnected devices, at least on Linux, show the
          // behavior that they are always ready to write immediately
          // but writing returns nothing.
          continue;
        }

        // Update bytes_written
        bytes_written += static_cast<size_t>(bytes_written_now);

        // If bytes_written == size then we have written everything we need to
        if (bytes_written == length) {
          break;
        }

        // If bytes_written < size then we have more to write
        if (bytes_written < length) {
          continue;
        }

        // If bytes_written > size then we have over written, which shouldn't happen
        if (bytes_written > length) {
          break;
        }
      }

      // This shouldn't happen, if r > 0 our fd has to be in the list!
      break;
      //THROW (IOException, "select reports ready to write, but our fd isn't in the list, this shouldn't happen!");
    }
  }

  return bytes_written;
}


uint32_t Serial_Port::getByteTime() {
  return byte_time_ns_;
}

bool Serial_Port::getTermios(termios *tio) {
  ::memset(tio, 0, sizeof(termios));

  if (::tcgetattr(fd_, tio) == -1) {
    return false;
  }

  return true;
}


void Serial_Port::set_databits(termios *tio, bytesize_t databits) {
  tio->c_cflag &= ~CSIZE;

  switch (databits) {
    case fivebits:
      tio->c_cflag |= CS5;
      break;

    case sixbits:
      tio->c_cflag |= CS6;
      break;

    case sevenbits:
      tio->c_cflag |= CS7;
      break;

    case eightbits:
      tio->c_cflag |= CS8;
      break;

    default:
      tio->c_cflag |= CS8;
      break;
  }
}

void Serial_Port::set_parity(termios *tio,parity_t parity) {
  tio->c_iflag &= ~(PARMRK | INPCK);
  tio->c_iflag |= IGNPAR;

  switch (parity) {

#ifdef CMSPAR

    case parity_space:
      tio->c_cflag &= ~PARODD;
      tio->c_cflag |= PARENB | CMSPAR;
      break;

    case parity_mark:
      tio->c_cflag |= PARENB | CMSPAR | PARODD;
      break;
#endif

    case parity_none:
      tio->c_cflag &= ~PARENB;
      break;

    case parity_even:
      tio->c_cflag &= ~PARODD;
      tio->c_cflag |= PARENB;
      break;

    case parity_odd:
      tio->c_cflag |= PARENB | PARODD;
      break;

    default:
      tio->c_cflag |= PARENB;
      tio->c_iflag |= PARMRK | INPCK;
      tio->c_iflag &= ~IGNPAR;
      break;
  }
}

void Serial_Port::set_stopbits(termios *tio, stopbits_t stopbits) {
  switch (stopbits) {
    case stopbits_one:
      tio->c_cflag &= ~CSTOPB;
      break;

    case stopbits_two:
      tio->c_cflag |= CSTOPB;
      break;

    default:
      tio->c_cflag &= ~CSTOPB;
      break;
  }
}

void Serial_Port::set_flowcontrol(termios *tio,flowcontrol_t flowcontrol) {
  switch (flowcontrol) {
    case flowcontrol_none:
      tio->c_cflag &= ~CRTSCTS;
      tio->c_iflag &= ~(IXON | IXOFF | IXANY);
      break;

    case flowcontrol_hardware:
      tio->c_cflag |= CRTSCTS;
      tio->c_iflag &= ~(IXON | IXOFF | IXANY);
      break;

    case flowcontrol_software:
      tio->c_cflag &= ~CRTSCTS;
      tio->c_iflag |= IXON | IXOFF | IXANY;
      break;

    default:
      tio->c_cflag &= ~CRTSCTS;
      tio->c_iflag &= ~(IXON | IXOFF | IXANY);
      break;
  }
}

bool Serial_Port::setCustomBaudRate(unsigned long baudrate) {
  struct termios2 tio2;

  if (::ioctl(fd_, TCGETS2, &tio2) != -1) {
    tio2.c_cflag &= ~CBAUD;
    tio2.c_cflag |= BOTHER;

    tio2.c_ispeed = baudrate;
    tio2.c_ospeed = baudrate;

    tcflush(fd_, TCIFLUSH);

    if (fcntl(fd_, F_SETFL, FNDELAY)) {
      return false;
    }

    if (::ioctl(fd_, TCSETS2, &tio2) != -1 && ::ioctl(fd_, TCGETS2, &tio2) != -1) {
      return true;
    }
  }
}

bool Serial_Port::setBaudrate(unsigned long baudrate) {

  if (fd_ == -1) {
    return false;
  }
  speed_t new_baud = static_cast<speed_t>(baudrate);

  return setCustomBaudRate(baudrate);
}
bool Serial_Port::setTermios(const termios *tio) {

  tcflush(fd_, TCIFLUSH);

  if (fcntl(fd_, F_SETFL, FNDELAY)) {
    return false;
  }

  if (::tcsetattr(fd_, TCSANOW, tio) == -1) {
    return false;
  }

  return true;
}

void Serial_Port::set_common_props(termios *tio) {
#ifdef OS_SOLARIS
  tio->c_iflag &= ~(IMAXBEL | IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR |
                    ICRNL | IXON);
  tio->c_oflag &= ~OPOST;
  tio->c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
  tio->c_cflag &= ~(CSIZE | PARENB);
  tio->c_cflag |= CS8;
#else
  ::cfmakeraw(tio);
#endif
  tio->c_cflag |= CLOCAL | CREAD;
  tio->c_cc[VTIME] = 0;
  tio->c_cc[VMIN] = 0;
}

bool Serial_Port::open() {
  
	if (port_.empty()) {
		return false;
	}

	if (is_open_ == true) {
		return true;
	}
	/*
	pid = -1;
	pid = getpid();
	*/
	fd_ = ::open(port_.c_str(),
			O_RDWR | O_NOCTTY | O_NONBLOCK | O_APPEND | O_NDELAY);

	if (fd_ == -1) {
		return false;
	}


	termios tio;
	if(!getTermios(&tio)){
		close();
		return false;
	}

	set_common_props(&tio);
	set_databits(&tio, bytesize_);
	set_parity(&tio, parity_);
	set_stopbits(&tio, stopbits_);
	set_flowcontrol(&tio, flowcontrol_);

	if (!setTermios(&tio)) {
    	close();
    	return false;
  	}
	if (!setBaudrate(baudrate_)) {
		return false;
	}

	// Update byte_time_ based on the new settings.
	uint32_t bit_time_ns = 1e9 / baudrate_;
	byte_time_ns_ = bit_time_ns * (1 + eightbits + parity_none + stopbits_one);


	is_open_ = true;
	return true;
}

bool Serial_Port::setDTR(bool level) {
  if (is_open_ == false) {
    return false;
  }
  int command = TIOCM_DTR;
  if (level) {
    if (-1 == ioctl(fd_, TIOCMBIS, &command)) {
      return false;
    }
  } else {
    if (-1 == ioctl(fd_, TIOCMBIC, &command)) {
      return false;
    }
  }
  return true;
}

/*关闭串口*/
void Serial_Port::close() 
{
  if (is_open_ == true) 
  {
    if (fd_ != -1) 
    {
      ::close(fd_);
    }
    fd_ = -1;
    pid = -1;
    is_open_ = false;
  }
}



```
## `cspc_lidar_sdk_ros1/src/lidar_data_processing.cpp`

```
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <vector>
#include <thread>
#include "msg_recept.h"
#include "serial_port.h"
#include "lidar_data_processing.h"
#include "mtime.h"
#include "node_lidar.h"
#include <math.h>

bool has_device_header = false;

Lidar_Data_Processing::Lidar_Data_Processing(){
  CheckSumCal = 0;
  CheckSum = 0;	//校验和
  SampleNumlAndCTCal = 0;
  LastSampleAngleCal = 0;
  Valu8Tou16 = 0;
  package_Sample_Index = 0;
  FirstSampleAngle = 0; //< 起始采样角
	LastSampleAngle = 0;  //< 结束采样角
  scan_frequence = 0;	      //协议中雷达转速
  CheckSumResult = false;
  has_package_error = false;
  IntervalSampleAngle = 0.0;
	IntervalSampleAngle_LastPackage = 0.0;
  PackageSampleBytes = 2; //< 一个包包含的激光点数
  package_index = 0;
  recvNodeCount = 0;
  start_t = 0;

  //uint64_t m_node_time_ns = current_times(TIME_NANOSECOND);			  //< time stamp
  //uint64_t m_node_last_time_ns = current_times(TIME_NANOSECOND); //< time stamp
  m_pointTime = 1e9 / 5000;
}

Lidar_Data_Processing::~Lidar_Data_Processing(){
}

/************************************************************************/
/*  向激光雷达发布控制指令　Issue control command to lidar                  */
/************************************************************************/
result_t Lidar_Data_Processing::sendCommand(uint8_t cmd)
{
  uint8_t pkt_header[10];
	
	switch (cmd)
	{
	  case 0x60:
		  break;
	  case 0x65:
		  break;
	  case 0x63:
      pkt_header[0]=0xAA;
      pkt_header[1]=0x55;
      pkt_header[2]=0xF0;
      pkt_header[3]=0x0F;
      node_lidar.serial_port->write_data(pkt_header,4);
		break;
	default:
		break;
	}
  //add by jiang
  return 0;
}

result_t Lidar_Data_Processing::sendData(const uint8_t *data, size_t size)
{

  if (data == NULL || size == 0)
  {
    return RESULT_FAIL;
  }

  size_t r;

  while (size)
  {
    r = node_lidar.serial_port->write_data(data, size);

    if (r < 1)
    {
      return RESULT_FAIL;
    }

    size -= r;
    data += r;
  }
  return RESULT_OK;
}

result_t Lidar_Data_Processing::waitSpeedRight(uint8_t cmd,uint64_t timeout)
{
    int  recvPos     = 0;
    uint32_t startTs = getms();
    uint8_t  recvBuffer[100];
    uint32_t waitTime = 0;
    //uint16_t data_count = 0;
    uint16_t check_sum_cal = 0;  //校验和
    uint16_t data_check_sum = 0; //累加数据
    //uint8_t check_data[4];
    bool head_right = false;

    uint16_t data_lenth = 0; //数据长度

    while ((waitTime = getms() - startTs) <= timeout){
      size_t remainSize = 9;
      size_t recvSize = 0;
      result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);
      if (!IS_OK(ans)) {
        return ans;
      }
      if (recvSize >= remainSize) {
        recvSize = remainSize - recvPos;
      }
      ans = node_lidar.serial_port->read_data(recvBuffer, recvSize);
      if (IS_FAIL(ans)) {
        printf("read waitResponseHeader fail\n");
        return RESULT_FAIL;
      }
      for (size_t pos = 0; pos < recvSize; ++pos) {
        uint8_t currentByte = recvBuffer[pos];
        switch (recvPos) {
          case 0:
            if(currentByte == 0xFA){
              printf("head_speed_000=%x\n",currentByte);
            }else{
              continue;
            }
            break;

          case 1:
            if(currentByte == 0xFA){
              printf("head_speed_111=%x\n",currentByte);
            }else{
              continue;
            }
            break;

          case 2:
            if(currentByte == 0xA5){
              printf("head_speed_222=%x\n",currentByte);
              data_check_sum+=currentByte; 
            }else{
              continue;
            }
            break;
        
          case 3:
            if(currentByte == 0x5A){
              printf("head_speed_333=%x\n",currentByte);
              data_check_sum+=currentByte; 
            }else{
              continue;
            }
            break;

          case 4:
            data_lenth = currentByte;
            data_check_sum+=currentByte; 
            printf("head_speed_444=%x\n",currentByte);
            break; 
          
          case 5:
            data_lenth += (currentByte * 0x100);
            data_check_sum+=currentByte;
            printf("head_speed_555=%x\n",currentByte);
            break;

          case 6:
            check_sum_cal = currentByte;
            printf("head_speed_666=%x\n",currentByte);
            break; 
          
          case 7:
            check_sum_cal += (currentByte * 0x100);
            printf("head_speed_777=%x\n",currentByte);
            break;
          
          case 8:
            if(currentByte==0x01)
            {
              printf("head_speed_888=%x count=%d\n",currentByte,recvPos);
              data_check_sum+=currentByte; 
              head_right = true;
            }
          default:
                break;
          }
        recvPos++;
        if(head_right)
        {
          printf("111\n");
          break;
        }
      }
      printf("recv_pos---=%d\n",recvPos);
      if(recvPos == 9){
        printf("222\n");
        break;
      }
    }

    if(recvPos == 9)
    {
      printf("333\n");
      startTs = getms();
      recvPos = 0;
      while ((waitTime = getms() - startTs) <= timeout)
      {
        size_t remainSize = data_lenth + 1;
        size_t recvSize = 0;
        result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);

        if (!IS_OK(ans))
        {
          return ans;
        }
        if(recvSize > remainSize)
        {
          recvSize = remainSize;
        }
        node_lidar.serial_port->read_data(recvBuffer, recvSize);
        for (size_t pos = 0; pos < 20; ++pos)
        {
              data_check_sum += recvBuffer[pos];
        }
        if(check_sum_cal == data_check_sum)
        {
          printf("------TRUE\n");
          return RESULT_OK;
        }else{
          printf("------WRONG\n");
        }
      }
    }
    return RESULT_FAIL;

}


result_t Lidar_Data_Processing::waitResponseHeader(uint8_t cmd, uint64_t timeout)
{
  int  recvPos     = 0;
  uint32_t startTs = getms();
  uint8_t  recvBuffer[10];
  uint32_t waitTime = 0;
  uint8_t data_count = 0;
  uint8_t check_sum_cal = 0;
  uint8_t check_data[4];

  while ((waitTime = getms() - startTs) <= timeout) {
    size_t remainSize = 4;
    size_t recvSize = 0;
    result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);
    if (!IS_OK(ans)) {
      return ans;
    }
    if (recvSize > remainSize) {
      recvSize = remainSize;
    }
    ans = node_lidar.serial_port->read_data(recvBuffer, recvSize);
    if(node_lidar.lidar_general_info.version == M1C1_Mini_v2 && cmd==0x63)
    {
      check_data[0]=0xA5;
      check_data[1]=0x5A;
      check_data[2]=0xE0;
      check_data[3]=0x08;

    }else{
      check_data[0]=0xAA;
      check_data[1]=0x55;
      check_data[2]=0xFC;
      check_data[3]=0x08;
    }
    if(cmd==0x64)
    {
      check_data[0]=0xA5;
      check_data[1]=0x5A;
      check_data[2]=0x5C;
      check_data[3]=0x07;
    }

    if (IS_FAIL(ans)) {
      printf("read waitResponseHeader fail\n");
      return RESULT_FAIL;
    }
    for (size_t pos = 0; pos < recvSize; ++pos) {
      uint8_t currentByte = recvBuffer[pos];
      printf("head_byte=%d\n",currentByte);
      switch (recvPos) {
        case 0:
          if(currentByte == check_data[0]){
            check_sum_cal ^= currentByte;
          }else{
            continue;
          }
          break;

        case 1:
          if(currentByte == check_data[1]){
            check_sum_cal ^= currentByte;
          }else{
            continue;
          }
          break;

        case 2:
          if(currentByte == check_data[2]){
            check_sum_cal ^= currentByte;
          }else{
            continue;
          }
          break;
      
        case 3:
          if(currentByte == check_data[3]){
            check_sum_cal ^= currentByte;
            data_count = currentByte;
          }else{
            continue;
          }
          break;

        default:
              break;
        }
      recvPos++;
    }
    if(recvPos == 4){
      break;
    }
  }
  if(recvPos == 4)
  {
    startTs = getms();
    recvPos = 0;
    while ((waitTime = getms() - startTs) <= timeout)
    {
      size_t remainSize = data_count + 1;
      size_t recvSize = 0;
      result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);

      if (!IS_OK(ans))
      {
        return ans;
      }
      if(recvSize > remainSize)
      {
        recvSize = remainSize;
      }
      node_lidar.serial_port->read_data(recvBuffer, recvSize);
      for (size_t pos = 0; pos < recvSize - 1; ++pos)
      {
            printf("data*=%d\n",recvBuffer[pos]);
            check_sum_cal ^= recvBuffer[pos];
            if(cmd==0x63)
            {
              node_lidar.recv_encryp[pos] = recvBuffer[pos];
            }else if(cmd==0x64){
              node_lidar.lidar_version[pos] = recvBuffer[pos];
            }
      }
      printf("data**%d,%d,%d\n",check_sum_cal,recvBuffer[remainSize-1],remainSize);
      if(check_sum_cal == recvBuffer[remainSize-1])
      {
        return RESULT_OK;
      }
    }
  }
  return RESULT_FAIL;
}

result_t Lidar_Data_Processing::waitPackage(node_info *node, uint32_t timeout)
{ 
  if(!node_lidar.serial_port)
  {
    return RESULT_FAIL;
  }
  int recvPos = 0;
  uint32_t startTs = getms();
  uint32_t waitTime = 0;
  uint8_t *packageBuffer = (node_lidar.lidar_general_info.m_intensities) ? 
                                    (uint8_t *)&node_lidar.scan_packages.package.package_Head : (uint8_t *)&node_lidar.scan_packages.packages.package_Head;
  uint8_t package_Sample_Num = 0;
  int32_t AngleCorrectForDistance = 0;
  int package_recvPos = 0;
  uint8_t package_type = 0;

  if (package_Sample_Index == 0)
  {
    recvPos = 0;
    while ((waitTime = getms() - startTs) <= timeout)
    {
      size_t remainSize = PackagePaidBytes - recvPos;
      size_t recvSize = 0;
 
      result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);

      if (!IS_OK(ans))
      {
        return ans;
      }

      if (recvSize > remainSize)
      {
        recvSize = remainSize;
      }

      node_lidar.serial_port->read_data(node_lidar.globalRecvBuffer, recvSize);

      for (size_t pos = 0; pos < recvSize; ++pos)
      {
        uint8_t currentByte = node_lidar.globalRecvBuffer[pos];
        switch (recvPos)
        {
        case 0:
          if (currentByte == (PH & 0xFF)){
          }else{
            continue;
          }
          break;

        case 1:
          CheckSumCal = PH;
          if (currentByte == (PH >> 8)){
          }else{
            recvPos = 0;
            continue;
          }
          break;

        case 2:
          SampleNumlAndCTCal = currentByte;
          package_type = currentByte & 0x01;
          if ((package_type == CT_Normal) || (package_type == CT_RingStart))
          {
            if (package_type == CT_RingStart)
            {
              scan_frequence = (currentByte & 0xFE) >> 1;
            }
          }
          else{
            has_package_error = true;
            recvPos = 0;
            continue;
          }

          break;

        case 3:
          SampleNumlAndCTCal += (currentByte * 0x100);
          package_Sample_Num = currentByte;
          break;

        case 4:
          if (currentByte & LIDAR_RESP_MEASUREMENT_CHECKBIT)
          {
            FirstSampleAngle = currentByte;
          }else{
            has_package_error = true;
            recvPos = 0;
            continue;
          }

          break;

        case 5:
          FirstSampleAngle += currentByte * 0x100;
          CheckSumCal ^= FirstSampleAngle;
          FirstSampleAngle = FirstSampleAngle >> 1;
          break;

        case 6:
          if (currentByte & LIDAR_RESP_MEASUREMENT_CHECKBIT)
          {
            LastSampleAngle = currentByte;
          }
          else
          {
            has_package_error = true;
            recvPos = 0;
            continue;
          }
          break;

        case 7:
          LastSampleAngle = currentByte * 0x100 + LastSampleAngle;
          LastSampleAngleCal = LastSampleAngle;
          LastSampleAngle = LastSampleAngle >> 1;

          if (package_Sample_Num == 1)
          {
            IntervalSampleAngle = 0;
          }
          else{
            if (LastSampleAngle < FirstSampleAngle)
            {
              if ((FirstSampleAngle > 270 * 64) && (LastSampleAngle < 90 * 64))
              {
                IntervalSampleAngle = (float)((360 * 64 + LastSampleAngle - FirstSampleAngle) /
                                                          ((package_Sample_Num - 1) *1.0));
                IntervalSampleAngle_LastPackage = IntervalSampleAngle;
              }
              else
              {
                IntervalSampleAngle = IntervalSampleAngle_LastPackage;
              }
            }
            else
            {
              IntervalSampleAngle = (float)((LastSampleAngle - FirstSampleAngle) /
                                                          ((package_Sample_Num - 1) * 1.0));
              IntervalSampleAngle_LastPackage = IntervalSampleAngle;
            }
          }

          break;

        case 8:
          CheckSum = currentByte;
          break;

        case 9:
          CheckSum += (currentByte * 0x100);
          break;
        }
        packageBuffer[recvPos++] = currentByte;
      }

      if (recvPos == PackagePaidBytes)
      {
        package_recvPos = recvPos;
        break;
      }
    }

    if (PackagePaidBytes == recvPos)
    {
      startTs = getms();
      recvPos = 0;

      while ((waitTime = getms() - startTs) <= timeout)
      {
        size_t remainSize = package_Sample_Num * PackageSampleBytes - recvPos;
        size_t recvSize = 0;
        result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);

        if (!IS_OK(ans))
        {
          return ans;
        }

        if (recvSize > remainSize)
        {
          recvSize = remainSize;
        }

        node_lidar.serial_port->read_data(node_lidar.globalRecvBuffer, recvSize);

        for (size_t pos = 0; pos < recvSize; ++pos)
        {
            if (node_lidar.lidar_general_info.m_intensities) {
              if (recvPos % 3 == 2) {
                Valu8Tou16 += node_lidar.globalRecvBuffer[pos] * 0x100;
                CheckSumCal ^= Valu8Tou16;
              } else if (recvPos % 3 == 1) {
                Valu8Tou16 = node_lidar.globalRecvBuffer[pos];
              } else {
                Valu8Tou16 = node_lidar.globalRecvBuffer[pos];
                Valu8Tou16 += 0x00 * 0x100;
                CheckSumCal ^= node_lidar.globalRecvBuffer[pos];
              }
            } else {
              if (recvPos % 2 == 1) {
                Valu8Tou16 += node_lidar.globalRecvBuffer[pos] * 0x100;
                CheckSumCal ^= Valu8Tou16;
              } else {
                Valu8Tou16 = node_lidar.globalRecvBuffer[pos];
              }
            }
          packageBuffer[package_recvPos + recvPos] = node_lidar.globalRecvBuffer[pos];
          recvPos++;
        }

        if (package_Sample_Num * PackageSampleBytes == recvPos)
        {
          package_recvPos += recvPos;
          break;
        }
      }

      if (package_Sample_Num * PackageSampleBytes != recvPos)
      {
        return RESULT_FAIL;
      }
    }else{
      return RESULT_FAIL;
    }

    CheckSumCal ^= SampleNumlAndCTCal;
    CheckSumCal ^= LastSampleAngleCal;
    if (CheckSumCal != CheckSum)
    {
      printf("data check,%x,%x,%d,%d\n",CheckSumCal,CheckSum,package_Sample_Num,recvPos);
      CheckSumResult = false;
      has_package_error = true;
    }
    else
    {
      CheckSumResult = true;
    }
  }
  uint8_t package_CT;
  if(node_lidar.lidar_general_info.m_intensities)
  {
    package_CT = node_lidar.scan_packages.package.package_CT;
  }else{
    package_CT = node_lidar.scan_packages.packages.package_CT;
  }

  (*node).scan_frequence = 0;

  if ((package_CT & 0x01) == CT_Normal)
  {
    (*node).sync_flag = Node_NotSync;
    memset((*node).debug_info, 0xff, sizeof((*node).debug_info));

    if (!has_package_error)
    {
      if (package_index < 10)
      {
        (*node).debug_info[package_index] = (package_CT >> 1);
        (*node).index = package_index;
      }else{
        (*node).index = 0xff;
      }
      if (package_Sample_Index == 0)
      {
        package_index++;
      }
    }else{
      (*node).index = 255;
      package_index = 0;
    }
  }else{
    (*node).sync_flag = Node_Sync;
    (*node).index = 255;
    package_index = 0;

    if (CheckSumResult)
    {
      has_package_error = false;
      (*node).scan_frequence = scan_frequence;
    }
  }

  (*node).sync_quality = Node_Default_Quality;
  (*node).stamp = 0;

  if (CheckSumResult)
  {
    if(node_lidar.lidar_general_info.m_intensities)
    {
      
      (*node).distance_q2 = (node_lidar.scan_packages.package.packageSampleDistance[package_Sample_Index*3+2] * 64) + 
                            (node_lidar.scan_packages.package.packageSampleDistance[package_Sample_Index*3+1] >> 2);
      (*node).sync_quality = (node_lidar.scan_packages.package.packageSampleDistance[package_Sample_Index*3+1] & 0x03)*64 + 
                            (node_lidar.scan_packages.package.packageSampleDistance[package_Sample_Index*3] >> 2);
      (*node).exp_m = node_lidar.scan_packages.package.packageSampleDistance[package_Sample_Index*3] & 0x03;
      //(*node).distance_q2 = (node_lidar.scan_packages.packages.packageSampleDistance[package_Sample_Index*3+1] >> 2 | (node_lidar.scan_packages.packages.packageSampleDistance[package_Sample_Index*3+2] << 6));
      //(*node).sync_quality = ((node_lidar.scan_packages.packages.packageSampleDistance[package_Sample_Index*3] >> 2) & 0x3F) + (node_lidar.scan_packages.packages.packageSampleDistance[package_Sample_Index*3+1] & 0x03) * 64;
    }else{
      (*node).distance_q2 = node_lidar.scan_packages.packages.packageSampleDistance[package_Sample_Index]>>2;
      (*node).sync_quality = ((uint16_t)((node_lidar.scan_packages.packages.packageSampleDistance[package_Sample_Index]) & 0x03));
    }
    
    if ((*node).distance_q2 != 0)
    {
      //结构引起的补偿
      /*
      AngleCorrectForDistance = (int32_t)(((atan(((21.8 * (155.3 - ((*node).distance_q2 / 4.0))) / 155.3) /
                                                 ((*node).distance_q2 / 4.0))) *180.0 / 3.1415) * 64.0);*/

      AngleCorrectForDistance = (int32_t)(atan(19.16*((*node).distance_q2-90.15)/(90.15*(*node).distance_q2))*64);
      
    }else{
      AngleCorrectForDistance = 0;
    }

    float sampleAngle = IntervalSampleAngle * package_Sample_Index;

    if ((FirstSampleAngle + sampleAngle + AngleCorrectForDistance) < 0)
    {
      (*node).angle_q6_checkbit = (((uint16_t)(FirstSampleAngle + sampleAngle +
                                               AngleCorrectForDistance + 23040))
                                   << LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) +
                                  LIDAR_RESP_MEASUREMENT_CHECKBIT;
    }else{
      if ((FirstSampleAngle + sampleAngle + AngleCorrectForDistance) > 23040)
      {
        (*node).angle_q6_checkbit = (((uint16_t)(FirstSampleAngle + sampleAngle +
                                                 AngleCorrectForDistance - 23040))
                                     << LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) +
                                    LIDAR_RESP_MEASUREMENT_CHECKBIT;
      }else{
        (*node).angle_q6_checkbit = (((uint16_t)(FirstSampleAngle + sampleAngle +
                                                 AngleCorrectForDistance))
                                     << LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) +
                                    LIDAR_RESP_MEASUREMENT_CHECKBIT;
      }
    }
  }else{
    (*node).sync_flag = Node_NotSync;
    (*node).sync_quality = Node_Default_Quality;
    (*node).angle_q6_checkbit = LIDAR_RESP_MEASUREMENT_CHECKBIT;
    (*node).distance_q2 = 0;
    (*node).scan_frequence = 0;
  }

  uint8_t nowPackageNum;

  if(node_lidar.lidar_general_info.m_intensities)
  {
    nowPackageNum = node_lidar.scan_packages.package.nowPackageNum;
  }else{
    nowPackageNum = node_lidar.scan_packages.packages.nowPackageNum;
  }

  package_Sample_Index ++;

  if (package_Sample_Index >= nowPackageNum)
  {
    package_Sample_Index = 0;
    CheckSumResult = false;
  }
  return RESULT_OK;
}


result_t Lidar_Data_Processing::waitPackage_coin(node_info *node,uint32_t timeout)
{
  
  int recvPos = 0;
  uint32_t startTs = getms();
  uint32_t waitTime = 0;

  uint8_t *packageBuffer = (uint8_t *)&node_lidar.scan_packages.package_coin.headL;
  uint8_t package_Sample_Num = 0;
  int32_t AngleCorrectForDistance = 0;
  int package_recvPos = 0;
  uint8_t package_type = 0;

  uint16_t start;
  uint16_t stop;
  float sampleAngle_t = 0.0;


  if (package_Sample_Index == 0)
  {
    recvPos = 0;

    while ((waitTime = getms() - startTs) <= timeout)
    {
      size_t remainSize = PackagePaidBytes - recvPos;
      size_t recvSize = 0;
      result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);

      if (!IS_OK(ans))
      {
        return ans;
      }

      if (recvSize > remainSize)
      {
        recvSize = remainSize;
      }

      node_lidar.serial_port->read_data(node_lidar.globalRecvBuffer, recvSize);

      for (size_t pos = 0; pos < recvSize; ++pos)
      {
        uint8_t currentByte = node_lidar.globalRecvBuffer[pos];
        switch (recvPos)
        {
        case 0:
          if (currentByte == 0x55)
          {
            //printf("收到头数据帧\n");
          }
          else{
            continue;
          }
          break;
        case 1:
          if (currentByte == 0xAA){
          }
          else{
            recvPos = 0;
            continue;
          }
          break;
        case 2:
          if(currentByte==0x83){
          }
          else{
            recvPos = 0;
            continue;
          }
          break;

        case 3:
          if(currentByte==0x08){ 
            package_Sample_Num = currentByte;           
          }
          else{
            recvPos = 0;
            continue;
          }
          break;

        case 4:
          break;

        case 5:
          break;

        case 6:
          FirstSampleAngle = currentByte;
          break;
        
        case 7:
          FirstSampleAngle += currentByte * 0x100;
          
          start_t = 360.0F * (FirstSampleAngle - FRAME_ANGLE_BASE)/FRAME_ANGLE_RANGE;
          //node_lidar.FirstSampleAngle = node_lidar.FirstSampleAngle >> 1;
          //node_lidar.FirstSampleAngle = node_lidar.FirstSampleAngle >> 1;
          break;
        }    

        packageBuffer[recvPos++] = currentByte;
      }

      if (recvPos == PackagePaidBytes)
      {
        package_recvPos = recvPos;
        break;
      }
    }
    int k;
    if (PackagePaidBytes == recvPos)
    {
      startTs = getms();
      recvPos = 0;
    
      while ((waitTime = getms() - startTs) <= timeout)
      {
        size_t remainSize = package_Sample_Num * PackageSampleBytes + 4 - recvPos;
        size_t recvSize = 0;
        result_t ans = node_lidar.serial_port->waitForData(remainSize, timeout - waitTime, &recvSize);

        if (!IS_OK(ans))
        {
          return ans;
        }
        if (recvSize > remainSize)
        {
          recvSize = remainSize;
        }

        node_lidar.serial_port->read_data(node_lidar.globalRecvBuffer, recvSize);

        for (size_t pos = 0; pos < recvSize; ++pos) {
          packageBuffer[package_recvPos + recvPos] = node_lidar.globalRecvBuffer[pos];
          recvPos++;
        }

        if (package_Sample_Num * PackageSampleBytes + 4 == recvPos)
        {
          package_recvPos += recvPos;
          break;
        }
      }
      if (package_Sample_Num * PackageSampleBytes + 4 != recvPos)
      {
        return RESULT_FAIL;
      }
    }
    else
    {
      return RESULT_FAIL;
    }
    unsigned int datajgs[17]={0};
    int temp_i=0;
    unsigned int chk32 = 0;
    for(temp_i = 0;temp_i < 17;temp_i++)
    {
      datajgs[temp_i]=packageBuffer[2*temp_i]+(packageBuffer[2*temp_i+1]<<8);
    }

    for(temp_i =0;temp_i<17;temp_i++)
    {
      chk32 =(chk32 <<1)+datajgs[temp_i];
    }
    CheckSumCal = (chk32 & 0x7FFF)+(chk32 >>15);
    CheckSumCal = CheckSumCal &0x7FFF;
    //node_lidar.LastSampleAngle = 360.0F * ((node_lidar.scan_packages.package_coin.stopAngleL + node_lidar.scan_packages.package_coin.stopAngleH*256)-FRAME_ANGLE_BASE)/FRAME_ANGLE_RANGE;
    LastSampleAngle = node_lidar.scan_packages.package_coin.stopAngleL;
    LastSampleAngle += node_lidar.scan_packages.package_coin.stopAngleH * 0x100;
    
    stop_t = 360.0F * (LastSampleAngle - FRAME_ANGLE_BASE)/FRAME_ANGLE_RANGE;
    //printf("node_lidar.LastSampleAngle =%f\n",360.0F * (node_lidar.LastSampleAngle - FRAME_ANGLE_BASE)/FRAME_ANGLE_RANGE);
    
    //node_lidar.LastSampleAngle = node_lidar.LastSampleAngle >> 1;
    
    /*
    if (node_lidar.LastSampleAngle < node_lidar.FirstSampleAngle) {
      if ((node_lidar.FirstSampleAngle > 270 * 64) && (node_lidar.LastSampleAngle < 90 * 64)) {
        node_lidar.IntervalSampleAngle = (float)((360 * 64 + node_lidar.LastSampleAngle -
                                        node_lidar.FirstSampleAngle) / ((
                                              package_Sample_Num - 1) * 1.0));
        node_lidar.IntervalSampleAngle_LastPackage = node_lidar.IntervalSampleAngle;
      } else {
        node_lidar.IntervalSampleAngle = node_lidar.IntervalSampleAngle_LastPackage;
      }
    } else {
      node_lidar.IntervalSampleAngle = (float)((node_lidar.LastSampleAngle - node_lidar.FirstSampleAngle) / ((
                                      package_Sample_Num - 1) * 1.0));
      node_lidar.IntervalSampleAngle_LastPackage = node_lidar.IntervalSampleAngle;
    }*/
    if(LastSampleAngle < FirstSampleAngle)
    {
      IntervalSampleAngle = (360 - start_t + stop_t)/(package_Sample_Num-1);

    }
    else
    {
      IntervalSampleAngle = (stop_t - start_t)/(package_Sample_Num-1);

    }
    if (node_lidar.scan_packages.package_coin.csL != (CheckSumCal & 0xFF) || node_lidar.scan_packages.package_coin.csH != (CheckSumCal >> 8))
    {
      CheckSumResult = false;
      has_package_error = true;
    }
    else
    {
      CheckSumResult = true;
    }
  }
  /*
  uint8_t package_CT;

  if (node_lidar.m_intensities)
  {
    package_CT = node_lidar.scan_packages.package.package_CT;
  }
  else
  {
    package_CT = node_lidar.scan_packages.packages.package_CT;
  }

  (*node).scan_frequence = 0;

  if ((package_CT & 0x01) == CT_Normal)
  {
    (*node).sync_flag = Node_NotSync;
    memset((*node).debug_info, 0xff, sizeof((*node).debug_info));

    if (!node_lidar.has_package_error)
    {
      if (node_lidar.scan_packages.package_index < 10)
      {
        (*node).debug_info[node_lidar.scan_packages.package_index] = (package_CT >> 1);
        (*node).index = node_lidar.scan_packages.package_index;
      }
      else
      {
        (*node).index = 0xff;
      }
      if (node_lidar.scan_packages.package_Sample_Index == 0)
      {
        node_lidar.scan_packages.package_index++;
      }
    }
    else
    {
      (*node).index = 255;
      node_lidar.scan_packages.package_index = 0;
    }
  }
  else
  {
    (*node).sync_flag = Node_Sync;
    (*node).index = 255;
    node_lidar.scan_packages.package_index = 0;

    if (node_lidar.CheckSumResult)
    {
      node_lidar.has_package_error = false;
      (*node).scan_frequence = node_lidar.scan_frequence;
    }
  }*/

  (*node).sync_quality = Node_Default_Quality;
  (*node).stamp = 0;

  if (CheckSumResult)
  {
    (*node).distance_q2 = (node_lidar.scan_packages.package_coin.data[package_Sample_Index].d0 +
          (node_lidar.scan_packages.package_coin.data[package_Sample_Index].d1*256))&0x3FFF;
   
    (*node).sync_quality = (node_lidar.scan_packages.package_coin.data[package_Sample_Index].d2>>2);
    

    if ((*node).distance_q2 != 0)
    {
      AngleCorrectForDistance = 0; 
    }
    else
    {
      AngleCorrectForDistance = 0;
    }

    sampleAngle_t = IntervalSampleAngle * package_Sample_Index + start_t;
    if(sampleAngle_t >360)
    {
      sampleAngle_t = sampleAngle_t - 360;
    }
    (*node).angle_q6_checkbit = (uint16_t)(sampleAngle_t*100); 
  }
  
  else
  {
    (*node).sync_flag = Node_NotSync;
    (*node).sync_quality = Node_Default_Quality;
    (*node).angle_q6_checkbit = LIDAR_RESP_MEASUREMENT_CHECKBIT;
    (*node).distance_q2 = 0;
    (*node).scan_frequence = 0;
  }
  angle_new = sampleAngle_t;
  if(angle_bak >350 && angle_new <10)
  {
    (*node).sync_flag = Node_Sync;
  }
  else
  {
    (*node).sync_flag = Node_NotSync;
  }
  
  angle_bak = angle_new;
					
  uint8_t nowPackageNum;
  nowPackageNum = node_lidar.scan_packages.package_coin.sampleinfo;

  package_Sample_Index++;

  if (package_Sample_Index >= nowPackageNum)
  {
    package_Sample_Index = 0;
    CheckSumResult = false;
  }
  return RESULT_OK;
}


result_t Lidar_Data_Processing::waitScanData(node_info *nodebuffer, size_t &count, uint32_t timeout)
{
  if(!node_lidar.lidar_status.isConnected)
  {
    count = 0;
    return RESULT_FAIL;
  }

  recvNodeCount = 0;
  uint32_t startTs = getms();
  uint32_t waitTime = 0;
  result_t ans = RESULT_FAIL;
  /*超时处理及点数判断*/
  while ((waitTime = getms() - startTs) <= timeout && recvNodeCount < count)
  {
    node_info node;
    if(node_lidar.lidar_general_info.version == M1CT_Coin_Plus)
    {
      ans = waitPackage_coin(&node, timeout - waitTime);
    }else{
      ans = waitPackage(&node, timeout - waitTime);
    }
    
    if (!IS_OK(ans))
    {
      count = recvNodeCount;
      return ans;
    }

    nodebuffer[recvNodeCount++] = node;

    if (node.sync_flag & LIDAR_RESP_MEASUREMENT_SYNCBIT)
    {
      /*检查缓冲区中的字节数*/
      size_t size = node_lidar.serial_port->available();
      uint64_t delayTime = 0;
      /*数据包的数据量*/
      size_t PackageSize = (node_lidar.lidar_general_info.m_intensities ? INTENSITY_NORMAL_PACKAGE_SIZE :
                            NORMAL_PACKAGE_SIZE);

      if (size > PackagePaidBytes && size < PackagePaidBytes * PackageSize)
      {
        size_t packageNum = size / PackageSize;
        size_t Number = size % PackageSize;
        delayTime = packageNum * node_lidar.lidar_general_info.m_PointTime * PackageSize / 2;

        if (Number > PackagePaidBytes)
        {
          delayTime += node_lidar.lidar_general_info.m_PointTime * ((Number - PackagePaidBytes) / 2);
        }

        size = Number;

        if (packageNum > 0 && Number == 0)
        {
          size = PackageSize;
        }
      }
      nodebuffer[recvNodeCount - 1].stamp = size * node_lidar.lidar_general_info.trans_delay + delayTime;
      nodebuffer[recvNodeCount - 1].scan_frequence = node.scan_frequence;
      count = recvNodeCount;
      return RESULT_OK;
    }
    if (recvNodeCount == count)
    {
      return RESULT_OK;
    }
  }
  count = recvNodeCount;
  return RESULT_FAIL;
}

```
## `cspc_lidar_sdk_ros1/src/timer.cpp`

```
#include <assert.h>
#include <time.h>
#include "sys/time.h"

#include <inttypes.h>
#include "timer.h"
#include <unistd.h>

uint32_t getms()
{
    struct timespec t;
    t.tv_sec = t.tv_nsec = 0;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1000L + t.tv_nsec / 1000000L;
}

int gettimeofday_t(struct timeval *tv, void * /*tzv*/)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    tv->tv_sec = ts.tv_sec;
    tv->tv_usec = ts.tv_nsec / 1000;
    return 0;
}

uint64_t getTime()
{
#if HAS_CLOCK_GETTIME
    struct timespec tim;
    clock_gettime(CLOCK_REALTIME, &tim);
    return static_cast<uint64_t>(tim.tv_sec) * 1000000000LL + tim.tv_nsec;
#else
    struct timeval timeofday;
    gettimeofday_t(&timeofday, NULL);
    return static_cast<uint64_t>(timeofday.tv_sec) * 1000000000LL +
           static_cast<uint64_t>(timeofday.tv_usec) * 1000LL;
#endif
}

void delay(uint32_t ms) {
  while (ms >= 1000) {
    usleep(1000 * 1000);
    ms -= 1000;
  };

  if (ms != 0) {
    usleep(ms * 1000);
  }
}
```
## `cspc_lidar_sdk_ros1/src/lidar_information.cpp`

```
#include "node_lidar.h"


bool get_version_t()
{
    printf("encry check version\n");
    //下发获取版本的指令
    node_lidar.serial_port->write_data(get_version,4);
    //获取回复
    if(node_lidar.lidar_data_processing.waitResponseHeader(0x64)==RESULT_OK)
    {
        printf("version=%d,%d\n",node_lidar.lidar_version[0],node_lidar.lidar_version[1]);
        return true;
        
    }else{
        printf("check version wrong\n");
        return false;
    }
}

```
## `cspc_lidar_sdk_ros1/src/point_cloud_optimize.cpp`

```
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include "node_lidar.h"
#include "point_cloud_optimize.h"


/*****************************************
*             点云滤波函数                 *
******************************************/
void Point_cloud_optimize::PointCloudFilter(LaserScan *Scan)
{
	int i0, i1, i2, i3, i4;
	float x0, y0, x1, y1, x2, y2, x3, y3, r1, r2;
	float d01, d12, d23, d34;
	float a, b, Adeta;
	float FilterRatioAdj;
	float AngDiff;
	int DepthState;
	float FilterRatio = 2.5;

	AngDiff = 2 * PI / (Scan->points.size() - 1);
	FilterRatioAdj = FilterRatio * sin(AngDiff);

	for (i0 = 0; i0 < Scan->points.size(); i0++)
	{
		i1 = i0 + 1;
		i1 = i1 < Scan->points.size() ? i1 : i1 - Scan->points.size();
		i2 = i0 + 2;
		i2 = i2 < Scan->points.size() ? i2 : i2 - Scan->points.size();
		i3 = i0 + 3;
		i3 = i3 < Scan->points.size() ? i3 : i3 - Scan->points.size();
		DepthState = 0;
		DepthState += (Scan->points[i0].range != 0) * 1;
		DepthState += (Scan->points[i1].range != 0) * 2;
		DepthState += (Scan->points[i2].range != 0) * 4;
		DepthState += (Scan->points[i3].range != 0) * 8;
		if (DepthState == 0x0F)
		{ //1111
			x0 = Scan->points[i0].range * cos(Scan->points[i0].angle * PI / 180);
			y0 = Scan->points[i0].range * sin(Scan->points[i0].angle * PI / 180);
			x3 = Scan->points[i3].range * cos(Scan->points[i3].angle * PI / 180);
			y3 = Scan->points[i3].range * sin(Scan->points[i3].angle * PI / 180);
			x1 = (x3 + 2 * x0) / 3;
			y1 = (y3 + 2 * y0) / 3;
			x2 = (2 * x3 + x0) / 3;
			y2 = (2 * y3 + y0) / 3;
			r1 = sqrt(x1 * x1 + y1 * y1);
			r2 = sqrt(x2 * x2 + y2 * y2);

			a = Scan->points[i0].range;
			b = Scan->points[i1].range;
			Adeta = fabs(Scan->points[i0].angle - Scan->points[i1].angle) * PI / 180;
			d01 = sqrt(a * a + b * b - 2 * a * b * cos(Adeta));
			a = Scan->points[i1].range;
			b = Scan->points[i2].range;
			Adeta = fabs(Scan->points[i1].angle - Scan->points[i2].angle) * PI / 180;
			d12 = sqrt(a * a + b * b - 2 * a * b * cos(Adeta));
			a = Scan->points[i2].range;
			b = Scan->points[i3].range;
			Adeta = fabs(Scan->points[i2].angle - Scan->points[i3].angle) * PI / 180;
			d23 = sqrt(a * a + b * b - 2 * a * b * cos(Adeta));

			if (FilterRatioAdj * Scan->points[i1].range < d01 && FilterRatioAdj * Scan->points[i1].range < d12)
			{
				Scan->points[i1].range = 0;
			}
			if (FilterRatioAdj * Scan->points[i2].range < d12 && FilterRatioAdj * Scan->points[i2].range < d23)
			{
				Scan->points[i2].range = 0;
			}
			if (0 == Scan->points[i1].range || 0 == Scan->points[i2].range)
			{
				continue;
			}

			if ((Scan->points[i1].range > r1 && Scan->points[i2].range < r2) || (Scan->points[i1].range < r1 && Scan->points[i2].range > r2))
			{
				if (
					(d01 > FilterRatioAdj * Scan->points[i0].range && d12 < FilterRatioAdj * Scan->points[i1].range && d23 < FilterRatioAdj * Scan->points[i2].range) || (d01 < FilterRatioAdj * Scan->points[i0].range && d12 > FilterRatioAdj * Scan->points[i1].range && d23 < FilterRatioAdj * Scan->points[i2].range) || (d01 < FilterRatioAdj * Scan->points[i0].range && d12 < FilterRatioAdj * Scan->points[i1].range && d23 > FilterRatioAdj * Scan->points[i2].range))
				{
				}
				else
				{
					Scan->points[i1].range = r1 + 0.4 * (Scan->points[i1].range - r1);
					Scan->points[i2].range = r2 + 0.4 * (Scan->points[i2].range - r2);
				}
			}
			else
			{
			}
		}
		else if (DepthState == 0x00 || DepthState == 0x08 || DepthState == 0x01)
		{ // 0000 1000 0001
		}
		else if ((DepthState & 0x0E) == 0x04)
		{ //010x
			Scan->points[i2].range = 0;
		}
		else if ((DepthState & 0x07) == 0x02)
		{ //x010
			Scan->points[i1].range = 0;
		}
		else if ((DepthState & 0x07) == 0x03)
		{ //x011
			a = Scan->points[i0].range;
			b = Scan->points[i1].range;
			if (sqrt(a * a + b * b - 2 * a * b * cos(AngDiff)) > FilterRatioAdj * Scan->points[i1].range)
			{
				Scan->points[i1].range = 0;
			}
		}
		else if (DepthState == 0x0E)
		{ //1110
			a = Scan->points[i1].range;
			b = Scan->points[i2].range;
			if (sqrt(a * a + b * b - 2 * a * b * cos(AngDiff)) > FilterRatioAdj * Scan->points[i1].range)
			{
				Scan->points[i1].range = 0;
			}
		}
		else if ((DepthState & 0x0E) == 0x0C)
		{ //110x 0111
			a = Scan->points[i2].range;
			b = Scan->points[i3].range;
			if (sqrt(a * a + b * b - 2 * a * b * cos(AngDiff)) > FilterRatioAdj * Scan->points[i2].range)
			{
				Scan->points[i2].range = 0;
			}
		}
		else if (DepthState == 0x07)
		{ //0111
			a = Scan->points[i1].range;
			b = Scan->points[i2].range;
			if (sqrt(a * a + b * b - 2 * a * b * cos(AngDiff)) > FilterRatioAdj * Scan->points[i2].range)
			{
				Scan->points[i2].range = 0;
			}
		}
		else if (DepthState == 0x06)
		{ //0110
			a = Scan->points[i1].range;
			b = Scan->points[i2].range;
			if (sqrt(a * a + b * b - 2 * a * b * cos(AngDiff)) > FilterRatioAdj * Scan->points[i1].range)
			{
				Scan->points[i1].range = 0;
				Scan->points[i2].range = 0;
			}
		}
		else
		{
		}
	}

	for (i0 = 0; i0 < Scan->points.size(); i0++)
	{
		i1 = i0 + 1;
		i1 = i1 < Scan->points.size() ? i1 : i1 - Scan->points.size();
		i2 = i0 + 2;
		i2 = i2 < Scan->points.size() ? i2 : i2 - Scan->points.size();
		i3 = i0 + 3;
		i3 = i3 < Scan->points.size() ? i3 : i3 - Scan->points.size();
		i4 = i0 + 4;
		i4 = i4 < Scan->points.size() ? i4 : i4 - Scan->points.size();
		if (Scan->points[i0].range != 0 && Scan->points[i1].range != 0 && Scan->points[i2].range != 0 && Scan->points[i3].range != 0 && Scan->points[i4].range != 0)
		{
			a = Scan->points[i0].range;
			b = Scan->points[i1].range;
			Adeta = fabs(Scan->points[i0].angle - Scan->points[i1].angle) * PI / 180;
			d01 = sqrt(a * a + b * b - 2 * a * b * cos(Adeta));

			a = Scan->points[i1].range;
			b = Scan->points[i2].range;
			Adeta = fabs(Scan->points[i1].angle - Scan->points[i2].angle) * PI / 180;
			d12 = sqrt(a * a + b * b - 2 * a * b * cos(Adeta));

			a = Scan->points[i2].range;
			b = Scan->points[i3].range;
			Adeta = fabs(Scan->points[i2].angle - Scan->points[i3].angle) * PI / 180;
			d23 = sqrt(a * a + b * b - 2 * a * b * cos(Adeta));

			a = Scan->points[i3].range;
			b = Scan->points[i4].range;
			Adeta = fabs(Scan->points[i3].angle - Scan->points[i4].angle) * PI / 180;
			d34 = sqrt(a * a + b * b - 2 * a * b * cos(Adeta));

			if (
				d01 < FilterRatioAdj * Scan->points[i1].range && d34 < FilterRatioAdj * Scan->points[i3].range && (d12 > FilterRatioAdj * Scan->points[i2].range || d23 > FilterRatioAdj * Scan->points[i2].range))
			{
				if (
					(Scan->points[i0].range < Scan->points[i1].range && Scan->points[i3].range < Scan->points[i4].range) || (Scan->points[i0].range > Scan->points[i1].range && Scan->points[i3].range > Scan->points[i4].range))
				{
					Scan->points[i2].range = (Scan->points[i1].range + Scan->points[i3].range) / 2;
				}
			}
		}
		else if (Scan->points[i0].range == 0 && Scan->points[i1].range != 0 && Scan->points[i2].range != 0 && Scan->points[i3].range != 0 && Scan->points[i4].range != 0)
		{
			x2 = Scan->points[i2].range * cos(Scan->points[i2].angle * PI / 180);
			y2 = Scan->points[i2].range * sin(Scan->points[i2].angle * PI / 180);
			x3 = Scan->points[i3].range * cos(Scan->points[i3].angle * PI / 180);
			y3 = Scan->points[i3].range * sin(Scan->points[i3].angle * PI / 180);
			x1 = 2 * x2 - x3;
			y1 = 2 * y2 - y3;
			Scan->points[i1].range = Scan->points[i1].range + 0.4 * (sqrt(x1 * x1 + y1 * y1) - Scan->points[i1].range);
		}
		else if (Scan->points[i0].range != 0 && Scan->points[i1].range != 0 && Scan->points[i2].range != 0 && Scan->points[i3].range != 0 && Scan->points[i4].range == 0)
		{
			x1 = Scan->points[i1].range * cos(Scan->points[i1].angle * PI / 180);
			y1 = Scan->points[i1].range * sin(Scan->points[i1].angle * PI / 180);
			x2 = Scan->points[i2].range * cos(Scan->points[i2].angle * PI / 180);
			y2 = Scan->points[i2].range * sin(Scan->points[i2].angle * PI / 180);
			x3 = 2 * x2 - x1;
			y3 = 2 * y2 - y1;
			Scan->points[i3].range = Scan->points[i3].range + 0.4 * (sqrt(x3 * x3 + y3 * y3) - Scan->points[i3].range);
		}
		else
		{
		}
	}
}

/*****************************************
* 雷达实际测距距离-雷达安装位置到扫地机边缘的距离*
******************************************/
int Point_cloud_optimize::UltrasonicSimRanging(LaserPoint &pScan)
{
	int i, index;
	short tempdep;
	float target_angle = pScan.angle + node_lidar.lidar_robot_info.install_to_zero;

	if(target_angle > 360.0)
	{
		target_angle = (target_angle-360.0);
	}
	if(target_angle > 360.0 || target_angle < 0.0)
	{
		target_angle = 0;
	}
	index = (int)(target_angle/ULTRASONIC_ANGLE_INC_DEG + 0.5);

	if (index < node_lidar.lidar_block.blocked_size)
	{
		if(pScan.range==0)
		{
			pScan.range_check = 0;
		}else{
			pScan.range_check = pScan.range - Lidar_Blocked[index];
		}
	}else{
		pScan.range_check = 0;
	}
}

/*****************************************
*         获取结构缺口剔除的角度             *
******************************************/
void Point_cloud_optimize::getLidarCoverAngle(char *charbuf)
{
	LidarCoverAngleStr tempAngle;
	char tempstr[ANGLESTRLENMAX];
	int searstate = 0, index; 

	int len = strlen(charbuf);
	node_lidar.lidar_robot_info.LidarCoverBarNumber = 0;
	for (int i = 0; i < len; i++)
	{
		if (charbuf[i] == '[')
		{
			searstate = 1;
			index = 0;
			memset(tempstr, 0, ANGLESTRLENMAX);
		}
		else if (charbuf[i] == ',' && strlen(tempstr) > 0)
		{
			searstate = 2;
			index = 0;
			tempAngle.f_begin = atof(tempstr);
			memset(tempstr, 0, ANGLESTRLENMAX);
		}
		else if (charbuf[i] == ']' && searstate == 2 && strlen(tempstr) > 0)
		{
			tempAngle.f_end = atof(tempstr);
			if (tempAngle.f_begin < tempAngle.f_end && tempAngle.f_end <= 360.0)
			{
				node_lidar.lidar_robot_info.LidarCoverBarNumber++;
				node_lidar.lidar_robot_info.LidarCoverAngle.push_back(tempAngle);
			}
			searstate = 0;
		}
		else if (searstate != 0)
		{
			tempstr[index++] = charbuf[i];
			index = (index >= ANGLESTRLENMAX) ? (ANGLESTRLENMAX - 1) : index;
		}
		else
		{
		}
	}
}


void Point_cloud_optimize::lidar_blocked_count(LaserPoint &pScan,int count_lidar)
{
	int cnt_judge_count = count_lidar / (2*7);
	if(pScan.range_check < -10 && pScan.range_check > -200)
	{
		cnt_all++;
		if(abs(cnt_judge-cnt_record) < 20)
		{
			cnt++;
		}else{
			cnt = 0;
		}
		if(cnt > cnt_judge_count)
		{
			cumulation = true;
		}
		cnt_record = cnt_judge;
	}
	cnt_judge++;
}


/*****************************************
*         雷达被遮挡判断             		*
******************************************/
void Point_cloud_optimize::lidar_blocked_judge(int count)
{
	if((float)node_lidar.lidar_block.lidar_zero_count / (float)count > 0.70)
	{
		node_lidar.lidar_block.point_check++;
	}else{
		if(node_lidar.lidar_block.point_check > 0)
		{
			node_lidar.lidar_block.point_check--;
		}
	}
	if(node_lidar.lidar_block.point_check > 200)
	{
		printf("lidar 雷达被严重遮挡百分之七十 %d,%d\n",node_lidar.lidar_block.lidar_zero_count,node_lidar.scan_node_count);
		node_lidar.lidar_status.lidar_abnormal_state |= 0x04;
		node_lidar.lidar_block.point_check = 0;
	}
	datas_clear();
}


/*****************************************
*         雷达点云缺口剔除             		*
******************************************/
void Point_cloud_optimize::lidar_cover_cut(float &range,float &angle)
{
	for (int k = 0; k < node_lidar.lidar_robot_info.LidarCoverBarNumber; k++)
	{
		if (node_lidar.lidar_robot_info.LidarCoverAngle[k].f_begin < angle && angle < node_lidar.lidar_robot_info.LidarCoverAngle[k].f_end)
		{
			range = 0;
		}
	}
}

void Point_cloud_optimize::datas_clear()
{
	cnt=0;
    cnt_all=0;
    cnt_judge=0;
    cnt_record=0;
    cumulation = false;
}

void Point_cloud_optimize::lidar_blocked_init()
{
	float angle,radian;
	float r, d, temp;

	r = node_lidar.lidar_robot_info.ROBOT_DIAMETER_mm / 2.0F;
	d = node_lidar.lidar_robot_info.LIDAR_ROBOT_CENTER_DISTANCE_mm * 1.0;

	float x,y;
	float k,s,a,b,c;

	int size = 360/ULTRASONIC_ANGLE_INC_DEG;
	node_lidar.lidar_block.blocked_size = size;

	for (int j = 0; j < size; j++)
	{
		angle = (360.0 - j * ULTRASONIC_ANGLE_INC_DEG);
		radian = angle * PI / 180.0;
		if(angle == 90.0)
		{
			Lidar_Blocked[j] = r-d;
		}else if(angle == 270)
		{
			Lidar_Blocked[j] = r+d;
		}
		else{
			radian = fabs(radian);
			k = tan(radian);
			a=1+k*k;
			b=2*d*k;
			c=d*d-r*r; 
			s=b*b-4*a*c;
			if((angle >= 0 && angle < 90)|| angle > 270 && angle <=360){
				x=(-1*b+sqrt(s))/(2*a);
			}else{
				x=(-1*b-sqrt(s))/(2*a);
			}
			y=k*x+d;
			Lidar_Blocked[j] = sqrt(x*x+(y-d)*(y-d));
		}
	}
}


```
## `cspc_lidar_sdk_ros1/.vscode/c_cpp_properties.json`

```
{
    "configurations": [
        {
            "name": "Linux",
            "includePath": [
                "${workspaceFolder}/**"
            ],
            "defines": [],
            "compilerPath": "/usr/bin/gcc",
            "cStandard": "c11",
            "cppStandard": "c++17",
            "intelliSenseMode": "linux-gcc-x64"
        }
    ],
    "version": 4
}
```
## `cspc_lidar_sdk_ros1/.vscode/settings.json`

```
{
    "files.associations": {
        "bitset": "cpp",
        "chrono": "cpp",
        "algorithm": "cpp",
        "cctype": "cpp",
        "clocale": "cpp",
        "cmath": "cpp",
        "cstdarg": "cpp",
        "cstddef": "cpp",
        "cstdio": "cpp",
        "cstdlib": "cpp",
        "cstring": "cpp",
        "ctime": "cpp",
        "cwchar": "cpp",
        "cwctype": "cpp",
        "array": "cpp",
        "atomic": "cpp",
        "strstream": "cpp",
        "*.tcc": "cpp",
        "complex": "cpp",
        "condition_variable": "cpp",
        "cstdint": "cpp",
        "deque": "cpp",
        "list": "cpp",
        "unordered_map": "cpp",
        "vector": "cpp",
        "exception": "cpp",
        "functional": "cpp",
        "iterator": "cpp",
        "map": "cpp",
        "memory": "cpp",
        "memory_resource": "cpp",
        "numeric": "cpp",
        "optional": "cpp",
        "random": "cpp",
        "ratio": "cpp",
        "set": "cpp",
        "string": "cpp",
        "string_view": "cpp",
        "system_error": "cpp",
        "tuple": "cpp",
        "type_traits": "cpp",
        "utility": "cpp",
        "fstream": "cpp",
        "initializer_list": "cpp",
        "iomanip": "cpp",
        "iosfwd": "cpp",
        "iostream": "cpp",
        "istream": "cpp",
        "limits": "cpp",
        "mutex": "cpp",
        "new": "cpp",
        "ostream": "cpp",
        "sstream": "cpp",
        "stdexcept": "cpp",
        "streambuf": "cpp",
        "thread": "cpp",
        "cfenv": "cpp",
        "cinttypes": "cpp",
        "typeindex": "cpp",
        "typeinfo": "cpp",
        "variant": "cpp",
        "bit": "cpp",
        "csignal": "cpp",
        "any": "cpp"
    }
}
```

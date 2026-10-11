# m1ct_d4_ros2_v16.zip

Original archive: [m1ct_d4_ros2_v16.zip](../_originals/2%20ROS%20and%20ROS2%20feature%20pack%20information/m1ct_d4_ros2_v16.zip). All original bytes, including compiled drivers and executables, are preserved in that archive.

Text files are transcribed below. Embedded PDF manuals have their own Markdown conversions. Binary files remain available in the original archive. No software was executed.

## Archive contents

| Entry | Bytes | Representation |
| --- | ---: | --- |
| m1ct_d2/ | 0 | Directory or non-regular entry |
| m1ct_d2/include/ | 0 | Directory or non-regular entry |
| m1ct_d2/include/m1ct_d2/ | 0 | Directory or non-regular entry |
| m1ct_d2/include/m1ct_d2/timer.h | 113 | Full text below |
| m1ct_d2/include/m1ct_d2/mtime.h | 1059 | Full text below |
| m1ct_d2/include/m1ct_d2/locker.h | 6505 | Full text below |
| m1ct_d2/include/m1ct_d2/msg_recept.h | 113 | Full text below |
| m1ct_d2/include/m1ct_d2/lidar_information.h | 5196 | Full text below |
| m1ct_d2/include/m1ct_d2/point_cloud_optimize.h | 1001 | Full text below |
| m1ct_d2/include/m1ct_d2/node_lidar.h | 3907 | Full text below |
| m1ct_d2/include/m1ct_d2/lidar_data_processing.h | 1989 | Full text below |
| m1ct_d2/include/m1ct_d2/serial_port.h | 3535 | Full text below |
| m1ct_d2/params/ | 0 | Directory or non-regular entry |
| m1ct_d2/params/m1ct_d2.yaml | 377 | Full text below |
| m1ct_d2/.vscode/ | 0 | Directory or non-regular entry |
| m1ct_d2/.vscode/settings.json | 114 | Full text below |
| m1ct_d2/readme.txt | 66 | Full text below |
| m1ct_d2/package.xml | 1155 | Full text below |
| m1ct_d2/sc_mini.rules | 205 | Full text below |
| m1ct_d2/CMakeLists.txt | 958 | Full text below |
| m1ct_d2/src/ | 0 | Directory or non-regular entry |
| m1ct_d2/src/lidar_information.cpp | 481 | Full text below |
| m1ct_d2/src/point_cloud_optimize.cpp | 12595 | Full text below |
| m1ct_d2/src/Error.msg | 102 | Full text below |
| m1ct_d2/src/serial_port.cpp | 15617 | Full text below |
| m1ct_d2/src/timer.cpp | 1033 | Full text below |
| m1ct_d2/src/node_lidar.cpp | 18198 | Full text below |
| m1ct_d2/src/mtime.cpp | 2159 | Full text below |
| m1ct_d2/src/lidar_data_processing.cpp | 31717 | Full text below |
| m1ct_d2/src/main.cpp | 3018 | Full text below |

## `m1ct_d2/include/m1ct_d2/timer.h`

```
#ifndef NODE_TIMER_H
#define NODE_TIMER_H

uint32_t getms();
uint64_t getTime();
void delay(uint32_t ms);

#endif
```
## `m1ct_d2/include/m1ct_d2/mtime.h`

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
## `m1ct_d2/include/m1ct_d2/locker.h`

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
## `m1ct_d2/include/m1ct_d2/msg_recept.h`

```
#ifndef __H_MESSAGE_RECEPT_H__
#define __H_MESSAGE_RECEPT_H__

bool get_version_t();
bool encry_doing();


#endif
```
## `m1ct_d2/include/m1ct_d2/lidar_information.h`

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
  uint8_t exp_m;              //! 当前是否为高反光材质
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
  M1CT_Coin_D2,
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
## `m1ct_d2/include/m1ct_d2/point_cloud_optimize.h`

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
## `m1ct_d2/include/m1ct_d2/node_lidar.h`

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
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include <iostream>

using namespace std;

/*雷达基本信息*/
typedef struct{
  int version = 1; //雷达版本
  string port = "/dev/sc_mini";     //串口名称
  int m_SerialBaudrate = 230400;   //波特率
  bool m_intensities = false;
  uint64_t m_PointTime = 1e9/5000; 
  uint32_t trans_delay = 0;
  string frame_id = "laser_link";
  uint16_t frequency_max = 103;
  uint16_t frequency_min = 97;
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
  uint64_t scan_start_time = 0;
  uint64_t scan_end_time = 0;
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

  ~node_lidar_t();
};

extern node_lidar_t node_lidar;


bool initialize(); 
int node_start(int argc, char **argv);
int send_lidar_data(LaserScan &outscan);
void flushSerial();
result_t grabScanData(uint32_t timeout = DEFAULT_TIMEOUT);
result_t connect(const char *port_path, uint32_t baudrate,node_lidar_t &lidar_arg);


#endif
```
## `m1ct_d2/include/m1ct_d2/lidar_data_processing.h`

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
## `m1ct_d2/include/m1ct_d2/serial_port.h`

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
## `m1ct_d2/params/m1ct_d2.yaml`

```
m1ct_d2_node:
  ros__parameters:
    port: /dev/sc_mini
    frame_id: laser_link
    ignore_array: ""
    baudrate: 230400
    samp_rate: 9
    resolution_fixed: true
    singleChannel: false
    auto_reconnect: true
    reversion: true
    isToFLidar: false
    angle_max: 180.0
    angle_min: -180.0
    max_range: 16.0
    min_range: 0.01
    frequency: 10.0
    version: 4
```
## `m1ct_d2/.vscode/settings.json`

```
{
    "files.associations": {
        "bitset": "cpp",
        "chrono": "cpp",
        "algorithm": "cpp"
    }
}
```
## `m1ct_d2/readme.txt`

```
sudo cp sc_mini.rules /etc/udev/rules.d

ros2 run m1ct_d2 m1ct_d2
```
## `m1ct_d2/package.xml`

```
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>m1ct_d2</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="bby@todo.todo">bby</maintainer>
  <license>TODO: License declaration</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <build_depend>rclcpp</build_depend>
  <build_depend>sensor_msgs</build_depend>
  <build_depend>visualization_msgs</build_depend>
  <build_depend>geometry_msgs</build_depend>

  <exec_depend>rclcpp</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>visualization_msgs</exec_depend>
  <exec_depend>geometry_msgs</exec_depend>

  <test_depend>ament_cmake_gtest</test_depend>
  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <build_depend>rosidl_default_generators</build_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>

```
## `m1ct_d2/sc_mini.rules`

```
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE:="0666", SYMLINK+="sc_mini"
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE:="0777", SYMLINK+="sc_m_c"
```
## `m1ct_d2/CMakeLists.txt`

```
cmake_minimum_required(VERSION 3.5)

project(m1ct_d2)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
#find_package(rosidl_default_generators REQUIRED)

set(SDK_PATH "./src/")

FILE(GLOB SDK_SRC 
  "${SDK_PATH}*.cpp"
)

include_directories(
  ${PROJECT_SOURCE_DIR}/include/m1ct_d2
)

add_executable(m1ct_d2 ${SDK_SRC})

ament_target_dependencies(m1ct_d2
  "rclcpp"
  "sensor_msgs"
  "visualization_msgs"
  "geometry_msgs"
)



install(TARGETS
  m1ct_d2
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```
## `m1ct_d2/src/lidar_information.cpp`

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
## `m1ct_d2/src/point_cloud_optimize.cpp`

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
## `m1ct_d2/src/Error.msg`

```
#block
int32 blocked_size
int32 lidar_zero_count
bool blocked_judge

#restart
bool lidar_trap_restart
```
## `m1ct_d2/src/serial_port.cpp`

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
## `m1ct_d2/src/timer.cpp`

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
## `m1ct_d2/src/node_lidar.cpp`

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
#include "std_msgs/msg/string.hpp"
#include "std_msgs/msg/u_int16.hpp"

//#include "interface/Error.hpp"
using namespace std;

node_lidar_t node_lidar;

//#define ENCRYPTION_T

using std::placeholders::_1;

class MinimalSubscriber : public rclcpp::Node
{
  public:
    MinimalSubscriber()
    : Node("m1ct_d2")
    {
      subscription_ = this->create_subscription<std_msgs::msg::UInt16>(
      "lidar_status", 10, std::bind(&MinimalSubscriber::topic_callback, this, _1));
    }

  private:
    void topic_callback(const std_msgs::msg::UInt16::SharedPtr msg) const
    {
		switch (msg->data)
		{
			/*启动雷达*/
			case 1:
				node_lidar.lidar_status.lidar_ready = true;
				node_lidar.lidar_status.lidar_abnormal_state = 0;
				printf("#start lidar\n");
				break;
			/*关闭雷达*/
			case 2:
				node_lidar.lidar_status.lidar_ready = false;
				node_lidar.lidar_status.close_lidar = true;
				node_lidar.serial_port->write_data(end_lidar,4);
				printf("#stop lidar\n");
				break;
			/*high_exposure*/
			case 3:
				node_lidar.serial_port->write_data(high_exposure,4);
				break;
			/*low_exposure*/
			case 4:
				node_lidar.serial_port->write_data(low_exposure,4);
				break;
			/*清空异常状态*/
			case 5:
				node_lidar.lidar_status.lidar_abnormal_state = 0;
				break;
			/*高转速*/
			case 6:
				node_lidar.serial_port->write_data(high_speed,4);
				node_lidar.lidar_general_info.frequency_max = 103;
				node_lidar.lidar_general_info.frequency_min = 97;
				break;
			/*低转速*/
			case 7:
				node_lidar.serial_port->write_data(low_speed,4);
				node_lidar.lidar_general_info.frequency_max = 68;
				node_lidar.lidar_general_info.frequency_min = 52;
				break;
			
			default:
				break;
		}
     // RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg->data.c_str());
    }
    rclcpp::Subscription<std_msgs::msg::UInt16>::SharedPtr subscription_;
};

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
					printf("V2版本启动雷达\n");
					node_lidar.serial_port->write_data(start_lidar,4);
					wait_speed_right = true;
					break;
				
				case M1CT_Coin_D2:
					printf("D2版本启动雷达\n");
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
						if(local_scan[0].scan_frequence > node_lidar.lidar_general_info.frequency_max 
						    || local_scan[0].scan_frequence < node_lidar.lidar_general_info.frequency_min)
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
						node_lidar.lidar_time.scan_start_time = node_lidar.lidar_time.tim_scan_start;
						node_lidar.lidar_time.scan_end_time = node_lidar.lidar_time.tim_scan_end;
						if(node_lidar.lidar_time.tim_scan_start != node_lidar.lidar_time.tim_scan_end)
						{
							node_lidar.lidar_time.tim_scan_start = node_lidar.lidar_time.tim_scan_end;
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
int send_lidar_data(LaserScan &outscan)
{
	node_lidar._lock.lock();

	size_t count = node_lidar.scan_node_count;

	if(count < MAX_SCAN_NODES && count > 0)
	{	
		//node_lidar.lidar_time.tim_scan_end = getTime();
		uint64_t scan_time = (node_lidar.lidar_time.scan_end_time - node_lidar.lidar_time.scan_start_time);

		//node_lidar.lidar_time.tim_scan_start = node_lidar.lidar_time.tim_scan_end -  scan_time ;

		node_lidar.lidar_block.lidar_zero_count = 0;


		outscan.config.angle_increment = (2.0*M_PI/count);
		outscan.config.min_angle = 0;
		outscan.config.max_angle = 2*M_PI;
		outscan.config.min_range = 0.10;
		outscan.config.max_range = 10.0; //测量的最远距离是10m
		outscan.config.scan_time =  static_cast<float>(scan_time * 1.0 / 1e9);
    	outscan.config.time_increment = outscan.config.scan_time / (double)(count - 1);
		outscan.stamp = node_lidar.lidar_time.scan_start_time;
		std::cout << "scantime:" << outscan.config.scan_time << "stamp:" << outscan.stamp << std::endl;
		//scan_msg->header.frame_id = node_lidar.lidar_general_info.frame_id;
		//scan_msg->header.stamp = ros::Time::now();

		if(node_lidar.lidar_status.isConnected)
		{
			//outscan.points.clear();
			float range = 0;
			float angle = 0.0;
			uint16_t intensity = 0;
			for (int i = count-1; i > 0; i--)
			{
				LaserPoint point;
				LaserPoint point_check;
				angle = static_cast<float>((node_lidar.scan_node_buf[count -i].angle_q6_checkbit >>
											LIDAR_RESP_MEASUREMENT_ANGLE_SHIFT) /64.0f);
				range = (node_lidar.scan_node_buf[i].distance_q2/1000.0f);
				intensity = node_lidar.scan_node_buf[i].sync_quality;

				if(node_lidar.scan_node_buf[i].exp_m == 1)
				{
					intensity = 255;
				}else{
					if(intensity >= 255)
					{
						intensity = 254;
					}
				}

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

				if(range < 0.1)
				{
					node_lidar.lidar_block.lidar_zero_count++;
				}
				outscan.points.push_back(point);
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
	
	case M1CT_Coin_D2:
		printf("version M1CT_D2\n");
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

/*接收外部消息的回调函数*/
/*
void topic_callback(const std_msgs::msg::UInt16::SharedPtr msg)
{
	printf("topic back----\n");
	switch (msg->data)
	{
		/*启动雷达*/
		/*case 1:
			node_lidar.lidar_status.lidar_ready = true;
			printf("ready to start lidar------\n");
			break;*/
		/*关闭雷达*/
		/*case 2:
			node_lidar.lidar_status.lidar_ready = false;
			node_lidar.lidar_status.close_lidar = true;
			node_lidar.serial_port->write_data(end_lidar,4);
			break;*/
		/*异常信息的反馈*/
		/*case 3:
			node_lidar.lidar_status.lidar_abnormal_state = 0;
			break;*/
		/*
		default:
			break;
	}
}*/

int topic_thread()
{
	rclcpp::spin(std::make_shared<MinimalSubscriber>());
}

int node_start(int argc, char **argv)
{

	
	rclcpp::init(argc, argv);
	auto node = rclcpp::Node::make_shared("c1ct_d2");
	
	node->declare_parameter("port");
  	node->get_parameter("port", node_lidar.lidar_general_info.port);
	
	node->declare_parameter("baudrate");
  	node->get_parameter("baudrate", node_lidar.lidar_general_info.m_SerialBaudrate);

	node->declare_parameter("frame_id");
  	node->get_parameter("frame_id", node_lidar.lidar_general_info.frame_id);
	
	node->declare_parameter("version");
  	node->get_parameter("version", node_lidar.lidar_general_info.version);
	//std::string frame_id = "base_scan";
	rclcpp::Publisher<std_msgs::msg::String>::SharedPtr error_pub;
	error_pub = node->create_publisher<std_msgs::msg::String>("lsd_error", 10);
	std_msgs::msg::String pubdata;
	/*
	auto subscription_ = node->create_subscription<std_msgs::msg::UInt16>(
      "lidar_status", 10, topic_callback);*/
	
	
	bool ret_init = initialize();

	if(!ret_init){
		printf("node_lidar init error\n");
		pubdata.data="node_lidar init error\n";
		error_pub->publish(pubdata);
		while(rclcpp::ok())
		{
			error_pub->publish(pubdata);
			delay(3000);
		}
		
		return -1;
	}
	/*读取激光雷达数据的线程*/
	thread t1(read_forever);
	t1.detach();

	thread t2(topic_thread);
	t2.detach();

	/*处理雷达数据的线程*/
	/*
	thread t2(data_handling(node));
	t2.detach();*/
	
	node_lidar.lidar_status.lidar_ready = true;
	
	auto laser_pub = node->create_publisher<sensor_msgs::msg::LaserScan>("scan", 1);
	
	while(rclcpp::ok())
	{
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
		LaserScan scan;
		if(data_handling(scan))
		{
			auto scan_msg = std::make_shared<sensor_msgs::msg::LaserScan>();

			scan_msg->ranges.resize(scan.points.size());
			scan_msg->intensities.resize(scan.points.size());

			scan_msg->header.stamp.sec = RCL_NS_TO_S(scan.stamp);;
			scan_msg->header.stamp.nanosec = scan.stamp - RCL_S_TO_NS(scan_msg->header.stamp.sec);
			scan_msg->header.frame_id = node_lidar.lidar_general_info.frame_id;

			scan_msg->angle_min = scan.config.min_angle;
			scan_msg->angle_max = scan.config.max_angle;
			scan_msg->angle_increment = scan.config.angle_increment;
			scan_msg->scan_time = scan.config.scan_time;
			scan_msg->time_increment = scan.config.time_increment;
			scan_msg->range_min = scan.config.min_range;
			scan_msg->range_max = scan.config.max_range;
			for(int i=0; i < scan.points.size(); i++) {
				scan_msg->ranges[i] = scan.points[i].range;
				scan_msg->intensities[i] = scan.points[i].intensity;
			}
			//printf("publish--------\n");
			laser_pub->publish(*scan_msg);
      	}
	}
	node_lidar.serial_port->write_data(end_lidar,4);
	return 0;
}

```
## `m1ct_d2/src/mtime.cpp`

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
## `m1ct_d2/src/lidar_data_processing.cpp`

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
              if(node_lidar.lidar_time.tim_scan_start == 0)
              {
                node_lidar.lidar_time.tim_scan_start = getTime();
              }else{
                node_lidar.lidar_time.tim_scan_end = getTime();
              }
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
      (*node).exp_m = node_lidar.scan_packages.package.packageSampleDistance[package_Sample_Index*3] & 0x01;
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
## `m1ct_d2/src/main.cpp`

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

	//priv_nh.param("baud_rate", node_lidar.lidar_general_info.m_SerialBaudrate, 115200);
	//priv_nh.param("frame_id", node_lidar.lidar_general_info.frame_id, std::string("base_link"));
	//priv_nh.param("port", node_lidar.lidar_general_info.port, std::string("/dev/sc_mini"));
	//priv_nh.param("version", node_lidar.lidar_general_info.version,4);
	node_lidar.lidar_general_info.version = 4;
	//node_lidar.laser_pub = n.advertise<sensor_msgs::LaserScan>("scan", 1);
	
	parse_args(argc, argv);

	node_start(argc, argv);
}                                                                                                           
```

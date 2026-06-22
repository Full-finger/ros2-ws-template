# 硬件清单与接线

> 本文档是示例模板（本仓库无真实硬件）。实际项目请替换为你的真实清单。

## 机型概览

| 项 | 值 |
|----|----|
| 底盘形式 | 差速驱动（两轮 + 万向轮） |
| 控制板 | 主控 PC + 下位机 MCU（串口通信） |
| 传感器 | 激光雷达、IMU、（可选）深度相机 |
| 供电 | 锂电池组，经 DC-DC 分压给各模块 |

## 部件清单

| 部件 | 型号 | 数量 | 接口 | 备注 |
|------|------|------|------|------|
| 主控 PC | x86 单板机 / NUC | 1 | — | 跑 ROS2 |
| 下位机 MCU | STM32F4 | 1 | USB-TTL 串口 | 读编码器/驱动电机 |
| 驱动电机 | 带编码器直流减速电机 | 2 | → MCU | 左右各一 |
| 激光雷达 | 2D LiDAR | 1 | USB / 以太网 | 发布 `/scan` |
| IMU | 6 轴 | 1 | I²C / 串口 | 融合到 odom |
| 电池 | 锂电池组 | 1 | — | 经过分压板 |

## 接线约定

```
  电池 ── DC-DC 分压板 ──┬── 主控 PC（12V）
                         ├── MCU（5V/3.3V）
                         └── 电机驱动（电机电压）

  MCU ──USB-TTL── 主控PC (/dev/ttyUSB0)   ← robot_hardware 的 serial_port
  LiDAR ──USB── 主控PC                    ← 发布 /scan
  IMU ──串口/I²C── MCU 或 主控PC
```

## 串口权限

```bash
sudo usermod -aG dialout $USER      # 加用户到 dialout 组，免 sudo 访问 /dev/ttyUSB*
# 重新登录生效
ls -l /dev/ttyUSB*                  # 确认组属主
```

`robot_hardware` 默认 `serial_port: "/dev/ttyUSB0"`，可在 `config/params.yaml` 或 `robot_bringup/config/system.yaml` 覆盖。

## 关键参数对照（机械尺寸）

> 这些值必须和实物一致，直接影响 `robot_hardware` 的里程计精度。

| 参数 | 默认值 | 测量方法 |
|------|--------|----------|
| `wheel_radius` | 0.05 m | 卡尺测轮缘外径 ÷ 2 |
| `wheel_base` | 0.3 m | 左右两轮接地中心距 |

改完实物，**同步改** `src/robot_hardware/config/params.yaml` 和 `plugin.yaml` 的 `default`，并跑里程计标定（推直线、原地转圈验证）。

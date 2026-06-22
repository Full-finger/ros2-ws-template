# 机器人整体状态
uint8 MODE_IDLE      = 0
uint8 MODE_MANUAL    = 1
uint8 MODE_AUTO      = 2
uint8 MODE_EMERGENCY = 3

uint8   mode             # 当前工作模式
float32 battery          # 电量百分比 0~100
uint32  error_code       # 错误码位图，0 表示无故障
builtin_interfaces/Time stamp

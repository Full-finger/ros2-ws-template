// ═══════════════════════════════════════════════════════════
//  Model 层：感知包的纯 C++ 数据结构（零 ROS2 依赖）
// ═══════════════════════════════════════════════════════════
#pragma once

#include <vector>

namespace robot_perception::model {

/// 单个激光点（极坐标）
struct LaserPoint {
    double range = 0.0;
    double angle = 0.0;
};

/// 聚类后的障碍物（笛卡尔）
struct ObstacleProto {
    double x = 0.0;
    double y = 0.0;
    double radius = 0.0;   // 包络半径
    int count = 0;         // 格内点数
};

/// 运行时配置
struct Config {
    double max_range = 5.0;     // m，超过则丢弃
    double min_range = 0.05;    // m，小于则丢弃（噪点）
    double cell_size = 0.2;     // m，网格聚类边长
    int min_points = 1;         // 格内至少多少点才算障碍物
    double update_rate = 10.0;  // Hz（限频）
};

}  // namespace robot_perception::model

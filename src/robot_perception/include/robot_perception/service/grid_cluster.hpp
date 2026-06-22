// ═══════════════════════════════════════════════════════════
//  Service 层：网格聚类（纯逻辑，零 ROS2 依赖）
//
//  算法（两遍遍历）：
//   1. 把有效激光点按 cell_size 量化到二维网格，统计每格点数与坐标和
//   2. 计算每格中心；第二遍遍历点，累计每格到中心的最大距离作为半径
//   3. 点数 >= min_points 的格输出为障碍物
// ═══════════════════════════════════════════════════════════
#pragma once

#include <cmath>
#include <unordered_map>
#include <vector>

#include "robot_common/math_utils.hpp"
#include "robot_perception/model/types.hpp"

namespace robot_perception::service {

class GridClusterService {
public:
    explicit GridClusterService(const model::Config &config)
        : config_(config) {}

    std::vector<model::ObstacleProto>
    cluster(const std::vector<model::LaserPoint> &points) const {
        struct CellStat {
            double sum_x = 0.0;
            double sum_y = 0.0;
            int count = 0;
        };

        std::unordered_map<long long, CellStat> grid;
        const double inv_cell = 1.0 / config_.cell_size;

        const auto cell_key = [&](double x, double y) {
            const auto gx = static_cast<long long>(std::floor(x * inv_cell));
            const auto gy = static_cast<long long>(std::floor(y * inv_cell));
            return (gx + 100000) * 200001LL + (gy + 100000);
        };

        const auto is_valid = [&](double range) {
            return robot_common::math::deadzone(range, config_.min_range) != 0.0
                && range <= config_.max_range;
        };

        // 第一遍：统计
        for (const auto &p : points) {
            if (!is_valid(p.range)) continue;
            const double x = p.range * std::cos(p.angle);
            const double y = p.range * std::sin(p.angle);
            auto &cell = grid[cell_key(x, y)];
            cell.sum_x += x;
            cell.sum_y += y;
            cell.count += 1;
        }

        // 计算各格中心（把 sum 转为中心）
        std::unordered_map<long long, std::pair<double, double>> center;
        for (auto &[key, cell] : grid) {
            center[key] = {cell.sum_x / cell.count, cell.sum_y / cell.count};
        }

        // 第二遍：累计到中心的最大距离
        std::unordered_map<long long, double> max_dist2;
        for (const auto &p : points) {
            if (!is_valid(p.range)) continue;
            const double x = p.range * std::cos(p.angle);
            const double y = p.range * std::sin(p.angle);
            const auto key = cell_key(x, y);
            const auto &c = center[key];
            const double dx = x - c.first;
            const double dy = y - c.second;
            const double d2 = dx * dx + dy * dy;
            if (d2 > max_dist2[key]) max_dist2[key] = d2;
        }

        // 输出
        std::vector<model::ObstacleProto> obstacles;
        for (const auto &[key, cell] : grid) {
            if (cell.count < config_.min_points) continue;
            const auto &c = center[key];
            model::ObstacleProto obs;
            obs.x = c.first;
            obs.y = c.second;
            obs.radius = std::sqrt(max_dist2[key]) + config_.cell_size * 0.5;
            obs.count = cell.count;
            obstacles.push_back(obs);
        }
        return obstacles;
    }

    void update_config(const model::Config &config) { config_ = config; }
    [[nodiscard]] const model::Config &config() const { return config_; }

private:
    model::Config config_;
};

}  // namespace robot_perception::service

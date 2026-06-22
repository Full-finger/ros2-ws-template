// ═══ 网格聚类测试（纯逻辑） ═══
#include <gtest/gtest.h>

#include "robot_perception/model/types.hpp"
#include "robot_perception/service/grid_cluster.hpp"

using robot_perception::model::Config;
using robot_perception::model::LaserPoint;
using robot_perception::model::ObstacleProto;
using robot_perception::service::GridClusterService;

class GridClusterTest : public ::testing::Test {
protected:
    void SetUp() override {
        Config config;
        config.max_range = 5.0;
        config.min_range = 0.05;
        config.cell_size = 0.2;
        config.min_points = 1;
        svc_ = std::make_unique<GridClusterService>(config);
    }
    std::unique_ptr<GridClusterService> svc_;
};

TEST_F(GridClusterTest, EmptyInputReturnsEmpty) {
    auto result = svc_->cluster({});
    EXPECT_TRUE(result.empty());
}

TEST_F(GridClusterTest, NearPointsClusterTogether) {
    // 同方向、近距离的两个点应聚到同一障碍物
    LaserPoint p1{.range = 1.0, .angle = 0.0};       // (1.0, 0.0)
    LaserPoint p2{.range = 1.0, .angle = 0.05};      // ≈ (0.999, 0.05)
    auto result = svc_->cluster({p1, p2});
    ASSERT_EQ(result.size(), 1u);
    EXPECT_EQ(result[0].count, 2);
    EXPECT_NEAR(result[0].x, 1.0, 0.15);
    EXPECT_NEAR(result[0].y, 0.025, 0.15);
}

TEST_F(GridClusterTest, FarPointsClusterSeparately) {
    // 正前方 1m 和正左方 1m，相距够远，应分成两个障碍物
    LaserPoint p1{.range = 1.0, .angle = 0.0};        // (1, 0)
    LaserPoint p2{.range = 1.0, .angle = M_PI / 2};   // (0, 1)
    auto result = svc_->cluster({p1, p2});
    EXPECT_EQ(result.size(), 2u);
}

TEST_F(GridClusterTest, OutOfRangePointsDropped) {
    LaserPoint too_far{.range = 10.0, .angle = 0.0};   // 超 max_range
    LaserPoint too_close{.range = 0.01, .angle = 0.0}; // 小于 min_range 死区
    auto result = svc_->cluster({too_far, too_close});
    EXPECT_TRUE(result.empty());
}

TEST_F(GridClusterTest, MinPointsFilter) {
    Config config;
    config.cell_size = 0.2;
    config.min_points = 3;  // 至少 3 点
    GridClusterService svc(config);

    LaserPoint p{.range = 1.0, .angle = 0.0};
    auto result = svc.cluster({p, p});  // 只有 2 点（同位置算 2 点）
    EXPECT_TRUE(result.empty());        // 不满足 min_points=3
}

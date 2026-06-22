// ═══ 差速驱动运动学测试（纯逻辑，不依赖 ROS2） ═══
#include <gtest/gtest.h>
#include <limits>

#include "robot_hardware/model/types.hpp"
#include "robot_hardware/service/differential_drive.hpp"

using robot_hardware::model::Config;
using robot_hardware::model::MotorReading;
using robot_hardware::model::OdometryData;
using robot_hardware::service::DifferentialDriveService;

class DifferentialDriveTest : public ::testing::Test {
protected:
    void SetUp() override {
        Config config;
        config.wheel_radius = 1.0;  // 测试取 1.0，让轮速(rad/s)与线速度(m/s)数值相等，便于读期望值
        config.wheel_base = 0.3;
        config.update_rate = 50.0;
        svc_ = std::make_unique<DifferentialDriveService>(config);
    }
    std::unique_ptr<DifferentialDriveService> svc_;
    const double dt = 0.02;  // 50 Hz
};

TEST_F(DifferentialDriveTest, StraightLineMovesForward) {
    MotorReading reading{.left_wheel_speed = 1.0, .right_wheel_speed = 1.0, .timestamp = 0.0};
    OdometryData odom = svc_->update_odometry(reading, dt);

    EXPECT_NEAR(odom.linear_velocity, 1.0, 1e-9);
    EXPECT_NEAR(odom.angular_velocity, 0.0, 1e-9);
    EXPECT_GT(odom.x, 0.0);
    EXPECT_NEAR(odom.y, 0.0, 1e-9);
    EXPECT_NEAR(odom.theta, 0.0, 1e-9);
}

TEST_F(DifferentialDriveTest, InPlaceRotation) {
    // 左轮后退、右轮前进，原地右转
    MotorReading reading{.left_wheel_speed = -0.5, .right_wheel_speed = 0.5, .timestamp = 0.0};
    OdometryData odom = svc_->update_odometry(reading, dt);

    EXPECT_NEAR(odom.linear_velocity, 0.0, 1e-9);
    EXPECT_NEAR(odom.angular_velocity, (0.5 - (-0.5)) / 0.3, 1e-9);  // w = 1/0.3
    EXPECT_NEAR(odom.x, 0.0, 1e-9);
    EXPECT_NEAR(odom.y, 0.0, 1e-9);
    EXPECT_GT(odom.theta, 0.0);
}

TEST_F(DifferentialDriveTest, WheelRadiusScalesLinearVelocity) {
    // wheel_radius=0.5 时，轮速 2.0 rad/s → 线速度 1.0 m/s
    Config config;
    config.wheel_radius = 0.5;
    config.wheel_base = 0.3;
    DifferentialDriveService svc(config);
    MotorReading reading{.left_wheel_speed = 2.0, .right_wheel_speed = 2.0, .timestamp = 0.0};
    OdometryData odom = svc.update_odometry(reading, dt);
    EXPECT_NEAR(odom.linear_velocity, 1.0, 1e-9);  // 2.0 * 0.5
}

TEST_F(DifferentialDriveTest, ContinuousIntegration) {
    MotorReading reading{.left_wheel_speed = 1.0, .right_wheel_speed = 1.0, .timestamp = 0.0};
    double prev_x = 0.0;
    for (int i = 0; i < 10; ++i) {
        reading.timestamp = i * dt;
        OdometryData odom = svc_->update_odometry(reading, dt);
        EXPECT_GT(odom.x, prev_x);  // x 单调递增
        prev_x = odom.x;
    }
}

TEST_F(DifferentialDriveTest, NanReadingThrows) {
    MotorReading reading{.left_wheel_speed = 0.0,
                         .right_wheel_speed = std::numeric_limits<double>::quiet_NaN(),
                         .timestamp = 0.0};
    EXPECT_THROW(svc_->update_odometry(reading, dt), robot_hardware::model::SensorReadError);
}

TEST_F(DifferentialDriveTest, NonPositiveDtThrows) {
    MotorReading reading{.left_wheel_speed = 1.0, .right_wheel_speed = 1.0, .timestamp = 0.0};
    EXPECT_THROW(svc_->update_odometry(reading, 0.0), robot_hardware::model::SensorReadError);
    EXPECT_THROW(svc_->update_odometry(reading, -0.1), robot_hardware::model::SensorReadError);
}

TEST_F(DifferentialDriveTest, Reset) {
    MotorReading reading{.left_wheel_speed = 1.0, .right_wheel_speed = 1.0, .timestamp = 0.0};
    svc_->update_odometry(reading, dt);
    svc_->reset();
    OdometryData odom = svc_->odom();
    EXPECT_DOUBLE_EQ(odom.x, 0.0);
    EXPECT_DOUBLE_EQ(odom.y, 0.0);
}

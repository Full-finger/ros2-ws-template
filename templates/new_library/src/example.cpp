#include "__PACKAGE_NAME__/example.hpp"

#include <cmath>

namespace __PACKAGE_NAME__ {

Deadzone::Deadzone(double threshold) : threshold_(threshold) {}

double Deadzone::apply(double value) const {
    if (std::abs(value) < threshold_) {
        return 0.0;
    }
    return value;
}

}  // namespace __PACKAGE_NAME__

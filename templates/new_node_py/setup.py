from setuptools import find_packages, setup

PACKAGE_NAME = "__PACKAGE_NAME__"

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, ["package.xml"]),
        ("share/" + PACKAGE_NAME + "/launch",
         ["launch/__PACKAGE_NAME__.launch.py"]),
        ("share/" + PACKAGE_NAME + "/config",
         ["config/params.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="TODO@todo.todo",
    description="TODO: 一句话描述这个包的功能",
    license="TODO: 例如 MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            # controller 层是唯一接触 rclpy 的入口
            "main_node = __PACKAGE_NAME__.controller.main_node:main",
        ],
    },
)

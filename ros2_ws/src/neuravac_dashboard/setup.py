from glob import glob

from setuptools import setup

package_name = "neuravac_dashboard"
setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    tests_require=["pytest"],
    maintainer="NeuraVac contributors",
    maintainer_email="maintainers@example.invalid",
    description="Connected ROS 2 Jazzy semantic vacuum adapter",
    license="Apache-2.0",
    entry_points={"console_scripts": ["dashboard_node = neuravac_dashboard.node:main"]},
)

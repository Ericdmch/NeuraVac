from setuptools import find_packages, setup

package_name = "neuravac_ros"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=("tests",)),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/neuravac_ros"]),
        ("share/neuravac_ros", ["package.xml"]),
        ("share/neuravac_ros", ["config.json"]),
        ("share/neuravac_ros/launch", ["launch/neuravac.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={"console_scripts": ["roomba_bridge = neuravac_ros.bridge_node:main"]},
)

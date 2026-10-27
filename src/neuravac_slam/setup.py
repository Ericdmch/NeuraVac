from setuptools import find_packages, setup

package_name = 'neuravac_slam'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='neuravac',
    maintainer_email='williamhuang.eng@gmail.com',
    description='Fused Roomba odometry and LiDAR occupancy mapper.',
    entry_points={'console_scripts': ['neuravac_slam_node = neuravac_slam.slam_node:main']},
)

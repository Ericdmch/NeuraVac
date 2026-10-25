from setuptools import find_packages, setup


package_name = 'vision'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='neuravac',
    maintainer_email='williamhuang.eng@gmail.com',
    description='ROS 2 camera and floor-object detection node for NeuraVac.',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'vision_node = vision.vision_node:main',
        ],
    },
)

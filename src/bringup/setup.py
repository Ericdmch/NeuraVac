from glob import glob

from setuptools import find_packages, setup

package_name = 'bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['tests']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='neuravac',
    maintainer_email='williamhuang.eng@gmail.com',
    description='Launch file and USB device setup for the full NeuraVac robot.',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'neuravac_udev_setup = bringup.udev_setup:main',
        ],
    },
)

from setuptools import find_packages, setup

package_name = 'web'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/templates',
            ['web/templates/index.html']),
        ('share/' + package_name + '/static',
            ['web/static/style.css', 'web/static/serial.js']),
    ],
    install_requires=['setuptools', 'Flask', 'pyserial'],
    zip_safe=True,
    maintainer='neuravac',
    maintainer_email='williamhuang.eng@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'web_node = web.web_node:main',
        ],
    },
)

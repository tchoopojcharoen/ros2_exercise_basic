from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'turtlesim_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
         (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pi31415',
    maintainer_email='pi31415@example.com',
    description='Turtlesim controller package',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'go_to_goal_controller = turtlesim_controller.go_to_goal:main',
        ],
    },
)
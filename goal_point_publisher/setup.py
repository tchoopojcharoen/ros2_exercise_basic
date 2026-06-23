from setuptools import find_packages, setup

package_name = 'goal_point_publisher'

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
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pi31415',
    maintainer_email='pi31415@example.com',
    description='GUI node for publishing goal points to a ROS 2 topic',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'goal_point_publisher = goal_point_publisher.goal_point_publisher_node:main',
        ],
    },
)

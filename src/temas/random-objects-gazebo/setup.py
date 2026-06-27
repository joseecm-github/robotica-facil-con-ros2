import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'random_objects_gazebo'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='José Enrique Cabrera',
    maintainer_email='contacto@robotica-facil-con-ros2.es',
    description='Spawn random objects in Gazebo Jetty from a ROS 2 node.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'spawn_objects_node = random_objects_gazebo.spawn_objects_node:main',
        ],
    },
)

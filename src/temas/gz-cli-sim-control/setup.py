import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'gz_cli_sim_control'

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
    description='Demo de la CLI de Gazebo Jetty (gz sim/service/topic) controlando una simulación desde ROS 2.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'gz_cli_demo = gz_cli_sim_control.gz_cli_demo:main',
        ],
    },
)

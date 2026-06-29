from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Render engine. 'ogre2' (default) is the standard on Ubuntu with a GPU.
    # On WSL2 or without graphics acceleration, 'ogre' (Ogre 1.x) is much lighter.
    render_engine_arg = DeclareLaunchArgument('render_engine', default_value='ogre2',
                                              description="Gazebo render engine ('ogre2' or 'ogre')")

    package_share = FindPackageShare('instalacion_gazebo_jetty')
    world_path = PathJoinSubstitution([package_share, 'worlds', 'empty_world.sdf'])

    # ros_gz_sim ships a reusable launch file that starts Gazebo; we only pass it
    # the world to load and the render engine to use.
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            ])
        ),
        # -r: start the simulation right away; --render-engine: pick the render engine
        launch_arguments={'gz_args': [
            '-r --render-engine ', LaunchConfiguration('render_engine'), ' ', world_path,
        ]}.items(),
    )

    return LaunchDescription([
        render_engine_arg,
        gazebo,
    ])

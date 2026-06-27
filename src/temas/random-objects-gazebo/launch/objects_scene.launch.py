from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    max_radius_arg = DeclareLaunchArgument('max_radius', default_value='4.0',
                                           description='Maximum distance from the origin to place objects (m)')
    min_separation_arg = DeclareLaunchArgument('min_separation', default_value='1.2',
                                               description='Minimum distance between objects (m)')
    seed_arg = DeclareLaunchArgument('seed', default_value='0',
                                     description='Random seed (0 = different on every run)')
    spawn_delay_arg = DeclareLaunchArgument('spawn_delay', default_value='0.8',
                                            description='Pause between object spawns (s)')
    # Render engine. 'ogre2' (default) is the standard on Ubuntu with a GPU.
    # On WSL2 or without graphics acceleration, 'ogre' (Ogre 1.x) is much lighter.
    render_engine_arg = DeclareLaunchArgument('render_engine', default_value='ogre2',
                                              description="Gazebo render engine ('ogre2' or 'ogre')")

    package_share = FindPackageShare('random_objects_gazebo')
    world_path = PathJoinSubstitution([package_share, 'worlds', 'objects_scene.sdf'])

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

    spawn_node = Node(
        package='random_objects_gazebo',
        executable='spawn_objects_node',
        parameters=[{
            'world': 'objects_scene',
            'max_radius': LaunchConfiguration('max_radius'),
            'min_separation': LaunchConfiguration('min_separation'),
            'seed': LaunchConfiguration('seed'),
            'spawn_delay': LaunchConfiguration('spawn_delay'),
        }],
        output='screen',
    )

    return LaunchDescription([
        max_radius_arg,
        min_separation_arg,
        seed_arg,
        spawn_delay_arg,
        render_engine_arg,
        gazebo,
        spawn_node,
    ])

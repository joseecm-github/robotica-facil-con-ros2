from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    step_delay_arg = DeclareLaunchArgument('step_delay', default_value='3.0',
                                           description='Pause between demo steps, in seconds')
    real_time_factor_arg = DeclareLaunchArgument('real_time_factor', default_value='2.0',
                                                 description='Real-time factor set in step 4 of the demo')
    # Render engine. 'ogre2' (default) is the standard on Ubuntu with a GPU.
    # On WSL2 or without graphics acceleration, 'ogre' (Ogre 1.x) is much lighter.
    render_engine_arg = DeclareLaunchArgument('render_engine', default_value='ogre2',
                                              description="Gazebo render engine ('ogre2' or 'ogre')")

    package_share = FindPackageShare('gz_cli_sim_control')
    world_path = PathJoinSubstitution([package_share, 'worlds', 'cli_demo_world.sdf'])

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

    demo_node = Node(
        package='gz_cli_sim_control',
        executable='gz_cli_demo',
        parameters=[{
            'world': 'cli_demo_world',
            'step_delay': LaunchConfiguration('step_delay'),
            'real_time_factor': LaunchConfiguration('real_time_factor'),
        }],
        output='screen',
    )

    return LaunchDescription([
        step_delay_arg,
        real_time_factor_arg,
        render_engine_arg,
        gazebo,
        demo_node,
    ])

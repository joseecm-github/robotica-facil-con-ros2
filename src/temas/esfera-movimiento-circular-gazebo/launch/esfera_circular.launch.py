from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    radio_arg = DeclareLaunchArgument('radio', default_value='2.0',
                                      description='Radio de la trayectoria circular (m)')
    velocidad_base_arg = DeclareLaunchArgument('velocidad_base', default_value='0.7',
                                               description='Velocidad lineal media (m/s)')
    amplitud_arg = DeclareLaunchArgument('amplitud_velocidad', default_value='0.35',
                                         description='Amplitud de la oscilación de velocidad (m/s)')
    periodo_arg = DeclareLaunchArgument('periodo_velocidad', default_value='10.0',
                                        description='Periodo de la oscilación sinusoidal (s)')
    frecuencia_arg = DeclareLaunchArgument('frecuencia_publicacion', default_value='30.0',
                                           description='Frecuencia de publicación del nodo (Hz)')
    # Motor de render. 'ogre2' (por defecto) es el estándar en Ubuntu con GPU.
    # En WSL2 o sin aceleración gráfica, 'ogre' (Ogre 1.x) es mucho más ligero y
    # evita que el render por software ahogue la física. Ver README, sección WSL2.
    render_engine_arg = DeclareLaunchArgument('render_engine', default_value='ogre2',
                                              description="Motor de render de Gazebo ('ogre2' o 'ogre')")

    paquete_share = FindPackageShare('esfera_circular_gazebo')
    ruta_mundo = PathJoinSubstitution([paquete_share, 'worlds', 'esfera_circular.sdf'])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            ])
        ),
        # -r: arranca la simulación automáticamente sin pulsar Play
        # --render-engine: elige el motor de render (ver render_engine_arg)
        launch_arguments={'gz_args': [
            '-r --render-engine ', LaunchConfiguration('render_engine'), ' ', ruta_mundo,
        ]}.items(),
    )

    # Puente bidireccional: ROS 2 geometry_msgs/Twist ↔ Gazebo gz.msgs.Twist
    puente = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/model/esfera_circular/cmd_vel'
            '@geometry_msgs/msg/Twist'
            '@gz.msgs.Twist',
        ],
        output='screen',
    )

    nodo_velocidad = Node(
        package='esfera_circular_gazebo',
        executable='nodo_velocidad_circular',
        parameters=[{
            'radio': LaunchConfiguration('radio'),
            'velocidad_base': LaunchConfiguration('velocidad_base'),
            'amplitud_velocidad': LaunchConfiguration('amplitud_velocidad'),
            'periodo_velocidad': LaunchConfiguration('periodo_velocidad'),
            'frecuencia_publicacion': LaunchConfiguration('frecuencia_publicacion'),
        }],
        output='screen',
    )

    return LaunchDescription([
        radio_arg,
        velocidad_base_arg,
        amplitud_arg,
        periodo_arg,
        frecuencia_arg,
        render_engine_arg,
        gazebo,
        puente,
        nodo_velocidad,
    ])

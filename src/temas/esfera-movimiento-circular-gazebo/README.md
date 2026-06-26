# esfera_circular_gazebo

Paquete ROS 2 que simula una esfera sobre un plano horizontal en Gazebo Jetty. La esfera sigue una trayectoria circular con velocidad variable, controlada desde un nodo ROS 2 mediante mensajes `geometry_msgs/msg/Twist`.

## Plataforma de referencia

- **ROS 2:** Lyrical Luth (LTS, mayo 2026)
- **Gazebo:** Jetty (pareja oficial de Lyrical Luth según REP-2000)
- **Sistema operativo:** Ubuntu Resolute 26.04

> Compilado y verificado sobre ROS 2 Lyrical Luth + Gazebo Jetty (Ubuntu Resolute 26.04).

## Qué hace este paquete

1. Carga un mundo Gazebo con un **plano horizontal** y una **esfera azul** apoyada sobre él.
2. Un **nodo ROS 2** (`nodo_velocidad_circular`) calcula en cada tick la velocidad lineal y angular necesarias para mantener una trayectoria circular, variando la velocidad con una función sinusoidal.
3. Un **puente** (`ros_gz_bridge`) traduce los mensajes `Twist` de ROS 2 al formato nativo de Gazebo.
4. Gazebo aplica la velocidad al modelo `esfera_circular` a través del plugin `VelocityControl`.

### Fórmula de movimiento circular

```
velocidad_angular = velocidad_lineal / radio
velocidad(t) = velocidad_base + amplitud * sin(2π * t / periodo)
```

Si la velocidad lineal varía pero se divide siempre por el mismo radio, la trayectoria sigue siendo circular.

## Estructura del paquete

```
esfera-movimiento-circular-gazebo/
├── esfera_circular_gazebo/
│   ├── __init__.py
│   └── nodo_velocidad_circular.py   ← nodo que calcula y publica Twist
├── launch/
│   └── esfera_circular.launch.py    ← lanza Gazebo + puente + nodo
├── worlds/
│   └── esfera_circular.sdf          ← mundo con suelo y esfera
├── resource/
│   └── esfera_circular_gazebo       ← marcador ament_index
├── package.xml
├── setup.py
└── setup.cfg
```

## Compilar

Desde la raíz del workspace (`ros2_ws`):

```bash
colcon build --packages-select esfera_circular_gazebo
source install/setup.bash
```

## Ejecutar

```bash
ros2 launch esfera_circular_gazebo esfera_circular.launch.py
```

### Parámetros configurables

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `radio` | `2.0` m | Radio de la trayectoria circular |
| `velocidad_base` | `0.7` m/s | Velocidad lineal media |
| `amplitud_velocidad` | `0.35` m/s | Amplitud de la oscilación |
| `periodo_velocidad` | `10.0` s | Periodo de la oscilación sinusoidal |
| `frecuencia_publicacion` | `30.0` Hz | Frecuencia de publicación del nodo |

Ejemplo con radio mayor y velocidad más alta:

```bash
ros2 launch esfera_circular_gazebo esfera_circular.launch.py \
  radio:=3.0 velocidad_base:=1.0 amplitud_velocidad:=0.5
```

## Resultado esperado

Al lanzar el ejemplo se abre Gazebo con una escena simple. La esfera azul, apoyada sobre el plano gris, comienza a trazar círculos. La velocidad sube y baja suavemente cada `periodo_velocidad` segundos. Se puede verificar el topic en otra terminal:

```bash
ros2 topic echo /model/esfera_circular/cmd_vel
```

## Dependencias

- `rclpy`
- `geometry_msgs`
- `ros_gz_sim` (`ros-lyrical-ros-gz-sim`)
- `ros_gz_bridge` (`ros-lyrical-ros-gz-bridge`)

Instalación de los paquetes de integración si no están presentes:

```bash
sudo apt install ros-lyrical-ros-gz-sim ros-lyrical-ros-gz-bridge
```

# instalacion_gazebo_jetty

Paquete de **primer contacto** con Gazebo: un **mundo vacío** mínimo (`empty_world.sdf`) y un **launch file** que lo abre desde ROS 2. Sirve para comprobar que tu instalación de **Gazebo Jetty** sobre **ROS 2 Lyrical Luth** funciona y para tener un punto de partida limpio sobre el que añadir tus propios modelos.

## Plataforma de referencia

- **ROS 2:** Lyrical Luth (LTS, mayo 2026)
- **Gazebo:** Jetty (gz-sim 10)
- **Sistema operativo:** Ubuntu Resolute 26.04

> Compilado con `colcon build` y **ejecutado con la GUI de Gazebo abierta** sobre ROS 2 Lyrical Luth + Gazebo Jetty (gz-sim 10.4.0), en Ubuntu 26.04 bajo WSLg. Ver la sección "GUI en WSL2 (WSLg)" para la variable de entorno necesaria en WSL.

## Qué hay en este paquete

1. `worlds/empty_world.sdf`: el **mundo más pequeño que abre correctamente** en Gazebo Jetty. Lleva solo lo imprescindible:
   - los tres sistemas básicos (`Physics`, `UserCommands`, `SceneBroadcaster`),
   - una luz direccional (sin ella la escena se ve negra),
   - un plano de suelo.
2. `launch/empty_world.launch.py`: arranca Gazebo cargando ese mundo, reutilizando el launch `gz_sim.launch.py` que aporta `ros_gz_sim`.

### Por qué un mundo necesita esos tres sistemas

En Gazebo Jetty (gz-sim) casi nada está activo por defecto: cada capacidad la aporta un *system* (plugin) que se declara en el `.sdf`.

- **`Physics`**: integra la simulación (sin él, el mundo está congelado).
- **`UserCommands`**: expone los servicios `/world/<mundo>/create`, `set_pose`, `remove`… (crear y mover entidades en caliente).
- **`SceneBroadcaster`**: publica la escena para que la GUI pueda dibujarla.

Es el conjunto mínimo: a partir de aquí, añadir modelos es cuestión de sumar bloques `<model>`.

## Estructura del paquete

```
instalacion-gazebo-jetty/
├── instalacion_gazebo_jetty/
│   └── __init__.py
├── launch/
│   └── empty_world.launch.py   ← abre Gazebo con el mundo vacío
├── worlds/
│   └── empty_world.sdf         ← mundo mínimo (suelo + luz + 3 sistemas)
├── resource/instalacion_gazebo_jetty
├── package.xml
├── setup.py
└── setup.cfg
```

## Compilar

Desde la raíz del workspace (`ros2_ws`):

```bash
colcon build --packages-select instalacion_gazebo_jetty
source install/setup.bash
```

## Ejecutar

```bash
ros2 launch instalacion_gazebo_jetty empty_world.launch.py
```

Debería abrirse la ventana de Gazebo con un plano de suelo gris y nada más.

> En WSL2, exporta antes `QT_QPA_PLATFORM=xcb` (ver "GUI en WSL2 (WSLg)").

### Parámetros configurables

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `render_engine` | `ogre2` | Motor de render de Gazebo (`ogre2` o `ogre`) |

## GUI en WSL2 (WSLg)

En WSL2 con WSLg, la única variable necesaria para que la GUI de Gazebo abra es forzar a
Qt a usar X11 en vez de Wayland:

```bash
export QT_QPA_PLATFORM=xcb
ros2 launch instalacion_gazebo_jetty empty_world.launch.py
```

- `QT_QPA_PLATFORM=xcb` es la clave: en WSLg conviven `DISPLAY` (X11) y `WAYLAND_DISPLAY`;
  si Qt elige Wayland, el visor 3D de Ogre no encuentra el contexto OpenGL que espera
  (error "no current GL context" en `OgreGLXWindow`) y el cliente GUI revienta con un
  *segmentation fault*. Conviene dejar este `export` fijo en tu `~/.bashrc`.
- **No fuerces el render por software** (`LIBGL_ALWAYS_SOFTWARE=1`): con WSLg, la
  aceleración por GPU funciona y forzar software puede dejar la ventana sin pintar. Úsalo
  solo como último recurso si `ogre2` te da problemas, y entonces combínalo con
  `render_engine:=ogre`.
- Si tras varias pruebas la GUI deja de abrir (estado de OpenGL corrupto en WSLg),
  **reinicia WSL** (`wsl --shutdown` desde PowerShell) o el equipo: suele restaurarlo.
- En un equipo con GPU y aceleración nativa (no WSL), nada de esto hace falta: basta
  `ros2 launch instalacion_gazebo_jetty empty_world.launch.py` con `ogre2` por defecto.

### Motor de render ligero

Si el rendimiento es bajo, puedes usar Ogre 1.x (más ligero que el `ogre2` por defecto):

```bash
ros2 launch instalacion_gazebo_jetty empty_world.launch.py render_engine:=ogre
```

## Abrir el mundo sin ROS 2 (solo Gazebo)

Como es un `.sdf` normal, también puedes abrirlo directamente con el binario `gz`:

```bash
gz sim -r --render-engine ogre worlds/empty_world.sdf
```

## Dependencias

- `ros_gz_sim` (`ros-lyrical-ros-gz-sim`): aporta `gz_sim.launch.py`.

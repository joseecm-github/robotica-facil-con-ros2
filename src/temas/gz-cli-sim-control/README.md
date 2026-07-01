# gz_cli_sim_control

Paquete de demostración de la **línea de comandos de Gazebo** (`gz`): un **mundo** con una
esfera que cae bajo gravedad (`cli_demo_world.sdf`), un **launch file** que lo abre, y un
**nodo ROS 2** (`gz_cli_demo`) que automatiza, mediante los comandos `gz service` y
`gz topic`, la secuencia pausar → reanudar → cambiar velocidad → consultar información del
mundo sobre la simulación en marcha.

## Plataforma de referencia

- **ROS 2:** Lyrical Luth (LTS, mayo 2026)
- **Gazebo:** Jetty (gz-sim 10)
- **Sistema operativo:** Ubuntu Resolute 26.04

## Qué hay en este paquete

1. `worlds/cli_demo_world.sdf`: mundo mínimo (suelo + luz + los tres sistemas básicos:
   `Physics`, `UserCommands`, `SceneBroadcaster`) más un modelo `falling_ball` — una esfera
   dinámica soltada a 5 m de altura. No es un capricho decorativo: pausar, reanudar o
   cambiar la velocidad de una simulación **vacía** no se nota a simple vista; con la
   esfera cayendo, cada operación tiene un efecto visible en la ventana de Gazebo.
2. `launch/gz_cli_demo_launch.py`: arranca Gazebo con ese mundo (reutilizando
   `gz_sim.launch.py` de `ros_gz_sim`) y, en paralelo, lanza el nodo `gz_cli_demo`.
3. `gz_cli_sim_control/gz_cli_demo.py`: el nodo que ejecuta la demo. **No** usa las
   bindings de Python de `gz-transport` — llama literalmente al binario `gz` con
   `subprocess`, exactamente los mismos comandos que teclearías a mano en una terminal.
   Es intencionado: el tema del post es la CLI de Gazebo, así que el código enseña a
   automatizarla, no a sustituirla por otra API.

### Secuencia que ejecuta el nodo

| Paso | Qué hace | Comando `gz` equivalente |
|---|---|---|
| 1 | Espera a que la simulación esté arrancada | `gz service -l` (comprueba que los servicios existen) |
| 2 | Pausa la simulación | `gz service -s /world/<mundo>/control --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean --timeout 2000 --req 'pause: true'` |
| 3 | La reanuda | igual que el paso 2, con `pause: false` |
| 4 | Cambia la velocidad de simulación (`real_time_factor`) | `gz service -s /world/<mundo>/set_physics --reqtype gz.msgs.Physics --reptype gz.msgs.Boolean --timeout 2000 --req 'real_time_factor: 2.0'` |
| 5 | Consulta información del mundo (tiempo simulado, pausa, iteraciones...) | `gz topic -e -t /world/<mundo>/stats -n 1` |

Entre cada paso espera `step_delay` segundos (3 s por defecto) para que puedas observar el
efecto en la ventana de Gazebo antes de que llegue el siguiente comando.

## Estructura del paquete

```
gz-cli-sim-control/
├── gz_cli_sim_control/
│   ├── __init__.py
│   └── gz_cli_demo.py          ← nodo que automatiza la secuencia gz service/topic
├── launch/
│   └── gz_cli_demo_launch.py   ← abre Gazebo con el mundo y lanza el nodo
├── worlds/
│   └── cli_demo_world.sdf      ← mundo con la esfera que cae
├── resource/gz_cli_sim_control
├── package.xml
├── setup.py
└── setup.cfg
```

## Compilar

Desde la raíz del workspace (`ros2_ws`):

```bash
colcon build --packages-select gz_cli_sim_control
source install/setup.bash
```

## Ejecutar

```bash
ros2 launch gz_cli_sim_control gz_cli_demo_launch.py
```

Se abre Gazebo con la esfera cayendo y, en la misma terminal, verás el log del nodo
ejecutando cada paso (`$ gz service ...`, `$ gz topic ...`) junto con su resultado.

> En WSL2, exporta antes `QT_QPA_PLATFORM=xcb` para que la GUI de Gazebo abra
> correctamente (ver el README de `instalacion_gazebo_jetty` para el detalle).

### Parámetros configurables

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `render_engine` | `ogre2` | Motor de render de Gazebo (`ogre2` o `ogre`) |
| `step_delay` | `3.0` | Segundos de espera entre cada paso de la demo |
| `real_time_factor` | `2.0` | Velocidad de simulación fijada en el paso 4 |

Por ejemplo, para ver la demo más despacio y con el motor de render ligero en WSL:

```bash
ros2 launch gz_cli_sim_control gz_cli_demo_launch.py step_delay:=5.0 render_engine:=ogre
```

## Probar los mismos comandos a mano

El propio nodo no es más que estos comandos encadenados; puedes teclearlos tú mismo en
otra terminal mientras la simulación está abierta (sustituyendo `<mundo>` por
`cli_demo_world`):

```bash
gz service -l | grep /world/cli_demo_world
gz service -s /world/cli_demo_world/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 2000 --req 'pause: true'
gz topic -e -t /world/cli_demo_world/stats -n 1
```

## Dependencias

- `ros_gz_sim` (`ros-lyrical-ros-gz-sim`): aporta `gz_sim.launch.py`.
- El binario `gz` (paquete `gz-sim-vendor` / `ros-lyrical-gz-sim-vendor`) debe estar en el
  `PATH` — lo está automáticamente tras instalar Gazebo Jetty vía los paquetes vendor de
  ROS 2 Lyrical Luth.

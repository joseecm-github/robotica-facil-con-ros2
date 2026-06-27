# random_objects_gazebo

Nodo ROS 2 que **crea tres objetos** (una esfera, un cono y un cubo) en posiciones aleatorias dentro de un radio límite, usando el **servicio de spawn de Gazebo** (`/world/<world>/create`).

## Plataforma de referencia

- **ROS 2:** Lyrical Luth (LTS, mayo 2026)
- **Gazebo:** Jetty (gz-sim 10)
- **Sistema operativo:** Ubuntu Resolute 26.04

> Compilado y verificado sobre ROS 2 Lyrical Luth + Gazebo Jetty.

## Qué hace este paquete

1. Carga un mundo Gazebo con un plano (suelo) y **sin objetos**.
2. El nodo ROS 2 `spawn_objects_node` llama al servicio `create` de Gazebo para crear, una sola vez:
   - una **esfera** azul,
   - un **cono** verde,
   - un **cubo** naranja.
3. Cada objeto se coloca en una posición `(x, y)` aleatoria **dentro de un radio límite** desde el origen (para que quede dentro de la vista), con una separación mínima entre objetos para que no se solapen.
4. Los objetos se crean como `static`, así se quedan exactamente donde el nodo los coloca.

### Por qué el servicio y no un topic

Crear o posicionar entidades en Gazebo es una operación puntual de tipo petición/respuesta: encaja con un **servicio**, no con un topic de streaming. Gazebo expone `create` (y `set_pose`, `remove`...) como servicios del mundo, provistos por el sistema `UserCommands`.

El nodo los llama directamente con los **bindings de Python de Gazebo** (`gz.transport` + `gz.msgs`), sin pasar por `ros_gz_bridge`: como habla el protocolo de Gazebo de forma nativa, no hay nada que traducir.

## El reto: crear objetos justo al arrancar la GUI

Crear los objetos nada más lanzar Gazebo tiene dos trampas que este paquete resuelve:

1. **La GUI no renderiza lo que se crea demasiado pronto.** El servicio `create` está disponible antes de que la GUI termine de montar su escena 3D. Un objeto creado en esa ventana existe en el servidor pero la GUI nunca lo dibuja (el primero saldría invisible). Solución: esperar a que la GUI esté lista comprobando que anuncia su topic `/gui/camera/pose` (el namespace `/gui/*` es exclusivo de la GUI). Así sabemos que el visor 3D está montado y va a renderizar los modelos nuevos.

2. **`create` no es idempotente.** Si reintentas a ciegas (porque la primera respuesta tardó), creas un duplicado (`sphere` + `sphere_0`); si no reintentas, pierdes el objeto cuando la primera llamada llega demasiado pronto. Solución: spawn **idempotente** — comprobar si el modelo ya existe (vía `/world/<world>/scene/info`) y crear solo si falta, con `allow_renaming=False`.

Además, las creaciones se **espacian** ~0.8 s para que la GUI registre cada modelo uno a uno.

## Estructura del paquete

```
random-objects-gazebo/
├── random_objects_gazebo/
│   ├── __init__.py
│   └── spawn_objects_node.py     ← nodo que llama al servicio create
├── launch/
│   └── objects_scene.launch.py   ← lanza Gazebo + nodo
├── worlds/
│   └── objects_scene.sdf         ← mundo con suelo (sin objetos)
├── resource/random_objects_gazebo
├── package.xml
├── setup.py
└── setup.cfg
```

## Compilar

```bash
colcon build --packages-select random_objects_gazebo
source install/setup.bash
```

## Ejecutar

```bash
ros2 launch random_objects_gazebo objects_scene.launch.py
```

### Parámetros configurables

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `max_radius` | `2.0` m | Distancia máxima al origen para colocar objetos |
| `min_separation` | `1.2` m | Separación mínima entre objetos |
| `seed` | `0` | Semilla aleatoria (`0` = distinta en cada arranque) |
| `spawn_delay` | `0.8` s | Pausa entre creaciones (para que la GUI registre cada modelo) |
| `render_engine` | `ogre2` | Motor de render de Gazebo (`ogre2` o `ogre`) |

Ejemplo (posiciones reproducibles y radio menor):

```bash
ros2 launch random_objects_gazebo objects_scene.launch.py seed:=42 max_radius:=3.0
```

## Resultado esperado

Gazebo abre la escena con el suelo. En cuanto la GUI está lista, aparecen la esfera, el cono y el cubo en posiciones aleatorias, uno tras otro. En la terminal verás:

```
GUI ready; spawning objects.
Spawn sphere at (1.58, 0.25) -> OK
Spawn cone at (0.18, 1.03) -> OK
Spawn box at (-0.76, -1.54) -> OK
Objects spawned. Shutting down the node.
```

El nodo termina solo una vez creados los objetos (es una tarea de una sola vez). Gazebo sigue abierto mostrando la escena. Puedes comprobar los modelos creados con:

```bash
gz model --list
```

## Rendimiento en WSL2

En WSL2 conviene usar el motor de render ligero Ogre 1 para que la GUI no vaya a tirones:

```bash
ros2 launch random_objects_gazebo objects_scene.launch.py render_engine:=ogre
```

## Dependencias

- `rclpy`
- `ros_gz_sim` (`ros-lyrical-ros-gz-sim`)
- `gz_transport_vendor`, `gz_msgs_vendor` (bindings de Python de Gazebo, ya incluidos con la instalación de ROS de Gazebo)

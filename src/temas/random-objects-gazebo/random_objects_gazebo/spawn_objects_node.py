import math
import random
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

# Python bindings for Gazebo (vendor packages gz_transport_vendor / gz_msgs_vendor,
# available after `source /opt/ros/lyrical/setup.bash`).
from gz.transport import Node as GzNode
from gz.msgs.entity_factory_pb2 import EntityFactory
from gz.msgs.boolean_pb2 import Boolean
from gz.msgs.empty_pb2 import Empty
from gz.msgs.scene_pb2 import Scene

# (shape, RGBA color, z height so the object rests on the ground)
OBJECTS = (
    ('sphere', '0.1 0.4 0.9 1', 0.3),   # blue
    ('cone',   '0.2 0.7 0.2 1', 0.3),   # green
    ('box',    '0.9 0.4 0.1 1', 0.25),  # orange
)

GEOMETRY = {
    'sphere': '<sphere><radius>0.3</radius></sphere>',
    'cone':   '<cone><radius>0.3</radius><length>0.6</length></cone>',
    'box':    '<box><size>0.5 0.5 0.5</size></box>',
}


class SpawnObjectsNode(Node):
    def __init__(self):
        super().__init__('spawn_objects_node')

        self.declare_parameter('world', 'objects_scene')
        self.declare_parameter('max_radius', 2.0)       # distance limit from the origin (m)
        self.declare_parameter('min_separation', 1.2)   # minimum distance between objects (m)
        self.declare_parameter('seed', 0)               # 0 = random on every run
        self.declare_parameter('spawn_delay', 0.8)      # pause between spawns (s)

        self.world = self.get_parameter('world').get_parameter_value().string_value
        self.max_radius = self.get_parameter('max_radius').get_parameter_value().double_value
        self.min_separation = self.get_parameter('min_separation').get_parameter_value().double_value
        self.spawn_delay = self.get_parameter('spawn_delay').get_parameter_value().double_value
        seed = self.get_parameter('seed').get_parameter_value().integer_value
        if seed != 0:
            random.seed(seed)

        self.gz = GzNode()
        self.service = f'/world/{self.world}/create'
        self.scene_service = f'/world/{self.world}/scene/info'

    def _wait_for_service(self, timeout_s=30.0):
        """Block until Gazebo advertises the create service (it takes a moment to load)."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.service in self.gz.service_list():
                return True
            time.sleep(0.3)
        return False

    # A model created before the GUI has built its 3D scene exists on the server
    # but never gets rendered (the first object would be invisible). The GUI
    # publishes its camera pose on /gui/camera/pose; that topic belongs to the
    # GUI's own '/gui/...' namespace (no other process advertises it), so its
    # presence tells us both that *this is the GUI* and that the 3D viewport is
    # up and ready to render new models.
    GUI_READY_TOPIC = '/gui/camera/pose'
    # We always launch Gazebo with its GUI, so this topic will appear. The
    # timeout is only a safety net: if it expires, the GUI failed to start.
    GUI_TIMEOUT = 30.0

    def _wait_for_gui(self):
        """Wait until the GUI's 3D viewport is ready. Returns True once detected,
        or False after GUI_TIMEOUT seconds (which means the GUI failed to start)."""
        deadline = time.monotonic() + self.GUI_TIMEOUT
        while time.monotonic() < deadline:
            if self.GUI_READY_TOPIC in self.gz.topic_list():
                return True
            time.sleep(0.2)
        return False

    def _scene_models(self):
        """Names of the models currently in the world (empty set if the query fails)."""
        ok, scene = self.gz.request(self.scene_service, Empty(), Empty, Scene, 3000)
        return {m.name for m in scene.model} if ok else set()

    def _spawn_one(self, req, name, tries=15):
        """Idempotent spawn: create() is not idempotent, so instead of blindly
        retrying (which would duplicate the model) we check whether it already
        exists. This is robust both when the first call is too early (model
        missing -> retry) and when the response is slow (model already there ->
        stop). allow_renaming=False also blocks any accidental duplicate."""
        for _ in range(tries):
            if name in self._scene_models():
                return True
            self.gz.request(self.service, req, EntityFactory, Boolean, 3000)
            time.sleep(0.4)
        return name in self._scene_models()

    def _random_position(self, placed):
        """Uniformly random point inside the max_radius disc, kept apart from the rest."""
        x = y = 0.0
        for _ in range(100):
            # r = R * sqrt(u) yields a uniform distribution over the disc area
            r = self.max_radius * math.sqrt(random.random())
            th = random.uniform(0.0, 2.0 * math.pi)
            x, y = r * math.cos(th), r * math.sin(th)
            if all(math.hypot(x - px, y - py) >= self.min_separation for px, py in placed):
                return x, y
        return x, y  # if no free spot after 100 tries, use the last one

    def _model_sdf(self, name, shape, color):
        geom = GEOMETRY[shape]
        # static=true: the object stays exactly where the node places it
        # (a dynamic sphere would roll away and the cone could topple).
        return (
            f"<sdf version='1.8'><model name='{name}'><static>true</static>"
            f"<link name='link'>"
            f"<collision name='collision'><geometry>{geom}</geometry></collision>"
            f"<visual name='visual'><geometry>{geom}</geometry>"
            f"<material><ambient>{color}</ambient><diffuse>{color}</diffuse></material>"
            f"</visual></link></model></sdf>"
        )

    def spawn_objects(self):
        if not self._wait_for_service():
            self.get_logger().error(f'Service {self.service} not available; aborting.')
            return

        # Wait until the GUI viewport is ready (see _wait_for_gui) instead of
        # guessing with a fixed delay, so the first object is never invisible.
        if self._wait_for_gui():
            self.get_logger().info('GUI ready; spawning objects.')
        else:
            self.get_logger().warning(
                f'GUI not detected after {self.GUI_TIMEOUT:.0f}s; spawning anyway '
                '(did Gazebo start correctly?).')

        placed = []
        for i, (shape, color, z) in enumerate(OBJECTS):
            x, y = self._random_position(placed)
            placed.append((x, y))

            # Space out the spawns so the GUI registers each model one by one.
            if i > 0:
                time.sleep(self.spawn_delay)

            req = EntityFactory()
            req.sdf = self._model_sdf(shape, shape, color)
            req.name = shape
            req.allow_renaming = False  # names are unique; never silently duplicate
            req.pose.position.x = x
            req.pose.position.y = y
            req.pose.position.z = z

            ok = self._spawn_one(req, shape)
            self.get_logger().info(
                f'Spawn {shape} at ({x:.2f}, {y:.2f}) -> {"OK" if ok else "FAILED"}'
            )

        self.get_logger().info('Objects spawned. Shutting down the node.')


def main(args=None):
    rclpy.init(args=args)
    node = SpawnObjectsNode()
    try:
        # One-shot task: the retry loop waits for Gazebo to advertise the service,
        # spawns the three objects, and the node exits.
        node.spawn_objects()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

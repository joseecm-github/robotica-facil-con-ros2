import re
import subprocess
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

# Fields we care about in the plain-text output of `gz topic -e -t .../stats`
# (a serialized gz.msgs.WorldStatistics). We only need a handful of lines out
# of the full message, so a couple of regexes are simpler than pulling in the
# gz-msgs Python bindings just to parse five numbers.
#
# Gotcha: this text format follows protobuf's proto3 convention of omitting
# any scalar field that equals its default value (0, 0.0 or false) -- it does
# NOT print e.g. "paused: false" or "real_time_factor: 0". A missing field
# below means "default", not "unknown", so every lookup falls back to 0/false
# instead of "?".
_SIM_TIME_BLOCK_RE = re.compile(r'sim_time\s*\{([^}]*)\}', re.S)
_SEC_RE = re.compile(r'sec:\s*(\d+)')
_PAUSED_RE = re.compile(r'paused:\s*(true|false)')
_RTF_RE = re.compile(r'real_time_factor:\s*([\d.]+)')
_ITERATIONS_RE = re.compile(r'iterations:\s*(\d+)')


class GzCliDemoNode(Node):
    """Drives a running Gazebo simulation using only the `gz` CLI tool.

    Every step below is the exact command you would type by hand in a
    terminal (`gz service ...`, `gz topic ...`); this node just runs them in
    sequence with `subprocess`, with a short pause in between so the effect
    is visible in the Gazebo GUI, and prints what it is doing.
    """

    def __init__(self):
        super().__init__('gz_cli_demo_node')

        self.declare_parameter('world', 'cli_demo_world')
        self.declare_parameter('step_delay', 3.0)     # pause between steps (s), so you can watch the ball fall
        self.declare_parameter('real_time_factor', 2.0)

        self.world = self.get_parameter('world').get_parameter_value().string_value
        self.step_delay = self.get_parameter('step_delay').get_parameter_value().double_value
        self.rtf = self.get_parameter('real_time_factor').get_parameter_value().double_value

        self.control_service = f'/world/{self.world}/control'
        self.physics_service = f'/world/{self.world}/set_physics'
        self.stats_topic = f'/world/{self.world}/stats'

    def _run_gz(self, args, timeout_s=5.0):
        """Run a `gz <args...>` command and return its stdout (empty on failure)."""
        cmd = ['gz'] + args
        self.get_logger().info('$ ' + ' '.join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            self.get_logger().error(f'Timed out running: {" ".join(cmd)}')
            return ''
        if result.returncode != 0:
            self.get_logger().error(f'gz exited with {result.returncode}: {result.stderr.strip()}')
        return result.stdout

    def wait_for_services(self, timeout_s=30.0):
        """Step 1 - confirm the simulation is up: poll `gz service -l` until
        Gazebo advertises the world control and physics services."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            services = self._run_gz(['service', '-l'])
            if self.control_service in services and self.physics_service in services:
                self.get_logger().info(f'Simulation "{self.world}" is up.')
                return True
            time.sleep(0.5)
        self.get_logger().error(f'Simulation "{self.world}" did not come up after {timeout_s:.0f}s.')
        return False

    def pause(self):
        """Step 2 - pause the simulation via the world control service."""
        self._run_gz([
            'service', '-s', self.control_service,
            '--reqtype', 'gz.msgs.WorldControl',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '2000',
            '--req', 'pause: true',
        ])

    def resume(self):
        """Step 3 - resume the simulation via the same control service."""
        self._run_gz([
            'service', '-s', self.control_service,
            '--reqtype', 'gz.msgs.WorldControl',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '2000',
            '--req', 'pause: false',
        ])

    def set_real_time_factor(self, rtf):
        """Step 4 - change the simulation speed via the physics service."""
        self._run_gz([
            'service', '-s', self.physics_service,
            '--reqtype', 'gz.msgs.Physics',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '2000',
            '--req', f'real_time_factor: {rtf}',
        ])

    def query_world_info(self):
        """Step 5 - read one message off the world stats topic and log a summary."""
        output = self._run_gz(['topic', '-e', '-t', self.stats_topic, '-n', '1'], timeout_s=5.0)

        sim_time_block = _SIM_TIME_BLOCK_RE.search(output)
        sim_time_sec = _SEC_RE.search(sim_time_block.group(1)) if sim_time_block else None
        paused = _PAUSED_RE.search(output)
        rtf = _RTF_RE.search(output)
        iterations = _ITERATIONS_RE.search(output)

        self.get_logger().info(
            'World info -> '
            f'sim_time={sim_time_sec.group(1) if sim_time_sec else 0}s, '
            f'paused={paused.group(1) if paused else "false"}, '
            f'real_time_factor={rtf.group(1) if rtf else 0.0}, '
            f'iterations={iterations.group(1) if iterations else 0}'
        )

    def run_demo(self):
        if not self.wait_for_services():
            return

        self.get_logger().info('--- Step 2: pausing the simulation ---')
        self.pause()
        time.sleep(self.step_delay)

        self.get_logger().info('--- Step 3: resuming the simulation ---')
        self.resume()
        time.sleep(self.step_delay)

        self.get_logger().info(f'--- Step 4: setting real_time_factor to {self.rtf} ---')
        self.set_real_time_factor(self.rtf)
        time.sleep(self.step_delay)

        self.get_logger().info('--- Step 5: querying world info ---')
        self.query_world_info()

        self.get_logger().info('Demo finished. Shutting down the node.')


def main(args=None):
    rclpy.init(args=args)
    node = GzCliDemoNode()
    try:
        # One-shot task: run the pause/resume/speed/query sequence once and exit.
        node.run_demo()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class NodoVelocidadCircular(Node):
    def __init__(self):
        super().__init__('nodo_velocidad_circular')

        self.declare_parameter('radio', 2.0)
        self.declare_parameter('velocidad_base', 0.7)
        self.declare_parameter('amplitud_velocidad', 0.35)
        self.declare_parameter('periodo_velocidad', 10.0)
        self.declare_parameter('frecuencia_publicacion', 30.0)

        self.radio = self.get_parameter('radio').get_parameter_value().double_value
        self.velocidad_base = self.get_parameter('velocidad_base').get_parameter_value().double_value
        self.amplitud_velocidad = self.get_parameter('amplitud_velocidad').get_parameter_value().double_value
        self.periodo_velocidad = self.get_parameter('periodo_velocidad').get_parameter_value().double_value
        frecuencia = self.get_parameter('frecuencia_publicacion').get_parameter_value().double_value

        self.publicador = self.create_publisher(Twist, '/model/esfera_circular/cmd_vel', 10)
        self.tiempo_inicio = self.get_clock().now()
        self.create_timer(1.0 / frecuencia, self._publicar_velocidad)

        self.get_logger().info(
            f'Nodo iniciado — radio={self.radio} m, '
            f'velocidad_base={self.velocidad_base} m/s, '
            f'amplitud={self.amplitud_velocidad} m/s, '
            f'periodo={self.periodo_velocidad} s'
        )

    def _publicar_velocidad(self):
        transcurrido = (self.get_clock().now() - self.tiempo_inicio).nanoseconds / 1e9
        fase = 2.0 * math.pi * transcurrido / self.periodo_velocidad
        # La velocidad oscila en torno a velocidad_base con una onda sinusoidal.
        # max(0.0, ...) evita velocidad negativa si la amplitud supera la base.
        velocidad = max(0.0, self.velocidad_base + self.amplitud_velocidad * math.sin(fase))

        comando = Twist()
        comando.linear.x = velocidad
        # Mantener radio constante aunque la velocidad cambie
        comando.angular.z = velocidad / self.radio

        self.publicador.publish(comando)


def main(args=None):
    rclpy.init(args=args)
    nodo = NodoVelocidadCircular()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        nodo.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
import socket
import json
import threading

LISTEN_PORT = 5005

class HandTrackerNode(Node):
    def __init__(self):
        super().__init__('hand_tracker')
        self.publisher = self.create_publisher(Point, '/hand_position', 10)
        self.grip_publisher = self.create_publisher(Bool, '/hand_grip', 10)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', LISTEN_PORT))
        self.get_logger().info(f'Listening for hand data on port {LISTEN_PORT}')
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()

    def listen_loop(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                d = json.loads(data.decode())
                msg = Point()
                msg.x = d['x']
                msg.y = d.get('depth', 0.0)   # using Point.y to carry depth
                msg.z = d['y']                # using Point.z to carry vertical
                self.publisher.publish(msg)
                grip_msg = Bool()
                grip_msg.data = d['grip']
                self.grip_publisher.publish(grip_msg)
                self.get_logger().info(f'Received: x={msg.x:.2f} depth={msg.y:.3f} vert={msg.z:.2f} grip={grip_msg.data}')
            except Exception as e:
                self.get_logger().error(f'Error: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = HandTrackerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

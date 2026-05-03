import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
from sensor_msgs.msg import JointState

class RobotControllerNode(Node):
    def __init__(self):
        super().__init__('robot_controller')
        self.subscription = self.create_subscription(
            Point, '/hand_position', self.hand_callback, 10)
        self.grip_subscription = self.create_subscription(
            Bool, '/hand_grip', self.grip_callback, 10)
        self.joint_publisher = self.create_publisher(
            JointState, '/joint_states', 10)
        self.target_joints = [0.0, 0.3, 0.0, 1.5, 0.0, 1.0, 0.0]
        self.current_joints = [0.0, 0.3, 0.0, 1.5, 0.0, 1.0, 0.0]
        self.hand_detected = False
        self.timer = self.create_timer(0.05, self.publish_joints)
        self.get_logger().info('Robot controller ready - show your hand to move arm!')

    def hand_callback(self, msg):
        self.hand_detected = True
        # Lower scaling = smoother less aggressive movement
        self.target_joints[0] = msg.x * 1.5
        self.target_joints[1] = -msg.z * 1.0 + 0.3
        self.target_joints[2] = msg.x * 0.8
        self.target_joints[3] = msg.z * 1.0 + 0.5
        self.target_joints[4] = msg.x * 0.3
        self.target_joints[5] = msg.z * 0.5 + 0.5
        self.target_joints[6] = 0.0
        self.get_logger().info(f'Hand detected: x={msg.x:.2f} z={msg.z:.2f}')

    def grip_callback(self, msg):
        state = 'CLOSED' if msg.data else 'OPEN'
        self.get_logger().info(f'Gripper: {state}')

    def publish_joints(self):
        if not self.hand_detected:
            return
        # Smooth interpolation - moves slowly toward target
        alpha = 0.1
        for i in range(7):
            self.current_joints[i] += alpha * (self.target_joints[i] - self.current_joints[i])
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = [
            'joint_1', 'joint_2', 'joint_3',
            'joint_4', 'joint_5', 'joint_6', 'joint_7'
        ]
        js.position = self.current_joints
        self.joint_publisher.publish(js)

def main(args=None):
    rclpy.init(args=args)
    node = RobotControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

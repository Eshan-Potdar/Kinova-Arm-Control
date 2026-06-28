import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
from sensor_msgs.msg import JointState
import time
from collections import deque

class RobotControllerNode(Node):
    def __init__(self):
        super().__init__('robot_controller')
        self.subscription = self.create_subscription(
            Point, '/hand_position', self.hand_callback, 10)
        self.grip_subscription = self.create_subscription(
            Bool, '/hand_grip', self.grip_callback, 10)
        self.joint_publisher = self.create_publisher(
            JointState, '/joint_states', 10)

        # Straight upright resting pose - all zeros
        self.rest_pose = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.target_joints = list(self.rest_pose)
        self.current_joints = list(self.rest_pose)

        self.smooth_x = 0.0
        self.smooth_vert = 0.0
        self.smooth_depth = 0.0
        self.depth_window = deque(maxlen=12)
        self.grip_active = False

        self.baseline_depth = None
        self.last_seen_time = 0.0
        self.hand_present = False
        self.timeout = 0.5

        self.timer = self.create_timer(0.02, self.publish_joints)
        self.get_logger().info('Robot controller ready - standing straight until hand detected!')

    def hand_callback(self, msg):
        now = time.time()
        self.last_seen_time = now
        self.hand_present = True

        depth_raw = msg.y
        if self.baseline_depth is None:
            self.baseline_depth = depth_raw
            self.get_logger().info(f'Calibrated baseline depth={depth_raw:.3f}')

        raw_x = -msg.x
        raw_vert = msg.z
        raw_depth_rel = depth_raw - self.baseline_depth

        raw_x = max(-0.4, min(0.4, raw_x))
        raw_vert = max(-0.3, min(0.3, raw_vert))
        raw_depth_rel = max(-0.12, min(0.12, raw_depth_rel))

        self.depth_window.append(raw_depth_rel)
        depth_avg = sum(self.depth_window) / len(self.depth_window)

        x_alpha = 0.25
        vert_alpha = 0.2
        depth_alpha = 0.03
        self.smooth_x += x_alpha * (raw_x - self.smooth_x)
        self.smooth_vert += vert_alpha * (raw_vert - self.smooth_vert)
        self.smooth_depth += depth_alpha * (depth_avg - self.smooth_depth)

    def grip_callback(self, msg):
        self.grip_active = msg.data
        state = 'CLOSED' if msg.data else 'OPEN'
        self.get_logger().info(f'Gripper: {state}')

    def publish_joints(self):
        now = time.time()
        # If hand hasn't been seen recently, mark as not present
        if now - self.last_seen_time > self.timeout:
            self.hand_present = False

        if not self.hand_present:
            # Hold perfectly still at rest pose - no drift, no movement
            self.target_joints = list(self.rest_pose)
        else:
            x = self.smooth_x
            vert = self.smooth_vert if abs(self.smooth_vert) > 0.015 else 0.0
            depth = self.smooth_depth if abs(self.smooth_depth) > 0.02 else 0.0
            grip_top_offset = 0.6 if self.grip_active else 0.0

            self.target_joints[0] = x * 6.0
            self.target_joints[1] = -vert * 4.0
            self.target_joints[2] = x * 3.0
            self.target_joints[3] = depth * 6.0
            self.target_joints[4] = x * 2.0
            self.target_joints[5] = vert * 2.5 - depth * 14.0 + grip_top_offset
            self.target_joints[6] = 0.0

        joint_alpha = [0.2, 0.12, 0.2, 0.06, 0.2, 0.12, 0.1]
        for i in range(7):
            self.current_joints[i] += joint_alpha[i] * (self.target_joints[i] - self.current_joints[i])

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

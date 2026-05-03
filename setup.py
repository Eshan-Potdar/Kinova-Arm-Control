from setuptools import setup

package_name = 'gesture_teleop'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='eshan',
    maintainer_email='eshan@example.com',
    description='Gesture-based robot telemanipulation',
    license='MIT',
    entry_points={
        'console_scripts': [
            'hand_tracker = gesture_teleop.hand_tracker:main',
            'robot_controller = gesture_teleop.robot_controller:main',
        ],
    },
)

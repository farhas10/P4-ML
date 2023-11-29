import subprocess
import time
import math

from mbot_bridge.api import MBot

MAP_PATH = "/home/mbot/current.map"
TURN_KP = 5
MAX_TURN_SPEED = 1.5
TURN_ERROR = 0.03
POSE_ERROR = 0.03


def wrap_angle(angle):
    """
    Wrap angle to within the range [-2pi, 2pi].

    Arguments:
        angle: The angle to wrap in radians.

    Returns:
        The input angle wrapped within the range [-2pi, 2pi].
    """
    while(angle > math.pi):
        angle -= 2*math.pi
    while(angle <= -math.pi):
        angle += 2*math.pi
    return angle


def plan_to_pose(x, y, robot):
    """
    Call the path planning binary in /bin and wait until the robot arrives
    at its goal [x, y] position.

    Arguments:
        x: Goal x position in meters in map frame.
        y: Goal y position in meters in map frame.
        robot: Mbot object.
    """
    print(f"INFO: Planning to pose ({x}, {y})...")
    # Run the p3 code and go to specified coordinates.
    subprocess.call(["bin/robot_plan_path", MAP_PATH, str(x), str(y)])

    # Release the hold once the robot is close to the goal
    # (slightly less close than required by the motion controller).
    p_x,p_y,p_t = robot.read_slam_pose()
    while(((p_x - x)**2 + (p_y - y)**2)**0.5 > POSE_ERROR):
        p_x,p_y, p_t = robot.read_slam_pose()
    
    # Wait for motion controller to get the rest of the way there.
    time.sleep(2)
    robot.stop()
    print("INFO: Finished driving to pose!")


def turn_to_theta(theta, robot):
    """
    Control to the angle theta using p control.

    Arguments:
        theta: Goal angle in radians.
        robot: Mbot object.
    """
    print(f"INFO: Turning to theta {theta} radians...")
    p_x,p_y, p_t = robot.read_slam_pose()
    while(abs(wrap_angle(theta - p_t)) > TURN_ERROR):
        error = wrap_angle(theta - p_t)
        p = TURN_KP * error
        if(p > MAX_TURN_SPEED):
            robot.drive(0, 0, MAX_TURN_SPEED)
        elif(p < -MAX_TURN_SPEED):
            robot.drive(0, 0, -MAX_TURN_SPEED)
        else:
            robot.drive(0, 0, p)
        time.sleep(.1)
        p_x, p_y, p_t = robot.read_slam_pose()
    robot.stop()
    print("INFO: Finished turning to theta!")
    print(p_t)

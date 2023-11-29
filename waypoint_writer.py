from mbot_bridge.api import MBot
from utils.camera import CameraHandler


def read_labels_and_waypoints(path="waypoints.txt"):
    """
    Read labels and waypoints from a file.
    
    Arguments:
        path: Path to read labels and waypoints from, defaults to waypoints.txt.
    
    Returns:
        Tuple of list of label integer values and list of lists of [x, y, theta] float values.
    """
    file = open(path, "r")
    all_values = [float(num) for line in file for num in line.split()]
    labels = [int(val) for val in all_values[::4]]
    waypoints = [[x, y, theta] for x, y, theta in zip(all_values[1::4], all_values[2::4], all_values[3::4])]
    return labels, waypoints


def write_labels_and_waypoints(labels, waypoints, path="waypoints.txt"):
    """
    Write labels and waypoints to a file.
    
    Arguments:
        labels: List of integer values parallel to waypoints.
        waypoints: List of lists of [x, y, theta] values parallel to labels.
        path: Path to write labels and waypoints to, defaults to waypoints.txt. 
    """
    all_values = '\n'.join([' '.join([str(label), str(waypoint[0]), str(waypoint[1]), str(waypoint[2])])
                            for label, waypoint in zip(labels, waypoints)])
    file = open(path, "w")
    file.write(all_values)


def update_labels_and_waypoints(labels, waypoints, robot):
    """
    Update waypoints and labels using current position and user provided label.

    Arguments:
        labels: List of integer values parallel to waypoints.
        waypoints: List of lists of [x, y, theta] values parallel to labels.
        robot: Mbot object.

    Returns:
        Tuple of updated labels and waypoints.
    """
    waypoint = list(robot.read_slam_pose())
    print(f"\nwaypoint: [{waypoint[0]}, {waypoint[1]}, {waypoint[2]}]")

    label = None
    while True:
        try:
            label = int(input("\nenter label for recorded coordinates: "))
            break
        except Exception as e:
            pass
    if label in labels:
        waypoints[labels.index(label)] = waypoint
        print(f"\nupdated waypoint at label {label}\n")
    else:
        labels.append(label)
        waypoints.append(waypoint)
        print(f"\nadded new waypoint at label {label}\n")
    return labels, waypoints


def write_photo(camera_handle):
    """
    Write photo from current camera position.

    Arguments:
        camera_handle: Camera handle
    """
    camera_handle.capture(0, True)
    print("\nview photo at output/01_raw_frame_X.jpg\n")


def main():
    robot = MBot()
    ch = CameraHandler()
    labels, waypoints = read_labels_and_waypoints()
    
    answer = None
    while(answer != "q"):
        answer = input("\nm to save waypoint \np to take a photo \nq to end \n: ")

        if(answer == "m"):
            labels, waypoints = update_labels_and_waypoints(labels, waypoints, robot)

        elif(answer == "p"):
            write_photo(ch)

    write_labels_and_waypoints(labels, waypoints)
    print("\nwrote waypoints and labels to waypoints.txt\n")


if __name__ == '__main__':
    main()

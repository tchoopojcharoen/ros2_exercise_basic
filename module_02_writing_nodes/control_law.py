import math

def compute_go_to_goal_control(
    pose,
    goal,
    Kv=1.0,
    Kw=5.0,
    tolerance=0.01
):
    """
    Compute the linear and angular velocity commands for a go-to-goal controller.

    Parameters
    ----------
    pose : list or None
        Current robot pose in the form [x, y, theta].
        x and y are the current position.
        theta is the current heading angle in radians.

    goal : list or None
        Desired goal position in the form [x_goal, y_goal].

    Kv : float
        Linear velocity gain.
        A larger Kv makes the robot move faster toward the goal.

    Kw : float
        Angular velocity gain.
        A larger Kw makes the robot turn faster toward the goal direction.

    Returns
    -------
    v : float
        Linear velocity command.

    w : float
        Angular velocity command.

    d : float
        Distance between the current position and the goal
    """

    # Start with zero velocity.
    # If pose or goal is missing, the robot should not move.
    v = 0.0
    w = 0.0

    # Compute the difference between the goal position and current position.
    # pos_diff[0] is the x-direction error.
    # pos_diff[1] is the y-direction error.
    pos_diff = [
        goal[i] - pose[i]
        for i in range(2)
    ]

    # Compute the Euclidean distance from the robot to the goal.
    d = math.sqrt(pos_diff[0] ** 2 + pos_diff[1] ** 2)

    # If the robot is already close enough to the goal,
    # keep both velocity commands at zero.
    # Linear velocity is proportional to distance from the goal.
    v = Kv * d

    # Compute the direction angle from the robot to the goal.
    desired_angle = math.atan2(pos_diff[1], pos_diff[0])

    # Compute heading error between desired direction and current heading.
    angle_error = desired_angle - pose[2]

    # Wrap the angle error to the range [-pi, pi].
    # This makes the robot turn through the shortest direction.
    angle_error = math.atan2(
        math.sin(angle_error),
        math.cos(angle_error)
    )

    # Angular velocity is proportional to heading error.
    w = Kw * angle_error

    return v, w, d


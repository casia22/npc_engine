"""
Helper module.
"""
from math import atan2, cos, sin, pi, sqrt

def convert_color(color):
    """Convert color tupel(r, g, b) to string("rgb({r}, {g}, {b}").

    Args:
        color (tupel): RGB color. e.g. (134, 8, 45)

    Returns:
        string: "rgb({r}, {g}, {b}"
    """
    return "rgb({}, {}, {})".format(color[0], color[1], color[2])

class Node(object):
    """A node.

    Attributes:
        pos (tupel): The position of the node. (x, y)
    """
    def __init__(self, pos):
        self.pos = pos

    def make_new_node(self, distance, angle):
        """Make a new node from an existing one.

        This method creates a new node with a distance and angle given.
        The position of the new node is calculated with:
        x2 = cos(-angle)*distance+x1
        y2 = sin(-angle)*distance+y1

        Args:
            distance (float): The distance of the original node to the new node.
            angle (rad): The angle between the old and new node, relative to the horizont.

        Returns:
            object: The node with calculated poistion.
        """
        return Node((cos(-angle)*distance+self.pos[0],
                     sin(-angle)*distance+self.pos[1]))

    def get_node_angle(self, node):
        """Get the angle beetween 2 nodes relative to the horizont.

        Args:
            node (object): The other node.

        Returns:
            rad: The angle
        """
        return atan2(self.pos[0]-node.pos[0], self.pos[1]-node.pos[1]) - pi / 2

    def get_distance(self, node):
        """Get the distance beetween 2 nodes

        Args:
            node (object): The other node.
        """
        delta = (node.pos[0]-self.pos[0], node.pos[1]-self.pos[1])
        return sqrt(delta[0]**2+delta[1]**2)

    def get_tuple(self):
        """Get the position of the node as tuple.

        Returns:
            tupel: (x, y)
        """
        return self.pos

    def move(self, delta):
        """Move the node.

        Args:
            delta (tupel): A tupel, holding the adjustment of the position.
        """
        self.pos = (self.pos[0]+delta[0], self.pos[1]+delta[1])

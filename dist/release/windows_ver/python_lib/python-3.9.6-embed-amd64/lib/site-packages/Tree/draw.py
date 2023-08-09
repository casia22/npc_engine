"""
Module for drawing trees.
"""
from PIL import ImageDraw
import svgwrite
from Tree.utils import convert_color

class Drawer(object):
    """A generic class for drawing tree on acanvas."""
    def __init__(self, tree, canvas, stem_color=(255, 255, 255), leaf_color=(230, 120, 34), thickness=1, ages=None):
        """Constructor of drawer.

        Args:
            tree (object): The tree, which should drawn on canvas.
            canvas (object): The canvas for drawing the tree.
            stem_color (tupel): Color or gradient for the steam of the tree.
            leaf_color (tupel): Color for the leaf (= the color for last iteration).
            thickness (int): The start thickness of the tree.
            ages (array): Contains the ages you want to draw.

        Returns:
            int: The thickness of the branch/es
        """
        self.canvas = canvas
        self.tree = tree
        self.stem_color = stem_color
        self.leaf_color = leaf_color
        self.thickness = thickness
        self.ages = range(tree.age+1) if ages is None else ages

    def _get_thickness(self, age):
        """Get the thickness depending on age.

        Args:
            age (int): The age of the branch/es

        Returns:
            int: The thickness of the branch/es
        """
        return int((self.thickness*5)/(age+5))

    def _get_color(self, age):
        """Get the fill color depending on age.

        Args:
            age (int): The age of the branch/es

        Returns:
            tuple: (r, g, b)
        """
        if age == self.tree.age:
            return self.leaf_color
        color = self.stem_color
        tree = self.tree

        if len(color) == 3:
            return color

        diff = [color[i+3]-color[i] for i in range(3)]
        per_age = [diff[i]/(tree.age-1) for i in range(3)]

        return tuple([int(color[i]+per_age[i]*age) for i in range(3)])

    def _draw_branch(self, branch, color, thickness, age):
        """Placeholder for specific draw methods for a branch.

        Args:
            branch (tupel): The coordinates of the branch.
            color (tupel): The color of the branch.
            thickness (int): The thickness of the branch.
            age (int): The age of the tree the branch is drawn.
        """
        pass

    def draw(self):
        """Draws the tree.

        Args:
            ages (array): Contains the ages you want to draw.
        """
        for age, level in enumerate(self.tree.get_branches()):
            if age in self.ages:
                thickness = self._get_thickness(age)
                color = self._get_color(age)
                for branch in level:
                    self._draw_branch(branch, color, thickness, age)

class PilDrawer(Drawer):
    """A drawer class for drawing on PIL/Pillow images."""
    def _draw_branch(self, branch, color, thickness, age):
        ImageDraw.Draw(self.canvas).line(branch, color, thickness)

class SvgDrawer(Drawer):
    """A drawer class for drawing on svg documents.

    Attributes:
        group (list): Saves the groups created for every age.
    """
    def __init__(self, tree, canvas, color=(255, 255, 255), thickness=1):
        super(SvgDrawer, self).__init__(tree, canvas, color, thickness)
        self.group = []

    def _draw_branch(self, branch, color, thickness, age):
        color = convert_color(color)
        self.group[age].add(
            self.canvas.line(
                start=branch[:2],
                end=branch[2:],
                stroke=color,
                stroke_width=thickness
            )
        )

    def draw(self):
        self.group = []
        for _ in self.ages:
            self.group.append(self.canvas.add(svgwrite.container.Group()))
        Drawer.draw(self)

SUPPORTED_CANVAS = {
    "PIL.Image": PilDrawer,
    "svgwrite.drawing": SvgDrawer
}

from math import radians

import click

from PIL import Image
import svgwrite

from Tree.core import Tree

def get_format(path):
    pos = path.find(".")

    if pos == -1:
        return False
    return path[pos+1:]

@click.command()
@click.option("--length", "-l", help="The start length of tree.", type=float, default=300)
@click.option("--branches", "-b", help="Add a branch with a scale and a angle.", multiple=True, type=(float, int), default=[[.5, 45], [.5, -45]])
@click.option("--sigma", "-s", help="Add randomness to scale and angle.", nargs=2, type=float, default=(0, 0))
@click.option("--age", "-a", help="Indicates how many time the tree should be iterated.",type=int, default=5)
@click.option("--path", "-p", help="The path for saving the tree. Multiple formats supported e.g. svg.", default=None)
@click.option("--show", help="Shows a image of the tree.", is_flag=True)
@click.option("--stem_color1", "-sc1", help="The stem start color given as r g b", nargs=3, type=int, default=(255, 0, 255))
@click.option("--stem_color2", "-sc2", help="The stem end color given as r g b", nargs=3, type=int, default=(255, 0, 255))
@click.option("--leaf_color", "-lc", help="The leaf color given as r g b", nargs=3, type=int, default=(255, 255, 255))
@click.option("--thickness", "-t", help="The start width of the first branch.", type=int, default=5)

def create_tree(length, branches, sigma, age, path, show, stem_color1, stem_color2, leaf_color, thickness):
    stem_color = stem_color1+stem_color2
    options = [
        stem_color,
        leaf_color,
        thickness
    ]
    
    #Convert angles to radians
    branches = [[branch[0], radians(branch[1])] for branch in branches]

    tree = Tree((0, 0, 0, -length), branches, sigma)
    tree.grow(times=age)
    tree.move_in_rectangle()

    form = get_format(path) if path is not None else None

    if show or form not in ("svg", None):
        im = Image.new("RGB", tree.get_size())
        tree.draw_on(im, *options)

    if form == "svg":
        svg = svgwrite.Drawing(path)
        tree.draw_on(svg, *options)
        svg.save()

    if form not in ("svg", None):
        im.save(path)

    if show:
        im.show()

if __name__ == "__main__":
    create_tree()

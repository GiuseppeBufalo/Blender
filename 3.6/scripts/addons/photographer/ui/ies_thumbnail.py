# Args:
# img input path
# size X
# img output path

# example usage:
# blender --background --factory-startup --python resize.py -- "C:\big image.hdr" 200 "C:\small image.jpg"

import bpy
import sys
from math import floor

argv = sys.argv
argv = argv[argv.index("--") + 1:]  # Get all args after  '--'
FILEPATH, SIZE_X, OUTPATH = argv
SIZE_X = int(SIZE_X)

context = bpy.context
scene = context.scene

light = bpy.data.objects['Point'].data

if light.use_nodes:
    nodes = light.node_tree.nodes
    for node in nodes:
        if type(node) is bpy.types.ShaderNodeTexIES:
            node.filepath = FILEPATH

# Render
r = scene.render
r.image_settings.file_format = 'PNG'
r.resolution_x = resolution_y = SIZE_X
r.resolution_percentage = 100
r.filepath = OUTPATH

bpy.ops.render.render(write_still=True)

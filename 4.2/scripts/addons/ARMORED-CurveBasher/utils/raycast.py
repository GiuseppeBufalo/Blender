import bpy

from bpy_extras import view3d_utils
from mathutils import Vector

from .. utils import addon


def raycast(context, event):
    # from bpy_extras import view3d_utils

    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    # depsgraph = context.evaluated_depsgraph_get()
    view_layer = context.view_layer 


    # get the ray from the viewport and mouse
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    result, location, normal, index, obj, matrix = scene.ray_cast(view_layer, origin, direction)
    # print(f'location {location}')
    # print(f'normal {normal}')
    # print(f'index {index}')
    # print(f'object {obj}')
    # print(f'matrix {matrix}')

    return result, location, normal, obj

def cursorcast(context, rot_as_vector=False):
    # from mathutils import Vector

    cursor = context.scene.cursor
    cursor.rotation_mode = 'XYZ'
    original_cursor_location = Vector(cursor.location[:])
    original_cursor_rotation = cursor.rotation_euler.copy()

    bpy.ops.view3d.cursor3d('INVOKE_DEFAULT', orientation='GEOM')

    loc = cursor.location[:]            # Vector
    rot = cursor.rotation_euler.copy()  # Euler
    
    cursor.location       = original_cursor_location
    cursor.rotation_euler = original_cursor_rotation

    if rot_as_vector:
        up = Vector((0, 0, 1))
        up.rotate(rot)
        rot = up
    
    return loc, rot

    # import bpy

def curve_test(context):
    o1 = bpy.data.objects['a1']
    o2 = bpy.data.objects['a2']

    scn = context.scene
    curve = bpy.data.curves.new("link", 'CURVE')
    spline = curve.splines.new('BEZIER')

    spline.bezier_points.add(2)
    p0 = spline.bezier_points[0]
    p1 = spline.bezier_points[1]
    p2 = spline.bezier_points[2]
    p0.co = (0, 0, 0)
    p1.co = (1, 1, 1)
    p2.co = (0, 1, 0)

    p0.handle_right_type = 'AUTO'
    p0.handle_left_type  = 'AUTO'

    p1.handle_right_type = 'AUTO'
    p1.handle_left_type  = 'AUTO'

    p2.handle_right_type = 'AUTO'
    p2.handle_left_type  = 'AUTO'

    obj = bpy.data.objects.new("link", curve)
    context.collection.objects.link(obj)
    context.view_layer.objects.active = obj

    # scn.objects.link(obj)
    # scn.objects.active = obj


    return obj
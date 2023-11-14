import bpy
from mathutils import Vector, Euler, Matrix, Quaternion

from .. utils import addon
from .. utils import colors


# def local_to_world(obj, vector1):
#     mat_world = obj.matrix_world
#     world_pos = mat_world @ vector1
#     return world_pos


# def world_to_local(obj, vector1):
#     mat_world = obj.matrix_world
#     world_pos = mat_world.inverted() @ vector1
#     return world_pos


def distance_finder(p1, p2):
    x1, y1, z1 = p1  # first coordinates
    x2, y2, z2 = p2  # second coordinates

    return (((x2-x1)**2) + ((y2-y1)**2) + ((z2-z1)**2))**(1/2)


def circle_marker(self, context, name='M1', radius=0.1, location=(0, 0, 0), rotation=(0, 0, 0), normal=None, surface_offset=0):
    # edit_flag = False
    if context.mode != 'OBJECT':
        # edit_flag = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # previous_active = context.object
    previous_selection = context.selected_objects

    if normal:
        up = Vector((0, 0, 1))
        rotation = up.rotation_difference(normal).to_euler()

    bpy.ops.curve.primitive_bezier_circle_add(
        radius=radius, 
        enter_editmode = False,
        align='WORLD', 
        location=location, 
        rotation=rotation, 
        scale=(1, 1, 1)
    )
    ob = context.object
    ob.name = name
    ob.show_name = True
    ob.show_in_front = True

    offset_location = Matrix.Translation((0.0, 0.0, surface_offset))
    ob.matrix_world = ob.matrix_world @ offset_location

    # context.view_layer.objects.active = previous_active
    for element in previous_selection:
        element.select_set(True)

    # if edit_flag:
    #     bpy.ops.object.mode_set(mode='EDIT')

    return ob

# Legacy
def new_circle(context, name='Circle', radius=0.1, location=(0, 0, 0), rotation=(0, 0, 0), normal=None, surface_offset=0.0):
    # from mathutils import Matrix, Vector

    if normal:
        up = Vector((0, 0, 1))
        rotation = up.rotation_difference(normal).to_euler()

    bpy.ops.curve.primitive_bezier_circle_add(
        radius=radius, 
        enter_editmode = False,
        align='WORLD', 
        location=location, 
        rotation=rotation, 
        scale=(1, 1, 1)
    )
    ob = context.object
    ob.name = name
    ob.show_name = True

    offset_location = Matrix.Translation((0.0, 0.0, surface_offset))
    ob.matrix_world = ob.matrix_world @ offset_location

    return ob


def split_bezier(v1, v2, t=0.5):
    # Bless those mathematicians.
    A = v1.co
    B = v1.handle_right
    C = v2.handle_left
    D = v2.co
    
    E = (A+B)*t
    F = (B+C)*t
    G = (C+D)*t
    H = (E+F)*t
    J = (F+G)*t
    K = (H+J)*t

    return A, E, H, K, J, G, D


# def new_bezier(self, context, points=3, handle_type='AUTO'):
    # NEW WAY:

    # bpy.ops.curve.primitive_bezier_curve_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    # curve = context.object
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.curve.subdivide()
    # if not self.enter_edit:
    #     bpy.ops.object.mode_set(mode='OBJECT')

def new_bezier(context, point_count=3, handle_type='FREE', coll=None):
    curve = bpy.data.curves.new('Curve', 'CURVE')
    curve.dimensions = '3D'

    spline = curve.splines.new(type='BEZIER')
    spline.bezier_points.add(point_count-1)

    for p in spline.bezier_points:
        p.handle_left_type = handle_type 
        p.handle_right_type = handle_type

    ob = bpy.data.objects.new('Curve', curve)
    ob.color = colors.DEMO_COLOR
    
    # ob['mode']  =  1
    # ob['index'] = -1

    if coll is None:
        context.collection.objects.link(ob) # Links to current collection.
    elif type(coll) == str:
        bpy.data.collections[coll].objects.link(ob)
    else:
        coll.objects.link(ob)

    return ob


def new_normal_handle_bezier(self, context, locations, normals):
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    prev_sel = []
    if self.keep_prev_sel:
         prev_sel = context.selected_objects

    # prev_sel = context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')
    for ob in prev_sel:
        ob.select_set(True)

    curve = new_bezier(context)
    splines = curve.data.splines[:]
    spline = splines[0]
    points = spline.bezier_points

    # curve.data.splines[0].use_smooth = False
    curve.data.bevel_depth = self.radius
    curve.data.resolution_u = self.resolution_u
    curve.data.bevel_resolution = self.bevel_resolution
    curve.color = colors.DEMO_COLOR

    if curve.data.bevel_depth != 0:
        curve['mode'] = 1
        curve['index'] = -1

    # --------------------------------------

    multiplier = self.handle_offset

    if self.outer_handle_type == 'ADAPTIVE':
        distance = distance_finder(locations[0], locations[-1])
        multiplier *= self.adaptive_strength * distance
        
    # Only apply to start and end points.
    for i, p in enumerate((points[0], points[-1])):
        p.co = (locations[i])

        p.handle_left_type = 'FREE' 
        p.handle_right_type = 'FREE' 

        p.handle_left  = p.co
        p.handle_right = p.co

        # Setting them independently bypasses the ALIGNED handle bug
        if i == 0:
            p.handle_left  -= normals[i] * multiplier /2    # Brute resize for now.
            p.handle_right += normals[i] * multiplier
        else:
            p.handle_left  += normals[i] * multiplier
            p.handle_right -= normals[i] * multiplier /2
        
        # Cuz why not.
        p.handle_left_type = 'ALIGNED' 
        p.handle_right_type = 'ALIGNED' 
        # 
    # It's midpoint's turn...
    A, E, H, K, J, G, D = split_bezier(points[0], points[-1]) # Returns: (A, E, H, K, J, G, D)
    midpoint = points[1]

    points[0].handle_right = E

    midpoint.handle_left   = H
    midpoint.co            = K
    midpoint.handle_right  = J

    points[-1].handle_left  = G

    if self.curve_sag:
    # Bezier handles are bugged or something. Move independently instead.
        s = self.sag_strength
        midpoint.handle_left.z  -= s
        midpoint.co.z           -= s
        midpoint.handle_right.z -= s

    midpoint.handle_left_type = self.mid_handle_type
    midpoint.handle_right_type = self.mid_handle_type

    points[-1].select_left_handle = False
    midpoint.select_left_handle = True
    midpoint.select_control_point = True
    midpoint.select_right_handle = True

    return curve

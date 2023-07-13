import bpy, bmesh
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty

from random import uniform, random, seed
from mathutils import Vector
from math import copysign

from .. utils import addon
from .. utils import collections
from .. utils import curve_utils
from .. utils import transforms


def hook_curve_points(curve, volumes, hooks_in_edit=True):
    for i, vol in enumerate(volumes):
        mod = curve.modifiers.new(f'volume{i}', 'HOOK')
        mod.show_in_editmode = hooks_in_edit
        mod.object = vol
        mod.vertex_indices_set([i*3, i*3+1, i*3+2])


def closest_world_vector(self, point, axis=None):
    p = point

    dir_vec_left  = p.handle_left  - p.co
    dir_vec_right = p.handle_right - p.co

    dist_left, dist_right = reset_handles(p)

    if axis is None:
        max_left  = max(dir_vec_left,  key=abs)
        max_right = max(dir_vec_right, key=abs)
    else:    
        max_left  = getattr(dir_vec_left,  axis)
        max_right = getattr(dir_vec_right, axis)

    max_left_index  = list(dir_vec_left).index(max_left)
    max_right_index = list(dir_vec_right).index(max_right)

    dist_left  *= self.handle_size * self.handle_direction
    dist_right *= self.handle_size * self.handle_direction

    p.handle_left[max_left_index]   += copysign(dist_left,  max_left)
    p.handle_right[max_right_index] += copysign(dist_right, max_right)

    # p.handle_left  *= self.handle_size * self.handle_direction
    # p.handle_right *= self.handle_size * self.handle_direction


# DEPRECATED
def flatten_handle(self, point, align_axis=None, ignore_axis=None):
    p = point
    world_axis = ['x', 'y', 'z']

    dist_left  = curve_utils.distance_finder(p.handle_left,  p.co)
    dist_right = curve_utils.distance_finder(p.handle_right, p.co)

    

    # d1 = curve_utils.distance_finder(p.handle_left, p.co)

    axis_deltas = dict()
    for axis in world_axis:
        axis_deltas[axis] = abs(getattr(p.handle_left, axis) - getattr(p.handle_right, axis))
    
    # print(f'axis deltas {axis_deltas}')

    if ignore_axis:
        del axis_deltas[ignore_axis]
        setattr(p.handle_left,  ignore_axis, getattr(p.co, ignore_axis))
        setattr(p.handle_right, ignore_axis, getattr(p.co, ignore_axis))

    if align_axis:
        del axis_deltas[align_axis]

    else:
        longest_axis = max(axis_deltas, key=axis_deltas.get)    # This looks mistaken but works according to the internet
        del axis_deltas[longest_axis]
        # print(f'longuest axis is {longest_axis}')

    for axis in axis_deltas:
        setattr(p.handle_left,  axis, getattr(p.co, axis))
        setattr(p.handle_right, axis, getattr(p.co, axis))
    
    dir_vec_left  = p.handle_left  - p.co
    dir_vec_right = p.handle_right - p.co

    # dir_vec_left.normalize()
    # dir_vec_right.normalize()

    # dir_vec_left  *= self.handle_size * self.handle_direction
    # dir_vec_right *= self.handle_size * self.handle_direction
    
    p.handle_left  = p.co
    p.handle_right = p.co

    p.handle_left  += dir_vec_left.normalized()  * dist_left  * self.handle_size * self.handle_direction
    p.handle_right += dir_vec_right.normalized() * dist_right * self.handle_size * self.handle_direction


def reset_handles(point):
    p = point

    # Store the vector length before resetting.
    dist_left  = curve_utils.distance_finder(p.handle_left,  p.co)
    dist_right = curve_utils.distance_finder(p.handle_right, p.co)

    p.handle_left  = p.co
    p.handle_right = p.co

    return dist_left, dist_right


def orient_handle_world(self, point, align_axis):
    p = point
    dist_left, dist_right = reset_handles(p)

    dist_left  *= self.handle_size * self.handle_direction
    dist_right *= self.handle_size * self.handle_direction

    setattr(p.handle_left,  align_axis, getattr(p.handle_left,  align_axis) - dist_left)
    setattr(p.handle_right, align_axis, getattr(p.handle_right, align_axis) + dist_right)

    # p.handle_left  *= self.handle_size * self.handle_direction
    # p.handle_right *= self.handle_size * self.handle_direction


def orient_handle_local(self, point, i, up, volumes):
    p = point
    dist_left, dist_right = reset_handles(p)

    vol = volumes[i]
    loc, rot, scale = vol.matrix_world.decompose()

    up.rotate(rot)
    dir_vec = up

    p.handle_left  -= dir_vec * dist_left * self.handle_size * self.handle_direction
    p.handle_right += dir_vec * dist_right * self.handle_size * self.handle_direction
    

def flatten_curve_handles(self, curve, flatten_type, handle_size, volumes):
    flatten_handle_func       = flatten_handle
    orient_handle_local_func  = orient_handle_local
    orient_handle_world_func  = orient_handle_world

    def auto():
        # flatten_handle_func(p)
        closest_world_vector(self, p, axis=None)

    def horizontal():
        flatten_handle_func(self, p, ignore_axis='z')

    def vertical():
        if p in {points[0], points[-1]}:
            flatten_handle_func(self, p, align_axis='z')
        else:
            flatten_handle_func(self, p)
    
    def x():
        # closest_world_vector(self, p, axis='x')
        orient_handle_world(self, p, align_axis='x')

    def y():
        # closest_world_vector(self, p, axis='y')
        orient_handle_world(self, p, align_axis='y')

    def z():
        # closest_world_vector(self, p, axis='z')
        orient_handle_world(self, p, align_axis='z')

    def lx():
        orient_handle_local_func(self, p, i, up=Vector((1, 0, 0)), volumes=volumes)

    def ly():
        orient_handle_local_func(self, p, i, up=Vector((0, 1, 0)), volumes=volumes)

    def lz():
        orient_handle_local_func(self, p, i, up=Vector((0, 0, 1)), volumes=volumes)
        
    # def single_axis(axis):
    #     flatten_handle_func(p, align_axis=axis)

    def switcher(flatten_type) :
        cases = {
            'AUTO':       auto, 
            'HORIZONTAL': horizontal, 
            'VERTICAL':   vertical, 
            'x':          x, 
            'y':          y, 
            'z':          z, 
            'lx':         lx, 
            'ly':         ly, 
            'lz':         lz, 
        }

        cases.get(flatten_type)()

    points = curve.data.splines[0].bezier_points
    for i, p in enumerate(points):
        switcher(flatten_type)
        
        # This is stupid but hey it's working.
        # left_dir_vec  = p.handle_left  - p.co
        # right_dir_vec = p.handle_right - p.co

        # p.handle_left   = p.co + left_dir_vec  * handle_size * self.handle_direction
        # p.handle_right  = p.co + right_dir_vec * handle_size * self.handle_direction

        # p.handle_left  *= handle_size * self.handle_direction
        # p.handle_right *= handle_size * self.handle_direction

    # for p in points:
    #     p.handle_left_type  = 'ALIGNED'
    #     p.handle_right_type = 'ALIGNED'

def rangeit(start=0, stop=.9, count: int=10):
    if count == 1:
        start = 0
        step = 0
    else:
        step = abs(start - stop) / (count - 1)

    for r in range(count):
        yield start + r * step


def set_curve_settings(self, curve):
    # curve['mode'] = 1
    # curve['index'] = -1

    scale = uniform(self.multiplier, self.multiplier + self.random_offset)
    curve.data.bevel_depth = scale
    curve.data.bevel_resolution = self.bevel_resolution
    curve.data.resolution_u = self.resolution_u

    if curve.data.bevel_depth != 0:
        curve['mode'] = 1
        curve['index'] = -1


def grid_curves(self, context, volumes):
    seed(self.seed)
    generated_curves = list()
    longuest = 0
    shortest = 10**10
    
    columns = self.columns
    rows = self.rows
    axis = int(self.array_axis)

    # Start, Stop values are default bounding box coords (worry about scale later).
    matrix = list()
    for i in rangeit(-1, 1, columns):
        array = list()
        for j in rangeit(-1, 1, rows):
            if axis == 0:
                array.append(Vector((0, i, j)))
            elif axis == 1:
                array.append(Vector((i, 0, j)))
            elif axis == 2:
                array.append(Vector((i, j, 0)))
        matrix.append(array)
    
    if axis == 0:
        up = Vector((1, 0, 0))
        ax1, ax2 = (1, 2)
    elif axis == 1:
        up = Vector((0, 1, 0))
        ax1, ax2 = (0, 2)
    elif axis == 2:
        up = Vector((0, 0, 1))
        ax1, ax2 = (0, 1)

    for x in range(columns):
        for y in range(rows):
            curve = curve_utils.new_bezier(context, len(volumes), handle_type='AUTO', coll=self.wire_coll)
            
            generated_curves.append(curve)
            spline = curve.data.splines[0]
            points = spline.bezier_points

            set_curve_settings(self, curve)

            for p, vol in zip(points, volumes):
                axis = int(self.array_axis)

                new_vec = up.copy()
                new_vec.rotate(vol.rotation_euler)
                normal = new_vec
                mult = 1.5

                normalized_co = matrix[x][y]
                u = normalized_co[ax1] * vol.dimensions[ax1] / vol.scale[ax1] / 2   # Don't ask cuz I don't know.
                v = normalized_co[ax2] * vol.dimensions[ax2] / vol.scale[ax2] / 2

                if axis == 0:
                    vec = Vector((0, u, v))
                elif axis == 1:
                    vec = Vector((u, 0, v))
                elif axis == 2:
                    vec = Vector((u, v, 0))

                # vec = Vector( (u, v, 0) )
                co = vol.matrix_world @ vec
                p.co = co

            for p in points:
                p.handle_left_type  = self.handle_type
                p.handle_right_type = self.handle_type
            
            curve_len = curve.data.splines[0].calc_length()

            if curve_len > longuest:
                longuest = curve_len

            if curve_len < shortest:
                shortest = curve_len

    # print(f'longuest length {longuest}')
    # print(f'shortest length {shortest}')
    
    if self.handle_type == 'FREE':

        for curve in generated_curves:
            spline = curve.data.splines[0]
            points = spline.bezier_points

            curve_len = spline.calc_length()

            for p, vol in zip(points, volumes):
                new_vec = up.copy()
                new_vec.rotate(vol.rotation_euler)
                normal = new_vec

                dist_left  = curve_utils.distance_finder(p.handle_left,  p.co)
                dist_right = curve_utils.distance_finder(p.handle_right, p.co)

                p.handle_left  = p.co
                p.handle_right = p.co

                p.handle_left  -= normal * dist_left  * self.handle_size * self.handle_direction * curve_len / longuest
                p.handle_right += normal * dist_right * self.handle_size * self.handle_direction * curve_len / longuest

            for p in points:
                p.handle_left_type  = 'ALIGNED'
                p.handle_right_type = 'ALIGNED'
            
        
    return generated_curves
            

def generate_random_curve(self, context, volumes, curve_index):
    seed(self.seed * (curve_index + 2))
    
    curve = curve_utils.new_bezier(context, point_count=len(volumes), handle_type='AUTO', coll=self.wire_coll)
    
    set_curve_settings(self, curve)

    spline = curve.data.splines[0]
    points = spline.bezier_points

    for p, vol in zip(points, volumes):
        if self.random_style == 'PARALLEL':
            seed(self.seed * (curve_index + 2))
        
        bbox = [Vector(corner) for corner in vol.bound_box]
        xmin, xmax = bbox[0].x, bbox[6].x
        ymin, ymax = bbox[0].y, bbox[6].y
        zmin, zmax = bbox[0].z, bbox[6].z

        random_co = vol.matrix_world @ Vector((uniform(xmin, xmax), uniform(ymin, ymax), uniform(zmin, zmax))) 
        p.co = random_co
    
    # Looping again saves us from updating the scene for some reason.
    for p in points:
        p.handle_left_type  = self.handle_type 
        p.handle_right_type = self.handle_type

    return curve


class CURVEBASH_OT_wire_generator(bpy.types.Operator):
    '''Generate curves that intersect primitive bounding boxes randomly or in a grid pattern.

(www.armoredColony.com)'''

    bl_idname = 'object.curvebash_wire_generator'
    bl_label  = 'Wire Generator'
    bl_options = {'REGISTER', 'UNDO'}
    

    mode : EnumProperty(name='Mode', default='RANDOM',
            items=[ ('RANDOM', 'Random', 'Randomized curve points'), 
                    ('ARRAY',   'Array',   'Arrange curve points in a grid'), ])

    wire_count : IntProperty(name='Wire Count', default=10, 
            description='How many curves will be generated' ,
            min=1, soft_max=100)
    

    # CURVE SETTINGS
    multiplier : FloatProperty(name='Radius', default=0.1,  
            description='Set to 0 to disable width', 
            precision=3, min=0.0, step=0.5)

    random_offset : FloatProperty(name='Random Offset', default=0,  
            description='Set to 0 to disable scale randomness (allows negative values)', 
            precision=3, step=0.5)

    bevel_resolution : IntProperty(name='Bevel Resolution', default=2,
            description='Controls the profile side count (0=4 sides, 1=6 sides, ..',
            min=0, soft_max=6)

    resolution_u : IntProperty(name='Curve Segments', default=24,
            description='Controls the curve segments',
            min=1, soft_max=64)


    seed : IntProperty(name='Seed', default=5, 
            description='Determines which pattern will be generated', 
            min=1)
    
    random_style : EnumProperty(name='Random Style', default='CHAOTIC', 
            items=[ ('CHAOTIC',  'Chaotic',  'Randomize curve points for each volume'), 
                    ('PARALLEL', 'Parallel', 'All volumes share the same randomization (minimizes intersecting wires')  ])

    handle_type : EnumProperty(name='Handle Type', default='AUTO', 
            items=[ ('AUTO',   'Auto',    'Smooth Curve'), 
                    ('FREE',   'Aligned', 'Horizontal Handles' ),
                    ('VECTOR', 'Vector',  'Straight Curve' ),   ])

    flatten_type : EnumProperty(name='Align Mode', default='HORIZONTAL', 
            items=[ ('AUTO',       'Adaptive',   'Handles adaptively align to the longest axis'), 
                    ('HORIZONTAL', 'Horizontal', 'End Handles align to the closest horizontal axis' ),
                    ('VERTICAL',   'Vertical',   'End Handles align to the closest vertical axis' ),
                    ('x',          'World X',    'All Handles align to world X' ),
                    ('y',          'World Y',    'All Handles align to world Y' ),
                    ('z',          'World Z',    'All Handles align to world Z' ),   
                    ('lx',         'Local X',    'All Handles align to local X' ),   
                    ('ly',         'Local Y',    'All Handles align to local Y' ),   
                    ('lz',         'Local Z',    'All Handles align to local Z' ),   ])

    volume_view : EnumProperty(name='Volume View', default='BOUNDS',
            items=[ ('BOUNDS', 'Bounding Box', 'View as Bounding Box'), 
                    ('WIRE',   'Wireframe',    'View as Wireframe'   ),
                    ('SOLID',  'Solid',        'View as Solid'       ), ])


    # ARRAY DIMENSIONS
    columns : IntProperty(name='', default=4,
            description='Ammount of horizontal curves',
            min=1, soft_max=15)

    rows : IntProperty(name='', default=2,
            description='Ammount of vertical curves',
            min=1, soft_max=15)

    array_axis : EnumProperty(
            name='Face Axis',
            default='2',
            items=[ ('0', 'X', 'Flatten the array in X'), 
                    ('1', 'Y', 'Flatten the array in Y'),
                    ('2', 'Z', 'Flatten the array in Z'),   ])


    handle_size : FloatProperty(name='Handle Size', default=1.0,
            description='Handle Size Multiplier',)

    reverse_handles : BoolProperty(name='Reverse Handles', default=False,
            description='Reverse the orientation of the bezier handles')

    # GRAVITY
    intermediate_volumes : BoolProperty(name='Gravity', default=False,
            description='Simulate gravity')

    sag_strength : FloatProperty(name='Strength', default=0.5,
            description='Gravity Strength')

    gravity_volume_scale : FloatProperty(name='Range', default=1,
            description='Gravity Range')


    # VISIBILITY OPTIONS
    show_bounds : BoolProperty(name='Show Bounds', default=True,
            description='Visibility of the curve spawning volumes')

    hooks_in_editmode : BoolProperty(name='Hooks in Edit Mode', default=True,
            description='Curves follow the spawning volumes even in Edit Mode')

    relationship_lines : BoolProperty(name='Relationship Lines', default=False,
            description='This looks ugly when it\'s on, not really needed')

    select_wires : BoolProperty(name='Select Wires', default=False,
            description='Select all the generated curves')


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, 'multiplier')
        layout.prop(self, 'random_offset')
        layout.separator()
        
        row = layout.row()
        row.prop(self, 'mode', expand=True)

        if self.mode == 'RANDOM':
            layout.prop(self, 'wire_count')
            layout.separator()
            row = layout.row(align=True)
            row.prop(self, 'random_style', expand=True)
            layout.prop(self, 'seed')

        elif self.mode == 'ARRAY':
            row = layout.row(align=True)
            row.prop(self, 'columns', text='Dimensions', expand=True)
            row.prop(self, 'rows', text='', expand=True)
            layout.separator()
            row = layout.row(align=True)
            row.prop(self, 'array_axis', expand=True)
            layout.label(text='')            
            # layout.prop(self, 'reverse_handles', toggle=True)
            # sub.enabled = True if self.handle_type == 'FREE' else False
            # sub = layout.row(align=True)
            # layout.prop(self, 'handle_size')

        layout.separator()

        row = layout.row(align=True)
        row.prop(self, 'handle_type', expand=True)
        if self.mode == 'RANDOM':
            sub = layout.row()
            sub.enabled = True if self.handle_type == 'FREE' else False
            sub.prop(self, 'flatten_type')
        elif self.mode == 'ARRAY':
            col = layout.column(heading='Alignment', align=True)
            col.enabled = False
            col.label(text='                   Align Modes are unavailable for Arrays')
        layout.separator()
        
        sub = layout.row(align=True)
        sub.enabled = True if self.handle_type == 'FREE' else False
        sub.prop(self, 'handle_size')
        sub = layout.row(align=True)
        sub.enabled = True if self.handle_type == 'FREE' else False
        sub.prop(self, 'reverse_handles', toggle=True)
        layout.separator()

        # layout.prop(self, 'handle_size')
        # layout.separator()

        layout.prop(self, 'intermediate_volumes', toggle=True)
        sub = layout.column()
        sub.enabled = True if self.intermediate_volumes else False
        sub.prop(self, 'sag_strength')
        sub.prop(self, 'gravity_volume_scale')
        layout.separator()

        layout.prop(self, 'volume_view')
        layout.separator()
        
        col = layout.column(heading='Curve Settings')
        col.prop(self, 'bevel_resolution')
        col.prop(self, 'resolution_u')
        # col.prop(self, 'show_bounds')
        # col.prop(self, 'hooks_in_editmode')
        # col.prop(self, 'relationship_lines')
        col.separator()
        layout.prop(self, 'select_wires', toggle=True)


    def invoke(self, context, event):
        if addon.get_prefs().wg_undo_push:
            bpy.ops.ed.undo_push()

        self.seed = int(uniform(0, 99999))
        # self.seed = 8344

        self.intermediate_volumes = True if event.shift else False

        # bpy.ops.ed.undo_push()
        return self.execute(context)


    def execute(self, context):
        if len(context.selected_objects) < 2:
            self.report({'ERROR'}, 'Wire Gen\n You need at least 2 objects to generate curves between them.')
            return {'CANCELLED'}
        
        volumes = context.selected_objects

        # self.mid_volumes = set()
        if self.intermediate_volumes:
            temp = list()
            vol_count = len(volumes)

            for i, vol in enumerate(volumes):
                # if i == vol_count-1:
                if vol == volumes[-1]:
                    temp.append(vol)
                    break

                vol1 = volumes[i]
                vol2 = volumes[i+1]

                bpy.ops.mesh.primitive_cube_add(
                    size=2, 
                    align='WORLD', 
                    location=(0, 0, 0), 
                    rotation=(0, 0, 0),
                    scale=(1, 1, 1)
                )
                mid_vol = context.object

                mid_vol.location = (vol1.location + vol2.location) / 2
                dimensions = (vol1.dimensions + vol2.dimensions) / 2
                dim = addon.get_prefs().gravity_dimensions_override
                mid_vol.dimensions = dimensions if dimensions != Vector() else Vector((dim, dim, dim))
                mid_vol.rotation_euler = (Vector(vol1.rotation_euler) + Vector(vol2.rotation_euler)) / 2

                # Gravity Props
                mid_vol.location.z -= curve_utils.distance_finder(vol1.location, vol2.location)/2 * self.sag_strength
                mid_vol.scale.z *= self.gravity_volume_scale
                # mid_vol.dimensions.z *= self.gravity_volume_scale     # Not sure why this doesn't work

                # self.mid_volumes.add(mid_vol)
                temp.append(vol)
                temp.append(mid_vol)
            
            volumes = temp

        self.wire_coll = collections.create_collection(context, 'CB Wires')
        self.volume_coll = collections.create_collection(context, 'CB Bounds')

        # Move to new collection and edit volume properties.
        for vol in volumes:
            for coll in vol.users_collection:
                coll.objects.unlink(vol)
            self.volume_coll.objects.link(vol)
            
            vol.display_type = self.volume_view
            # vol.hide_viewport(True)                # Global VLayer
            vol.hide_set(not self.show_bounds)     # Local VLayer
            vol.hide_render = True

        bpy.ops.object.select_all(action='DESELECT')
        self.handle_direction = -1 if self.reverse_handles else 1

        generated_curves = list()

        if self.mode == 'RANDOM':
            for i in range(self.wire_count):
                curve = generate_random_curve(self, context, volumes, curve_index=i)
                generated_curves.append(curve)
        
            if self.handle_type == 'FREE':
                flatten_func = flatten_curve_handles
                for curve in generated_curves:
                    flatten_func(self, curve, self.flatten_type, self.handle_size, volumes)
            
        elif self.mode == 'ARRAY':
            generated_curves = grid_curves(self, context, volumes)

        # POST GEN OPERATIONS
        for curve in generated_curves:
            hook_curve_points(curve, volumes, self.hooks_in_editmode)
            curve.select_set(self.select_wires)

        # if self.select_wires:
            # for curve in generated_curves:
                # curve.select_set(True)
        
        if addon.debug():
            context.view_layer.objects.active = generated_curves[-1]
            bpy.ops.object.mode_set(mode='EDIT')
            
        context.space_data.overlay.show_relationship_lines = self.relationship_lines
        return {'FINISHED'}


def draw_menu(self, context):
    # self.layout.separator()
    self.layout.operator(CURVEBASH_OT_wire_generator.bl_idname, text='Wire Generator', icon='MOD_INSTANCE')


classes = (
    CURVEBASH_OT_wire_generator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_curve_add.append(draw_menu)
    
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_curve_add.remove(draw_menu)

import bpy

from math import radians, degrees
from mathutils import Matrix, Vector, Quaternion

from .. utils import addon
from .. utils import objects


def apply_transforms(ob):
    ob.data.transform(ob.matrix_world)
    ob.matrix_world = Matrix()


def apply_location_rotation(ob):
    if addon.debug():
        print('Apply Location and Rotation only\n')

    local_origin = ob.matrix_world.inverted() @ Vector.Fill(3, 0)
    ob.data.transform(Matrix.Translation(-local_origin))
    ob.matrix_world.translation = Vector.Fill(3, 0)
    
    rot_mat = get_rotation_matrix(ob.rotation_euler)
    ob.data.transform(rot_mat)
    ob.matrix_world = ob.matrix_world @ rot_mat.inverted()


# def apply_scale(ob):
#     loc, rot, scale = ob.matrix_world.decompose()
#     ob.matrix_world = get_location_matrix(loc) @ get_rotation_matrix(rot) @ get_scale_matrix(Vector.Fill(3, 1))


# def apply_rotation(ob):
#     loc, rot, scale = ob.matrix_world.decompose()
#     ob.matrix_world = get_location_matrix(loc) @ get_rotation_matrix(Quaternion()) @ get_scale_matrix(scale)


def center_origin(ob):
    move_origin(ob, ob.bounds_center)


def move_origin(ob, world_target):
    local_origin = ob.matrix_world.inverted() @ world_target
    ob.data.transform(Matrix.Translation(-local_origin))

    ob.matrix_world.translation = world_target


# Not sure if this works better or not.
# def move_origin(ob, world_target):
#     local_loc = ob.matrix_world.inverted() @ world_target

#     mat = Matrix.Translation(-local_loc)

#     me = ob.data
#     if me.is_editmode:
#         bm = bmesh.from_edit_mesh(me)
#         bm.transform(mat)
#         bmesh.update_edit_mesh(me, False, False)
#     else:
#         me.transform(mat)

#     me.update()

#     ob.matrix_world.translation = world_target


def get_location_matrix(location):
    return Matrix.Translation(location)


def get_rotation_matrix(rotation):
    return rotation.to_matrix().to_4x4()


def get_scale_matrix(scale):
    mat = Matrix()
    for i in range(3):
        mat[i][i] = scale[i]
    return mat


def rotate_and_apply(ob, angle=180):
    new_rot = ob.rotation_euler
    new_rot.x += (radians(angle))

    mat = ob.matrix_world
    loc, rot, sca = mat.decompose()

    ob.data.transform(get_rotation_matrix(new_rot))
    ob.matrix_world = get_location_matrix(loc) @ get_rotation_matrix(Quaternion()) @ get_scale_matrix(sca)
    

def scale_mesh(ob, scale):
    mesh = ob.data
    mat_scale = Matrix.Diagonal( (scale, scale, scale, scale) )
    mesh.transform(mat_scale)
    ob.curvebash.mesh_scale = scale


def set_radius(self, context, curve, i):
    ob = objects.retrieve(context, curve.get('geo'))
    if ob is not None:
        cap1 = objects.find(ob.get('cap1'))
        cap2 = objects.find(ob.get('cap2'))

    index = curve['index']
    mode = curve['mode']

    if mode == 1 and index == -1:
        curve.data.bevel_depth = self.last_scale

    elif mode == 2:
        ob.data.uniform_scale = self.last_scale
        if cap1 and cap2:
            cap1.data.uniform_scale = self.last_scale
            cap2.data.uniform_scale = self.last_scale

    elif mode in {1, 3}:
        ob.uniform_scale = self.last_scale
    

def set_rotation(self, context, curve, i):
    ob = objects.retrieve(context, curve.get('geo'))
    mode  = curve['mode']
    index = curve['index']

    if mode == 1 and index == -1:
        return

    elif mode == 1:
        ob.profile_rot = radians(self.last_rotation)

    elif mode == 2:
        ob.rotation_euler.z = radians(self.last_rotation)
    
    elif mode == 3:
        ob.rotation_euler.z = radians(self.last_rotation)


def set_twist(self, context, curve, i):

    for point in self.curve_points[i]:

        for index, point in enumerate(self.curve_points[i]):
            point.tilt = index * (self.last_twist / ( len( self.curve_points[i] ) -1 )) + self.last_twist_offset
        

def set_slide(self, context, curve, i):
    ob = objects.retrieve(context, curve.get('geo'))
    mode  = curve['mode']
    index = curve['index']

    # spline = curve.data.splines[0]
    # midpoint = spline.calc_length() / 2

    if mode == 1 and index == -1:
        return

    elif mode == 1:
        return

    elif mode == 2:
        ob.array_center = self.last_slide
    
    elif mode == 3:
        ob.location.z = self.last_slide



def set_transforms(self, context, curve, i,  use_last_radius=False, use_last_rotation=False, use_last_twist=False):
    # Sets the curve's initial transform values.
    # If True the curve will inherit transforms from the previous curve.

    if use_last_radius:
        set_radius(self, context, curve, i)    
    
    if use_last_rotation:
        set_rotation(self, context, curve, i)       
    
    if use_last_twist:
        set_twist(self, context, curve, i)   


def reset_radius(self, context, relative=False):
    # Used to cancel any scale operation without canceling the modal.
    
    # reset_random_scale(self, context)

    if relative: # (OPERATOR WAS CANCELLED) Use the starting values.

        for i, curve in enumerate(self.selection):
            ob = objects.retrieve(context, curve.get('geo'))

            if ob is not None:
                cap1 = objects.find(ob.get('cap1'))
                cap2 = objects.find(ob.get('cap2'))

            mode  = curve['mode']
            index = curve['index']

            if mode == 1 and index == -1:
                curve.data.bevel_depth = self.original_scale[i]

            elif mode == 2:
                scale = self.original_scale[i]  # Never mutate "original" val lists.
                if scale < .001:                 # Array scale can never be set
                    scale = .001                 # to 0 or blender will crash.

                ob.data.uniform_scale = scale
                if cap1 and cap2:
                    cap1.data.uniform_scale = ob.data.uniform_scale
                    cap2.data.uniform_scale = ob.data.uniform_scale

            elif mode in {1, 3}:
                ob.uniform_scale = self.original_scale[i]
            
    else: # (NORMAL RESET) Use ABSOLUTE values instead.

        for curve in self.selection:
            ob = objects.retrieve(context, curve.get('geo'))

            if ob is not None:
                cap1 = objects.find(ob.get('cap1'))
                cap2 = objects.find(ob.get('cap2'))

            mode  = curve['mode']
            index = curve['index']

            if mode == 1 and index == -1:
                curve.data.bevel_depth = .1

            elif mode == 2:
                ob.data.uniform_scale = .1
                if cap1 and cap2:
                    cap1.data.uniform_scale = ob.data.uniform_scale
                    cap2.data.uniform_scale = ob.data.uniform_scale

            elif mode in {1, 3}:
                ob.uniform_scale = .1
    
    if addon.debug():
        print(f'Reset Scale (relative={relative})')

def reset_rotation(self, context, relative=False):
    # Used to cancel any rotate operation without canceling the modal.

    # reset_random_rotation(self, context)

    if relative: # (OPERATOR WAS CANCELLED) Use the starting values.

        for i, curve in enumerate(self.selection):
            ob = objects.retrieve(context, curve.get('geo'))
            mode  = curve['mode']
            index = curve['index']

            if mode == 1 and index == -1:
                continue

            if mode == 1:
                ob.profile_rot = radians(self.original_rotation[i])
            
            elif mode in {2, 3}:
                ob.rotation_euler.z = radians(self.original_rotation[i])
        
    else: # (NORMAL RESET) Use ABSOLUTE values instead.

        for curve in self.selection:
            ob = objects.retrieve(context, curve.get('geo'))
            mode  = curve['mode']
            index = curve['index']

            if mode == 1 and index == -1:
                continue

            if mode == 1:
                ob.profile_rot = 0
            
            elif mode in {2, 3}:
                ob.rotation_euler.z = 0
    
    if addon.debug():
        print(f'Reset Rotation (relative={relative})')


def reset_twist(self, context, relative=False):
    # Used to cancel any rotate operation without canceling the modal.

    if relative:

        for i, curve in enumerate(self.selection):
            for index, point in enumerate(self.curve_points[i]):
                point.tilt = index * (self.original_twist[i] / ( len( self.curve_points[i] ) -1 )) + self.original_twist_offset[i]
            
    else:

        for i, curve in enumerate(self.selection):
            for point in self.curve_points[i]:
                point.tilt = 0

    if addon.debug():
        print(f'Reset Twist (relative={relative})')


def reset_slide(self, context, relative=False):

    if relative:

        for i, curve in enumerate(self.selection):
            ob = objects.retrieve(context, curve.get('geo'))
            mode  = curve['mode']
            index = curve['index']

            # spline = curve.data.splines[0]
            # midpoint = spline.calc_length() / 2

            if mode == 1 and index == -1:
                continue

            elif mode == 1:
                continue

            elif mode == 2:
                ob.array_center = self.original_slide[i]
            
            elif mode == 3:
                ob.location.z = self.original_slide[i]
    
    else:

        for i, curve in enumerate(self.selection):
            ob = objects.retrieve(context, curve.get('geo'))
            mode  = curve['mode']
            index = curve['index']

            spline = curve.data.splines[0]
            midpoint = spline.calc_length() / 2

            if mode == 1 and index == -1:
                continue

            elif mode == 1:
                continue

            elif mode == 2:
                ob.array_center = midpoint
            
            elif mode == 3:
                ob.location.z = midpoint


def reset_transforms(self, context, relative):
    # Reset's all transforms (Twist is unadvertedly undone when the rotation resets).

    reset_radius(self, context, relative)
    reset_rotation(self, context, relative)
    reset_twist(self, context, relative)
    reset_slide(self, context, relative)


def update_start_values(self, context, curve, i):
    # START transforms are used for controlling/resetting transformations mid-modal (values are mutable).

    reset_random_scale(self, context)
    reset_random_rotation(self, context)
    # reset_random_twist(self, context)

    mode  = curve['mode']
    index = curve['index']

    # Twist is applied on the curve so it's mode insensitive.
    self.twist_offset[i] = self.curve_points[i][0].tilt
    self.start_twist[i] = self.curve_points[i][-1].tilt - self.curve_points[i][0].tilt

    if mode == 1 and index == -1:
        self.start_rotation[i] = 0
        self.start_scale[i] = curve.data.bevel_depth

        if addon.debug():
            print(f'Start Mesh Scale (pre return): {self.start_scale[i]}')

        return

    ob = objects.retrieve(context, curve.get('geo'))
    if ob is None:
        print('Missing Geo')
        return
    
    if mode == 1:
        self.start_scale[i] = ob.uniform_scale
        self.start_rotation[i] = degrees(ob.profile_rot)

    elif mode == 2:
        self.start_scale[i] = ob.data.uniform_scale
        self.start_rotation[i] = degrees(ob.rotation_euler.z)
        # self.start_slide[i] = curve.data.splines[0].calc_length()/2
        self.start_slide[i] = ob.array_center
    
    elif mode == 3:
        self.start_scale[i] = ob.uniform_scale
        self.start_rotation[i] = degrees(ob.rotation_euler.z)
        # self.start_slide[i] = curve.data.splines[0].calc_length()/2
        self.start_slide[i] = ob.location.z

    
    if addon.debug():
        print(f'Start Mesh Scale (post return): {self.start_scale[i]}')
    

def store_original_transforms(self, context):
    # ORIGINAL transforms are only used when canceling the operator (immutable after this initialization).

    self.original_scale        = self.start_scale.copy()
    self.original_rotation     = self.start_rotation.copy()
    self.original_twist        = self.start_twist.copy()
    self.original_twist_offset = self.twist_offset.copy()
    self.original_slide        = self.start_slide.copy()

    if addon.debug():
        print(f'Original Scale     {self.original_scale}')
        print(f'Original Rotation  {self.original_rotation}')
        print(f'Original Twist     {self.original_twist}')
        print(f'Original Twist Off {self.original_twist_offset}')
        print(f'Original Slide     {self.original_slide}\n')


def set_defaults_for_new_curves(self, context, base_curve):
    # Set the default transformation values for new curves from the input base.

    ob = objects.retrieve(context, base_curve.get('geo'))

    mode  = base_curve['mode']
    index = base_curve['index']

    # SCALE and ROTATION >>
    if mode == 1 and index == -1:
        self.last_scale = base_curve.data.bevel_depth
        self.last_rotation = 0

    elif mode == 1:
        self.last_scale = ob.uniform_scale
        self.last_rotation = degrees(ob.profile_rot)

    elif mode == 2:
        self.last_scale = ob.data.uniform_scale
        self.last_rotation = degrees(ob.rotation_euler.z)
        self.last_slide = ob.array_center
    
    elif mode == 3:
        self.last_scale = ob.uniform_scale
        self.last_rotation = degrees(ob.rotation_euler.z)
        self.last_slide = ob.location.z


    # TWIST >> (mode insensitive)
    curve_type = base_curve.data.splines[0].type
    spline = base_curve.data.splines[0]

    if curve_type == 'BEZIER':
        points = spline.bezier_points

    elif curve_type == 'POLY':
        points = spline.points

    self.last_twist = points[-1].tilt - points[0].tilt
    self.last_twist_offset = points[0].tilt


    # MODE AND INDEX >>
    self.index_list[mode-1] = index

    self.last_mode  = mode
    # self.last_index = index

    if addon.debug():
        print(f'Taking last transforms from selected curve "{base_curve.name}"...')
        print(f'Last Mode:  {self.last_mode}')
        # print(f'Last Index: {self.last_index}')
        print(f'Last Index list: {self.index_list}')
        print(f'Last Scale: {self.last_scale}')
        print(f'Last Rotation: {self.last_rotation}')
        print(f'Last Twist: {self.last_twist}')
        print(f'Last Twist Off: {self.last_twist_offset}\n')


def reset_random_scale(self, context):
    C = len(self.selection)

    self.start_rand_scale = [0] * C
    self.end_rand_scale   = [0] * C


def reset_random_rotation(self, context):
    C = len(self.selection)

    self.start_rand_rotation = [0] * C
    self.end_rand_rotation   = [0] * C


def center_along_curve(context, curve):
    ob = objects.retrieve(context, curve.get('geo'))
    if not ob:
        return
    
    mode  = curve['mode']
    index = curve['index']

    curve_len = curve.data.splines[0].calc_length()

    if mode == 2:
        ob.array_center = curve_len / 2
    elif mode == 3:
        ob.location.z = curve_len / 2
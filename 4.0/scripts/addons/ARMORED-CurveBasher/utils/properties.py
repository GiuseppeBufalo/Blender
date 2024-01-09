import bpy
from bpy.props import FloatVectorProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Object, Mesh, Curve, Collection

import numpy as np
import math
from mathutils import Matrix, Vector, Quaternion

from .. utils import addon
from .. utils import objects
    

def register():
    Object.uniform_scale = FloatProperty(name='Uniform Object Scale', 
            set=set_uniform_object_scale, get=get_uniform_object_scale, unit='LENGTH')
    
    Object.profile_rot = FloatProperty(name='Curve Profile Rotation', 
            set=set_profile_rot, get=get_profile_rot,)

    Object.curve_slide = FloatProperty(name='Curve Slide', 
            set=set_curve_slide, get=get_curve_slide)
    
    Object.bounds_center = FloatVectorProperty(name='Bounding Box Center', 
            get=get_bounds_center, subtype='XYZ', unit='LENGTH')

    Object.array_fit_count = IntProperty(name='Fit to Curve Array Count', 
            get=get_array_fit_count)

    Object.array_count = IntProperty(name='Array Count', 
            get=get_array_count)
            
    Object.array_center = FloatProperty(name='Center Z of the array', 
            get=get_array_center, set=set_array_center)

    Object.array_dimensions = FloatProperty(name='Length Z of the array', 
            get=get_array_dimensions)

    Mesh.dimensions = FloatVectorProperty(name='Mesh Dimensions', 
            get=get_mesh_dimensions, subtype='XYZ', unit='LENGTH')

    Mesh.uniform_scale = FloatProperty(name='Uniform Mesh Scale', 
            set=set_uniform_mesh_scale, get=get_uniform_mesh_scale, unit='LENGTH')

    Collection.type = StringProperty(name=' Type', 
            get=get_collection_type)


def unregister():
    del Object.uniform_scale
    del Object.profile_rot
    del Object.curve_slide
    del Object.bounds_center
    del Object.array_fit_count
    del Mesh.dimensions
    del Mesh.uniform_scale
    del Collection.type


# PROPERTY FUNCTIONS >>
# ---------------------------------------------------------------------

def get_uniform_object_scale(self):
    return self.get('uniform_scale', self.scale.z)


def set_uniform_object_scale(self, value):
    ob = self

    ob.scale = (value, value, value)
    ob['uniform_scale'] = value


def get_uniform_mesh_scale(self):
    return self.get('uniform_scale', 1)    # Small defauklt val is preferable.


def set_uniform_mesh_scale(self, value):
    me = self

    prev_scale = self.uniform_scale
    scale = 1 / prev_scale * value
    mat_scale = Matrix.Diagonal((scale, scale, scale, scale))

    me.transform(mat_scale)
    me['uniform_scale'] = value


def get_profile_rot(self):
    return self.get('profile_rot', 0)


def set_profile_rot(self, value):
    ob = self

    prev_rot = self.profile_rot
    rot = value - prev_rot      # Assume Radians
    mat_rot = Matrix.Rotation(rot, 4, 'Z')

    ob.data.transform(mat_rot)
    ob['profile_rot'] = value


def get_curve_slide(self):
    return self.get('curve_slide', 0)


def set_curve_slide(self, value):
    ob = self

    prev_rot = self.curve_slide
    rot = value - prev_rot      # Assume Radians
    mat_rot = Matrix.Rotation(rot, 4, 'Z')

    ob.data.transform(mat_rot)
    ob['curve_slide'] = value


def get_mesh_dimensions(self):
    me = self
    
    coords = np.empty(3 * len(me.vertices))
    me.vertices.foreach_get('co', coords)

    x, y, z = coords.reshape((-1, 3)).T

    mesh_dim = (
            x.max() - x.min(),
            y.max() - y.min(),
            z.max() - z.min()
            )

    return mesh_dim


def get_bounds_center(self):
    ob = self
    
    local_bbox_center = 0.125 * sum((Vector(b) for b in ob.bound_box), Vector())
    global_bbox_center = ob.matrix_world @ local_bbox_center

    return global_bbox_center


def get_array_dimensions(self):
    ob = self

    array = ob.modifiers.get('CB Array')
    if not array:
        return 0

    array_len = ob.array_count * ob.data.dimensions.z

    if array.start_cap is not None:
        array_len += array.start_cap.dimensions.z

    if array.end_cap is not None:
        array_len += array.end_cap.dimensions.z

    array_len *=  ob.scale.z

    return array_len


def get_array_fit_count(self):
    ob = self

    array = ob.modifiers.get('CB Array')
    if not array:
        return 1
    
    curve = array.curve
    if not curve:
        return 1
    
    curve_len = curve.data.splines[0].calc_length()
    mesh_len = ob.data.dimensions.z * ob.scale.z

    fit_count = math.ceil(curve_len / mesh_len)

    return fit_count


def get_array_count(self):
    ob = self

    mesh_len = ob.data.dimensions.z #* ob.scale.z   # Don't think this is needed
                                                    # considering how curve arrays work.
    array = ob.modifiers.get('CB Array')
    if not array:
        return
    
    if array.fit_type == 'FIXED_COUNT':
        return array.count

    if array.fit_type == 'FIT_LENGTH':
        return math.ceil(array.fit_length / mesh_len)

    if array.fit_type == 'FIT_CURVE':
        curve = array.curve
        if not curve:
            return
        
        return math.ceil(curve.data.splines[0].calc_length() / mesh_len)


def set_array_center(self, value):
    ob = self

    # Use other properties.
    mesh_len = ob.data.dimensions.z# * ob.scale.z
    count = ob.array_count

    mid_z = value - mesh_len * (count-1) / 2

    ob.location.z = mid_z


def get_array_center(self):
    ob = self
    
    # return ob.array_dimensions / 2
    
    # Use other properties.
    mesh_len = ob.data.dimensions.z #* ob.scale.z
    count = ob.array_count

    return ob.location.z + mesh_len / 2 * (count-1)


def get_collection_type(self):
    return 'COLLECTION'
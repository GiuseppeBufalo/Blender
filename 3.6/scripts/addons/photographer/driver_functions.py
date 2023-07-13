import bpy
from bpy.app.handlers import persistent
from mathutils.geometry import distance_point_to_plane
from mathutils import Vector
from .operators.autofocus import dof_calculation


def distance_to_plane(cam_matrix,tracker_matrix):
    cam_dir = cam_matrix.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    dist = abs(distance_point_to_plane(cam_matrix.translation, tracker_matrix.translation, cam_dir))
    return -dist

def dof_near_tracker(cam_matrix,tracker_matrix, fstop, fl, sw, sh):
    cam_dir = cam_matrix.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    dist = abs(distance_point_to_plane(cam_matrix.translation, tracker_matrix.translation, cam_dir))
    return dof_near(fstop, dist, fl, sw, sh)

def dof_far_tracker(cam_matrix,tracker_matrix, fstop, fl, sw, sh):
    cam_dir = cam_matrix.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    dist = abs(distance_point_to_plane(cam_matrix.translation, tracker_matrix.translation, cam_dir))
    return dof_far(fstop, dist, fl, sw, sh)

def dof_near(fstop, dist, fl, sw, sh):
    a, f, h = dof_calculation(fstop, fl, sw, sh)
    nL = (a * dist) / (a + (dist - f))
    return nL

def dof_far(fstop, dist, fl, sw, sh):
    a,f, h = dof_calculation(fstop, fl, sw, sh)
    if (0.01 > (h - dist)):
        fL = 1000 # Clamping to 1km
    else:
        fL = (a * dist) / (a - (dist - f)) 
    return fL

@persistent
def load_handler(dummy):
    # register your drivers
    bpy.app.driver_namespace['distance_to_plane'] = distance_to_plane
    bpy.app.driver_namespace['dof_near'] = dof_near
    bpy.app.driver_namespace['dof_far'] = dof_far
    bpy.app.driver_namespace['dof_near_tracker'] = dof_near_tracker
    bpy.app.driver_namespace['dof_far_tracker'] = dof_far_tracker

def register():
    load_handler(None)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    bpy.app.handlers.load_post.remove(load_handler)

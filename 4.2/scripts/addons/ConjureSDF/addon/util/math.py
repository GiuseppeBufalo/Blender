import bpy

from mathutils import Vector



# from https://b3d.interplanety.org/en/how-to-calculate-the-bounding-sphere-for-selected-objects/
def objects_sphere_bounds(objects):

    # allow for both a list of objects and a single object as input
    if not isinstance(objects, list):
        objects = [objects]

    points_co_global = []

    for obj in objects:
        points_co_global.extend([obj.matrix_world @ Vector(bbox) for bbox in obj.bound_box])

    def get_center(l):
        return (max(l) + min(l)) / 2 if l else 0.0

    x, y, z = [[point_co[i] for point_co in points_co_global] for i in range(3)]
    b_sphere_center = Vector([get_center(axis) for axis in [x, y, z]]) if (x and y and z) else None
    b_sphere_radius = max(((point - b_sphere_center) for point in points_co_global)) if b_sphere_center else None

    
    return b_sphere_center, b_sphere_radius.length


def vec3_min(vecA, vecB):

    tupA = vecA[:]
    tupB = vecB[:]

    return Vector(( min(tupA[0], tupB[0]), min(tupA[1], tupB[1]), min(tupA[2], tupB[2])  ))

def vec3_max(vecA, vecB):

    tupA = vecA[:]
    tupB = vecB[:]

    return Vector(( max(tupA[0], tupB[0]), max(tupA[1], tupB[1]), max(tupA[2], tupB[2]) ))

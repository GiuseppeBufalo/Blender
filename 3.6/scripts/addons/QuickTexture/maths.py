from mathutils import Vector, Matrix
import bpy
import bmesh
import math
import random
from mathutils import *
from math import *
from bpy_extras.view3d_utils import (
    location_3d_to_region_2d,
    region_2d_to_vector_3d,
    region_2d_to_location_3d,
)
from bpy_extras import view3d_utils
from mathutils.geometry import intersect_line_plane
from . import utils
import numpy


def matrix_from_face(obj, index, context):

    # World = Global
    # Local = Object
    # Matrix World Space is the unapplied global transformation
    # If transformations have been applied, you can create your own object matrix from a normal and up or any 3 non collinear points
    # Put an object back to origin with reset transformations by multiplying the world matrix with the matrix.inverted()
    # Matrix multiplication goes right to left -> C * B * A
    # Vectors can be multiplied, use mw @ vector to move it into object space. Use vector @ mwi to move it into global space

    mw = obj.matrix_world.copy()
    mwi = mw.inverted()

    deg = context.evaluated_depsgraph_get()

    src_bm = bmesh.new()

    mesh = obj.evaluated_get(deg).to_mesh()
    src_bm.from_mesh(mesh)

    # src_bm.from_object(obj, deg)

    src_bm.faces.ensure_lookup_table()
    src_bm.verts.ensure_lookup_table()
    src_face = src_bm.faces[index]

    normal = src_bm.faces[index].normal @ mwi
    tangent = src_face.calc_tangent_edge() @ mwi
    bitangent = normal.cross(tangent)

    src_mat = Matrix()
    src_mat[0].xyz = tangent.normalized()
    src_mat[1].xyz = bitangent.normalized()
    src_mat[2].xyz = normal.normalized()

    # C# is column major, so you need to transpose it to make it row major. Now [2] will access the "normal"
    return src_mat.transposed()


def angle_cosine(v1, v2):
    # returns the cosine of the angle between v1 and v2. For collinear vectors, this is 1. A zero-vector argument will result in division by zero
    return v1.dot(v2) / math.sqrt(v1.dot(v1) * v2.dot(v2))


def closest_vec(vec1, vec2, test):

    # squared if I don't care about the 'direction', just the axis
    c1 = angle_cosine(vec1, test) ** 2  # remove the **2
    c2 = angle_cosine(vec2, test) ** 2  # remove the **2

    return 0 if c1 >= c2 else 1


def draw_circle(start, r):

    # circle
    theta = 2 * 3.1415926 / 32
    c = math.cos(theta)  # precalculate the sine and cosine
    s = math.sin(theta)
    aX = r  # we start at angle = 0
    aY = 0
    ptArray = []

    for i in range(33):
        vX = aX + start[0]  # output vertex
        vY = aY + start[1]  # output vertex

        t = aX
        aX = c * aX - s * aY
        aY = s * t + c * aY
        circ = Vector((vX, vY))

        ptArray.append(circ)

    ptArray = ptArray[1:]

    return ptArray


def rotate_point(point, angle, center_point=(0, 0)):
    """Rotates a point around center_point(origin by default)
    Angle is in degrees.
    Rotation is counter-clockwise
    """
    angle_rad = radians(angle % 360)
    # Shift the point so that center_point becomes the origin
    new_point = (point[0] - center_point[0], point[1] - center_point[1])
    new_point = (
        new_point[0] * cos(angle_rad) - new_point[1] * sin(angle_rad),
        new_point[0] * sin(angle_rad) + new_point[1] * cos(angle_rad),
    )
    # Reverse the shifting we have done
    new_point = (new_point[0] + center_point[0], new_point[1] + center_point[1])
    return new_point


def draw_circle_2d(start, r, res, reg, rv3d, view):

    # meters to pixels
    x1 = region_2d_to_location_3d(reg, rv3d, start, Vector((0, 0, 0)))
    aa = Vector((rv3d.perspective_matrix[1][0:3])).normalized()

    y = x1 + aa * r

    x2 = location_3d_to_region_2d(reg, rv3d, y)
    dist = (start - x2).length

    # circle
    theta = 2 * 3.1415926 / res
    c = math.cos(theta)  # precalculate the sine and cosine
    s = math.sin(theta)
    aX = dist / 2  # we start at angle = 0
    aY = 0
    ptArray = []

    for i in range(res + 1):
        vX = aX + start[0]  # output vertex
        vY = aY + start[1]  # output vertex

        t = aX
        aX = c * aX - s * aY
        aY = s * t + c * aY
        circ = Vector((vX, vY))

        circ = rotate_point(circ, 45, start)

        ptArray.append(circ)

    ptArray = ptArray[1:]

    return ptArray


def draw_circle_3d(coord, location, r, m, viewmat, brushres, reg, rv3d):

    if brushres == 10:
        res = 64
    if brushres == 9:
        res = 32
    if brushres == 8:
        res = 24
    if brushres == 7:
        res = 16
    if brushres == 6:
        res = 12
    if brushres == 5:
        res = 10
    if brushres == 4:
        res = 8
    if brushres == 3:
        res = 6
    if brushres == 2:
        res = 5
    if brushres == 1:
        res = 3

    startloc = utils.coord_on_plane(
        reg, rv3d, coord, location, Vector((m.transposed()[2][:3]))
    )

    theta = 2 * 3.1415926 / res
    c = math.cos(theta)  # precalculate the sine and cosine
    s = math.sin(theta)
    aX = r  # we start at angle = 0
    aY = 0
    ptArray = []
    ptArray2 = []

    for i in range(res + 1):
        vX = aX + coord[0]  # output vertex
        vY = aY + coord[1]  # output vertex

        t = aX
        aX = c * aX - s * aY
        aY = s * t + c * aY
        circ = (vX, vY)

        # converting 2d points to 3d
        v = Vector((region_2d_to_location_3d(reg, rv3d, circ, startloc)))

        t = Matrix.Translation(startloc)
        v = t.inverted() @ v
        v = v @ viewmat.inverted().to_3x3()
        v = v @ m.transposed().to_3x3()
        v = t @ v
        ptArray.append(v)

        circ2 = location_3d_to_region_2d(reg, rv3d, v)
        ptArray2.append(circ2)

    # return 3D and 2D coords
    return ptArray, ptArray2


def calc_percent(value, percentage):
    result = value * (percentage / 100)
    return result


def remap(value, srcMin, srcMax, resMin, resMax):
    srcRange = srcMax - srcMin
    if srcRange == 0:
        return resMin
    else:
        resRange = resMax - resMin
        return (((value - srcMin) * resRange) / srcRange) + resMin


def moving_avg(x, n):
    cumsum = numpy.cumsum(numpy.insert(x, 0, 0))
    return (cumsum[n:] - cumsum[:-n]) / float(n)


def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

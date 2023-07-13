import sys
from mathutils import Vector, Matrix
from math import radians
import numpy as np
from . draw import draw_vector, draw_point, draw_points



def mul(a, b):
    return a * b

def remap(value, srcMin, srcMax, resMin, resMax):
    srcRange = srcMax - srcMin
    if srcRange == 0:
        return resMin
    else:
        resRange = resMax - resMin
        return (((value - srcMin) * resRange) / srcRange) + resMin



def absvector(vector):
    return Vector([abs(v) for v in vector])

def get_center_between_points(point1, point2, center=0.5):
    return point1 + (point2 - point1) * center


def get_center_between_verts(vert1, vert2, center=0.5):
    return get_center_between_points(vert1.co, vert2.co, center=center)


def get_midpoint(coords):
    avg = Vector()
    for co in coords:
        avg += Vector(co)

    return avg / len(coords)


def get_edge_normal(edge):
    return average_normals([f.normal for f in edge.link_faces])


def average_locations(locationslist, size=3):
    avg = Vector.Fill(size)

    for n in locationslist:
        avg += n

    return avg / len(locationslist)


def average_normals(normalslist):
    avg = Vector()

    for n in normalslist:
        avg += n

    return avg.normalized()


def get_world_space_normal(normal, mx):

    return (mx.inverted_safe().transposed().to_3x3() @ normal).normalized()



def flatten_matrix(mx):
    return [i for col in mx.col for i in col]


def serialize_matrix(mx, trimsheet=False):
    if trimsheet:
        return [list(row) for row in mx.row[:2]]
    else:
        return [list(row) for row in mx.row]


def deserialize_matrix(listoflists, trimsheet=False):
    if trimsheet:
        return Matrix(listoflists + [0, 0, 0, 0] + [0, 0, 0, 1])
    else:
        return Matrix(listoflists)


def get_loc_matrix(location):
    return Matrix.Translation(location)


def get_rot_matrix(rotation):
    return rotation.to_matrix().to_4x4()


def get_sca_matrix(scale):
    scale_mx = Matrix()
    for i in range(3):
        scale_mx[i][i] = scale[i]
    return scale_mx


def create_rotation_matrix_from_normal(mx, normal, location=Vector((0, 0, 0)), debug=False):
    objup = (mx.to_3x3() @ Vector((0, 0, 1))).normalized()
    normal = normal.normalized()
    dot = normal.normalized().dot(objup)

    if abs(round(dot, 6)) == 1:
        objup = mx.to_3x3() @ Vector((1, 0, 0))

    tangent = objup.cross(normal)
    binormal = tangent.cross(-normal)

    if debug:
        objloc, _, _ = mx.decompose()
        draw_vector(objup, objloc, modal=False)
        draw_vector(normal, location, color=(0, 0, 1), modal=False)
        draw_vector(tangent, location, color=(1, 0, 0), modal=False)
        draw_vector(binormal, location, color=(0, 1, 0), modal=False)


    rotmx = Matrix()
    rotmx.col[0].xyz = tangent.normalized()
    rotmx.col[1].xyz = binormal.normalized()
    rotmx.col[2].xyz = normal.normalized()

    return rotmx


def create_rotation_matrix_from_vertex(obj, vert, debug=False):
    mx = obj.matrix_world

    normal = mx.to_3x3() @ vert.normal

    if vert.link_edges:
        longest_edge = max([e for e in vert.link_edges], key=lambda x: x.calc_length())
        binormal = (mx.to_3x3() @ (longest_edge.other_vert(vert).co - vert.co)).normalized()

        tangent = binormal.cross(normal).normalized()

        binormal = normal.cross(tangent).normalized()

    else:
        objup = (mx.to_3x3() @ Vector((0, 0, 1))).normalized()


        dot = normal.dot(objup)
        if abs(round(dot, 6)) == 1:
            objup = (mx.to_3x3() @ Vector((1, 0, 0))).normalized()

        if debug:
            draw_vector(objup, origin=mx @ vert.co, modal=False)

        tangent = normal.cross(objup).normalized()
        binormal = normal.cross(tangent).normalized()

    if debug:
        draw_vector(normal, origin=mx @ vert.co, color=blue, modal=False)
        draw_vector(binormal, origin=mx @ vert.co, color=green, modal=False)
        draw_vector(tangent, origin=mx @ vert.co, color=red, modal=False)

    rot = Matrix()
    rot[0].xyz = tangent
    rot[1].xyz = binormal
    rot[2].xyz = normal
    return rot.transposed()


def create_rotation_matrix_from_edge(obj, edge, location=Vector((0, 0, 0)), debug=False):
    mx = obj.matrix_world

    binormal = (mx.to_3x3() @ (edge.verts[1].co - edge.verts[0].co)).normalized()

    if edge.link_faces:
        normal = (mx.to_3x3() @ get_edge_normal(edge)).normalized()
        tangent = binormal.cross(normal)

    else:
        objup = (mx.to_3x3() @ Vector((0, 0, 1))).normalized()

        dot = binormal.dot(objup)
        if abs(round(dot, 6)) == 1:
            objup = (mx.to_3x3() @ Vector((1, 0, 0))).normalized()

        tangent = (binormal.cross(objup)).normalized()
        normal = tangent.cross(binormal)

    if debug:
        draw_vector(normal, origin=location, color=blue, modal=False)
        draw_vector(binormal, origin=location, color=green, modal=False)
        draw_vector(tangent, origin=location, color=red, modal=False)

    rotmx = Matrix()
    rotmx[0].xyz = tangent
    rotmx[1].xyz = binormal
    rotmx[2].xyz = normal

    return rotmx.transposed()


def create_rotation_matrix_from_face(mx, face, location=Vector((0, 0, 0)), debug=False):

    normal = (mx.to_3x3() @ face.normal).normalized()

    tangent = (mx.to_3x3() @ face.calc_tangent_edge_pair()).normalized()

    binormal = normal.cross(tangent)

    if debug:
        draw_vector(normal, origin=location, color=blue, modal=False)
        draw_vector(binormal, origin=location, color=green, modal=False)
        draw_vector(tangent, origin=location, color=red, modal=False)

    rot = Matrix()
    rot[0].xyz = tangent
    rot[1].xyz = binormal
    rot[2].xyz = normal
    return rot.transposed()


def create_rotation_difference_matrix_from_quat(v1, v2):
    q = v1.rotation_difference(v2)
    return q.to_matrix().to_4x4()


def create_rotation_difference_matrix_from_angle(v1, v2):
    angle = v1.angle(v2)
    axis = v1.cross(v2)

    return Matrix.Rotation(angle, 4, axis)


def resample_coords(coords, cyclic, segments=None, shift=0, debug=False):

    if not segments:
        segments = len(coords) - 1


    if len(coords) < 2:
        return coords

    if not cyclic and shift != 0:  # not PEP but it shows that we want shift = 0
        print('Not shifting because this is not a cyclic vert chain')
        shift = 0

    arch_len = 0
    cumulative_lengths = [0]  # TODO: make this the right size and dont append

    for i in range(0, len(coords) - 1):
        v0 = coords[i]
        v1 = coords[i + 1]
        V = v1 - v0
        arch_len += V.length
        cumulative_lengths.append(arch_len)

    if cyclic:
        v0 = coords[-1]
        v1 = coords[0]
        V = v1 - v0
        arch_len += V.length
        cumulative_lengths.append(arch_len)
        segments += 1


    if cyclic:
        new_coords = [[None]] * segments
    else:
        new_coords = [[None]] * (segments + 1)
        new_coords[0] = coords[0]
        new_coords[-1] = coords[-1]

    n = 0

    for i in range(0, segments - 1 + cyclic * 1):
        desired_length_raw = (i + 1 + cyclic * -1) / segments * arch_len + shift * arch_len / segments
        if desired_length_raw > arch_len:
            desired_length = desired_length_raw - arch_len
        elif desired_length_raw < 0:
            desired_length = arch_len + desired_length_raw  # this is the end, + a negative number
        else:
            desired_length = desired_length_raw

        for j in range(n, len(coords) + 1):

            if cumulative_lengths[j] > desired_length:
                break

        extra = desired_length - cumulative_lengths[j- 1]

        if j == len(coords):
            new_coords[i + 1 + cyclic * -1] = coords[j - 1] + extra * (coords[0] - coords[j - 1]).normalized()
        else:
            new_coords[i + 1 + cyclic * -1] = coords[j - 1] + extra * (coords[j] - coords[j - 1]).normalized()

    if debug:
        print(len(coords), len(new_coords))
        print(cumulative_lengths)
        print(arch_len)

    return new_coords



def create_bbox(obj=None, coords=None):
    minx = miny = minz = sys.maxsize
    maxx = maxy = maxz = -sys.maxsize

    if obj:
        coords = [v.co for v in obj.data.vertices]

    if coords:
        for co in coords:
            minx = co.x if co.x < minx else minx
            miny = co.y if co.y < miny else miny
            minz = co.z if co.z < minz else minz

            maxx = co.x if co.x > maxx else maxx
            maxy = co.y if co.y > maxy else maxy
            maxz = co.z if co.z > maxz else maxz


        coords = [(minx, miny, minz), (maxx, miny, minz), (maxx, maxy, minz), (minx, maxy, minz),
                  (minx, miny, maxz), (maxx, miny, maxz), (maxx, maxy, maxz), (minx, maxy, maxz)]

        edge_indices = [(0, 1), (1, 2), (2, 3), (3, 0),
                        (4, 5), (5, 6), (6, 7), (7, 4),
                        (0, 4), (1, 5), (2, 6), (3, 7)]

        tri_indices = [(0, 1, 2), (0, 2, 3),
                       (4, 5, 6), (4, 6, 7),
                       (0, 1, 5), (0, 5, 4),
                       (3, 0, 3), (3, 4, 7),
                       (1, 2, 6), (1, 6, 5),
                       (2, 3, 7), (2, 7, 6)]

        return coords, edge_indices, tri_indices


def get_bbox_dimensions(coords):
    width = (Vector(coords[1]) - Vector(coords[0])).length
    depth = (Vector(coords[3]) - Vector(coords[0])).length
    height = (Vector(coords[4]) - Vector(coords[0])).length

    return width, depth, height


def create_selection_bbox(coords, mx, debug=False):
    minx = min(coords, key=lambda c: c.x)
    maxx = max(coords, key=lambda c: c.x)

    miny = min(coords, key=lambda c: c.y)
    maxy = max(coords, key=lambda c: c.y)

    minz = min(coords, key=lambda c: c.z)
    maxz = max(coords, key=lambda c: c.z)

    if debug:
        draw_point(minx, mx=mx, color=(1, 0, 0), modal=False)
        draw_point(maxx, mx=mx, color=(1, 0, 0), modal=False)

        draw_point(miny, mx=mx, color=(0, 1, 0), modal=False)
        draw_point(maxy, mx=mx, color=(0, 1, 0), modal=False)

        draw_point(minz, mx=mx, color=(0, 0, 1), modal=False)
        draw_point(maxz, mx=mx, color=(0, 0, 1), modal=False)

    midx = get_center_between_points(minx, maxx)
    midy = get_center_between_points(miny, maxy)
    midz = get_center_between_points(minz, maxz)

    if debug:
        draw_point(midx, mx=mx, color=(1, 0, 0), modal=False)
        draw_point(midy, mx=mx, color=(0, 1, 0), modal=False)
        draw_point(midz, mx=mx, color=(0, 0, 1), modal=False)

    mid = Vector((midx.x, midy.y, midz.z))

    if debug:
        draw_point(mid, mx=mx, color=(1, 1, 1), modal=False)

    bbox = [Vector((minx.x, miny.y, minz.z)), Vector((maxx.x, miny.y, minz.z)),
            Vector((maxx.x, maxy.y, minz.z)), Vector((minx.x, maxy.y, minz.z)),
            Vector((minx.x, miny.y, maxz.z)), Vector((maxx.x, miny.y, maxz.z)),
            Vector((maxx.x, maxy.y, maxz.z)), Vector((minx.x, maxy.y, maxz.z))]

    if debug:
        draw_points(bbox, mx=mx, color=(1, 1, 0), modal=False)

    return bbox, mid



def create_trimmx_from_location_and_scale(location, scale):
    trimmx = Matrix()
    trimmx.col[3][0:2] = location

    trimmx[0][0] = scale[0]
    trimmx[1][1] = scale[1]

    return trimmx


def box_coords_to_trimmx(start, end, dimensions):

    mid = average_locations([start, end])

    trimmx = Matrix()
    trimmx.col[3].xyz = Vector((*mid.xy, 0))

    width = (start - Vector((end.x, start.y, 0))).length
    height = (start - Vector((start.x, end.y, 0))).length

    trimmx[0][0] = width / dimensions.x
    trimmx[1][1] = height / dimensions.y
    trimmx[2][2] = 0

    return trimmx


def trimmx_to_box_coords(trimmx, dimensions):

    mid = trimmx.col[3].xy

    width = trimmx[0][0] * dimensions.x
    height = trimmx[1][1] * dimensions.y

    start = Vector((mid.x - width / 2, mid.y + height / 2, 0))
    end = Vector((mid.x + width / 2, mid.y - height / 2, 0))

    return start, end



def img_coords_to_trimmx(coords, dimensions, resolution):

    location = [(coords[0] + dimensions[0] / 2 - resolution[0] / 2) / 1000, - (coords[1] + dimensions[1] / 2 - resolution[1] / 2) / 1000]
    scale = (dimensions[0] / resolution[0], dimensions[1] / resolution[1])

    trimmx = Matrix()
    trimmx.col[3].xy = location
    trimmx[0][0] = scale[0]
    trimmx[1][1] = scale[1]
    trimmx[2][2] = 0

    return trimmx


def trimmx_to_img_coords(trimmx, resolution):

    mid = trimmx.col[3].xy

    width = trimmx[0][0] * resolution[0] / 1000
    height = trimmx[1][1] * resolution[1] / 1000

    top_left = [co for co in Vector((resolution[0] / 2, resolution[1] / 2)) + Vector((mid.x - width / 2, - (mid.y + height / 2))) * 1000]
    bottom_right = [co for co in Vector((resolution[0] / 2, resolution[1] / 2)) + Vector((mid.x + width / 2, - (mid.y - height / 2))) * 1000]

    dimensions = [bottom_right[0] - top_left[0], bottom_right[1] - top_left[1]]

    return [round(co) for co in top_left], [round(dim) for dim in dimensions]


def img_coords_to_mesh_coords(dimensions):

    return [Vector((-dimensions[0] / 2 / 1000, -dimensions[1] / 2 / 1000, 0)), Vector((dimensions[0] / 2 / 1000, -dimensions[1] / 2 / 1000, 0)), Vector((dimensions[0] / 2 / 1000, dimensions[1] / 2 / 1000, 0)), Vector((-dimensions[0] / 2 / 1000, dimensions[1] / 2 / 1000, 0))]


def img_coords_to_uv_coords(top_left, dimensions, resolution):

    co1 = Vector((top_left[0] / resolution[0], 1 - ((top_left[1] + dimensions[1]) / resolution[1])))
    co2 = Vector(((top_left[0] + dimensions[0]) / resolution[0], 1 - ((top_left[1] + dimensions[1]) / resolution[1])))
    co3 = Vector(((top_left[0] + dimensions[0]) / resolution[0], 1 - top_left[1] / resolution[1]))
    co4 = Vector(((top_left[0] / resolution[0], 1 - top_left[1] / resolution[1])))

    return [co1, co2, co3, co4]



def trilaterate(coords, distances, debug=False):

    p1, p2, p3, p4 = coords
    r1, r2, r3, r4 = distances

    e_x = (p2 - p1) / np.linalg.norm(p2 - p1)
    i = np.dot(e_x, (p3 - p1))

    e_y = (p3 - p1 - (i * e_x)) / (np.linalg.norm(p3 - p1 - (i * e_x)))
    e_z = np.cross(e_x, e_y)

    d = np.linalg.norm(p2 - p1)
    j = np.dot(e_y, (p3 - p1))

    x = ((r1**2) - (r2**2) + (d**2)) / (2 * d)
    y = (((r1**2) - (r3**2) + (i**2) + (j**2)) / (2 * j)) - ((i / j) * (x))

    z1 = np.sqrt(abs(r1**2 - x**2 - y**2))
    z2 = np.sqrt(abs(r1**2 - x**2 - y**2)) * (-1)

    ans1 = p1 + (x * e_x) + (y * e_y) + (z1 * e_z)
    ans2 = p1 + (x * e_x) + (y * e_y) + (z2 * e_z)

    if "nan" in str(ans1):
        coords = [Vector(co) for co in coords]
        return average_locations(coords)

    dist1 = np.linalg.norm(p4 - ans1)
    dist2 = np.linalg.norm(p4 - ans2)

    if np.abs(r4 - dist1) < np.abs(r4 - dist2):
        ans = [round(co, 6) for co in ans1]
    else:
        ans = [round(co, 6) for co in ans2]

    return ans

import bpy
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree as BVH
from mathutils.geometry import intersect_line_plane
from math import radians
import sys
from . math import average_locations, get_sca_matrix, get_world_space_normal

from . draw import draw_point

def cast_bvh_ray_from_object(source, ray_direction, backtrack=None, limit=None, exclude_decals=True, debug=False):
    mxw = source.matrix_world
    origin, _, _ = mxw.decompose()
    direction = mxw @ Vector(ray_direction) - origin

    if backtrack:
        origin = origin - direction * backtrack

    if exclude_decals:
        visible = [obj for obj in bpy.context.visible_objects if obj.type == "MESH" and obj != source and not obj.DM.isdecal]
    else:
        visible = [obj for obj in bpy.context.visible_objects if obj.type == "MESH" and obj != source]

    hitobj = None
    hitlocation = None
    hitnormal = None
    hitindex = None
    hitdistance = sys.maxsize

    for obj in visible:
        mx = obj.matrix_world
        mxi = mx.inverted_safe()

        origin_local = mxi @ origin
        direction_local = mxi.to_3x3() @ direction

        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bvh = BVH.FromBMesh(bm)

        location, normal, index, distance = bvh.ray_cast(origin_local, direction_local)

        if debug:
            print("candidate:", obj.name, location, normal, index, distance)

        if normal:
            dot = normal.dot(direction_local)

            if dot > 0:
                rlocation, rnormal, rindex, rdistance = bvh.ray_cast(origin_local, direction_local * -1)

                if debug:
                    print(" reverse candidate:", obj.name, rlocation, rnormal, rindex, rdistance)

                if rnormal and rnormal.dot(direction_local) < 0 and rdistance < distance:
                    location = rlocation
                    normal = rnormal
                    index = rindex
                    distance = rdistance

                    if debug:
                        print("  reverse ray cast found a closer and properly aligned face.")

                else:
                    distance = None

                    if debug:
                        print(" a backface was hit, treating it as if nothing was hit.")

        bm.free()

        if distance:
            if distance < hitdistance:
                hitobj, hitlocation, hitnormal, hitindex, hitdistance = obj, mx @ location, mx.to_3x3() @ normal, index, distance

    if debug:
        print("best hit:", hitobj.name if hitobj else None, hitlocation, hitnormal, hitindex, hitdistance if hitobj else None)

    if hitobj:
        if limit:
            if hitdistance < limit:
                return hitobj, hitlocation, hitnormal, hitindex, hitdistance
            else:
                if debug:
                    print("hit is beyond the limit")
                return None, None, None, None, None

        else:
            return hitobj, hitlocation, hitnormal, hitindex, hitdistance

    return None, None, None, None, None

def get_bvh_ray_distance_from_verts(target, source, ray_direction, backtrack=None, limit=None, debug=False):
    smxw = source.matrix_world
    origin, _, _ = smxw.decompose()
    direction = smxw @ Vector(ray_direction) - origin

    tmxw = target.matrix_world
    tmxi = tmxw.inverted_safe()
    direction_local = tmxi.to_3x3() @ direction

    bm = bmesh.new()
    bm.from_mesh(target.data)
    bvh = BVH.FromBMesh(bm)

    front_distances = []
    back_distances = []

    for v in source.data.vertices:
        co_world = smxw @ v.co

        co_local = tmxi @ co_world

        location, normal, index, distance = bvh.ray_cast(co_local, direction_local)

        reverse = False

        if normal:
            dot = normal.dot(direction_local)

            if dot < 0:
                front_distances.append(distance)

                if debug:
                    print("frontside", index, distance)

            else:
                reverse = True

        else:
            reverse = True

        if reverse:
            location, normal, index, distance = bvh.ray_cast(co_local, direction_local * -1)

            if normal:
                dot = normal.dot(direction_local)

                if dot < 0:
                    back_distances.append(distance)

                    if debug:
                        print("backside", index, distance)

        if debug and index:
            target.data.polygons[index].select = True

    bm.free()

    front = max(front_distances) if front_distances else 0
    back = max(back_distances) if back_distances else 0

    scalemx = get_sca_matrix(tmxw.to_scale())

    return (scalemx @ Vector((0, 0, front))).z, (scalemx @ Vector((0, 0, back))).z

def cast_bvh_ray_from_mouse(mousepos, candidates=None, depsgraph=None, exclude_decals=True, debug=False):
    region = bpy.context.region
    region_data = bpy.context.region_data

    origin_3d = region_2d_to_origin_3d(region, region_data, mousepos)
    vector_3d = region_2d_to_vector_3d(region, region_data, mousepos)

    if not candidates:
        candidates = bpy.context.visible_objects

    if exclude_decals:
        objects = [(obj, None) for obj in candidates if obj.type == "MESH" and not obj.DM.isdecal]
    else:
        objects = [(obj, None) for obj in candidates if obj.type == "MESH"]

    hitobj = None
    hitlocation = None
    hitnormal = None
    hitindex = None
    hitdistance = sys.maxsize

    for obj, src in objects:
        mx = obj.matrix_world
        mxi = mx.inverted_safe()

        ray_origin = mxi @ origin_3d
        ray_direction = mxi.to_3x3() @ vector_3d

        bm = bmesh.new()

        mesh = obj.evaluated_get(depsgraph).to_mesh() if depsgraph else obj.data
        bm.from_mesh(mesh)

        bvh = BVH.FromBMesh(bm)

        location, normal, index, distance = bvh.ray_cast(ray_origin, ray_direction)

        if distance:
            distance = (mx @ location - origin_3d).length

        bm.free()

        if debug:
            print("candidate:", obj.name, location, normal, index, distance)

        if distance and distance < hitdistance:
            hitobj, hitlocation, hitnormal, hitindex, hitdistance = obj, mx @ location, mx.to_3x3() @ normal, index, distance

    if debug:
        print("best hit:", hitobj.name if hitobj else None, hitlocation, hitnormal, hitindex, hitdistance if hitobj else None)
        print()

    if hitobj:
        return hitobj, hitlocation, hitnormal, hitindex, hitdistance

    return None, None, None, None, None

def cast_obj_ray_from_object(depsgraph, source, ray_direction, backtrack=None, limit=None, exclude_decals=True, debug=False):
    mxw = source.matrix_world
    origin, _, _ = mxw.decompose()
    direction = mxw @ Vector(ray_direction) - origin

    if backtrack:
        origin = origin - direction * backtrack

    if exclude_decals:
        visible = [obj for obj in bpy.context.visible_objects if obj.type == "MESH" and obj != source and not obj.DM.isdecal]
    else:
        visible = [obj for obj in bpy.context.visible_objects if obj.type == "MESH" and obj != source]

    hitobj = None
    hitlocation = None
    hitnormal = None
    hitindex = None
    hitdistance = sys.maxsize

    for obj in visible:
        mx = obj.matrix_world
        mxi = mx.inverted_safe()

        origin_local = mxi @ origin
        direction_local = mxi.to_3x3() @ direction

        obj_eval = obj.evaluated_get(depsgraph)

        if obj_eval.data.polygons:
            success, location, normal, index = obj.ray_cast(origin=origin_local, direction=direction_local)
            distance = (mx @ location - origin).length if success else sys.maxsize

            if debug:
                print("candidate:", success, obj.name, location, normal, index, distance)

            if success:
                dot = normal.dot(direction_local)

                if dot > 0:
                    rsuccess, rlocation, rnormal, rindex = obj.ray_cast(origin=origin_local, direction=direction_local * -1)
                    rdistance = (mx @ rlocation - origin).length if rsuccess else sys.maxsize

                    if debug:
                        print(" reverse candidate:", rsuccess, obj.name, rlocation, rnormal, rindex, rdistance)

                    if rsuccess and rnormal.dot(direction_local) < 0 and rdistance < distance:
                        location = rlocation
                        normal = rnormal
                        index = rindex
                        distance = rdistance

                        if debug:
                            print("  reverse ray cast found a closer and properly aligned face.")

                    else:
                        distance = sys.maxsize

                        if debug:
                            print(" a backface was hit, treating it as if nothing was hit.")

            if success:
                if distance < hitdistance:
                    hitobj, hitlocation, hitnormal, hitindex, hitdistance = obj, mx @ location, mx.to_3x3() @ normal, index, distance

        elif debug:
                print("candidate:", obj, "has no evaluated mesh containing faces")

    if debug:
        print("best hit:", hitobj.name if hitobj else None, hitlocation, hitnormal, hitindex, hitdistance if hitobj else None)
        print()

    if hitobj:
        if limit:
            if hitdistance < limit:
                return hitobj, hitobj.evaluated_get(depsgraph), hitlocation, hitnormal, hitindex, hitdistance
            else:
                if debug:
                    print("hit is beyond the limit")
                return None, None, None, None, None, None

        else:
            return hitobj, hitobj.evaluated_get(depsgraph), hitlocation, hitnormal, hitindex, hitdistance

    return None, None, None, None, None, None

def cast_obj_ray_from_mouse(mousepos, candidates=None, exclude_decals=True, exclude_objects=[], debug=False):
    region = bpy.context.region
    region_data = bpy.context.region_data

    origin_3d = region_2d_to_origin_3d(region, region_data, mousepos)
    vector_3d = region_2d_to_vector_3d(region, region_data, mousepos)

    if not candidates:
        candidates = bpy.context.visible_objects

    if exclude_decals:
        objects = [obj for obj in candidates if obj.type == "MESH" and not obj.DM.isdecal and obj not in exclude_objects]
    else:
        objects = [obj for obj in candidates if obj.type == "MESH" and obj not in exclude_objects]

    hitobj = None
    hitlocation = None
    hitnormal = None
    hitindex = None
    hitdistance = sys.maxsize

    for obj in objects:
        mx = obj.matrix_world
        mxi = mx.inverted_safe()

        ray_origin = mxi @ origin_3d
        ray_direction = mxi.to_3x3() @ vector_3d

        success, location, normal, index = obj.ray_cast(origin=ray_origin, direction=ray_direction)
        distance = (mx @ location - origin_3d).length

        if debug:
            print("candidate:", success, obj.name, location, normal, index, distance)

        if success and distance < hitdistance:
            hitobj, hitlocation, hitnormal, hitindex, hitdistance = obj, mx @ location, get_world_space_normal(normal, mx), index, distance

    if debug:
        print("best hit:", hitobj.name if hitobj else None, hitlocation, hitnormal, hitindex, hitdistance if hitobj else None)
        print()

    if hitobj:
        return hitobj, hitlocation, hitnormal, hitindex, hitdistance

    return None, None, None, None, None

def find_nearest(targets, origin, debug=False):
    nearestobj = None
    nearestlocation = None
    nearestnormal = None
    nearestindex = None
    nearestdistance = sys.maxsize

    for target in targets:
        bm = bmesh.new()
        bm.from_mesh(target.data)
        bvh = BVH.FromBMesh(bm)

        mx = target.matrix_world

        origin_local = mx.inverted_safe() @ origin

        location, normal, index, distance = bvh.find_nearest(origin_local)

        if debug:
            print("candidate:", target, location, normal, index, distance)

        if distance is not None and distance < nearestdistance:
            nearestobj, nearestlocation, nearestnormal, nearestindex, nearestdistance = target, location, normal, index, distance

    if debug:
        print("best hit:", nearestobj, nearestlocation, nearestnormal, nearestindex, nearestdistance)

    return nearestobj, mx @ nearestlocation, mx.to_3x3() @ nearestnormal, nearestindex, nearestdistance

def shrinkwrap(bm, bmt, debug=False):
    bvh = BVH.FromBMesh(bmt)

    for v in bm.verts:
        location, normal, index, distance = bvh.find_nearest(v.co)

        if debug:
            print(location, normal, index, distance)

        if location:
            v.co = location

    bmt.free()

def find_nearest_normals(bm, targetmesh, debug=False):
    bmt = bmesh.new()
    bmt.from_mesh(targetmesh)
    bvh = BVH.FromBMesh(bmt)

    normals = {}

    for v in bm.verts:
        location, normal, index, distance = bvh.find_nearest(v.co)

        if debug:
            print(v.index, location, normal, index, distance)

        normals[v] = normal

    return normals, bmt

def get_closest(depsgraph, targets, origin, debug=False):
    nearestobj = None
    nearestlocation = None
    nearestnormal = None
    nearestindex = None
    nearestdistance = sys.maxsize

    for target in targets:
        mx = target.matrix_world

        origin_local = mx.inverted_safe() @ origin

        target_eval = target.evaluated_get(depsgraph)

        if target_eval.data.polygons:
            success, location, normal, index = target.closest_point_on_mesh(origin_local)

            distance = (mx @ location - origin).length if success else sys.maxsize

            if debug:
                print("candidate:", success, target, location, normal, index, distance)

            if distance is not None and distance < nearestdistance:
                nearestobj, nearestlocation, nearestnormal, nearestindex, nearestdistance = target, location, normal, index, distance

        elif debug:
                print("candidate:", "%s's evaluated mesh contains no faces" % (target))

    if debug:
        print("best hit:", nearestobj, nearestlocation, nearestnormal, nearestindex, nearestdistance)

    if nearestobj:
        return nearestobj, nearestobj.evaluated_get(depsgraph), mx @ nearestlocation, mx.to_3x3() @ nearestnormal, nearestindex, nearestdistance

    return None, None, None, None, None, None

def get_origin_from_object(obj, direction=(0, 0, -1), debug=False):
    mxw = obj.matrix_world
    origin, _, _ = mxw.decompose()

    direction = mxw @ Vector(direction) - origin

    if debug:
        print("world origin:", origin, "world direction:", direction)

    return origin, direction

def get_origin_from_object_boundingbox(depsgraph, obj, ignore_mirrors=True):
    if ignore_mirrors:
        for mod in [mod for mod in obj.modifiers if mod.type == 'MIRROR']:
            mod.show_viewport = False

        depsgraph.update()

    avg = average_locations([Vector(co) for co in obj.bound_box])
    mx = obj.matrix_world

    if ignore_mirrors:
        for mod in [mod for mod in obj.modifiers if mod.type == 'MIRROR']:
            mod.show_viewport = True

    return mx @ avg

def get_origin_from_face(obj, index=0, debug=False):
    mxw = obj.matrix_world

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    face = bm.faces[index]
    origin = face.calc_center_median()
    direction = face.normal

    bm.clear()

    if debug:
        print("local origin:", origin, "local direction:", direction)
        print("world origin:", mxw @ origin, "world direction:", mxw.to_3x3() @ direction)

    return mxw @ origin, mxw.to_3x3() @ direction

def get_two_origins_from_face(obj, index=0, debug=False):
    mxw = obj.matrix_world

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    uvs = bm.loops.layers.uv.active

    face = bm.faces[index]
    direction = face.normal

    rail_edges = [e for e in face.edges if len(e.link_faces) == 2]

    if rail_edges:
        edge = rail_edges[0]
    else:
        edge = min([e for e in face.edges], key=lambda x: x.calc_length())

    v1 = edge.verts[0]
    v2 = edge.verts[1]

    v1co = v1.co.copy()
    v2co = v2.co.copy()

    loop1 = [l for l in v1.link_loops if l.face == face][0]
    loop2 = [l for l in v2.link_loops if l.face == face][0]

    if loop1[uvs].uv[1] <= loop2[uvs].uv[1]:
        if debug:
            draw_point(v1co, mx=mxw, color=(1, 0, 0), modal=False)
            draw_point(v2co, mx=mxw, color=(0, 0, 1), modal=False)
        return mxw @ v1co, mxw @ v2co, mxw.to_3x3() @ direction

    else:
        if debug:
            draw_point(v1co, mx=mxw, color=(0, 0, 1), modal=False)
            draw_point(v2co, mx=mxw, color=(1, 0, 0), modal=False)
        return mxw @ v2co, mxw @ v1co, mxw.to_3x3() @ direction

def get_grid_intersection(mousepos):
    region = bpy.context.region
    region_data = bpy.context.region_data

    origin_3d = region_2d_to_origin_3d(region, region_data, mousepos)
    vector_3d = region_2d_to_vector_3d(region, region_data, mousepos)

    xdot = round(Vector((1, 0, 0)).dot(vector_3d), 2)
    ydot = round(Vector((0, 1, 0)).dot(vector_3d), 2)
    zdot = round(Vector((0, 0, 1)).dot(vector_3d), 2)

    if abs(zdot * 2) >= max([abs(xdot), abs(ydot)]):
        angle = 0 if zdot <= 0 else 180
        return intersect_line_plane(origin_3d, origin_3d + vector_3d, Vector((0, 0, 0)), Vector((0, 0, 1))), Matrix.Rotation(radians(angle), 4, "X")

    elif abs(ydot) > abs(xdot):
        angle = 90 if ydot >= 0 else -90
        return intersect_line_plane(origin_3d, origin_3d + vector_3d, Vector((0, 0, 0)), Vector((0, 1, 0))), Matrix.Rotation(radians(angle), 4, "X")

    else:
        angle = 90 if xdot <= 0 else -90
        return intersect_line_plane(origin_3d, origin_3d + vector_3d, Vector((0, 0, 0)), Vector((1, 0, 0))), Matrix.Rotation(radians(angle), 4, "Y")

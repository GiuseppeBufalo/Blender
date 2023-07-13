import bpy
import bpy_extras
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils
from mathutils.geometry import intersect_line_plane
from bpy_extras.view3d_utils import (location_3d_to_region_2d, 
        region_2d_to_vector_3d, region_2d_to_location_3d)
from math import radians 
import bmesh
import math
from mathutils.bvhtree import BVHTree
from mathutils.geometry import distance_point_to_plane
from mathutils.geometry import interpolate_bezier
from . import maths

import numpy

def is_front_facing(context, obj, polygon):
    """
    When deciding if a polygon is facing the camera, you need 
    only calculate the dot product of the normal vector of     
    that polygon, with a vector from the camera to one of the 
    polygon's vertices. 

    - If the dot product is less than zero, the polygon is facing the camera. 
    - If the value is greater than zero, it is facing away from the camera.
    """

    region = context.region  
    rv3d = context.space_data.region_3d  

    # neat eye location code with the help of paleajed
    eye = Vector(rv3d.view_matrix[2][:3])
    eye.length = rv3d.view_distance
    eye_location = rv3d.view_location + eye  

    pnormal = obj.matrix_world.to_3x3() @ polygon.normal
    world_coordinate = obj.matrix_world @ obj.data.vertices[0].co

    result_vector = eye_location - world_coordinate
    dot_value = pnormal.dot(result_vector)            

    return not (dot_value < 0.0)

def view_direction(view_dir):

    view_dir_abs = list(map(abs, view_dir))
    i = view_dir_abs.index(max(view_dir_abs))
    results = [['RIGHT', 'LEFT'], ['BACK', 'FRONT'], ['TOP', 'BOTTOM']]
    res = (results[i][view_dir[i] > 0])

    if i == 0:
        y = (results[1][view_dir[1] > 0])
        z = (results[2][view_dir[2] > 0])

    if i == 1:
        y = (results[0][view_dir[0] > 0])
        z = (results[2][view_dir[2] > 0])

    if i == 2:
        y = (results[0][view_dir[0] > 0])
        z = (results[1][view_dir[1] > 0])

    a = res

    if y == 'TOP' or y == 'BOTTOM':
        b = z
        c = y
    else:
        b = y
        c = z

    if res == 'TOP' or res == 'BOTTOM':
        a = c
        c = res

    viewlis = [[a, b, c]]
        
    return viewlis

def ortho_view_direction(view_dir):
    view_dir_abs = list(map(abs, view_dir))
    i = view_dir_abs.index(max(view_dir_abs))
    results = [['RIGHT', 'LEFT'], ['BACK', 'FRONT'], ['TOP', 'BOTTOM']]
    res = (results[i][view_dir[i] > 0])

    if res == 'FRONT':
        view = Vector((0,0,1))

    elif res == 'BACK':
        view = Vector((0,0,1))

    elif res == 'RIGHT':
        view = Vector((0,0,1))

    elif res == 'LEFT':
        view = Vector((0,0,1))

    elif res == 'BOTTOM':
        view = Vector((1,0,0))

    elif res == 'TOP':
        view = Vector((1,0,0))

    return view

def ortho_view_matrix(view_dir):
    view_dir_abs = list(map(abs, view_dir))
    i = view_dir_abs.index(max(view_dir_abs))
    results = [['RIGHT', 'LEFT'], ['BACK', 'FRONT'], ['TOP', 'BOTTOM']]
    res = (results[i][view_dir[i] > 0])

    mat = Matrix()

    if res == 'FRONT':
        rot_mat = Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
    
    elif res == 'BACK':
        rot_mat = Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))

    elif res == 'RIGHT':
        rot_mat = Matrix.Rotation(radians(90), 4, Vector((0,1,0)))

    elif res == 'LEFT':
        rot_mat = Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))

    elif res == 'BOTTOM':
        rot_mat = Matrix.Rotation(radians(180), 4, Vector((1,0,0)))

    elif res == 'TOP':
        rot_mat = Matrix.Rotation(radians(0), 4, Vector((1,0,0)))

    mat @= rot_mat
    return mat

def ortho_view_vectors(view_dir, axis):

    view_dir_abs = list(map(abs, view_dir))
    i = view_dir_abs.index(max(view_dir_abs))
    results = [['RIGHT', 'LEFT'], ['BACK', 'FRONT'], ['TOP', 'BOTTOM']]
    res = (results[i][view_dir[i] > 0])

    if i == 0:
        y = (results[1][view_dir[1] > 0])
        z = (results[2][view_dir[2] > 0])

    if i == 1:
        y = (results[0][view_dir[0] > 0])
        z = (results[2][view_dir[2] > 0])

    if i == 2:
        y = (results[0][view_dir[0] > 0])
        z = (results[1][view_dir[1] > 0])

    a = res

    if y == 'TOP' or y == 'BOTTOM':
        b = z
        c = y
    else:
        b = y
        c = z

    if res == 'TOP' or res == 'BOTTOM':
        a = c
        c = res

    viewlis = [[a, b, c]]

    mat = Matrix()

    if viewlis == [['FRONT', 'RIGHT', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(0), 4, Vector((1,0,0)))

    elif viewlis == [['FRONT', 'LEFT', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(0), 4, Vector((1,0,0)))

    elif viewlis == [['FRONT', 'RIGHT', 'BOTTOM']]:

        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))
        
    elif viewlis == [['FRONT', 'LEFT', 'BOTTOM']]:
        
        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))

    elif viewlis == [['BACK', 'RIGHT', 'BOTTOM']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))
        
    elif viewlis == [['BACK', 'LEFT', 'BOTTOM']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))
                
    elif viewlis == [['BACK', 'RIGHT', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(0), 4, Vector((1,0,0)))        

    elif viewlis == [['BACK', 'LEFT', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(0), 4, Vector((1,0,0)))
        
    elif viewlis == [['RIGHT', 'FRONT', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))        

    elif viewlis == [['RIGHT', 'BACK', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(0), 4, Vector((1,0,0)))        

    elif viewlis == [['RIGHT', 'FRONT', 'BOTTOM']]:

        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))
        
    elif viewlis == [['RIGHT', 'BACK', 'BOTTOM']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))        

    elif viewlis == [['LEFT', 'FRONT', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(0), 4, Vector((1,0,0)))        

    elif viewlis == [['LEFT', 'BACK', 'TOP']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(0), 4, Vector((1,0,0)))        

    elif viewlis == [['LEFT', 'FRONT', 'BOTTOM']]:

        x = mat @ Matrix.Rotation(radians(90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))        

    elif viewlis == [['LEFT', 'BACK', 'BOTTOM']]:

        x = mat @ Matrix.Rotation(radians(-90), 4, Vector((1,0,0)))
        y = mat @ Matrix.Rotation(radians(-90), 4, Vector((0,1,0)))
        z = mat @ Matrix.Rotation(radians(180), 4, Vector((1,0,0)))
        
    return x, y, z

def get_perp_vec(view_dir):
    view_dir_abs = list(map(abs, view_dir))
    i = view_dir_abs.index(max(view_dir_abs))
    results = [['RIGHT', 'LEFT'], ['BACK', 'FRONT'], ['TOP', 'BOTTOM']]
    res = (results[i][view_dir[i] > 0])

    if res == 'FRONT':
        x = Vector((1,0,0))
    
    elif res == 'BACK':
        x = Vector((1,0,0))        

    elif res == 'RIGHT':
        x = Vector((0,1,0))

    elif res == 'LEFT':
        x = Vector((0,1,0))

    elif res == 'BOTTOM':
        x = Vector((0,1,0))

    elif res == 'TOP':
        x = Vector((0,1,0))

    return x

def avg_3d(vertices):
    x = Vector(([sum(col) / float(len(col)) for col in zip(*vertices)]))

    return x

def avg_3d_global(vertices, mat):
        
    x = Vector(([sum(col) / float(len(col)) for col in zip(*vertices)]))

    return x
        
def coord_on_plane(reg, rv3d, coord, location, normal):

    #take in 2d coord, give me 3D point on defined plane
    view_vector = view3d_utils.region_2d_to_vector_3d(reg, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(reg, rv3d, coord)  
    vec = intersect_line_plane(ray_origin, ray_origin + view_vector, location, Vector((normal)))

    return vec

def coord_on_cursor(reg, rv3d, coord, cursor):

    #take in 2d coord, give me 3D point on cursors plane
    p = region_2d_to_location_3d(reg, rv3d, coord, cursor)     
    
    return p

def ray_cast(reg, rv3d, coord, context):
        
    view_vector = view3d_utils.region_2d_to_vector_3d(reg, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(reg, rv3d, coord)

    hitresult, location, normal, index, object, matrix = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)

    if object:        
        x = object.visible_get(view_layer=context.view_layer)
        if x:
            return location, normal, index, object
    else:
        
        deg = context.evaluated_depsgraph_get()

        objects = [(obj) for obj in bpy.context.visible_objects if obj.type in ['META', 'CURVE']]

        if objects is not None:
            
            for obj in objects:
                
                mw = obj.matrix_world
                mwi = mw.inverted()

                ray = mwi @ ray_origin
                view = mwi.to_3x3() @ view_vector

                bm = bmesh.new()

                obj_eval = obj.evaluated_get(deg)

                if obj_eval:
                    mesh = obj_eval.to_mesh()
                    if mesh:
                        bm.from_mesh(mesh)

                        bvh = BVHTree.FromBMesh(bm)

                        location, normal, index, distance = bvh.ray_cast(ray, view)

                        bm.free()
                        
                        if location is not None:
                            return mw @ location, mw.to_3x3() @ normal, index, obj
                            
    return None, None, None, None
                  
def obj_size(reg, rv3d, coord, scene, viewlayer):

    view_vector = view3d_utils.region_2d_to_vector_3d(reg, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(reg, rv3d, coord)

    hitresult, location, normal, index, ob, matrix = scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)

    if hitresult:
        longest_side = max(ob.dimensions[0], ob.dimensions[1], ob.dimensions[2])
        return longest_side
    
    return None

def curve_size(reg, rv3d, coord, scene, viewlayer):

    view_vector = view3d_utils.region_2d_to_vector_3d(reg, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(reg, rv3d, coord)

    hitresult, location, normal, index, ob, matrix = scene.ray_cast(viewlayer.depsgraph, ray_origin, view_vector)

    if hitresult:
        if ob.type == 'CURVE':
            size = []
            for i in range(len(ob.data.splines[0].bezier_points)):
                size.append(ob.data.splines[0].bezier_points[i].radius)
            longest_side = max(size)*2
            return longest_side
        else:
            return None
        
    return None

def modifier_exists(name, objects):

    if objects is None:
        return 0

    for ob in objects:
        for modifier in ob.modifiers:
            if modifier.name == name:
                return 0
                
    return 1

def window_info(context, event, buffer):
    for area in bpy.context.screen.areas:        
        if area.type == 'VIEW_3D':
            r3d = area.spaces[0].region_3d
            
            div = maths.remap(bpy.context.space_data.lens, 1, 250, 0, 1)

            zoomlevel = (r3d.view_distance * 0.1) / (div*5)

            for r in area.regions:
                if r.type == 'UI':
                    uiWidth = r.width
                    uiHeight = r.height
                if r.type == 'TOOLS':
                    toolsWidth= r.width
                    toolsHeight = r.height
                if r.type == 'HEADER':
                    headerWidth = r.width
                    headerHeight = r.height

            windowWidth = area.width
            windowHeight = area.height

            magic = maths.calc_percent(windowWidth, buffer)

            if event.mouse_region_x > (0+magic) and event.mouse_region_x < (windowWidth-uiWidth-magic) and event.mouse_region_y > (0+magic) and event.mouse_region_y < (windowHeight - magic - headerHeight*2):
                return 1, zoomlevel
    
    return 0, 1

def resample_coords(coords, cyclic, segments=None, shift=0):

    if not segments:
        segments = len(coords) - 1

    if len(coords) < 2:
        return coords

    if not cyclic and shift != 0:  # not PEP but it shows that we want shift = 0
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

    return new_coords

def spline_4p( t, p_1, p0, p1, p2 ):
    """ Catmull-Rom
        (Ps can be numpy vectors or arrays too: colors, curves ...)
    """
        # wikipedia Catmull-Rom -> Cubic_Hermite_spline
        # 0 -> p0,  1 -> p1,  1/2 -> (- p_1 + 9 p0 + 9 p1 - p2) / 16
    # assert 0 <= t <= 1
    return (
        t*((2-t)*t - 1)   * p_1
        + (t*t*(3*t - 5) + 2) * p0
        + t*((4 - 3*t)*t + 1) * p1
        + (t-1)*t*t         * p2 ) / 2  

def CatmullRomSpline(P0, P1, P2, P3, nPoints):
  """
  P0, P1, P2, and P3 should be (x,y) point pairs that define the
  Catmull-Rom spline.
  nPoints is the number of points to include in this curve segment.
  """
  # Convert the points to numpy so that we can do array multiplication
  P0, P1, P2, P3 = map(numpy.array, [P0, P1, P2, P3])

  # Calculate t0 to t4
  alpha = 0.5
  def tj(ti, Pi, Pj):
    xi, yi = Pi
    xj, yj = Pj
    return ( ( (xj-xi)**2 + (yj-yi)**2 )**0.5 )**alpha + ti

  t0 = 0
  t1 = tj(t0, P0, P1)
  t2 = tj(t1, P1, P2)
  t3 = tj(t2, P2, P3)

  # Only calculate points between P1 and P2
  t = numpy.linspace(t1,t2,nPoints)

  # Reshape so that we can multiply by the points P0 to P3
  # and get a point for each value of t.
  t = t.reshape(len(t),1)

  A1 = (t1-t)/(t1-t0)*P0 + (t-t0)/(t1-t0)*P1
  A2 = (t2-t)/(t2-t1)*P1 + (t-t1)/(t2-t1)*P2
  A3 = (t3-t)/(t3-t2)*P2 + (t-t2)/(t3-t2)*P3

  B1 = (t2-t)/(t2-t0)*A1 + (t-t0)/(t2-t0)*A2
  B2 = (t3-t)/(t3-t1)*A2 + (t-t1)/(t3-t1)*A3

  C  = (t2-t)/(t2-t1)*B1 + (t-t1)/(t2-t1)*B2
  return C

def CatmullRomChain(P, pts):
  """
  Calculate Catmull Rom for a chain of points and return the combined curve.
  """
  sz = len(P)

  # The curve C will contain an array of (x,y) points.
  C = []
  for i in range(sz-3):
    c = CatmullRomSpline(P[i], P[i+1], P[i+2], P[i+3], pts)
    C.extend(c)

  return C

def get_points(spline, clean=True):
    
    knots = spline.bezier_points

    if len(knots) < 2:
        return

    # verts per segment
    r = spline.resolution_u + 1
    
    # segments in spline
    segments = len(knots)
    
    if not spline.use_cyclic_u:
        segments -= 1

    master_point_list = []
    for i in range(segments):
        inext = (i + 1) % len(knots)

        knot1 = knots[i].co
        handle1 = knots[i].handle_right
        handle2 = knots[inext].handle_left
        knot2 = knots[inext].co
        
        bezier = knot1, handle1, handle2, knot2, r
        points = interpolate_bezier(*bezier)
        master_point_list.extend(points)

    # some clean up to remove consecutive doubles, this could be smarter...
    if clean:
        old = master_point_list
        good = [v for i, v in enumerate(old[:-1]) if not old[i] == old[i+1]]
        good.append(old[-1])
        return good
            
    return master_point_list

def splitslice(stackslice):
    interval = (stackslice.stop - stackslice.start) >> 1
    remainder = (stackslice.stop - stackslice.start) %  2
    return [ \
        slice(stackslice.start, stackslice.start + interval + remainder, 1), \
        slice(stackslice.start + interval, stackslice.stop, 1)              \
        ]

def tryfit(plotpoints):
    
    bf0 = lambda u: u**3
    bf1 = lambda u: 3*((u**2)*(1-u))
    bf2 = lambda u: 3*(u*((1-u)**2))
    bf3 = lambda u: (1-u)**3

    dln = len(plotpoints)
    ascol = (dln, 1)
    diff = plotpoints[1:] - plotpoints[:-1]
    slen = numpy.array([numpy.sqrt((p**2.0).sum()) for p in diff])
    ssum = numpy.array([0.0] + [slen[:k].sum() for k in range(1, len(slen)+1)])/slen.sum()
    obmx = numpy.hstack(                               \
                    (                             \
                        bf0(ssum).reshape(ascol), \
                        bf1(ssum).reshape(ascol), \
                        bf2(ssum).reshape(ascol), \
                        bf3(ssum).reshape(ascol)  \
                    )                             \
                    )
    return numpy.linalg.lstsq(obmx, plotpoints, -1)

def project_geo(self, context, ob, sel, rv3d, region):
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle()
    coord = None

    if ob:
        ob.hide_set(True)

        for i, v in enumerate(ob.data.vertices):
            pos = v.co 
            coord = view3d_utils.location_3d_to_region_2d(region, rv3d, pos)    

            if coord:
                view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

                hitresult, location, normal, index, object, matrix = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)

                if hitresult:
                    ob.data.vertices[i].co = location
                else:
                    v.select = True
        
        ob.hide_set(False)
            
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.editmode_toggle()
            
def align_plane_to_view(self, context, ob, rv3d, region, coord, cloc):
    
    ob.location = region_2d_to_location_3d(region, rv3d, coord, cloc) 
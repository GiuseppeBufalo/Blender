import bpy
import bmesh
from mathutils import Vector

#
# A set of stock functions to create basic shapes for greebles.
#
def get_square_1_shape_greeble():
    verts = [(+1.0, +1.0, -1.0),
             (+1.0, -1.0, -1.0),
             (-1.0, -1.0, -1.0),
             (-1.0, +1.0, -1.0),
             (+1.0, +1.0, +1.0),
             (+1.0, -1.0, +1.0),
             (-1.0, -1.0, +1.0),
             (-1.0, +1.0, +1.0),
             ]

    faces = [(0, 1, 2, 3),
             (4, 7, 6, 5),
             (0, 4, 5, 1),
             (1, 5, 6, 2),
             (2, 6, 7, 3),
             (4, 0, 3, 7),
            ]

    mesh = bpy.data.meshes.new("square_1_shape_greeble")

    bm = bmesh.new()

    for v_co in verts:
        bm.verts.new(v_co)

    bm.verts.ensure_lookup_table()
    for f_idx in faces:
        bm.faces.new([bm.verts[i] for i in f_idx])

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    return mesh

def get_square_2_shape_greeble():
    new_mesh = bpy.data.meshes.new("square_2_shape_greeble")
    square_mesh_1 = get_square_1_shape_greeble()
    square_mesh_2 = get_square_1_shape_greeble()
    bm = bmesh.new()
    bm.from_mesh(square_mesh_1)
    for v in bm.verts:
        v.co = v.co - Vector((0,-3,0))
    bm.from_mesh(square_mesh_2)
    bm.to_mesh(new_mesh)

    bm.free()
    return new_mesh


def get_square_3_shape_greeble():
    new_mesh = bpy.data.meshes.new("square_3_shape_greeble")
    square_mesh_1 = get_square_1_shape_greeble()
    square_mesh_2 = get_square_1_shape_greeble()
    square_mesh_3 = get_square_1_shape_greeble()
    bm = bmesh.new()
    bm.from_mesh(square_mesh_1)
    for v in bm.verts:
        v.co = v.co - Vector((0,-3,0))
    bm.from_mesh(square_mesh_2)
    for v in bm.verts:
        v.co = v.co - Vector((0,-3,0))
    bm.from_mesh(square_mesh_3)
    bm.to_mesh(new_mesh)

    bm.free()
    return new_mesh

def get_L_shape_greeble():
    new_mesh = bpy.data.meshes.new("L_shape_greeble")
    bm = bmesh.new()
    vert0 = bm.verts.new(Vector((1,0,0)))
    vert1 = bm.verts.new(Vector((-1,0,0)))
    vert2 = bm.verts.new(Vector((-1,-2,0)))
    vert3 = bm.verts.new(Vector((1,-2,0)))
    bm.faces.new([vert0,vert1,vert2,vert3])
    vert4 = bm.verts.new(Vector((1,-3,0)))
    vert5 = bm.verts.new(Vector((-1,-3,0)))
    bm.faces.new([vert3,vert2,vert5,vert4])
    vert6 = bm.verts.new(Vector((2,-3,0)))
    vert7 = bm.verts.new(Vector((2,-2,0)))
    bm.faces.new([vert7,vert3,vert4,vert6])

    result = bmesh.ops.extrude_face_region(bm, geom=bm.faces)

    for v in result['geom']:
        if isinstance(v, bmesh.types.BMVert):
            v.co = v.co + Vector((0,0,1))

    bm.to_mesh(new_mesh)

    bm.free()
    return new_mesh

def get_T_shape_greeble():
    new_mesh = bpy.data.meshes.new("T_shape_greeble")
    bm = bmesh.new()
    vert0 = bm.verts.new(Vector((-.5,.5,0)))
    vert1 = bm.verts.new(Vector((-1.5,.5,0)))
    vert2 = bm.verts.new(Vector((-1.5,-.5,0)))
    vert3 = bm.verts.new(Vector((-.5,-.5,0)))
    bm.faces.new([vert0,vert1,vert2,vert3])
    vert4 = bm.verts.new(Vector((.5,.5,0)))
    vert5 = bm.verts.new(Vector((.5,-.5,0)))
    bm.faces.new([vert4,vert0,vert3,vert5])
    vert6 = bm.verts.new(Vector((1.5,.5,0)))
    vert7 = bm.verts.new(Vector((1.5,-.5,0)))
    bm.faces.new([vert6,vert4,vert5,vert7])
    vert8 = bm.verts.new(Vector((-.5,-2.5,0)))
    vert9 = bm.verts.new(Vector((.5,-2.5,0)))
    bm.faces.new([vert5,vert3,vert8,vert9])

    result = bmesh.ops.extrude_face_region(bm, geom=bm.faces)

    for v in result['geom']:
        if isinstance(v, bmesh.types.BMVert):
            v.co = v.co + Vector((0,0,1))

    bm.to_mesh(new_mesh)

    bm.free()
    return new_mesh

def get_cylinder_greeble():
    new_mesh = bpy.data.meshes.new("cylinder_greeble")
    bm = bmesh.new()
    result = bmesh.ops.create_circle(
        bm,
        cap_ends=False,
        radius=1,
        segments=16)

    bmesh.ops.edgenet_fill(bm, edges=bm.edges)

    result = bmesh.ops.extrude_face_region(bm, geom=bm.faces)
    for v in result['geom']:
        if isinstance(v, bmesh.types.BMVert):
            v.co = v.co + Vector((0,0,1))

    bm.to_mesh(new_mesh)
    bm.free()
    return new_mesh

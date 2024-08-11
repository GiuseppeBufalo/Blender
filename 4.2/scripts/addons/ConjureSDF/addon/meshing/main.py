import bpy

from bpy.types import Operator

from bpy_extras.object_utils import AddObjectHelper, object_data_add


import numpy as np
import struct

import os.path
import time
import math


from ConjureSDF.get_path import get_path

from ..util.math import vec3_min, vec3_max
from ..util.object import get_csdf_prims

# --- GLOBALS
VALUES = 100



class CSDF_OT_SDF_TO_MESH(Operator, AddObjectHelper):
    """Converts SDF scene to mesh"""
    bl_idname = "mesh.csdf_sdftomesh"
    bl_label = "Convert to Mesh"

    @classmethod
    def poll(cls, context):
        scene_objs = context.scene.objects
        if scene_objs.get("CSDF_Meshing_Bounds") and scene_objs.get("CSDF_Meshing_Corner01") and scene_objs.get("CSDF_Meshing_Corner02"):
            return True
        return False

    def execute(self, context):

        try:  
            import moderngl
        except:
            self.report({'ERROR'}, "ModernGL not found, install via Addon Preferences!")
            return {'CANCELLED'}

        start = time.time()

        scene = context.scene
        CSDF_meshingprops = scene.csdf_meshingprops

        values = VALUES
        chunk_length = values/CSDF_meshingprops.triangle_density

        dims = (values, values, values)
        num_cells = dims[0]*dims[1]*dims[2]

        # mc compute has a local group size of 10xyz, hence the need for these divided values
        invoc_values = int(values/10)
        invoc_dims = (invoc_values, invoc_values, invoc_values)

        sdf_comp_src, mc_comp_src = get_shader_source(context)
        ctx = moderngl.create_context(standalone=False)

        depsgraph = context.evaluated_depsgraph_get()
        scene = depsgraph.scene

        load_sdf_comp_data(ctx, scene, num_cells)
        output_verts_buf = load_mc_comp_data(ctx, num_cells)

        bounds_01 = scene.objects["CSDF_Meshing_Corner01"].location
        bounds_02 = scene.objects["CSDF_Meshing_Corner02"].location
        startloc = vec3_min(bounds_01, bounds_02)[:]

        num_chunks_x, num_chunks_y, num_chunks_z = calculate_num_chunks(CSDF_meshingprops, bounds_01, bounds_02)
        total_chunks = num_chunks_x * num_chunks_y * num_chunks_z


        # based on https://blender.stackexchange.com/questions/220072/check-using-name-if-a-collection-exists-in-blend-is-linked-to-scene
        mesh_Coll = bpy.data.collections.get("CSDF Mesh")
        if not mesh_Coll:
            mesh_Coll = bpy.data.collections.new("CSDF Mesh")
            mesh_Coll.color_tag = 'COLOR_04'
            bpy.context.scene.collection.children.link(mesh_Coll)


        winman =  bpy.context.window_manager
        winman.progress_begin(0, total_chunks)

        chunk_count = 0

        for i in range(num_chunks_x):
            for j in range(num_chunks_y):
                for k in range(num_chunks_z):
                    loc = (startloc[0]+(chunk_length*i), startloc[1]+(chunk_length*j), startloc[2]+(chunk_length*k))
                    convert_to_mesh(self, context, ctx, sdf_comp_src, mc_comp_src, num_cells, chunk_length, dims, invoc_dims, output_verts_buf, loc)

                    active_chunk = bpy.context.active_object
                    active_chunk.location = loc
                    # based on https://blender.stackexchange.com/questions/132112/whats-the-blender-2-8-command-for-adding-an-object-to-a-collection-using-python
                    for col in active_chunk.users_collection:
                        col.objects.unlink(active_chunk)
                    mesh_Coll.objects.link(active_chunk)

                    chunk_count += 1
                    winman.progress_update(chunk_count)
        
        CSDF_meshingprops.last_chunk_count = total_chunks
        CSDF_meshingprops.last_chunk_time = time.time()-start

        return {'FINISHED'}



def convert_to_mesh(self, bcontext, glctx, sdf_comp_src, mc_comp_src, num_cells, chunk_length, dims, invoc_dims, output_verts_buf, loc):
    run_sdf_comp(glctx, sdf_comp_src, dims, loc, chunk_length)
    run_mc_comp(glctx, mc_comp_src, invoc_dims, chunk_length)

    data = np.frombuffer(output_verts_buf.read(), dtype=np.single)
    # data = struct.unpack(str(num_cells * 15 * 4)+"f", output_verts_buf.read())

    verts, faces = data_to_mesh(num_cells, data)
    add_chunk(self, bcontext, verts, faces)



def add_chunk(self, context, verts, faces):

    edges = []

    mesh = bpy.data.meshes.new(name="Chunk")
    mesh.from_pydata(verts, edges, faces)
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)


def get_shader_source(context):

    folderpath = os.path.dirname(__file__)
    shader_folder = os.path.join(folderpath, "shaders")

    # marching cubes compute shader files
    comp_sources = (
        'mc_setup.glsl', 
        'mc_main.comp.glsl'
    )

    mc_compute_source_files = read_files(shader_folder, comp_sources)

    # sdf volume compute shader files
    sdf_comp_sources = (
        'sdf_setup.comp.glsl', 
        'sdf_main.comp.glsl'
    )

    sdf_compute_src_files = read_files(shader_folder, sdf_comp_sources)

    # sdf scene description shader files
    # get path to addon
    addon_path = get_path()
    scene_src_relative_path = "addon\engine\sdf\source"

    # get path to shader source files
    scene_src_folder = os.path.join(addon_path, scene_src_relative_path)

    sdf_scene_src_files = (
        "sdf-ops.fs.glsl",
        "sdf-prims.fs.glsl",
    )   
    sdf_scene_src_files = read_files(scene_src_folder, sdf_scene_src_files)

    # get depsgraph and get scene from renderer builder
    depsgraph = context.evaluated_depsgraph_get()
    from ConjureSDF.addon.engine.sdf.builder import generate_scene

    scene = generate_scene(depsgraph, meshing=True)

    sdf_compute_source = f"{sdf_compute_src_files[0]}{sdf_scene_src_files[0]}{sdf_scene_src_files[1]}{scene}{sdf_compute_src_files[1]}"

    mc_compute_source = f"{mc_compute_source_files[0]}{mc_compute_source_files[1]}"

    return sdf_compute_source, mc_compute_source


def read_files(folder, filenames):
    file_sources = []
    for file in filenames:
        path = os.path.join(folder, file)
        with open(path) as f:
            file_sources.append(f.read())
    return file_sources


def load_sdf_comp_data(ctx, scene, num_cells):

    vox_data_buf = ctx.buffer(reserve=num_cells*4)
    vox_data_buf.bind_to_storage_buffer(binding=1)

    from ConjureSDF.addon.engine.renderer import compose_primitive_data

    sdf_objs = get_csdf_prims(scene)
    prim_data = compose_primitive_data(sdf_objs)

    buf = struct.pack('%sf' % len(prim_data), *prim_data)

    prim_data_buf = ctx.buffer(data=buf)
    prim_data_buf.bind_to_uniform_block(binding=0)

def run_sdf_comp(ctx, sdf_comp_src, dims, origin, chunk_length):

    sdf_compute = ctx.compute_shader(sdf_comp_src)

    sdf_compute['origin'] = origin
    sdf_compute['chunk_length'] = chunk_length
    
    sdf_compute.run(dims[0], dims[1], dims[2])


def load_mc_comp_data(ctx, num_cells):

    output_size = num_cells * 15 * 4 * 4
    output_verts_buf = ctx.buffer(reserve=output_size)
    output_verts_buf.bind_to_storage_buffer(binding=2)

    return output_verts_buf

def run_mc_comp(ctx, mc_comp_src, dims, chunk_length):

    mc_compute = ctx.compute_shader(mc_comp_src)

    mc_compute['chunk_length'] = chunk_length

    mc_compute.run(dims[0], dims[1], dims[2])


def data_to_mesh(num_cells, verts):

    num_verts = num_cells * 15

    faces = []

    # # this is the slow part, takes 2.4-2.7 seconds (for a 100xyz chunk)
    # for i in range(num_verts):
    #     if v[(i*4)+3] == 1.0:
    #         verts.append((v[i*4], v[(i*4)+1], v[(i*4)+2]))
    # # using list comprehension shaves off 0.4-0.6 seconds (for a 100xyz chunk)
    # verts = [(v[i*4], v[(i*4)+1], v[(i*4)+2]) for i in range(num_verts) if v[(i*4)+3] == 1.0]

    # about as fast as the above list comprehension
    # verts = np.array(v)

    # huge thanks to Spencer Magnusson for this lightning fast numpy code
    verts = np.reshape(verts, (-1, 4))
    verts = verts[verts[:,-1] > 0][:, :3]
    verts = verts.tolist()

    for i in range(int(len(verts)/3)):
        faces.append(((i*3), (i*3)+1, (i*3)+2))

    return verts, faces



def calculate_num_chunks(CSDF_meshingprops, bounds_01, bounds_02):

    chunk_length = VALUES/CSDF_meshingprops.triangle_density

    bounds_start = vec3_min(bounds_01, bounds_02)
    bounds_end = vec3_max(bounds_01, bounds_02)
    bounds_size = bounds_end-bounds_start

    num_chunks = bounds_size/chunk_length
    
    return math.ceil(num_chunks[:][0]), math.ceil(num_chunks[:][1]), math.ceil(num_chunks[:][2])

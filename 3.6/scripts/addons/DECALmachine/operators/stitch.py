import bpy
import bmesh
from mathutils import Vector
from .. utils.selection import get_boundary_edges
from .. utils.math import average_locations
from .. utils.uv import set_trim_uv_channel


class Stitch(bpy.types.Operator):
    bl_idname = "machin3.stitch"
    bl_label = "MACHIN3: Stitch"
    bl_description = "Stitch UVed faces together"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            if active.data.uv_layers:
                bm = bmesh.from_edit_mesh(context.active_object.data)

                if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False):
                    return [e for e in bm.edges if e.select]

                elif tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True):
                    return len([f for f in bm.faces if f.select]) > 1

    def execute(self, context):
        active = context.active_object

        set_trim_uv_channel(active)

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        uvs = bm.loops.layers.uv.active

        if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False):
            edges = [e for e in bm.edges if e.select]

        else:

            faces = [f for f in bm.faces if f.select]
            boundary = get_boundary_edges(faces)
            edges = {e for f in faces for e in f.edges if e not in boundary}

        verts = {}

        for e in edges:
            for loop in e.link_loops:
                next_loop = loop.link_loop_next

                for l in [loop, next_loop]:

                    if l.vert in verts:
                        verts[l.vert].add(l)

                    else:
                        verts[l.vert] = {l}

        for vert, loops in verts.items():

            avg = average_locations({loop[uvs].uv.copy().freeze() for loop in loops}, size=2)

            if any(loop[uvs].uv != avg for loop in loops):
                for loop in loops:
                    loop[uvs].uv = avg

        bmesh.update_edit_mesh(active.data)

        return {'FINISHED'}

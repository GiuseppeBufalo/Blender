# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
from ZenUV.utils.get_uv_islands import uv_bound_edges_indexes
from ZenUV.utils.finishing_util import FINISHED_FACEMAP_NAME
from ZenUV.utils.blender_zen_utils import ZenPolls
from ZenUV.utils.generic import (
    get_mesh_data,
    ensure_facemap,
)
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.messages import zen_message


class MarkStateManager:

    def __init__(self, context) -> None:
        aprefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        scprefs = context.scene.zen_uv
        self.Gpriority = aprefs.useGlobalMarkSettings
        self.Gseam = aprefs.markSeamEdges
        self.Gsharp = aprefs.markSharpEdges
        self.Lseam = scprefs.op_markSeamEdges
        self.Lsharp = scprefs.op_markSharpEdges
        self.QuadrifySeams = scprefs.op_quadrify_props.mark_seams
        self.QuadrifySharp = scprefs.op_quadrify_props.mark_sharp

    def get_state(self):
        if self.Gpriority:
            return self.Gseam, self.Gsharp
        else:
            return self.Lseam, self.Lsharp

    def get_state_quadrify(self):
        if self.Gpriority:
            return self.Gseam, self.Gsharp
        else:
            return self.QuadrifySeams, self.QuadrifySharp


# def call_from_zen_check():
#     return ZUV_OT_Mark_Seams.call_from_zen


def restore_selected_faces(selfaces):
    for face in selfaces:
        face.select = True


def assign_seam_to_edges(edges, assign=True):
    for edge in edges:
        edge.seam = assign


def assign_sharp_to_edges(edges, assign=True):
    for edge in edges:
        edge.smooth = not assign


def assign_seam_to_selected_edges(bm):
    for edge in bm.edges:
        if edge.select:
            edge.seam = True


def get_bound_edges(edges_from_polygons):
    boundary_edges = []
    for edge in edges_from_polygons:
        if False in [f.select for f in edge.link_faces] or edge.is_boundary:
            boundary_edges.append(edge)
    return boundary_edges


def zuv_mark_seams(context, bm, mSeam, mSharp, silent_mode=False, assign=True, switch=False):
    selfaces = []
    seledges = []
    # Check if face selection mode
    # Check if have currently selected faces
    # Check Mark Seams is True
    if bm.select_mode == {'FACE'} and True in [f.select for f in bm.faces]:
        fin_fmap = ensure_facemap(bm, FINISHED_FACEMAP_NAME)
        selfaces = [f for f in bm.faces if f.select]
        region_loop_edges = get_bound_edges([e for e in bm.edges if e.select])
        # Emulate Live Unwrap as Blender's native
        if switch and False not in [edge.seam for edge in region_loop_edges]:
            assign = not assign

        # Clear FINISHED for selected faces
        for face in selfaces:
            face[fin_fmap] = 0

        # Test if selected edges exist - seams to borders
        if region_loop_edges:
            # Clear sharp and seams for selected faces
            edges_from_faces = [e for f in selfaces for e in f.edges]
            if mSeam:
                for edge in edges_from_faces:
                    edge.seam = False
                assign_seam_to_edges(region_loop_edges, assign=assign)
            if mSharp:
                for edge in edges_from_faces:
                    edge.smooth = True
                assign_sharp_to_edges(region_loop_edges, assign=assign)
        else:
            if not silent_mode:
                if assign is True:
                    bpy.ops.wm.call_menu(name="ZUV_MT_ZenMark_Popup")
                    return False
                else:
                    zen_message(context, message="Nothing is produced. Selected polygons do not have a borders.")
                    return False
            # zen_message(message="Nothing is produced. Selected polygons do not have a borders.")

    # Check if Edge selection mode
    if bm.select_mode == {'EDGE'} and True in [x.select for x in bm.edges]:
        seledges = [e for e in bm.edges if e.select]
        # Emulate Live Unwrap as Blender's native
        if switch and False not in [edge.seam for edge in seledges]:
            assign = not assign
        if mSeam:
            # print("Seam is true")
            assign_seam_to_edges(seledges, assign=assign)
        if mSharp:
            # print("Sharp is true")
            assign_sharp_to_edges(seledges, assign=assign)

    return True


def unmark_all_seams_sharp(bms, cl_seam=False, cl_sharp=False):
    for obj in bms:
        bm = bms[obj]['data']
        bm.edges.ensure_lookup_table()
        if cl_seam:
            for edge in bm.edges:
                edge.seam = False
        if cl_sharp:
            for edge in bm.edges:
                edge.smooth = True

        bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def seams_by_uv_border(bms):
    for obj in bms:
        bm = bms[obj]['data']
        bm.edges.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        faces = [f for f in bm.faces if not f.hide]
        for i in uv_bound_edges_indexes(faces, uv_layer):
            bm.edges[i].seam = True
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def sharp_by_uv_border(bms):
    for obj in bms:
        bm = bms[obj]['data']
        bm.edges.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        faces = [f for f in bm.faces if not f.hide]
        for i in uv_bound_edges_indexes(faces, uv_layer):
            bm.edges[i].smooth = False
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def select_uv_border(context, objs, cles=False):
    area = context.area.type
    uv_sync = context.scene.tool_settings.use_uv_select_sync

    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        faces = [f for f in bm.faces if not f.hide]
        b_edges = uv_bound_edges_indexes(faces, uv_layer)
        if area == 'VIEW_3D':
            if cles:
                clear_selection(bm)
            for i in b_edges:
                bm.edges[i].select = True
        elif area == 'IMAGE_EDITOR':
            if uv_sync:
                if cles:
                    clear_selection(bm)
                for i in b_edges:
                    bm.edges[i].select = True
            else:
                if cles:
                    if not ZenPolls.version_greater_3_2_0:
                        for loop in [loop[uv_layer] for f in bm.faces for loop in f.loops]:
                            loop.select = False
                    else:
                        if context.scene.tool_settings.uv_select_mode == "EDGE":
                            for loop in [loop[uv_layer] for f in bm.faces for loop in f.loops]:
                                loop.select_edge = False
                        else:
                            for loop in [loop[uv_layer] for f in bm.faces for loop in f.loops]:
                                loop.select = False

                loops = [loop[uv_layer] for i in b_edges for vert in bm.edges[i].verts for loop in vert.link_loops]
                if not ZenPolls.version_greater_3_2_0:
                    for loop in loops:
                        loop.select = True
                else:
                    if context.scene.tool_settings.uv_select_mode == "EDGE":
                        loops = [loop[uv_layer] for i in b_edges for loop in bm.edges[i].link_loops]
                        for loop in loops:
                            loop.select_edge = True
                    else:
                        for loop in loops:
                            loop.select = True

        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def clear_selection(bm):
    for e in bm.edges:
        e.select = False
    # bm.select_flush_mode()


def seams_by_open_edges(bms):
    for obj in bms:
        bm = bms[obj]['data']
        sources = [e.index for e in bm.edges if True in [f.hide for f in e.link_faces] and not e.hide]
        bound = [e.index for e in bm.edges if e.is_boundary and not e.link_faces[0].hide]
        sources.extend(bound)
        for i in sources:
            bm.edges[i].seam = True
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def seams_by_sharp(context):
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        for edge in bm.edges:
            edge.seam = not edge.smooth
        bmesh.update_edit_mesh(me, loop_triangles=False)


def sharp_by_seam(context):
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        for edge in bm.edges:
            edge.smooth = not edge.seam
        bmesh.update_edit_mesh(me, loop_triangles=False)

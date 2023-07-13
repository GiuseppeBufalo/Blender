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

""" Zen UV Relax system """

import bmesh
import bpy
import numpy as np
import random
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.utils.base_clusters.base_cluster import (
    TransformCluster,
    ProjectCluster,
)
from ZenUV.utils.base_clusters.zen_cluster import ZenCluster
# from ZenUV.utils.base_clusters.diagnostic_clusters import CheckerZcluster
from ZenUV.utils.base_clusters.stripes import UvStripes
from ZenUV.utils.transform import BoundingBox2d
from mathutils import Vector
# from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.generic import (
    resort_by_type_mesh_in_edit_mode_and_sel,
    resort_objects,
    get_mesh_data
)
from ZenUV.utils import get_uv_islands as island_util

from ZenUV.utils.clib.lib_init import init_progress, finish_progress, get_zen_relax2_app
from ZenUV.ui.third_party_popups import draw_zensets_popup
from ZenUV.ui.pie import ZsPieFactory


class ProgressText:

    def __init__(self):
        self.prefix = ""
        self.preposition = ""


class ProgressBar:

    def __init__(self, context, iterations, text_only=True) -> None:
        self.pb = init_progress(context, message="", text_only=text_only)
        self.current_step = 0
        self.force = False
        self.iterations = iterations
        self.text_processor = ProgressText()
        self.obj_name_len = 20

    def __del__(self):
        finish_progress(self.pb)

    def set_text(self, prefix="", preposition=""):
        self.text_processor.prefix = prefix
        self.text_processor.preposition = preposition

    def set_text_relax(self, obj_name="", cluster_name="", preposition=""):
        name_len = len(obj_name)
        if name_len > self.obj_name_len:
            stripped_part = self.obj_name_len // 2
            obj_name = obj_name[0:stripped_part] + ".." + obj_name[name_len - stripped_part:name_len]
        if name_len == 0:
            self.text_processor.prefix = f"{cluster_name}: "
        else:
            self.text_processor.prefix = f"{obj_name} -> {cluster_name}: "
        self.text_processor.preposition = preposition

    def update(self):
        self._setTaskbarProgress()

    def finish(self):
        finish_progress(self.pb)

    def _getPercent(self):
        percent = 0
        if self.iterations != 0:
            if not percent > 100:
                percent = int(round(self.current_step / self.iterations * 100, 0))
            else:
                percent = 100
        return percent

    def _getText(self):
        return f"{self.text_processor.prefix} {self._getPercent()} {self.text_processor.preposition} 100%"

    def _setTaskbarProgress(self):
        self.current_step += 1
        self.pb.setTaskbarProgress(self.current_step, self.iterations, self.force, text=self._getText())


class rCluster():

    def __init__(self, context, obj, island):
        super().__init__(context, obj, island)

        self.init_r_cluster()

    def init_r_cluster(self):
        self.uvs = []
        self.pydata = []

    def to_mesh(self, with_injection=False, with_uv=True):
        """ Testing purposes ONLY!!! """
        reindex, verts, faces = self.get_zen_pydata(for_OBJ=False, compensate=False)
        if with_injection:
            solver = UvStripes(self.get_bound_edges(), self.uv_layer)
            solver.for_obj = False
            if solver.is_cluster_holey():
                injectors = solver.get_injectors(len(self.uv_verts))
                for injector in injectors:
                    verts.append(injector[0])
                    faces.extend(injector[1])
        new_mesh = bpy.data.meshes.new('Cluster_mesh')
        new_mesh.from_pydata(verts, [], faces)
        new_mesh.update()
        new_object = bpy.data.objects.new('Cluster_object', new_mesh)
        new_collection = bpy.data.collections.new('ZenClusters')
        bpy.context.scene.collection.children.link(new_collection)
        new_collection.objects.link(new_object)

        if with_uv and self.uvs:
            bm = bmesh.new()
            bm.from_mesh(new_object.data)
            uv_layer = bm.loops.layers.uv.verify()
            for v in bm.verts:
                for loop in v.link_loops:
                    loop[uv_layer].uv = self.uvs[v.index]
            bm.to_mesh(new_object.data)
            bm.free()

        return new_mesh

    def get_zen_pydata(self, for_OBJ=False, compensate=True, _print=False):
        faces = []
        reindex = dict()
        offset = 0
        if for_OBJ:
            offset = 1
        for face in self.uv_faces:
            face_verts = [v for v in face.uv_verts]
            face_verts_ids = [v.index + offset for v in face_verts]
            for vert in face_verts:
                reindex.update({vert.mesh_vert.index: vert.index})
            faces.append(face_verts_ids)
        verts = [v.mesh_vert.co + (Vector(np.random.rand(3, 1)) * 0.0000001) for v in self.uv_verts]

        if _print:
            print("\nZEN Pydata: --------------------------\n")
            print(f"Faces: {faces}")
            print(f"Verts: {len(verts)}\n {verts}")
            print(f"Reindex: {reindex}")

        self.pydata = [verts, [], faces]
        return reindex, verts, faces

    def zen_relax(self, props, Progress):

        reindex, verts, faces = self.get_zen_pydata(for_OBJ=False, compensate=False)
        boundary = self.get_bound_edges()
        if not boundary:
            return False, "The island has no boundaries."
        solver = UvStripes(boundary, self.uv_layer)
        solver.for_obj = False
        if solver.is_cluster_holey():
            injectors = solver.get_injectors(len(self.uv_verts))
            for injector in injectors:
                verts.append(injector[0])
                faces.extend(injector[1])

        import subprocess

        s_relax_app = get_zen_relax2_app()

        # progress = {}

        try:
            i_empties = 0

            with subprocess.Popen(
                    s_relax_app,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE) as proc:

                # print('Successfully started:', s_relax_app)

                i_iter_count = 20 - 1
                Progress.iterations = i_iter_count
                self.uvs = []

                state = "init"
                i_step = 0

                i_step_vlist = 0
                i_step_flist = 0

                e_msg = None

                while state != "quit":
                    if state == "init":
                        state = "idle"
                        proc.stdin.write(f'vs {len(verts)}\n'.encode('utf-8'))
                        proc.stdin.flush()
                    elif state == "out.vlist":
                        state = "idle"
                        v = verts[i_step_vlist]
                        proc.stdin.write(f'v {i_step_vlist} {v[0]} {v[1]} {v[2]}\n'.encode('utf-8'))
                        proc.stdin.flush()

                        i_step_vlist += 1

                    elif state == "out.fsize":
                        state = "idle"
                        proc.stdin.write(f'fs {len(faces)}\n'.encode('utf-8'))
                        proc.stdin.flush()
                    elif state == "out.flist":
                        state = "idle"
                        it_face = ' '.join([str(nf) for nf in faces[i_step_flist]])
                        proc.stdin.write(f'f {i_step_flist} {it_face}\n'.encode('utf-8'))
                        proc.stdin.flush()
                        i_step_flist += 1
                    elif state == "out.precalc":
                        state = "idle"
                        proc.stdin.write('p\n'.encode('utf-8'))
                        proc.stdin.flush()
                    elif state == "out.step":
                        state = "idle"

                        Progress.update()

                        if i_step == i_iter_count:
                            proc.stdin.write('u\n'.encode('utf-8'))
                        else:
                            proc.stdin.write('s\n'.encode('utf-8'))
                        i_step += 1
                        proc.stdin.flush()
                    elif state.startswith("_u:"):
                        self.uvs.append(tuple(map(float, state[3:].split(' '))))
                        state = "idle"
                    elif state.startswith("ERROR>"):
                        e_msg = state
                        state = "idle"

                    cppMessage = proc.stdout.readline()
                    state = cppMessage.decode('utf-8').strip()
                    # print("CPP -> " + state)
                    if state == '':
                        i_empties += 1

                    # Force Quit
                    if i_empties > 5:
                        print("FORCE_QUIT !!!")
                        proc.stdin.write('q\n'.encode('utf-8'))
                        proc.stdin.flush()

                    # abnormal termination
                    if i_empties > 10:
                        break

        except Exception as e:
            e_msg = str(e) + ". Full path:" + s_relax_app

        if len(self.uvs):
            # The cluster is returned to the center of the coordinates each time.
            # Here some calculations to return it back to initial coordinates.
            # diff - scalar value based on diagonal differences
            new_bbox = BoundingBox2d(points=self.uvs)
            uvs = np.array(self.uvs)
            uvs += new_bbox.center * -1

            dif = (self.bbox.len_x + self.bbox.len_y) / (new_bbox.len_x + new_bbox.len_y)
            pos = self.bbox.center
            if dif == 0:
                dif = 1.0
                pos = Vector((0.5, 0.5))
            uvs *= dif
            uvs += pos
            for vert, uv in zip(self.uv_verts, uvs):
                vert.set_position(Vector(uv))

            e_msg = "Done"

            return True, e_msg

        # ERROR> We must not come here!
        return False, e_msg


class ZSTsSubCollector:
    # Switch Zen Sets to Face Sets Mode.
    # ('vert', 'edge', 'face', 'vert_u', 'edge_u', 'face_u')
    # context.scene.zen_sets_unique_mode = 'SETS'
    # 'SETS', 'PARTS'
    index = None
    obj_name = None
    isl_name = None
    assign_to_group = False
    passed = True
    mode = None
    sys_message = ""
    adapted_message = ""
    indexes = None
    color = (0.5, 0.5, 0.5)

    def random_color(self):
        r, g, b = [random.random() for i in range(3)]
        # self.color = (r, g, b)
        return (r, g, b)

    def show_data(self):
        attrs = vars(self)
        print('--> '.join("%s: %s\n" % item for item in attrs.items()))

    def set_inform_level(self, level):
        """ level from {'WARNING', 'INFO', 'ERROR','RANDOM'}
        """
        if level in self.inf_levels.keys():
            self.color = self.inf_levels[level]
        else:
            print(f"Level must be in {self.self.inf_levels.keys()}")

    def append_sys_message(self, msg):
        self.sys_message = msg
        if 'Check Edge manifold' in msg:
            msg = 'Edge manifold'
        elif 'topology' in msg:
            msg = 'Disk topology'
        elif 'Multiple Components' in msg:
            msg = 'Multiple Components'
        elif 'Multiple loops' in msg:
            msg = 'Multiple faces'
        elif 'Zero Area Faces' in msg:
            msg = 'Zero Area Faces'

        self.adapted_message = msg


class RelaxCluster(
    # BaseCluster,
    ZenCluster,
    rCluster,
    ProjectCluster,
    TransformCluster,
    ZSTsSubCollector,
):
    def __init__(self, context, obj, island, bm=None) -> None:
        super().__init__(context, obj, island, bm)
        self.name = ''
        # self.init_cycles = 0
        # ZenCluster.__init__(self)
        rCluster.init_r_cluster(self)
        self.inf_levels = {
            'WARNING': (1.0, 1.0, 0.0),
            'INFO': (0.0, 0.0, 1.0),
            'ERROR': (1.0, 0.0, 0.0),
            'RANDOM': self.random_color()
        }


def get_relax_op_props(context):
    return context.scene.zen_uv.op_relax_props


class ZUV_OT_Relax(bpy.types.Operator):
    bl_idname = "uv.zenuv_relax"
    bl_label = "Relax (beta)"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Relax selected islands"

    # method: bpy.props.EnumProperty(
    #     name=ZuvLabels.PROP_RELAX_METHOD_LABEL,
    #     description=ZuvLabels.PROP_RELAX_METHOD_DESC,
    #     items=[
    #         ("ZENRELAX", "Zen Relax", ""),
    #         ("ANGLE_BASED", "Angle Based", ""),
    #         ("CONFORMAL", "Conformal", ""),
    #     ]
    # )
    # select: bpy.props.BoolProperty(
    #     name="Select",
    #     description="Select relaxed Island",
    #     default=False
    # )
    # relax: bpy.props.BoolProperty(
    #     name="Relax",
    #     description="Relax",
    #     default=True,
    #     options={'HIDDEN'}
    # )
    # show_log: bpy.props.BoolProperty(
    #     name="Show Log",
    #     description="Show Log",
    #     default=True,
    #     options={'HIDDEN'}
    # )
    # # relax_mode = None
    # # use_zensets = False
    # relax_mode: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})
    # use_zensets: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context):
        context.scene.zen_uv.op_relax_props.draw_relax_props(self.layout, context)
        # layout = self.layout
        # layout.prop(self, "method")
        # layout.prop(self, "select")

    # def invoke(self, context, event):
    #     addon_prefs = get_prefs()
    #     self.check_zen_sets(context, addon_prefs)
    #     return self.execute(context)

    def check_zen_sets(self, context, show_popup=False):
        props = get_relax_op_props(context)
        if get_prefs().use_zensets:
            if not hasattr(bpy.types, bpy.ops.zsts.assign_to_group.idname()):
                if show_popup:
                    context.window_manager.popup_menu(draw_zensets_popup, title="Zen UV", icon='INFO')
                props.use_zensets = False
            else:
                props.use_zensets = True
        else:
            props.use_zensets = False

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        props = get_relax_op_props(context)
        self.check_zen_sets(context)
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        objs = resort_objects(context, objs)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        if props.method == "ZENRELAX":
            self._zen_relax(context, objs)
            self.check_zen_sets(context, True)
        elif props.method in {"ANGLE_BASED", "CONFORMAL"}:
            props.relax_mode = props.method
            self._relax_native(context, props.select)
        else:
            return {'CANCELLED'}

        return {'FINISHED'}

    def _show_log(self, use_zensets, skip_done, results):
        islands_total = sum([len(data) for data in results.values()])
        g_errors = 0
        l_errors = 0
        info_scope = []
        insertion = "s " if islands_total != 1 else " "
        print("\nZen UV Relax log:", "-" * 25)
        print(f"Total {islands_total} Island{insertion}processed.")
        for obj_name, data in results.items():
            print(f"\n    Object: {obj_name}\n")
            for c_name, info in data.items():
                if not skip_done:
                    print(f"      {c_name} --> {info[1]}")
                else:
                    if not info[0]:
                        print(f"      {c_name} --> {info[1]}")
                if not info[0]:
                    g_errors += 1
                    l_errors += 1
                    info_scope.append(({"WARNING"}, f"{obj_name}[{c_name}] --> {info[1]}"))
                    # self.report({'WARNING'}, f"{obj_name}[{c_name}] --> {info[1]}")
                    # self.report(info_scope[-1][0], info_scope[-1][1])
            if not l_errors:
                print("    Result --> Finished.")
            else:
                print("    Result --> Errors occured.")
            l_errors = 0
        print("\n")
        if g_errors == 1:
            self.report(info_scope[-1][0], info_scope[-1][1])

        elif g_errors > 1:
            insertion = "s " if g_errors != 1 else " "
            self.report(
                {'WARNING'},
                f"Zen UV: In the process of Relaxation {g_errors} error*occurred.".replace("*", insertion) +
                " Look at the system console."
            )
            print("Some islands data inconsistent. Need to be fixed.")
            if use_zensets:
                print("Check Zen Sets Groups.\n")

        else:
            self.report({'INFO'}, f"Zen UV: Relaxation completed. {islands_total} Island{insertion}processed")

    def assign_to_ZSGroups(self, context, c):
        group = f'{c.obj_name} {c.name}-{c.adapted_message}'
        context.scene.zen_sets_active_mode = c.mode
        # Del previous Group if exist.
        if 'FINISHED' in bpy.ops.zsts.set_active_group(mode='GROUP_NAME', group=group):
            bpy.ops.zsts.del_group()
        # Assign to Group
        bpy.ops.zsts.assign_to_group(
            group_mode='INDICES',
            group_indices=tuple({'item': index, 'name': c.obj_name} for index in c.indexes),
            group_name=group, group_color=c.color)

    def convert_clusters_to_log(self, collectors):
        log = {}
        for c in collectors:
            if c.obj_name not in log:
                log.update({c.obj_name: {c.name: [c.passed, c.adapted_message]}})
            else:
                log[c.obj_name].update({c.name: [c.passed, c.adapted_message]})
        return log

    def _relax_native(self, context, _select):
        props = get_relax_op_props(context)
        init_select_mode = context.tool_settings.mesh_select_mode[:]
        objs = list(context.objects_in_mode_unique_data)
        view_layer = context.view_layer
        active_obj = view_layer.objects.active

        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in objs:
            obj.select_set(state=False)

        for obj in objs:
            view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.object.mode_set(mode='EDIT')

            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            uv_layer = bm.loops.layers.uv.verify()
            sync_uv = context.scene.tool_settings.use_uv_select_sync

            init_pins = []
            init_selection = set()

            sync_mode = context.space_data.type == 'IMAGE_EDITOR' and sync_uv or context.space_data.type == 'VIEW_3D'
            loops = {loop: loop[uv_layer] for face in bm.faces for loop in face.loops if not face.hide}

            for loop, uv_loop in loops.items():
                if uv_loop.pin_uv:
                    init_pins.append(uv_loop)
                    uv_loop.pin_uv = False
                if not sync_mode and uv_loop.select:
                    init_selection.add(loop)
                if sync_mode and loop.vert.select:
                    init_selection.add(loop.vert)
                uv_loop.pin_uv = True

            bm.faces.ensure_lookup_table()

            islands = island_util.get_island(context, bm, uv_layer)

            p_loops = [loop[uv_layer] for island in islands for f in island for loop in f.loops]

            for island in islands:
                p_loops = [loop[uv_layer] for f in island for loop in f.loops]
                for i in range(len(p_loops) - 1):
                    p_loops[i].pin_uv = False

            if not sync_mode:
                for loop in p_loops:
                    loop.select = True
            else:
                for face in [f for i in islands for f in i]:
                    face.select = True

            if bpy.ops.uv.unwrap.poll():
                bpy.ops.uv.unwrap(
                    method=props.relax_mode,
                    # fill_holes=self.fill_holes,
                    # correct_aspect=self.correct_aspect,
                    # ue_subsurf_data=self.use_subsurf_data,
                    margin=0
                )

            for loop in loops.values():
                loop.pin_uv = False

            for loop in init_pins:
                loop.pin_uv = True

            # Restore Init Selection
            if not _select:
                if not sync_mode:
                    for loop, uv_loop in loops.items():
                        if loop not in init_selection:
                            uv_loop.select = False
                else:
                    context.tool_settings.mesh_select_mode = [True, False, False]
                    bmesh.select_mode = {'VERT'}
                    for v in bm.verts:
                        v.select = v in init_selection
                    bm.select_flush_mode()

            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(state=False)

        for obj in objs:
            obj.select_set(state=True)
        view_layer.objects.active = active_obj
        bpy.ops.object.mode_set(mode='EDIT')
        context.tool_settings.mesh_select_mode = init_select_mode

    def _zen_relax(self, context, objs):
        props = get_relax_op_props(context)
        skip_done = True
        # self.use_zensets = addon_prefs.use_zensets
        clusters = []
        progress = ProgressBar(context, 100, text_only=True)
        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            islands = island_util.get_island(context, bm, uv_layer)
            for idx, island in enumerate(islands):
                cl = RelaxCluster(context, obj, island, bm)
                cl.obj_name = obj.name
                cl.name = f"Island {idx}"
                cl.index = idx
                progress.set_text_relax(obj_name=cl.obj_name if len(objs) > 1 else "", cluster_name=cl.name, preposition=" of")
                progress.current_step = 0

                m_loops = cl.check_multiple_loops()
                if m_loops:
                    message = "Multiple Loops"
                    cl.append_sys_message("Multiple Loops")
                    cl.indexes = m_loops
                    cl.mode = 'edge'
                    cl.passed = False
                    cl.set_inform_level('ERROR')
                    cl.assign_to_group = True

                if cl.passed:
                    if props.relax:
                        result, message = cl.zen_relax(self, progress)
                        cl.append_sys_message(message)
                        cl.indexes = [f.index for f in cl.island]
                        cl.mode = 'face'
                        cl.passed = True
                        cl.set_inform_level('RANDOM')
                        cl.assign_to_group = False
                    else:
                        result = True
                        message = "Test Mode"

                    if not result:
                        cl.append_sys_message(message)
                        cl.indexes = [f.index for f in cl.island]
                        cl.mode = 'face'
                        cl.passed = False
                        cl.set_inform_level('RANDOM')
                        cl.assign_to_group = True
                        cl.reset()
                clusters.append(cl)

                if props.select:
                    cl.select(context, state=True)

        bm.select_flush_mode()
        bmesh.update_edit_mesh(me)

        if props.use_zensets:
            for cl in clusters:
                if cl.assign_to_group:
                    self.assign_to_ZSGroups(context, cl)

        # else:
        #     if props.show_log:
        #         print("Zen UV: Zen Sets is not installed.")

        if progress.pb is not None:
            progress.finish()

        if not props.show_log:
            return {'FINISHED'}

        self._show_log(props.use_zensets, skip_done, self.convert_clusters_to_log(clusters))


relax_classes = (
    ZUV_OT_Relax,
)


if __name__ == "__main__":
    pass

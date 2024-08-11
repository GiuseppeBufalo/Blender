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

''' Zen UV Internal System Operators '''


import bpy
import bmesh
from ZenUV.utils.generic import (
    resort_objects,
)
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.tests.addon_test_utils import (
    _prepare_test,
    AddonTestError,
    _get_hided_faces_ids,
    _hide_faces_by_id_active_obj,
    _move_uv_by_faces_id
)
from ZenUV.utils.vlog import Log
from ZenUV.utils.blender_zen_utils import ZenPolls


class ContextSolver:

    def __init__(self, context) -> None:
        self.context_uv_edit = 'IMAGE_EDITOR'
        self.context_view3d = 'VIEW_3D'
        self.context_current = context.space_data.type
        self.info_message = f'Current Editor context --> {self.context_current}'
        self.warning_message = 'Need to be tested in the @ context.'
        self.wrong_context_message = 'Editior context undefined.'

    def get_warning(self):
        if self.context_current == self.context_uv_edit:
            return self.warning_message.replace('@', self.context_view3d)
        elif self.context_current == self.context_view3d:
            return self.warning_message.replace('@', self.context_uv_edit)
        else:
            return self.wrong_context_message

    def get_editor_context(self):
        return self.context_current


PHASE_DESCRIPTION = {
    'VIEW_3D': {
        1: '',
        2: '',
        3: '',
        4: '',
    },
    'IMAGE_EDITOR': {
        1: '',
        2: '',
        3: '',
        4: '',
    }
}


class ZUV_OT_SysCheckSelInSyncUv(bpy.types.Operator):
    bl_idname = "zenuv.check_sel_in_sync_states"
    bl_label = "Check Sel in Sync UV"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Check Selection in the Sync UV states"

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        self.island_01 = [1, 2, 3, 4]
        self.island_02 = [0, 5]
        self.all_islands = self.island_01.copy()
        self.all_islands.extend(self.island_02)

        objs = self.prepare_test(context)

        if not objs:
            raise AddonTestError("The test is not prepared correctly. There is no objects in the scene.")

        Log.info(f'Tested Object(s) --> {[o.name for o in objs]}')

        CS = ContextSolver(context)

        text = 'Check Islands System Started'
        Log.debug(f'{text:-^120}')
        Log.split()

        if CS.get_editor_context() == 'VIEW_3D':
            Log.split()
            Log.debug('Testing in the 3D View.')
            # Phase 01
            phase = 1
            self._show_state_phase(context, 1, CS)

            self.call_test(context, objs, CS, phase, test_islands_count=2)

            Log.split()

            # Phase 02
            phase = 2
            _hide_faces_by_id_active_obj(context, self.island_01)
            self._show_state_phase(context, 2, CS)

            self.call_test(context, objs, CS, phase, test_islands_count=1)

        elif CS.get_editor_context() == 'IMAGE_EDITOR':
            Log.split()
            Log.debug('Testing in the UV Editor.')

            # Phase 01
            phase = 1
            self._show_state_phase(context, 1, CS)

            self.call_test(context, objs, CS, phase, test_islands_count=2)

            # Phase 02
            phase = 2
            _hide_faces_by_id_active_obj(context, self.island_01)
            self._show_state_phase(context, 2, CS)

            self.call_test(context, objs, CS, phase, test_islands_count=1)

            # Phase 03
            phase = 3
            objs = self.prepare_test(context)
            context.scene.tool_settings.use_uv_select_sync = False
            self._show_state_phase(context, 3, CS)

            self.call_test(context, objs, CS, phase, test_islands_count=2)

            # Phase 04
            phase = 4
            objs = self.prepare_test(context)
            context.scene.tool_settings.use_uv_select_sync = False
            self._show_state_phase(context, 4, CS)

            self._select_faces_by_id_active_obj(context, self.all_islands, state=False)

            # Select only one island
            self._select_faces_by_id_active_obj(context, self.island_01, state=True)

            self.call_test(context, objs, CS, phase, test_islands_count=1)

        else:
            Log.debug(CS.wrong_context_message)

        Log.debug(CS.get_warning())

        return {"FINISHED"}

    def call_test(self, context, objs, CS, phase, test_islands_count):

        islands = self._get_islands(context, objs)

        collected_islands_count = len(islands)
        Log.debug(f'Tested Islands Count --> {test_islands_count}')
        Log.debug(f'Collected Islands Count --> {collected_islands_count}')
        Log.debug(f'Collected Islands --> {islands}')
        if test_islands_count != collected_islands_count:
            raise AddonTestError(f'TEST> {CS.get_editor_context()} Phase: 0{phase}. Collected Islands Count must be {test_islands_count} instead of {collected_islands_count}')
        Log.debug('TEST> Passed.')

    def _show_state_phase(self, context, phase, CS):
        Log.split()
        editor = CS.get_editor_context()
        phase_text = f' [ Phase 0{str(phase)} ] '
        Log.debug(f'{phase_text:#^100}')
        Log.info(f'Current Editor --> {editor}')
        Log.info(f"Phase Description: {PHASE_DESCRIPTION[editor][phase]}")
        Log.debug('Current Testing State:')
        Log.debug(f'Blender version is {bpy.app.version}. Greater 3.2.0 {ZenPolls.version_greater_3_2_0}')
        Log.debug(f"Sync UV State --> {context.scene.tool_settings.use_uv_select_sync}")
        Log.debug('Test function --> ZenUV.utils.get_uv_islands.get_islands(context, bm)')
        Log.debug(f'Hidden faces --> {_get_hided_faces_ids(context)}')

    def _get_islands(self, context, objs):
        islands = []
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data).copy()
            # uv_layer = bm.loops.layers.uv.verify()
            for island in island_util.get_islands(context, bm):
                islands.append([f.index for f in island])
            bm.free()
        return islands

    def prepare_test(self, context):
        _prepare_test(context, count=1)

        context.scene.tool_settings.use_uv_select_sync = True

        Log.debug('UV Sync Selection was switched to On.')
        Log.debug(f'Check UV Sync Selection --> {context.scene.tool_settings.use_uv_select_sync}')

        _move_uv_by_faces_id(context, self.island_01, offset=(0.7, 0))

        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            raise AddonTestError("The test is not prepared correctly. There is no objects in the scene.")
        return objs

    def _select_faces_by_id_active_obj(self, context, ids, state):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for i in ids:
            bm.faces[i].select = state
        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data)

    def select_all_loops_active_obj(self, context):
        obj = context.object
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        loops = [lp for f in bm.faces for lp in f.loops]
        if ZenPolls.version_greater_3_2_0:
            for loop in loops:
                loop[uv_layer].select = True
                loop[uv_layer].select_edge = True
        else:
            for loop in loops:
                loop[uv_layer].select = True


class ZUV_OT_DEBUG(bpy.types.Operator):
    bl_idname = "uv.zenuv_debug"
    bl_label = "Check Tests"
    bl_description = "Select Similar Islands"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ZenUV.utils.tests.transform_tests import tests_transform_sys
        for c in tests_transform_sys:
            if str(c.__name__) == 'Test_uv_zenuv_align_grab_position':
                c(context)

        return {'FINISHED'}


system_classes = (
    ZUV_OT_SysCheckSelInSyncUv,
    ZUV_OT_DEBUG
)


def register():
    for cl in system_classes:
        bpy.utils.register_class(cl)


def unregister():
    for cl in system_classes:
        bpy.utils.unregister_class(cl)


if __name__ == "__main__":
    pass

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

import csv
import os
import inspect

# from .sets.factories import sets_factories, obj_collection_factories, obj_simple_factories, get_sets_mgr_by_id
from ZenUV.prop.zuv_preferences import get_prefs
from ..vlog import Log
from ..progress import start_progress, update_progress, end_progress
from .addon_test_utils import (
    AddonTestError,
    AddonTestManual,
    set_skip_tests,
    _prepare_test
)
# from .blender_zen_utils import ZenPolls

from . adv_uv_maps_tests import (
    # Done
    Test_mesh_rename_uvs,
    Test_mesh_remove_inactive_uvs,
    Test_mesh_sync_uv_ids,
    Test_mesh_remove_uvs,
    Test_mesh_show_uvs,
    Test_mesh_add_uvs,
    Test_uv_zenuv_copy_uv,
    Test_uv_zenuv_paste_uv,
    Test_wm_auto_sync_uv_ids,
)

from . checker_tests import (
    # Done
    Test_view3d_zenuv_checker_toggle,
    Test_view3d_zenuv_checker_remove,
    Test_view3d_zenuv_checker_collect_images,
    Test_view3d_zenuv_checker_reset,
    Test_view3d_zenuv_checker_open_editor,
    Test_view3d_zenuv_checker_append_checker_file,
    Test_ops_zenuv_checker_reset_path,
)

from . finished_tests import (
    # Done
    Test_uv_zenuv_untag_finished,
    Test_uv_zenuv_islands_sorting,
    Test_uv_zenuv_display_finished,
    Test_uv_zenuv_tag_finished,
    Test_uv_zenuv_select_finished,
)

from . mark_tests import (
    # Done
    Test_uv_zenuv_seams_by_sharp,
    Test_uv_zenuv_seams_by_uv_islands,
    Test_uv_zenuv_seams_by_open_edges,
    Test_uv_zenuv_sharp_by_seams,
    Test_mesh_zenuv_select_sharp,
    Test_uv_zenuv_unified_mark,
    Test_uv_zenuv_mark_seams,
    Test_mesh_zenuv_select_seams,
    Test_uv_zenuv_auto_mark,
    Test_uv_zenuv_unmark_all,
    Test_uv_zenuv_sharp_by_uv_islands,
    Test_uv_zenuv_unmark_seams,
)

from . pack_tests import (
    # Done
    Test_uv_zenuv_pack,
    Test_uv_zenuv_sync_to_uvp,
    Test_uv_zenuv_offset_pack_excluded,
    Test_uv_zenuv_untag_pack_excluded,
    Test_uv_zenuv_unhide_pack_excluded,
    Test_uv_zenuv_tag_pack_excluded,
    Test_uv_zenuv_select_pack_excluded,
    Test_uv_zenuv_hide_pack_excluded,
)

from . seam_groups_tests import (
    # Done
    Test_zen_sg_list_delete_item,
    Test_zen_sg_list_move_item,
    Test_zen_sg_list_new_item,
    Test_uv_zenuv_assign_seam_to_group,
    Test_view3d_zenuv_set_smooth_by_sharp,
    Test_uv_zenuv_activate_seam_group,
)

from . select_tests import (
    # Done
    Test_uv_zenuv_select_by_direction,
    Test_uv_zenuv_show_sim_index,
    Test_uv_zenuv_select_similar,
    Test_uv_zenuv_select_island,
    Test_uv_zenuv_select_stretched_islands,
    Test_uv_zenuv_select_uv_borders,
    Test_uv_zenuv_select_uv_overlap,
    Test_uv_zenuv_select_flipped,
    Test_uv_zenuv_select_pack_excluded,
    Test_uv_zenuv_select_loop,
    Test_uv_zenuv_isolate_island,
    Test_mesh_zenuv_mirror_seams,
    Test_uv_zenuv_select_by_uv_area,
    Test_uv_zenuv_grab_sel_area
)

from . stacks_tests import (
    # Done
    Test_zen_stack_list_remove_all_m_stacks,
    Test_uv_zenuv_simple_stack,
    Test_uv_zenuv_unstack_manual_stack,
    Test_zen_stack_list_new_item,
    Test_uv_zenuv_select_stack,
    Test_uv_zenuv_select_stacked,
    Test_uv_zenuv_assign_manual_stack,
    Test_uv_zenuv_collect_manual_stacks,
    Test_uv_zenuv_paste_param,
    Test_uv_zenuv_select_m_stack,
    Test_uv_zenuv_simple_unstack,
    Test_uv_zenuv_unstack,
    Test_zen_stack_list_delete_item,
    Test_uv_zenuv_analyze_stack,
    Test_uv_zenuv_stack_similar,
    Test_uv_zenuv_copy_param
)

from . sticky_tests import (
    # Done
    Test_wm_sticky_uv_editor,
    Test_wm_sticky_uv_editor_split,
)

from .td_tests import (
    # Done
    Test_uv_zenuv_get_texel_density_obj,
    Test_uv_zenuv_set_texel_density_obj,
    Test_zen_tdpr_generate_presets,
    Test_zen_tdpr_new_item,
    Test_zen_tdpr_move_item,
    Test_zen_tdpr_set_td_from_preset,
    Test_zen_tdpr_clear_presets,
    Test_uv_zenuv_display_td_preset,
    Test_zen_tdpr_delete_item,
    Test_uv_zenuv_hide_texel_density,
    Test_zen_tdpr_select_by_texel_density,
    Test_uv_zenuv_display_td_balanced,
    Test_zenuv_set_current_td_to_checker_td,
    Test_zen_tdpr_get_td_from_preset,
    Test_uv_zenuv_get_texel_density,
    Test_uv_zenuv_set_texel_density,
    Test_uv_zenuv_get_uv_coverage,
    Test_uv_zenuv_get_image_size_uv_layout
    )

from . transform_tests import (
    # Done
    Test_uv_zenuv_unified_transform,
    Test_uv_zenuv_arrange_transform,
    Test_uv_zenuv_randomize_transform,
    Test_uv_zenuv_tr_scale_tuner,
    Test_uv_zenuv_fit_region,
    Test_uv_zenuv_fit_grab_region,
    Test_uv_zenuv_quadrify,
    Test_uv_zenuv_reshape_island,
    Test_uv_zenuv_scale_grab_size,
    Test_uv_zenuv_relax,
    Test_uv_zenuv_unwrap,
    Test_uv_zenuv_distribute_verts,
    Test_uv_zenuv_distribute_islands,
    Test_uv_zenuv_world_orient,
    Test_uv_zenuv_align_grab_position
)

from .misc_tests import tests_misc
from .pie_callers_tests import tests_pie_callers


class ZuvAddonTest(bpy.types.Operator):
    bl_idname = 'zenuv_test.addon_test'
    bl_label = 'Zen UV Addon Testing'
    bl_description = 'Executes list of Zen UV Tests'
    bl_options = {'REGISTER'}

    stop_on_fail: bpy.props.BoolProperty(name='Stop on fail', default=False)
    report_undefined: bpy.props.BoolProperty(name='Report about undefined tests', default=True)
    write_functions: bpy.props.BoolProperty(name='Write Functions', default=False)
    write_skipped: bpy.props.BoolProperty(name='Write Skipped', default=False)

    # @classmethod
    # def poll(cls, context):
    #     return get_prefs().common.developer_mode

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        skip_tests = set_skip_tests([tests_pie_callers, tests_misc])
        Log.split()
        Log.info("Skipped Tests --> ", skip_tests)
        Log.split()
        skip = False
        try:
            _prepare_test(context)

            csv_dirname = os.path.dirname(__file__)
            csv_filename = os.path.join(csv_dirname, 'report.csv')

            text_file = os.path.join(csv_dirname, 'tests_scope.py')

            if self.write_functions:
                func_file = open(text_file, 'w')

            with open(csv_filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["No", "Module", "Operator", "Result", "Description", "Command"])

                operators_list = set()

                for op_module_name in dir(bpy.ops):

                    # if is_zen_module(op_module_name):
                    op_module = getattr(bpy.ops, op_module_name)
                    start_progress(context, 0, 100, high_priority=True)
                    zenuv_operators = dir(op_module)
                    for i, op_submodule_name in enumerate(zenuv_operators):
                        op = getattr(op_module, op_submodule_name)
                        text = repr(op)
                        s_type = op.idname()
                        try:
                            cls = getattr(bpy.types, s_type)

                            s_op_path = inspect.getfile(cls)
                            if 'ZenUV' in s_op_path:
                                if text.split("\n")[-1].startswith("bpy.ops."):
                                    operators_list.add((text, op_module_name, op_submodule_name, cls.bl_description))
                        except Exception:
                            pass

                tot = 0
                start_progress(context, 0, 100, high_priority=True)
                full_list_of_functions = []
                for i, op_data in enumerate(operators_list):

                    text, op_module_name, op_submodule_name, op_description = op_data
                    # print("-->", text, op_module_name, op_submodule_name, op_description)

                    if f'Test_{op_module_name}_{op_submodule_name}' in skip_tests:
                        result = 'SKIPPED'
                        description = 'skipped'
                        skip = True
                    else:
                        result = 'UNKNOWN'
                        description = ''
                        skip = False

                    func_name_exec = "generic func name exec"

                    if not skip:
                        try:
                            Log.split()
                            Log.info('Starting:', text)

                            func_name = f'Test_{op_module_name}_{op_submodule_name}'
                            func_name_exec = f'{func_name}(context)'

                            exec(f'_func_check = {func_name}')
                            _prepare_test(context)
                            exec(func_name_exec)

                            result = 'SUCCESS'

                        except NameError:
                            result = 'NO TEST FOUND'
                            description = f'{func_name_exec} - not found!'
                            if self.report_undefined:
                                Log.warn(text, description)
                        except AddonTestManual:
                            result = 'MANUAL'
                            description = 'MANUAL!'
                            Log.warn(text, description)
                        except AddonTestError as e:
                            result = 'FAILED'
                            description = func_name_exec + ': ' + str(e)
                            Log.error(text, description)
                        except Exception as e:
                            result = 'ERROR EXCEPTION'
                            description = func_name_exec + ': ' + str(e)
                            Log.error(text, description)

                    if self.write_functions:
                        func_full = f"def {func_name_exec}:\n    ''' {op_description} '''\n    {text}\n\n\n"
                        full_list_of_functions.append(func_name_exec + "\n")

                    tot += 1

                    if self.report_undefined or result != 'NO TEST FOUND':
                        if not self.write_skipped and result == "SKIPPED":
                            pass
                        else:
                            writer.writerow([tot, op_module_name, op_submodule_name, result, description, text])

                        valid_results = ['SUCCESS', 'MANUAL', 'SKIPPED']

                        if result not in valid_results:
                            if self.stop_on_fail:
                                raise AddonTestError(result, description)
                            else:
                                self.report({'ERROR'}, description)

                    i_percent = int(i / len(operators_list) * 100)
                    Log.debug(f'Completed:{text} - {i_percent}%')
                    Log.split()
                    update_progress(context, i_percent, high_priority=True)

                end_progress(context, high_priority=True)

                if self.write_functions:
                    func_file.write(func_full)
                    func_file.writelines(full_list_of_functions)

        except Exception as e:
            self.report({'ERROR'}, str(e))

        if self.write_functions:
            func_file.close()

        end_progress(context, high_priority=True)

        try:
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode='EDIT')
        except Exception as e:
            print(e)

        return {'FINISHED'}


def menu_addon_test_func(self, context):
    if get_prefs().common.developer_mode:
        layout = self.layout
        layout.separator()
        layout.operator('zsts_test.addon_test')


def register():
    bpy.utils.register_class(ZuvAddonTest)
    # bpy.types.ZSTS_MT_GroupMenu.append(menu_addon_test_func)


def unregister():
    # bpy.types.ZSTS_MT_GroupMenu.remove(menu_addon_test_func)
    bpy.utils.unregister_class(ZuvAddonTest)

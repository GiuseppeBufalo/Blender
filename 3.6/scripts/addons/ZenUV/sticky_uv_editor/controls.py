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

# <pep8 compliant>

# Sticky UV Editor
# Original idea Oleg Stepanov (DotBow)
# https://github.com/DotBow/Blender-Sticky-UV-Editor-Add-on


import bpy

import functools
import math
from timeit import default_timer as timer

from bpy.props import BoolProperty
from bpy.types import GizmoGroup, Operator
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.generic import ZenKeyEventSolver


def get_prefs():
    """ Return Zen UV Properties obj """
    return bpy.context.preferences.addons[ZuvLabels.ADDON_NAME].preferences


_solver = None
_was_context = None


def ShowMessageBox(message="", title="Message Box", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def _handle_sticky_solver():
    if _solver is None:
        return

    if _solver.is_modifier_right:
        _solver.create_uv_editor(new_window=True)
        return None

    result = _solver.close_uv_editor()

    if result:
        return None
    elif result is None:
        ShowMessageBox(
            title="Sticky UV Editor",
            message="Failed to figure out current layout!",
            icon="ERROR")
        return None
    else:
        _solver.init_state(_was_context)
        _solver.create_uv_editor(new_window=False)

    return None


def _handle_snooper():
    if _solver is None:
        return

    if _solver.warp_it == 0:

        if math.fabs(_solver.view3d_area.width - (_solver.warp_was_width + math.fabs(_solver.delta))) < 2.0:
            return None

    _solver.context["window"].cursor_warp(_solver.warp_x, _solver.warp_y)

    _solver.warp_it += 1

    # no need to wait more than 1 sec, something wrong
    if timer() - _solver.warp_timer > 1.0:
        return None

    if not bpy.ops.screen.area_move.poll(_solver.context, 'INVOKE_REGION_WIN'):
        return 0.001

    # should poll now
    bpy.ops.screen.area_move(x=_solver.warp_x, y=_solver.warp_y, delta=_solver.delta)

    w = _solver.context["window"]
    w.cursor_warp(_solver.imp_x, _solver.imp_y)
    return None


class StkUvEditorSolver():

    def __init__(self, mouse_pos, ui_button, side=None) -> None:
        self.addon_prefs = get_prefs()
        self.ui_button = ui_button

        self.app_is_3 = bpy.app.version >= (3, 0, 0)
        self.side = side

        self.imp_x = mouse_pos[0]
        self.imp_y = mouse_pos[1]
        self.delta = -100
        self.init = False

    def init_state(self, context):
        self.context = context
        self.stk_props = context['scene'].StkUvEdProps
        if self.side is None:
            # If side is not defined:
            # Default value is "LEFT"
            self.side = self.addon_prefs.uv_editor_side
            self.prefs_side_left = self.side == "LEFT"
        else:
            self.prefs_side_left = self.side == "LEFT"

        self.input_areas = context['screen'].areas

        self.active = context['area']
        self.areas = self._get_sorted_areas()

        try:
            self.active_index = self.areas.index(self.active)
        except Exception:
            return None

        self.view3d_area = None
        self.v_3d_idx = None
        self.area_on_left = None
        self.area_on_right = None
        self._find_view3d_area()
        self._find_side_areas()

        self.init = True

        return True

    def __del__(self):
        return None

    def _find_view3d_area(self):
        if self.active.ui_type == "VIEW_3D":
            self.view3d_area = self.active
            self.v_3d_idx = self.active_index
        else:
            if self.active.ui_type == "UV":
                if self.prefs_side_left:
                    v_3d_idx = self.active_index + 1
                elif not self.prefs_side_left:
                    v_3d_idx = self.active_index - 1
            if self._index_in_list(v_3d_idx) and self.areas[v_3d_idx].ui_type == "VIEW_3D":
                self.view3d_area = self.areas[v_3d_idx]
            self.v_3d_idx = v_3d_idx

    def _index_in_list(self, index):
        if 0 <= index < len(self.areas):
            return True
        return False

    def _find_side_areas(self):
        l_index = self.v_3d_idx - 1
        r_index = self.v_3d_idx + 1
        if self._index_in_list(l_index):
            self.area_on_left = self.areas[l_index]
        if self._index_in_list(r_index):
            self.area_on_right = self.areas[r_index]

    def _get_sorted_areas(self):
        scope = [(area.x, area) for area in self.input_areas]
        from operator import itemgetter
        scope = sorted(scope, key=itemgetter(0))

        return [pair[1] for pair in scope]

    def _is_init(self):
        if not self.init:
            print("Zen UV: class StkUvEditorSolver must be initialized first. Use .init_state()")
            return False
        return True

    def close_uv_editor(self):
        if not self._is_init():
            return False
        if self.side not in {"LEFT", "RIGHT"}:
            print("Zen UV: class StkUvEditorSolver solver side not in ['LEFT', 'RIGHT']")
            return None

        if self.app_is_3:
            if self.prefs_side_left and self.area_on_left and self.area_on_left.ui_type == "UV":
                self.stk_props.save_from_area(self.context['scene'], self.area_on_left)
                ctx = self.context.copy()
                ctx["area"] = self.area_on_left
                self._warp()
                bpy.ops.screen.area_close(ctx)

                return True
            elif not self.prefs_side_left and self.area_on_right and self.area_on_right.ui_type == "UV":
                self.stk_props.save_from_area(self.context['scene'], self.area_on_right)
                ctx = self.context.copy()
                ctx["area"] = self.area_on_right
                self._warp()
                bpy.ops.screen.area_close(ctx)
                return True
            return False
        else:
            # Close UV Editor In 2.9
            # print("Close UV Editor In 2.9")
            if self.prefs_side_left and self.area_on_left and self.area_on_left.ui_type == "UV":
                self.stk_props.save_from_area(self.context['scene'], self.area_on_left)
                if self.active.ui_type == "UV":
                    self._close_UVE_on_left(self.view3d_area)
                else:
                    self._close_UVE_on_left(self.active)
                self._force_update_layout(self.view3d_area)
                return True

            elif not self.prefs_side_left and self.area_on_right and self.area_on_right.ui_type == "UV":
                self.stk_props.save_from_area(self.context['scene'], self.area_on_right)
                self._close_UVE_on_right(self.area_on_right)
                self._force_update_layout(self.area_on_right)
                return True
            else:
                return False

    def create_uv_editor(self, new_window=False):
        """ Create UV Editor on side """
        if not self._is_init():
            return False
        if not new_window:
            bpy.ops.screen.area_split(self.context, direction='VERTICAL', factor=0.5)

        if self.prefs_side_left:
            for area in reversed(self.input_areas):
                if area.ui_type == 'VIEW_3D':
                    uv_area = area
                    break
            # pos_x = self.imp_x + self.active.width
        else:
            uv_area = self.active
            # pos_x = self.imp_x - self.active.width

        # Why do we need this !?
        # if self.ui_button:
        #     self.context["window"].cursor_warp(pos_x >> 1, self.imp_y)

        init_ui_type = self.active.ui_type
        uv_area.ui_type = 'UV'

        self.set_stk_area_props(uv_area)

        self.set_stk_area_mode(uv_area)

        if new_window:
            bpy.ops.screen.area_dupli(self.context, 'INVOKE_DEFAULT')
            self.active.ui_type = init_ui_type

    def set_stk_area_mode(self, uv_area):
        # Set view mode
        view_mode = self.addon_prefs.view_mode

        if view_mode != 'DISABLE' and self.context['mode'] == 'EDIT_MESH':

            override = self.context.copy()
            override['area'] = uv_area

            if view_mode == 'FRAME_ALL':
                bpy.ops.image.view_all(override)
            elif view_mode == 'FRAME_SELECTED':
                bpy.ops.image.view_selected(override)
            elif view_mode == 'FRAME_ALL_FIT':
                bpy.ops.image.view_all(override, fit_view=True)

    def set_stk_area_props(self, uv_area):
        # Set UV Editor area settings

        if not self.stk_props.initialized or not self.addon_prefs.remember_uv_editor_settings:
            self.stk_props.save_from_property(self.context['scene'], self.addon_prefs.StkUvEdProps)
            self.stk_props.initialized = True
            self.context['scene'].tool_settings.use_uv_select_sync = self.addon_prefs.use_uv_select_sync

        self.stk_props.set(self.context['scene'], uv_area)

    def _warp(self):
        a = self.view3d_area
        if not a:
            return False

        if self.area_on_left:
            x = a.x
            y = a.y + (a.height >> 1)
            self.delta = - self.area_on_left.width

        if self.area_on_right and not self.prefs_side_left:
            x = a.x + a.width
            y = a.y + (a.height >> 1)
            self.delta = self.area_on_right.width

        self.warp_x = x
        self.warp_y = y
        self.warp_was_width = self.view3d_area.width
        self.warp_timer = timer()
        self.warp_it = 0

        if bpy.app.timers.is_registered(_handle_snooper):
            bpy.app.timers.unregister(_handle_snooper)
        bpy.app.timers.register(_handle_snooper)

    def _force_update_layout(self, area):
        # space = area.spaces[0]
        # space.show_region_toolbar = space.show_region_toolbar
        spaces = area.spaces
        if spaces:
            space = spaces[0]
            mode = space.show_region_toolbar
            space.show_region_toolbar = not mode
            space.show_region_toolbar = mode

    def _close_UVE_on_left(self, area):
        bpy.ops.screen.area_join(self.context, cursor=(area.x, area.y + int(area.height >> 1)))

    def _close_UVE_on_right(self, area):
        pos_y = area.y + int(area.height >> 1)
        bpy.ops.screen.area_swap(self.context, cursor=(area.x, pos_y))
        bpy.ops.screen.area_join(self.context, cursor=(area.x, pos_y))


class ZUV_StickyUVEditorSplit(Operator):
    """Open UV Editor in a separate window."""
    bl_idname = "wm.sticky_uv_editor_split"
    bl_label = "Sticky UV Editor Split"
    bl_description = "Open UV Editor in a separate window"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(self, context):
        return context.area and context.area.ui_type == 'VIEW_3D'

    def invoke(self, context, event):
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y
        return self.execute(context)

    def execute(self, context):
        solver = StkUvEditorSolver((self.mouse_x, self.mouse_y), False)
        if solver.init_state(context.copy()):
            solver.create_uv_editor(new_window=True)
            return {'FINISHED'}
        return {'CANCELLED'}


class ZUV_StickyUVEditor(Operator):

    bl_idname = "wm.sticky_uv_editor"
    bl_label = "Sticky UV Editor"
    bl_options = {'REGISTER'}
    bl_description = ""

    ui_button: BoolProperty(default=False)

    desc: bpy.props.StringProperty(
        name="Description",
        default=ZuvLabels.STK_UV_ED_OPERATOR_DESC,
        options={'HIDDEN'}
    )

    @classmethod
    def description(cls, context, properties):
        addon_prefs = get_prefs()
        zk_mod = addon_prefs.bl_rna.properties['zen_key_modifier'].enum_items
        zk_mod = zk_mod.get(addon_prefs.zen_key_modifier)
        cls.desc = ZuvLabels.STK_UV_ED_OPERATOR_DESC.replace("*", zk_mod.name)
        return cls.desc

    @classmethod
    def poll(self, context):
        return context.area and context.area.ui_type in ['UV', 'VIEW_3D']

    def modal(self, context, event):
        if event.type == "LEFTMOUSE" and event.value == 'RELEASE':
            return self.execute(context)
        elif event.type not in {'MOUSEMOVE', 'TIMER', 'TIMER_REPORT', 'INBETWEEN_MOUSEMOVE'}:
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if event.ctrl and event.shift:
            if event.type == "LEFTMOUSE":
                bpy.ops.ops.zenuv_show_prefs(tabs="STK_UV_EDITOR")
                return {'FINISHED'}

        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y
        self.is_modifier_right = ZenKeyEventSolver(context, event, get_prefs()).solve()

        if event.type == "LEFTMOUSE" and event.value == 'PRESS':
            if context.window_manager.modal_handler_add(self):
                return {'RUNNING_MODAL'}
        else:
            return self.execute(context)

        return {'CANCELLED'}

    def execute(self, context):
        if (bpy.app.timers.is_registered(_handle_sticky_solver) or
                bpy.app.timers.is_registered(_handle_snooper)):
            self.report({'WARNING'},
                        "Sticky UV Editor: Previous operation was not finished yet!")
            return {'CANCELLED'}

        if context.window.screen.show_fullscreen:
            self.report({'WARNING'},
                        "Sticky UV Editor: Fullscreen mode is not supported!")
            return {'CANCELLED'}

        global _solver

        _solver = StkUvEditorSolver((self.mouse_x, self.mouse_y), self.ui_button)
        _solver.is_modifier_right = self.is_modifier_right
        _solver.operator = self

        global _was_context
        _was_context = context.copy()

        if not _solver.init_state(_was_context):
            _solver = None
            print("Sticky UV Editor: Failed to init.")
            ShowMessageBox(
                title="Sticky UV Editor",
                message="Failed to figure out current layout!",
                icon="ERROR")
            return {'CANCELLED'}

        bpy.app.timers.register(_handle_sticky_solver)

        return {'FINISHED'}


class ZUV_StickyUVEditor_UI_Button(GizmoGroup):
    bl_idname = "StickyUVEditor_UI_Button"
    bl_label = "Sticky UV Editor UI Button"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return (addon_prefs.show_ui_button) and \
            (not context.window.screen.show_fullscreen)

    def draw_prepare(self, context):
        addon_prefs = get_prefs()
        ui_scale = context.preferences.view.ui_scale
        widget_size = self.foo_gizmo.scale_basis * ui_scale
        correction = 2

        if addon_prefs.uv_editor_side == 'RIGHT':
            n_panel_width = [region.width for region in context.area.regions if region.type == "UI"][0]
            base_position = context.region.width - n_panel_width - widget_size - correction
            props_influence = (100 - addon_prefs.stk_ed_button_h_position) * 0.01
            self.foo_gizmo.matrix_basis[0][3] = base_position * props_influence
        else:
            tools_width = [region.width for region in context.area.regions if region.type == "TOOLS"][0]
            base_position = tools_width + widget_size + correction
            props_influence = (((context.region.width - base_position) * addon_prefs.stk_ed_button_h_position) / 100)
            self.foo_gizmo.matrix_basis[0][3] = base_position + props_influence

        self.foo_gizmo.matrix_basis[1][3] = context.region.height * addon_prefs.stk_ed_button_v_position * 0.01

    def setup(self, context):
        mpr = self.gizmos.new("GIZMO_GT_button_2d")
        mpr.show_drag = False
        mpr.icon = 'UV'
        mpr.draw_options = {'BACKDROP', 'OUTLINE'}

        mpr.color = 0.0, 0.0, 0.0
        mpr.alpha = 0.5
        mpr.color_highlight = 0.8, 0.8, 0.8
        mpr.alpha_highlight = 0.2

        mpr.scale_basis = (80 * 0.35) / 2  # Same as buttons defined in C
        op = mpr.target_set_operator("wm.sticky_uv_editor")
        op.ui_button = True
        self.foo_gizmo = mpr


STK_classes = (
    ZUV_StickyUVEditor,
    ZUV_StickyUVEditor_UI_Button,
    ZUV_StickyUVEditorSplit,
)

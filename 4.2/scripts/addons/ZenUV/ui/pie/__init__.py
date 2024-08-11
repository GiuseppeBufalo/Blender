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

# Copyright 2021, Alex Zhornyak

# blender
import bpy
import blf

import math

from timeit import default_timer as timer

from .basic_pie import get_command_props

# from .mesh_pie import (
#     ZSTO_OT_PieCallerTop,
#     ZSTO_OT_PieCallerTopRight,
#     ZSTO_OT_PieCallerTopLeft,
#     ZSTO_OT_PieCallerBottom,
#     ZSTO_OT_PieCallerLeft,
#     ZSTO_OT_PieCallerRight,
#     ZSTO_OT_PieCallerBottomLeft,
#     ZSTO_OT_PieCallerBottomRight,
# )

from .mesh_pie import (
    ZUV_OT_PieCallerTop,
    ZUV_OT_PieCallerTopRight,
    ZUV_OT_PieCallerTopLeft,
    ZUV_OT_PieCallerBottom,
    ZUV_OT_PieCallerLeft,
    ZUV_OT_PieCallerRight,
    ZUV_OT_PieCallerBottomLeft,
    ZUV_OT_PieCallerBottomRight,
)

from ...ico import icon_get
# from ...vlog import Log
from ZenUV.utils.blender_zen_utils import ZsDrawConstans

from ZenUV.ui.bl_ui_widgets.bl_ui_drag_panel import BL_UI_Drag_Panel
from ZenUV.ui.bl_ui_widgets.bl_ui_label import BL_UI_Label
from ZenUV.utils.constants import ADDON_NAME


# ZUV_MT_BasicPie
class ZUV_MT_BasicPie(bpy.types.Menu):
    bl_label = 'Zen UV'

    def multi_operator(self, op_cls, layout, is_menu, icon_value=0):
        if is_menu:
            layout.operator_menu_enum(op_cls.bl_idname, 'cmd_enum')
        else:
            layout.operator(op_cls.bl_idname, icon_value=icon_value).is_menu = False

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        is_menu = False

        is_object_mode = context.mode == 'OBJECT'
        # op_prefix = 'zsto' if is_object_mode else 'zsts'

        # 4 - LEFT
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerLeft, pie, is_menu)
        else:
            self.multi_operator(ZUV_OT_PieCallerLeft, pie, is_menu, icon_value=icon_get("unmark-seams_32"))

        # 6 - RIGHT
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerRight, pie, is_menu)
        else:
            self.multi_operator(ZUV_OT_PieCallerRight, pie, is_menu, icon_value=icon_get("mark-seams_32"))

        # 2 - BOTTOM
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerBottom, pie, is_menu, icon_value=icon_get(ZIconsType.AddonLogoPng2x))
        else:
            self.multi_operator(ZUV_OT_PieCallerBottom, pie, is_menu, icon_value=icon_get("zen-unwrap_32"))

        # 8 - TOP
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerTop, pie, is_menu, icon_value=icon_get(ZIconsType.SmartSelect))
        else:
            # pie.operator('zsts.smart_select', icon_value=icon_get("zen-uv_32"))
            self.multi_operator(ZUV_OT_PieCallerTop, pie, is_menu)

        # 7 - TOP - LEFT
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerTopLeft, pie, is_menu)
        else:
            self.multi_operator(ZUV_OT_PieCallerTopLeft, pie, is_menu, icon_value=icon_get('select'))

        # 9 - TOP - RIGHT
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerTopRight, pie, is_menu)
        else:
            self.multi_operator(ZUV_OT_PieCallerTopRight, pie, is_menu)
            # pie.operator('zsts.new_group')

        # 1 - BOTTOM - LEFT
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerBottomLeft, pie, is_menu)
        else:
            # pie.operator(op_prefix + '.remove_from_group')
            self.multi_operator(ZUV_OT_PieCallerBottomLeft, pie, is_menu, icon_value=icon_get("quadrify_32"))

        # 3 - BOTTOM - RIGHT
        if is_object_mode:
            pass
            # self.multi_operator(ZSTO_OT_PieCallerBottomRight, pie, is_menu)
        else:
            # pie.operator(op_prefix + '.append_to_group')
            self.multi_operator(ZUV_OT_PieCallerBottomRight, pie, is_menu, icon_value=icon_get("checker_32"))


def direction_lookup(destination_x, origin_x, destination_y, origin_y):

    deltaX = destination_x - origin_x

    deltaY = destination_y - origin_y

    degrees_temp = math.degrees(math.atan2(deltaX, deltaY))

    if degrees_temp < 0:

        degrees_final = 360 + degrees_temp

    else:

        degrees_final = degrees_temp

    compass_brackets = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]

    compass_lookup = round(degrees_final / 45)

    return compass_brackets[compass_lookup], degrees_final


class FakeEvent():
    def __init__(self, event) -> None:
        for key in self.__annotations__.keys():
            setattr(self, key, getattr(event, key))

    alt: bool = None
    ascii: str = None
    ctrl: bool = None
    is_mouse_absolute: bool = None
    is_repeat: bool = None
    is_tablet: bool = None
    mouse_prev_x: int = None
    mouse_prev_y: int = None
    mouse_region_x: int = None
    mouse_region_y: int = None
    mouse_x: int = None
    mouse_y: int = None
    oskey: bool = None
    pressure: float = None
    shift: bool = None
    tilt = None
    type = None
    unicode = None
    value = None


class ZUV_OT_PieMenu(bpy.types.Operator):
    bl_idname = "zuv.pie_menu"
    bl_label = "Zen UV - Pie Menu"
    bl_description = "Call Zen UV - Pie menu. You can setup custom hotkey: RMB on the button > Change Shortcut"

    bl_options = {"REGISTER"}

    def __init__(self) -> None:
        self.draw_handle = None
        self.area = None

        self.x = 0
        self.y = 0

        self.region_x = 0
        self.region_y = 0

        self.delta_x = 0
        self.delta_y = 0

        self.timer_watch_dog = 0
        self.compass = ''

        self.widgets = []

        self.init_modifiers = set()

        self.operators = {
            # "OBJECT": {
            #     "N": ZSTO_OT_PieCallerTop,
            #     "NE": ZSTO_OT_PieCallerTopRight,
            #     "E": ZSTO_OT_PieCallerRight,
            #     "SE": ZSTO_OT_PieCallerBottomRight,
            #     "S": ZSTO_OT_PieCallerBottom,
            #     "SW": ZSTO_OT_PieCallerBottomLeft,
            #     "W": ZSTO_OT_PieCallerLeft,
            #     "NW": ZSTO_OT_PieCallerTopLeft
            # },
            "EDIT_MESH": {
                "N": ZUV_OT_PieCallerTop,
                "NE": ZUV_OT_PieCallerTopRight,
                "E": ZUV_OT_PieCallerRight,
                "SE": ZUV_OT_PieCallerBottomRight,
                "S": ZUV_OT_PieCallerBottom,
                "SW": ZUV_OT_PieCallerBottomLeft,
                "W": ZUV_OT_PieCallerLeft,
                "NW": ZUV_OT_PieCallerTopLeft
            },
        }

    def init_widgets(self, context):
        for widget in self.widgets:
            widget.init(context)

    def handle_widget_events(self, event):
        result = False
        for widget in self.widgets:
            if widget.handle_event(event):
                result = True
        return result

    def create_widgets(self, context: bpy.types.Context):
        self.widgets = []
        self.labels = {}

        ui_scale = context.preferences.view.ui_scale

        i_LABEL_WIDTH = 120
        i_WIN_WIDTH = 200
        i_WIN_HEIGHT = 30 * 5
        i_TEXT_OFFSET = 20 * ui_scale
        i_FONT_SIZE = context.preferences.addons[ADDON_NAME].preferences.pie_assist_font_size
        i_ROW_SIZE = (i_FONT_SIZE * 2) * ui_scale

        self.panel = BL_UI_Drag_Panel(0, 0, i_WIN_WIDTH, i_WIN_HEIGHT)

        self.panel.bg_color = (0.0, 0.0, 0.0, 0.95)

        self.widgets = [self.panel]
        widgets_panel = []

        max_col_w = 0

        p_mode = self.operators.get(context.mode, None)
        if p_mode:
            p_op = p_mode.get(self.compass, None)
            if p_op is not None:

                p_template_items = {}
                p_template_display_items = getattr(p_op, 'template_display_items', {})

                if isinstance(p_op, str):
                    p_template_items['Default'] = p_op
                else:
                    p_template_items = p_op.template_items

                y_pos = 15 * ui_scale
                for key, value in p_template_items.items():
                    self.labels[key] = BL_UI_Label(i_TEXT_OFFSET, y_pos, i_LABEL_WIDTH, i_FONT_SIZE)
                    op_props = get_command_props(value)
                    is_active = op_props.bl_op_cls and op_props.bl_op_cls.poll()
                    self.labels[key].active_alpha = 1.0 if is_active else 0.2
                    p_fixed_text = p_template_display_items.get(key, None)
                    self.labels[key].text = key + ": " + (op_props.bl_label if p_fixed_text is None else p_fixed_text)
                    self.labels[key].text_size = i_FONT_SIZE
                    self.labels[key].text_scale = ui_scale
                    blf.size(0, self.labels[key].text_size, round(72 * ui_scale))
                    lbl_w, _ = blf.dimensions(0, self.labels[key].text)
                    self.labels[key].width = lbl_w
                    max_col_w = max(max_col_w, lbl_w)
                    widgets_panel.append(self.labels[key])
                    y_pos += i_ROW_SIZE

        i_area_height = context.area.height
        ui_scale = context.preferences.view.ui_scale

        i_WIN_WIDTH = max_col_w + i_TEXT_OFFSET * 2
        i_WIN_HEIGHT = y_pos + 5 * ui_scale

        i_WIN_TOP = i_area_height - self.region_y + 150 * ui_scale
        i_WIN_TOP_2 = i_area_height - self.region_y - (150 * ui_scale + i_WIN_HEIGHT)
        if i_area_height - (i_WIN_TOP + i_WIN_HEIGHT) < 0:
            i_WIN_TOP = i_WIN_TOP_2

        i_WIN_LEFT = self.region_x - i_WIN_WIDTH / 2
        if i_WIN_LEFT < 100:
            i_WIN_LEFT = 100

        self.panel.x = i_WIN_LEFT
        self.panel.y = i_WIN_TOP
        self.panel.width = i_WIN_WIDTH
        self.panel.height = i_WIN_HEIGHT

        self.widgets += widgets_panel

        self.init_widgets(context)

        self.panel.add_widgets(widgets_panel)

    def modal(self, context, event):

        if ZsPieFactory.is_pie_cancelled() or event.type in {'RIGHTMOUSE', 'ESC', 'NONE'}:
            self.cancel(context)
            return {'CANCELLED'}

        s_compass, _ = direction_lookup(event.mouse_x, self.x, event.mouse_y, self.y)
        if s_compass != self.compass:
            self.compass = s_compass

            self.create_widgets(context)

        evs = []

        if len(self.init_modifiers) != 0:
            if not event.ctrl:
                self.init_modifiers.difference_update(['CTRL'])
            if not event.shift:
                self.init_modifiers.difference_update(['SHIFT'])
            if not event.alt:
                self.init_modifiers.difference_update(['ALT'])
        else:
            if event.ctrl:
                evs.append('CTRL')
            if event.shift:
                evs.append('SHIFT')
            if event.alt:
                evs.append('ALT')

        s_evs = '+'.join(evs)

        b_is_any_key_seq = False
        for k in self.labels.keys():
            if k.upper() == s_evs:
                b_is_any_key_seq = True

        for k, v in self.labels.items():
            k = k.upper()
            b_active = (k == 'DEFAULT' and (len(evs) == 0 or not b_is_any_key_seq)) or (k == s_evs)
            v.text_color = (
                (ZsDrawConstans.BGL_ACTIVE_FONT_COLOR + (v.active_alpha, ))
                if b_active else (ZsDrawConstans.BGL_INACTIVE_FONT_COLOR + (v.active_alpha,)))

        if event.type == 'TIMER':
            self.timer_watch_dog = timer()
            p_area = getattr(context, 'area')
            if p_area:
                p_area.tag_redraw()
        else:
            elapsed = timer() - self.timer_watch_dog
            if elapsed > 0.2:
                self.cancel(context)
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        try:
            if self.draw_handle:
                context.space_data.draw_handler_remove(self.draw_handle, 'WINDOW')
            context.area.tag_redraw()
        except Exception as e:
            print(f"ZenUV: {e}")
            # Log.error(e)
        self.draw_handle = None
        self.widgets = []
        self.labels = {}
        self.area = None
        self.init_modifiers = set()

        ZsPieFactory.unmark_pie_cancelled()

    def draw_zen_uv_pie(self, context: bpy.types.Context):
        if context.area is None or context.area != self.area:
            return

        for widget in self.widgets:
            widget.draw()

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):

        from ZenUV.prop.zuv_preferences import get_prefs

        addon_prefs = get_prefs()
        if not addon_prefs.pie_assist:
            return self.execute(context)

        # PIE ASSIST
        if self.draw_handle is not None or context.space_data is None:
            self.report({'ERROR'}, 'Can not activate Pie Help Assist!')
            return {'CANCELLED'}

        ZsPieFactory.unmark_pie_cancelled()

        wnd = context.window

        ui_scale = context.preferences.view.ui_scale

        self.x = event.mouse_x
        self.y = event.mouse_y

        i_PIE_MIN_BOUND_X_L = 260 * ui_scale
        i_PIE_MIN_BOUND_X_R = 235 * ui_scale
        i_PIE_MIN_BOUND_Y = 135 * ui_scale

        new_x = self.x
        new_y = self.y

        if self.x < i_PIE_MIN_BOUND_X_L:
            new_x = i_PIE_MIN_BOUND_X_L
        elif self.x > wnd.width - i_PIE_MIN_BOUND_X_R:
            new_x = wnd.width - i_PIE_MIN_BOUND_X_R

        if self.y < i_PIE_MIN_BOUND_Y:
            new_y = i_PIE_MIN_BOUND_Y
        elif self.y > wnd.height - i_PIE_MIN_BOUND_Y:
            new_y = wnd.height - i_PIE_MIN_BOUND_Y

        self.delta_x = round(self.x - new_x)
        self.delta_y = round(self.y - new_y)

        self.x = round(new_x)
        self.y = round(new_y)

        self.region_x = event.mouse_region_x - self.delta_x
        self.region_y = event.mouse_region_y - self.delta_y
        self.timer_watch_dog = timer()
        self.compass = ''
        self.area = context.area

        self.init_alt = event.alt
        self.init_shift = event.shift
        self.init_ctrl = event.ctrl

        if event.alt:
            self.init_modifiers.add('ALT')
        if event.ctrl:
            self.init_modifiers.add('CTRL')
        if event.shift:
            self.init_modifiers.add('SHIFT')

        self.draw_handle = context.space_data.draw_handler_add(self.draw_zen_uv_pie, (context,), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        self.execute(context)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ZUV_MT_BasicPie")
        return {"FINISHED"}


# class ZUV_OT_SetWorkspaceTool(bpy.types.Operator):
#     bl_idname = "zsts.set_workspace_tool"
#     bl_label = ZsLabels.OT_TOOL_GROUP_SELECTOR
#     bl_description = ZsLabels.TOOL_DESCRIPTION

#     bl_options = {"REGISTER"}

#     def execute(self, context):
#         if context.mode == 'EDIT_MESH':
#             if context.area:
#                 if context.area.type == 'VIEW_3D':
#                     bpy.ops.wm.tool_set_by_id(name="zsts.select_box_tool")
#                 elif context.area.type == 'IMAGE_EDITOR':
#                     bpy.ops.wm.tool_set_by_id(name="zsts.select_uv_tool")
#         elif context.mode == 'OBJECT':
#             bpy.ops.wm.tool_set_by_id(name="zsts.select_object_tool")

#         return {"FINISHED"}


class ZsPieFactory:

    _pie_cancelled = False

    classes = (
        ZUV_OT_PieMenu,

        ZUV_OT_PieCallerTop,
        ZUV_OT_PieCallerTopRight,
        ZUV_OT_PieCallerTopLeft,
        ZUV_OT_PieCallerBottom,
        ZUV_OT_PieCallerLeft,
        ZUV_OT_PieCallerRight,
        ZUV_OT_PieCallerBottomLeft,
        ZUV_OT_PieCallerBottomRight,

        # ZSTO_OT_PieCallerTop,
        # ZSTO_OT_PieCallerTopRight,
        # ZSTO_OT_PieCallerTopLeft,
        # ZSTO_OT_PieCallerBottom,
        # ZSTO_OT_PieCallerLeft,
        # ZSTO_OT_PieCallerRight,
        # ZSTO_OT_PieCallerBottomLeft,
        # ZSTO_OT_PieCallerBottomRight,

        ZUV_MT_BasicPie,
    )

    @classmethod
    def mark_pie_cancelled(cls):
        cls._pie_cancelled = True

    @classmethod
    def unmark_pie_cancelled(cls):
        cls._pie_cancelled = False

    @classmethod
    def is_pie_cancelled(cls):
        return cls._pie_cancelled is True

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

# Copyright: https://github.com/jayanam/bl_ui_widgets

import bpy


class BL_UI_OT_draw_operator(bpy.types.Operator):
    bl_idname = "object.bl_ui_ot_draw_operator"
    bl_label = "bl ui widgets operator"
    bl_description = "Operator for bl ui widgets"
    bl_options = {'REGISTER'}

    handlers = set()

    def __init__(self):
        self.draw_handle = None
        self._finished = False

        self.widgets = []

        self.space_data = None
        self.wm = None
        self.area_height = 0

    def init_widgets(self, context, widgets):
        self.widgets = widgets
        for widget in self.widgets:
            widget.init(context)

    def on_invoke(self, context, event):
        pass

    def on_finish(self, context):
        self._finished = True

    def invoke(self, context, event):

        self.space_data = context.space_data
        self.wm = context.window_manager
        self.area_height = context.area.height if context.area else 0

        self.on_invoke(context, event)

        args = (self, context)

        self.register_handlers(args, context)

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def register_handlers(self, args, context):
        self.draw_handle = context.space_data.draw_handler_add(self.draw_callback_px, args, "WINDOW", "POST_PIXEL")

        BL_UI_OT_draw_operator.handlers.add((self.draw_handle, context.space_data.type))

    def unregister_handlers(self):
        if self.draw_handle:
            self.space_data.draw_handler_remove(self.draw_handle, "WINDOW")

            BL_UI_OT_draw_operator.handlers.remove((self.draw_handle, self.space_data.type))

        self.draw_handle = None

    @classmethod
    def unregister_all_handlers(cls):
        for handle, space_type in cls.handlers:
            if space_type == 'IMAGE_EDITOR':
                bpy.types.SpaceImageEditor.draw_handler_remove(handle, 'WINDOW')
            elif space_type == 'VIEW_3D':
                bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')

    def handle_widget_events(self, context: bpy.types.Context, event: bpy.types.Event):
        result = False
        for widget in self.widgets:
            if widget.handle_event(event):
                result = True
        return result

    def modal(self, context, event):
        if self._finished:
            return {'FINISHED'}

        if self.space_data != context.space_data or self.wm != context.window_manager:
            self.cancel(context)
            return {'CANCELLED'}

        if context.area:
            if context.area.height != self.area_height:
                self.area_height = context.area.height
                self.on_area_resized(context)
            context.area.tag_redraw()

        if self.handle_widget_events(context, event):
            return {'RUNNING_MODAL'}

        if event.type in {"ESC"}:
            self.cancel(context)

        return {"PASS_THROUGH"}

    def cancel(self, context: bpy.types.Context):
        self.unregister_handlers()
        self.on_finish(context)
        if context and context.area:
            context.area.tag_redraw()

    # Draw handler to paint onto the screen
    def draw_callback_px(self, op, context: bpy.types.Context):
        if context.space_data == self.space_data:
            for widget in self.widgets:
                widget.draw()

    def on_area_resized(self, context):
        pass

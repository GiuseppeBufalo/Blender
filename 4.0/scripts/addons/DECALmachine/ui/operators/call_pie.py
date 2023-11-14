import bpy
from bpy.props import StringProperty
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as view3d_tools
from ... utils.registration import get_prefs
from ... utils.ui import get_keymap_item, popup_message


class CallDecalPie(bpy.types.Operator):
    bl_idname = "machin3.call_decal_pie"
    bl_label = "MACHIN3: Call DECALmachine Pie"
    bl_options = {'INTERNAL', 'UNDO'}

    idname: StringProperty()

    def invoke(self, context, event):
        if get_prefs().decalmode == "NONE":
            get_prefs().decalmode = "INSERT"
            get_prefs().decalremovemode = False

        if context.space_data.type == 'VIEW_3D':
            active_tool = view3d_tools.tool_active_from_context(context)

            dm_kmi = get_keymap_item('Object Mode', 'machin3.call_decal_pie', 'D')
            bc_kmi = get_keymap_item('3D View Tool: BoxCutter', 'wm.call_menu_pie', 'D', properties=[('name', 'BC_MT_pie')])

            if active_tool.idname == 'BoxCutter' and dm_kmi and bc_kmi:
                return {'PASS_THROUGH'}

            else:
                self.open_pie(context, event)
                return {'FINISHED'}

        elif context.space_data.type == 'IMAGE_EDITOR':
            self.open_img_pie(context, event)
            return {'FINISHED'}

    def open_pie(self, context, event):
        context.window_manager.decal_mousepos = (event.mouse_region_x, event.mouse_region_y)
        bpy.ops.wm.call_menu_pie(name='MACHIN3_MT_%s' % (self.idname))

    def open_img_pie(self, context, event):
        select_sync = context.scene.tool_settings.use_uv_select_sync

        if not select_sync:
            context.scene.tool_settings.use_uv_select_sync = True

        bpy.ops.wm.call_menu_pie(name='MACHIN3_MT_%s' % (self.idname))

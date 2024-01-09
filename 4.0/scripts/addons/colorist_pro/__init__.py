# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Colorist Pro",
    "author" : "Mikhael Tamosee", 
    "description" : "",
    "blender" : (4, 0, 0),
    "version" : (1, 1, 1),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Compositing" 
}


import bpy
import bpy.utils.previews
import os


addon_keymaps = {}
_icons = None
class SNA_OT_Operator026_2Ac7B(bpy.types.Operator):
    bl_idname = "sna.operator026_2ac7b"
    bl_label = "Operator.026"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[2].default_value = 0.5
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[3].default_value = 0
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[4].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator027_E268C(bpy.types.Operator):
    bl_idname = "sna.operator027_e268c"
    bl_label = "Operator.027"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[6].default_value = 0.5
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[7].default_value = 0
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[8].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_SELECTIVE_COLOR_6B020(bpy.types.Panel):
    bl_label = 'Selective Color'
    bl_idname = 'SNA_PT_SELECTIVE_COLOR_6B020'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_81FA8 = layout.row(heading='', align=True)
        row_81FA8.alert = False
        row_81FA8.enabled = True
        row_81FA8.active = True
        row_81FA8.use_property_split = False
        row_81FA8.use_property_decorate = False
        row_81FA8.scale_x = 1.0
        row_81FA8.scale_y = 1.5
        row_81FA8.alignment = 'Expand'.upper()
        row_81FA8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_81FA8.operator('sna.operator028_d6556', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_81FA8.operator('sna.operator029_0476c', text='Disable', icon_value=0, emboss=True, depress=False)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[26], 'default_value', text='Mix', icon_value=0, emboss=True)
        box_9DC06 = layout.box()
        box_9DC06.alert = False
        box_9DC06.enabled = True
        box_9DC06.active = True
        box_9DC06.use_property_split = False
        box_9DC06.use_property_decorate = False
        box_9DC06.alignment = 'Expand'.upper()
        box_9DC06.scale_x = 1.0
        box_9DC06.scale_y = 1.0
        if not True: box_9DC06.operator_context = "EXEC_DEFAULT"
        row_2D717 = box_9DC06.row(heading='', align=False)
        row_2D717.alert = False
        row_2D717.enabled = True
        row_2D717.active = True
        row_2D717.use_property_split = False
        row_2D717.use_property_decorate = False
        row_2D717.scale_x = 1.0
        row_2D717.scale_y = 1.0
        row_2D717.alignment = 'Expand'.upper()
        row_2D717.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_2D717.label(text='Red', icon_value=850)
        row_2D717.separator(factor=1.0299999713897705)
        row_1FAAA = row_2D717.row(heading='', align=False)
        row_1FAAA.alert = True
        row_1FAAA.enabled = True
        row_1FAAA.active = True
        row_1FAAA.use_property_split = False
        row_1FAAA.use_property_decorate = False
        row_1FAAA.scale_x = 0.8999999761581421
        row_1FAAA.scale_y = 1.0
        row_1FAAA.alignment = 'Expand'.upper()
        row_1FAAA.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_1FAAA.operator('sna.operator026_2ac7b', text='Reset', icon_value=715, emboss=True, depress=False)
        col_D5476 = box_9DC06.column(heading='', align=True)
        col_D5476.alert = False
        col_D5476.enabled = True
        col_D5476.active = True
        col_D5476.use_property_split = False
        col_D5476.use_property_decorate = False
        col_D5476.scale_x = 1.0
        col_D5476.scale_y = 1.0
        col_D5476.alignment = 'Expand'.upper()
        col_D5476.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_D5476.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[2], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_D5476.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[3], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_D5476.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[4], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_13C4D = layout.box()
        box_13C4D.alert = False
        box_13C4D.enabled = True
        box_13C4D.active = True
        box_13C4D.use_property_split = False
        box_13C4D.use_property_decorate = False
        box_13C4D.alignment = 'Expand'.upper()
        box_13C4D.scale_x = 1.0
        box_13C4D.scale_y = 1.0
        if not True: box_13C4D.operator_context = "EXEC_DEFAULT"
        row_FE5B8 = box_13C4D.row(heading='', align=False)
        row_FE5B8.alert = False
        row_FE5B8.enabled = True
        row_FE5B8.active = True
        row_FE5B8.use_property_split = False
        row_FE5B8.use_property_decorate = False
        row_FE5B8.scale_x = 1.0
        row_FE5B8.scale_y = 1.0
        row_FE5B8.alignment = 'Expand'.upper()
        row_FE5B8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_FE5B8.label(text='Green', icon_value=852)
        row_FE5B8.separator(factor=1.0299999713897705)
        row_B86A2 = row_FE5B8.row(heading='', align=False)
        row_B86A2.alert = True
        row_B86A2.enabled = True
        row_B86A2.active = True
        row_B86A2.use_property_split = False
        row_B86A2.use_property_decorate = False
        row_B86A2.scale_x = 0.8999999761581421
        row_B86A2.scale_y = 1.0
        row_B86A2.alignment = 'Expand'.upper()
        row_B86A2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_B86A2.operator('sna.operator027_e268c', text='Reset', icon_value=715, emboss=True, depress=False)
        col_3E894 = box_13C4D.column(heading='', align=True)
        col_3E894.alert = False
        col_3E894.enabled = True
        col_3E894.active = True
        col_3E894.use_property_split = False
        col_3E894.use_property_decorate = False
        col_3E894.scale_x = 1.0
        col_3E894.scale_y = 1.0
        col_3E894.alignment = 'Expand'.upper()
        col_3E894.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_3E894.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[6], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_3E894.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[7], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_3E894.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[8], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_0F3B9 = layout.box()
        box_0F3B9.alert = False
        box_0F3B9.enabled = True
        box_0F3B9.active = True
        box_0F3B9.use_property_split = False
        box_0F3B9.use_property_decorate = False
        box_0F3B9.alignment = 'Expand'.upper()
        box_0F3B9.scale_x = 1.0
        box_0F3B9.scale_y = 1.0
        if not True: box_0F3B9.operator_context = "EXEC_DEFAULT"
        row_F4338 = box_0F3B9.row(heading='', align=False)
        row_F4338.alert = False
        row_F4338.enabled = True
        row_F4338.active = True
        row_F4338.use_property_split = False
        row_F4338.use_property_decorate = False
        row_F4338.scale_x = 1.0
        row_F4338.scale_y = 1.0
        row_F4338.alignment = 'Expand'.upper()
        row_F4338.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_F4338.label(text='Blue', icon_value=853)
        row_F4338.separator(factor=1.0299999713897705)
        row_2C953 = row_F4338.row(heading='', align=False)
        row_2C953.alert = True
        row_2C953.enabled = True
        row_2C953.active = True
        row_2C953.use_property_split = False
        row_2C953.use_property_decorate = False
        row_2C953.scale_x = 0.8999999761581421
        row_2C953.scale_y = 1.0
        row_2C953.alignment = 'Expand'.upper()
        row_2C953.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_2C953.operator('sna.operator030_d0c31', text='Reset', icon_value=715, emboss=True, depress=False)
        col_A12CF = box_0F3B9.column(heading='', align=True)
        col_A12CF.alert = False
        col_A12CF.enabled = True
        col_A12CF.active = True
        col_A12CF.use_property_split = False
        col_A12CF.use_property_decorate = False
        col_A12CF.scale_x = 1.0
        col_A12CF.scale_y = 1.0
        col_A12CF.alignment = 'Expand'.upper()
        col_A12CF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_A12CF.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[10], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_A12CF.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[11], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_A12CF.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[12], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_AD71C = layout.box()
        box_AD71C.alert = False
        box_AD71C.enabled = True
        box_AD71C.active = True
        box_AD71C.use_property_split = False
        box_AD71C.use_property_decorate = False
        box_AD71C.alignment = 'Expand'.upper()
        box_AD71C.scale_x = 1.0
        box_AD71C.scale_y = 1.0
        if not True: box_AD71C.operator_context = "EXEC_DEFAULT"
        row_76002 = box_AD71C.row(heading='', align=False)
        row_76002.alert = False
        row_76002.enabled = True
        row_76002.active = True
        row_76002.use_property_split = False
        row_76002.use_property_decorate = False
        row_76002.scale_x = 1.0
        row_76002.scale_y = 1.0
        row_76002.alignment = 'Expand'.upper()
        row_76002.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_76002.label(text='Cyan', icon_value=857)
        row_76002.separator(factor=1.0299999713897705)
        row_8446C = row_76002.row(heading='', align=False)
        row_8446C.alert = True
        row_8446C.enabled = True
        row_8446C.active = True
        row_8446C.use_property_split = False
        row_8446C.use_property_decorate = False
        row_8446C.scale_x = 0.8999999761581421
        row_8446C.scale_y = 1.0
        row_8446C.alignment = 'Expand'.upper()
        row_8446C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_8446C.operator('sna.operator031_bb8c9', text='Reset', icon_value=715, emboss=True, depress=False)
        col_ECD6C = box_AD71C.column(heading='', align=True)
        col_ECD6C.alert = False
        col_ECD6C.enabled = True
        col_ECD6C.active = True
        col_ECD6C.use_property_split = False
        col_ECD6C.use_property_decorate = False
        col_ECD6C.scale_x = 1.0
        col_ECD6C.scale_y = 1.0
        col_ECD6C.alignment = 'Expand'.upper()
        col_ECD6C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_ECD6C.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[14], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_ECD6C.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[15], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_ECD6C.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[16], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_64ED0 = layout.box()
        box_64ED0.alert = False
        box_64ED0.enabled = True
        box_64ED0.active = True
        box_64ED0.use_property_split = False
        box_64ED0.use_property_decorate = False
        box_64ED0.alignment = 'Expand'.upper()
        box_64ED0.scale_x = 1.0
        box_64ED0.scale_y = 1.0
        if not True: box_64ED0.operator_context = "EXEC_DEFAULT"
        row_02746 = box_64ED0.row(heading='', align=False)
        row_02746.alert = False
        row_02746.enabled = True
        row_02746.active = True
        row_02746.use_property_split = False
        row_02746.use_property_decorate = False
        row_02746.scale_x = 1.0
        row_02746.scale_y = 1.0
        row_02746.alignment = 'Expand'.upper()
        row_02746.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_02746.label(text='Magenta', icon_value=860)
        row_02746.separator(factor=1.0299999713897705)
        row_A6710 = row_02746.row(heading='', align=False)
        row_A6710.alert = True
        row_A6710.enabled = True
        row_A6710.active = True
        row_A6710.use_property_split = False
        row_A6710.use_property_decorate = False
        row_A6710.scale_x = 0.8999999761581421
        row_A6710.scale_y = 1.0
        row_A6710.alignment = 'Expand'.upper()
        row_A6710.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_A6710.operator('sna.operator032_fba2a', text='Reset', icon_value=715, emboss=True, depress=False)
        col_050C5 = box_64ED0.column(heading='', align=True)
        col_050C5.alert = False
        col_050C5.enabled = True
        col_050C5.active = True
        col_050C5.use_property_split = False
        col_050C5.use_property_decorate = False
        col_050C5.scale_x = 1.0
        col_050C5.scale_y = 1.0
        col_050C5.alignment = 'Expand'.upper()
        col_050C5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_050C5.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[18], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_050C5.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[19], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_050C5.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[20], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_C6383 = layout.box()
        box_C6383.alert = False
        box_C6383.enabled = True
        box_C6383.active = True
        box_C6383.use_property_split = False
        box_C6383.use_property_decorate = False
        box_C6383.alignment = 'Expand'.upper()
        box_C6383.scale_x = 1.0
        box_C6383.scale_y = 1.0
        if not True: box_C6383.operator_context = "EXEC_DEFAULT"
        row_0ABA8 = box_C6383.row(heading='', align=False)
        row_0ABA8.alert = False
        row_0ABA8.enabled = True
        row_0ABA8.active = True
        row_0ABA8.use_property_split = False
        row_0ABA8.use_property_decorate = False
        row_0ABA8.scale_x = 1.0
        row_0ABA8.scale_y = 1.0
        row_0ABA8.alignment = 'Expand'.upper()
        row_0ABA8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_0ABA8.label(text='Yellow', icon_value=858)
        row_0ABA8.separator(factor=1.0299999713897705)
        row_31027 = row_0ABA8.row(heading='', align=False)
        row_31027.alert = True
        row_31027.enabled = True
        row_31027.active = True
        row_31027.use_property_split = False
        row_31027.use_property_decorate = False
        row_31027.scale_x = 0.8999999761581421
        row_31027.scale_y = 1.0
        row_31027.alignment = 'Expand'.upper()
        row_31027.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_31027.operator('sna.operator033_1e2a6', text='Reset', icon_value=715, emboss=True, depress=False)
        col_A2410 = box_C6383.column(heading='', align=True)
        col_A2410.alert = False
        col_A2410.enabled = True
        col_A2410.active = True
        col_A2410.use_property_split = False
        col_A2410.use_property_decorate = False
        col_A2410.scale_x = 1.0
        col_A2410.scale_y = 1.0
        col_A2410.alignment = 'Expand'.upper()
        col_A2410.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_A2410.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[22], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_A2410.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[23], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_A2410.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[24], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)


class SNA_OT_Operator028_D6556(bpy.types.Operator):
    bl_idname = "sna.operator028_d6556"
    bl_label = "Operator.028"
    bl_description = "Link Selective Color node in Compositor"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_selective_color_and_colorist_pro():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            selective_color_node_name = "Selective Color"
            render_layers_node = "Render Layers - Colorist"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            selective_color_node = compositor.nodes[selective_color_node_name]
            render_layers_node = compositor.nodes[render_layers_node]
            for link in compositor.links:
                if link.from_node == render_layers_node and link.to_node == colorist_pro_node:
                    compositor.links.remove(link)
            compositor.links.new(selective_color_node.outputs[0], colorist_pro_node.inputs[0])
        # Run the function to link the nodes
        link_selective_color_and_colorist_pro()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator030_D0C31(bpy.types.Operator):
    bl_idname = "sna.operator030_d0c31"
    bl_label = "Operator.030"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[10].default_value = 0.5
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[11].default_value = 0
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[12].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator031_Bb8C9(bpy.types.Operator):
    bl_idname = "sna.operator031_bb8c9"
    bl_label = "Operator.031"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[14].default_value = 0.5
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[15].default_value = 0
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[16].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator032_Fba2A(bpy.types.Operator):
    bl_idname = "sna.operator032_fba2a"
    bl_label = "Operator.032"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[18].default_value = 0.5
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[19].default_value = 0
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[20].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator033_1E2A6(bpy.types.Operator):
    bl_idname = "sna.operator033_1e2a6"
    bl_label = "Operator.033"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[22].default_value = 0.5
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[23].default_value = 0
        bpy.data.scenes["Scene"].node_tree.nodes["Selective Color"].inputs[24].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_SELECTIVE_COLOR_A0FCA(bpy.types.Panel):
    bl_label = 'Selective Color'
    bl_idname = 'SNA_PT_SELECTIVE_COLOR_A0FCA'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_061BE = layout.row(heading='', align=True)
        row_061BE.alert = False
        row_061BE.enabled = True
        row_061BE.active = True
        row_061BE.use_property_split = False
        row_061BE.use_property_decorate = False
        row_061BE.scale_x = 1.0
        row_061BE.scale_y = 1.5
        row_061BE.alignment = 'Expand'.upper()
        row_061BE.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_061BE.operator('sna.operator028_d6556', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_061BE.operator('sna.operator029_0476c', text='Disable', icon_value=0, emboss=True, depress=False)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[26], 'default_value', text='Mix', icon_value=0, emboss=True)
        box_AFB7E = layout.box()
        box_AFB7E.alert = False
        box_AFB7E.enabled = True
        box_AFB7E.active = True
        box_AFB7E.use_property_split = False
        box_AFB7E.use_property_decorate = False
        box_AFB7E.alignment = 'Expand'.upper()
        box_AFB7E.scale_x = 1.0
        box_AFB7E.scale_y = 1.0
        if not True: box_AFB7E.operator_context = "EXEC_DEFAULT"
        row_4E609 = box_AFB7E.row(heading='', align=False)
        row_4E609.alert = False
        row_4E609.enabled = True
        row_4E609.active = True
        row_4E609.use_property_split = False
        row_4E609.use_property_decorate = False
        row_4E609.scale_x = 1.0
        row_4E609.scale_y = 1.0
        row_4E609.alignment = 'Expand'.upper()
        row_4E609.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_4E609.label(text='Red', icon_value=850)
        row_4E609.separator(factor=1.0299999713897705)
        row_2296E = row_4E609.row(heading='', align=False)
        row_2296E.alert = True
        row_2296E.enabled = True
        row_2296E.active = True
        row_2296E.use_property_split = False
        row_2296E.use_property_decorate = False
        row_2296E.scale_x = 0.8999999761581421
        row_2296E.scale_y = 1.0
        row_2296E.alignment = 'Expand'.upper()
        row_2296E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_2296E.operator('sna.operator026_2ac7b', text='Reset', icon_value=715, emboss=True, depress=False)
        col_A6577 = box_AFB7E.column(heading='', align=True)
        col_A6577.alert = False
        col_A6577.enabled = True
        col_A6577.active = True
        col_A6577.use_property_split = False
        col_A6577.use_property_decorate = False
        col_A6577.scale_x = 1.0
        col_A6577.scale_y = 1.0
        col_A6577.alignment = 'Expand'.upper()
        col_A6577.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_A6577.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[2], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_A6577.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[3], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_A6577.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[4], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_1327A = layout.box()
        box_1327A.alert = False
        box_1327A.enabled = True
        box_1327A.active = True
        box_1327A.use_property_split = False
        box_1327A.use_property_decorate = False
        box_1327A.alignment = 'Expand'.upper()
        box_1327A.scale_x = 1.0
        box_1327A.scale_y = 1.0
        if not True: box_1327A.operator_context = "EXEC_DEFAULT"
        row_5C388 = box_1327A.row(heading='', align=False)
        row_5C388.alert = False
        row_5C388.enabled = True
        row_5C388.active = True
        row_5C388.use_property_split = False
        row_5C388.use_property_decorate = False
        row_5C388.scale_x = 1.0
        row_5C388.scale_y = 1.0
        row_5C388.alignment = 'Expand'.upper()
        row_5C388.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_5C388.label(text='Green', icon_value=852)
        row_5C388.separator(factor=1.0299999713897705)
        row_6A62E = row_5C388.row(heading='', align=False)
        row_6A62E.alert = True
        row_6A62E.enabled = True
        row_6A62E.active = True
        row_6A62E.use_property_split = False
        row_6A62E.use_property_decorate = False
        row_6A62E.scale_x = 0.8999999761581421
        row_6A62E.scale_y = 1.0
        row_6A62E.alignment = 'Expand'.upper()
        row_6A62E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_6A62E.operator('sna.operator027_e268c', text='Reset', icon_value=715, emboss=True, depress=False)
        col_68E52 = box_1327A.column(heading='', align=True)
        col_68E52.alert = False
        col_68E52.enabled = True
        col_68E52.active = True
        col_68E52.use_property_split = False
        col_68E52.use_property_decorate = False
        col_68E52.scale_x = 1.0
        col_68E52.scale_y = 1.0
        col_68E52.alignment = 'Expand'.upper()
        col_68E52.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_68E52.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[6], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_68E52.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[7], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_68E52.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[8], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_81BA7 = layout.box()
        box_81BA7.alert = False
        box_81BA7.enabled = True
        box_81BA7.active = True
        box_81BA7.use_property_split = False
        box_81BA7.use_property_decorate = False
        box_81BA7.alignment = 'Expand'.upper()
        box_81BA7.scale_x = 1.0
        box_81BA7.scale_y = 1.0
        if not True: box_81BA7.operator_context = "EXEC_DEFAULT"
        row_929F4 = box_81BA7.row(heading='', align=False)
        row_929F4.alert = False
        row_929F4.enabled = True
        row_929F4.active = True
        row_929F4.use_property_split = False
        row_929F4.use_property_decorate = False
        row_929F4.scale_x = 1.0
        row_929F4.scale_y = 1.0
        row_929F4.alignment = 'Expand'.upper()
        row_929F4.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_929F4.label(text='Blue', icon_value=853)
        row_929F4.separator(factor=1.0299999713897705)
        row_C7CD7 = row_929F4.row(heading='', align=False)
        row_C7CD7.alert = True
        row_C7CD7.enabled = True
        row_C7CD7.active = True
        row_C7CD7.use_property_split = False
        row_C7CD7.use_property_decorate = False
        row_C7CD7.scale_x = 0.8999999761581421
        row_C7CD7.scale_y = 1.0
        row_C7CD7.alignment = 'Expand'.upper()
        row_C7CD7.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_C7CD7.operator('sna.operator030_d0c31', text='Reset', icon_value=715, emboss=True, depress=False)
        col_3E324 = box_81BA7.column(heading='', align=True)
        col_3E324.alert = False
        col_3E324.enabled = True
        col_3E324.active = True
        col_3E324.use_property_split = False
        col_3E324.use_property_decorate = False
        col_3E324.scale_x = 1.0
        col_3E324.scale_y = 1.0
        col_3E324.alignment = 'Expand'.upper()
        col_3E324.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_3E324.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[10], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_3E324.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[11], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_3E324.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[12], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_3929F = layout.box()
        box_3929F.alert = False
        box_3929F.enabled = True
        box_3929F.active = True
        box_3929F.use_property_split = False
        box_3929F.use_property_decorate = False
        box_3929F.alignment = 'Expand'.upper()
        box_3929F.scale_x = 1.0
        box_3929F.scale_y = 1.0
        if not True: box_3929F.operator_context = "EXEC_DEFAULT"
        row_18230 = box_3929F.row(heading='', align=False)
        row_18230.alert = False
        row_18230.enabled = True
        row_18230.active = True
        row_18230.use_property_split = False
        row_18230.use_property_decorate = False
        row_18230.scale_x = 1.0
        row_18230.scale_y = 1.0
        row_18230.alignment = 'Expand'.upper()
        row_18230.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_18230.label(text='Cyan', icon_value=857)
        row_18230.separator(factor=1.0299999713897705)
        row_14B1A = row_18230.row(heading='', align=False)
        row_14B1A.alert = True
        row_14B1A.enabled = True
        row_14B1A.active = True
        row_14B1A.use_property_split = False
        row_14B1A.use_property_decorate = False
        row_14B1A.scale_x = 0.8999999761581421
        row_14B1A.scale_y = 1.0
        row_14B1A.alignment = 'Expand'.upper()
        row_14B1A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_14B1A.operator('sna.operator031_bb8c9', text='Reset', icon_value=715, emboss=True, depress=False)
        col_02AE8 = box_3929F.column(heading='', align=True)
        col_02AE8.alert = False
        col_02AE8.enabled = True
        col_02AE8.active = True
        col_02AE8.use_property_split = False
        col_02AE8.use_property_decorate = False
        col_02AE8.scale_x = 1.0
        col_02AE8.scale_y = 1.0
        col_02AE8.alignment = 'Expand'.upper()
        col_02AE8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_02AE8.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[14], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_02AE8.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[15], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_02AE8.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[16], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_A6CF9 = layout.box()
        box_A6CF9.alert = False
        box_A6CF9.enabled = True
        box_A6CF9.active = True
        box_A6CF9.use_property_split = False
        box_A6CF9.use_property_decorate = False
        box_A6CF9.alignment = 'Expand'.upper()
        box_A6CF9.scale_x = 1.0
        box_A6CF9.scale_y = 1.0
        if not True: box_A6CF9.operator_context = "EXEC_DEFAULT"
        row_52EA7 = box_A6CF9.row(heading='', align=False)
        row_52EA7.alert = False
        row_52EA7.enabled = True
        row_52EA7.active = True
        row_52EA7.use_property_split = False
        row_52EA7.use_property_decorate = False
        row_52EA7.scale_x = 1.0
        row_52EA7.scale_y = 1.0
        row_52EA7.alignment = 'Expand'.upper()
        row_52EA7.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_52EA7.label(text='Magenta', icon_value=860)
        row_52EA7.separator(factor=1.0299999713897705)
        row_0CB33 = row_52EA7.row(heading='', align=False)
        row_0CB33.alert = True
        row_0CB33.enabled = True
        row_0CB33.active = True
        row_0CB33.use_property_split = False
        row_0CB33.use_property_decorate = False
        row_0CB33.scale_x = 0.8999999761581421
        row_0CB33.scale_y = 1.0
        row_0CB33.alignment = 'Expand'.upper()
        row_0CB33.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_0CB33.operator('sna.operator032_fba2a', text='Reset', icon_value=715, emboss=True, depress=False)
        col_AD78A = box_A6CF9.column(heading='', align=True)
        col_AD78A.alert = False
        col_AD78A.enabled = True
        col_AD78A.active = True
        col_AD78A.use_property_split = False
        col_AD78A.use_property_decorate = False
        col_AD78A.scale_x = 1.0
        col_AD78A.scale_y = 1.0
        col_AD78A.alignment = 'Expand'.upper()
        col_AD78A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_AD78A.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[18], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_AD78A.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[19], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_AD78A.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[20], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)
        box_44558 = layout.box()
        box_44558.alert = False
        box_44558.enabled = True
        box_44558.active = True
        box_44558.use_property_split = False
        box_44558.use_property_decorate = False
        box_44558.alignment = 'Expand'.upper()
        box_44558.scale_x = 1.0
        box_44558.scale_y = 1.0
        if not True: box_44558.operator_context = "EXEC_DEFAULT"
        row_3F349 = box_44558.row(heading='', align=False)
        row_3F349.alert = False
        row_3F349.enabled = True
        row_3F349.active = True
        row_3F349.use_property_split = False
        row_3F349.use_property_decorate = False
        row_3F349.scale_x = 1.0
        row_3F349.scale_y = 1.0
        row_3F349.alignment = 'Expand'.upper()
        row_3F349.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_3F349.label(text='Yellow', icon_value=858)
        row_3F349.separator(factor=1.0299999713897705)
        row_6993A = row_3F349.row(heading='', align=False)
        row_6993A.alert = True
        row_6993A.enabled = True
        row_6993A.active = True
        row_6993A.use_property_split = False
        row_6993A.use_property_decorate = False
        row_6993A.scale_x = 0.8999999761581421
        row_6993A.scale_y = 1.0
        row_6993A.alignment = 'Expand'.upper()
        row_6993A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_6993A.operator('sna.operator033_1e2a6', text='Reset', icon_value=715, emboss=True, depress=False)
        col_54A3F = box_44558.column(heading='', align=True)
        col_54A3F.alert = False
        col_54A3F.enabled = True
        col_54A3F.active = True
        col_54A3F.use_property_split = False
        col_54A3F.use_property_decorate = False
        col_54A3F.scale_x = 1.0
        col_54A3F.scale_y = 1.0
        col_54A3F.alignment = 'Expand'.upper()
        col_54A3F.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_54A3F.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[22], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_54A3F.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[23], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        col_54A3F.prop(bpy.data.scenes['Scene'].node_tree.nodes['Selective Color'].inputs[24], 'default_value', text='Brightness', icon_value=0, emboss=True, slider=True)


class SNA_PT_LENS_FLARE_9C407(bpy.types.Panel):
    bl_label = 'Lens Flare'
    bl_idname = 'SNA_PT_LENS_FLARE_9C407'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_B03A5 = layout.row(heading='', align=True)
        row_B03A5.alert = False
        row_B03A5.enabled = True
        row_B03A5.active = True
        row_B03A5.use_property_split = False
        row_B03A5.use_property_decorate = False
        row_B03A5.scale_x = 1.0
        row_B03A5.scale_y = 1.5
        row_B03A5.alignment = 'Expand'.upper()
        row_B03A5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_B03A5.operator('sna.enable_lens_flare_29410', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_B03A5.operator('sna.disable_lens_flare_4a654', text='Disable', icon_value=0, emboss=True, depress=False)


class SNA_OT_Enable_Glares_C9218(bpy.types.Operator):
    bl_idname = "sna.enable_glares_c9218"
    bl_label = "Enable Glares"
    bl_description = "Link Glares node in Compositor"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_colorist_pro_and_glares():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            glares_node_name = "Glares"
            lens_dirt_node_name = "Lens Dirt"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            glares_node = compositor.nodes[glares_node_name]
            lens_dirt_node = compositor.nodes[lens_dirt_node_name]
            # Create links between nodes
            compositor.links.new(glares_node.outputs['Glares'], colorist_pro_node.inputs['Glares'])
            compositor.links.new(glares_node.outputs['Glares'], lens_dirt_node.inputs['Glares'])
        # Run the function to link the nodes
        link_colorist_pro_and_glares()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Disable_Glares_De435(bpy.types.Operator):
    bl_idname = "sna.disable_glares_de435"
    bl_label = "Disable Glares"
    bl_description = "Unlink Glares node, press to safe viewport performance"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def unlink_colorist_pro_and_glares():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            glares_node_name = "Glares"
            lens_dirt_node_name = "Lens Dirt"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            glares_node = compositor.nodes[glares_node_name]
            lens_dirt_node = compositor.nodes[lens_dirt_node_name]
            links_to_remove = []
            # Find the links to remove
            for link in compositor.links:
                if link.from_node == glares_node and (link.to_node == colorist_pro_node or link.to_node == lens_dirt_node):
                    links_to_remove.append(link)
            # Remove the identified links
            for link in links_to_remove:
                compositor.links.remove(link)
        # Run the function to unlink the nodes
        unlink_colorist_pro_and_glares()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_GLARE_59C9A(bpy.types.Panel):
    bl_label = 'Glare'
    bl_idname = 'SNA_PT_GLARE_59C9A'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 5
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_A16CD = layout.row(heading='', align=True)
        row_A16CD.alert = False
        row_A16CD.enabled = True
        row_A16CD.active = True
        row_A16CD.use_property_split = False
        row_A16CD.use_property_decorate = False
        row_A16CD.scale_x = 1.0
        row_A16CD.scale_y = 1.5
        row_A16CD.alignment = 'Expand'.upper()
        row_A16CD.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_A16CD.operator('sna.enable_glares_c9218', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_A16CD.operator('sna.disable_glares_de435', text='Disable', icon_value=0, emboss=True, depress=False)


class SNA_OT_Operator001_5409D(bpy.types.Operator):
    bl_idname = "sna.operator001_5409d"
    bl_label = "Operator.001"
    bl_description = "Unlink Lens Dirt node, press to save viewport performance"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def unlink_colorist_pro_and_lens_dirt():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            lens_dirt_node_name = "Lens Dirt"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            lens_dirt_node = compositor.nodes[lens_dirt_node_name]
            # Find and remove the links between nodes
            for link in compositor.links:
                if link.from_node == lens_dirt_node and link.to_node == colorist_pro_node:
                    compositor.links.remove(link)
        # Run the function to unlink the nodes
        unlink_colorist_pro_and_lens_dirt()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator_9650E(bpy.types.Operator):
    bl_idname = "sna.operator_9650e"
    bl_label = "Operator"
    bl_description = "Link Lens Dirt node in compositor"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_colorist_pro_and_lens_dirt():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            lens_dirt_node_name = "Lens Dirt"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            lens_dirt_node = compositor.nodes[lens_dirt_node_name]
            # Create links between nodes
            compositor.links.new(lens_dirt_node.outputs['Lens Dirt'], colorist_pro_node.inputs['Lens Dirt'])
        # Run the function to link the nodes
        link_colorist_pro_and_lens_dirt()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_LENS_DIRT_5A957(bpy.types.Panel):
    bl_label = 'Lens Dirt'
    bl_idname = 'SNA_PT_LENS_DIRT_5A957'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 6
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_7FB30 = layout.row(heading='', align=True)
        row_7FB30.alert = False
        row_7FB30.enabled = True
        row_7FB30.active = True
        row_7FB30.use_property_split = False
        row_7FB30.use_property_decorate = False
        row_7FB30.scale_x = 1.0
        row_7FB30.scale_y = 1.5
        row_7FB30.alignment = 'Expand'.upper()
        row_7FB30.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_7FB30.operator('sna.operator_9650e', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_7FB30.operator('sna.operator001_5409d', text='Disable', icon_value=0, emboss=True, depress=False)
        layout.prop(bpy.data.node_groups['Lens Dirt'].nodes['Blur.001'].inputs[1], 'default_value', text='Extra Brightness', icon_value=0, emboss=True)
        col_70B85 = layout.column(heading='', align=True)
        col_70B85.alert = False
        col_70B85.enabled = True
        col_70B85.active = True
        col_70B85.use_property_split = False
        col_70B85.use_property_decorate = False
        col_70B85.scale_x = 1.0
        col_70B85.scale_y = 1.0
        col_70B85.alignment = 'Expand'.upper()
        col_70B85.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_70B85.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.004'].inputs[1], 'default_value', text='Aberration', icon_value=0, emboss=True)
        col_70B85.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.004'].inputs[2], 'default_value', text='Dispersion', icon_value=0, emboss=True)
        box_88120 = layout.box()
        box_88120.alert = False
        box_88120.enabled = True
        box_88120.active = True
        box_88120.use_property_split = False
        box_88120.use_property_decorate = False
        box_88120.alignment = 'Expand'.upper()
        box_88120.scale_x = 1.0
        box_88120.scale_y = 1.0
        if not True: box_88120.operator_context = "EXEC_DEFAULT"
        box_88120.label(text='Lens Dirt 1 - Small Dirts 4K', icon_value=0)
        col_507E5 = box_88120.column(heading='', align=True)
        col_507E5.alert = False
        col_507E5.enabled = True
        col_507E5.active = True
        col_507E5.use_property_split = False
        col_507E5.use_property_decorate = False
        col_507E5.scale_x = 1.0
        col_507E5.scale_y = 1.0
        col_507E5.alignment = 'Expand'.upper()
        col_507E5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_507E5.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.013'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=True)
        col_507E5.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group'].inputs[0], 'default_value', text='Scale', icon_value=0, emboss=True, slider=True)
        col_507E5.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True, slider=True)
        box_E51AC = layout.box()
        box_E51AC.alert = False
        box_E51AC.enabled = True
        box_E51AC.active = True
        box_E51AC.use_property_split = False
        box_E51AC.use_property_decorate = False
        box_E51AC.alignment = 'Expand'.upper()
        box_E51AC.scale_x = 1.0
        box_E51AC.scale_y = 1.0
        if not True: box_E51AC.operator_context = "EXEC_DEFAULT"
        box_E51AC.label(text='Lens Dirt 2 - Medium Bokeh 4K', icon_value=0)
        col_3F1A2 = box_E51AC.column(heading='', align=True)
        col_3F1A2.alert = False
        col_3F1A2.enabled = True
        col_3F1A2.active = True
        col_3F1A2.use_property_split = False
        col_3F1A2.use_property_decorate = False
        col_3F1A2.scale_x = 1.0
        col_3F1A2.scale_y = 1.0
        col_3F1A2.alignment = 'Expand'.upper()
        col_3F1A2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_3F1A2.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.014'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=True)
        col_3F1A2.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.003'].inputs[0], 'default_value', text='Scale', icon_value=0, emboss=True, slider=True)
        col_3F1A2.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.003'].inputs[1], 'default_value', text='Extra Bokeh', icon_value=0, emboss=True)
        col_3F1A2.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.003'].inputs[2], 'default_value', text='Blur', icon_value=0, emboss=True, slider=True)
        box_352BC = layout.box()
        box_352BC.alert = False
        box_352BC.enabled = True
        box_352BC.active = True
        box_352BC.use_property_split = False
        box_352BC.use_property_decorate = False
        box_352BC.alignment = 'Expand'.upper()
        box_352BC.scale_x = 1.0
        box_352BC.scale_y = 1.0
        if not True: box_352BC.operator_context = "EXEC_DEFAULT"
        box_352BC.label(text='Lens Dirt 3 - Huge Bokeh 4K', icon_value=0)
        col_DEF48 = box_352BC.column(heading='', align=True)
        col_DEF48.alert = False
        col_DEF48.enabled = True
        col_DEF48.active = True
        col_DEF48.use_property_split = False
        col_DEF48.use_property_decorate = False
        col_DEF48.scale_x = 1.0
        col_DEF48.scale_y = 1.0
        col_DEF48.alignment = 'Expand'.upper()
        col_DEF48.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_DEF48.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.001'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=True)
        col_DEF48.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.005'].inputs[0], 'default_value', text='Scale', icon_value=0, emboss=True, slider=True)
        col_DEF48.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.005'].inputs[1], 'default_value', text='Extra Bokeh', icon_value=0, emboss=True)
        col_DEF48.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.005'].inputs[2], 'default_value', text='Blur', icon_value=0, emboss=True, slider=True)
        col_C6260 = layout.column(heading='', align=False)
        col_C6260.alert = False
        col_C6260.enabled = True
        col_C6260.active = True
        col_C6260.use_property_split = False
        col_C6260.use_property_decorate = False
        col_C6260.scale_x = 1.0
        col_C6260.scale_y = 0.75
        col_C6260.alignment = 'Expand'.upper()
        col_C6260.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_C6260.label(text='Enabled Glares will have influence on', icon_value=0)
        col_C6260.label(text="Lens Dirt's brightness and color", icon_value=0)


class SNA_PT_GLARE_74542(bpy.types.Panel):
    bl_label = 'Glare'
    bl_idname = 'SNA_PT_GLARE_74542'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 5
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_CD1F5 = layout.row(heading='', align=True)
        row_CD1F5.alert = False
        row_CD1F5.enabled = True
        row_CD1F5.active = True
        row_CD1F5.use_property_split = False
        row_CD1F5.use_property_decorate = False
        row_CD1F5.scale_x = 1.0
        row_CD1F5.scale_y = 1.5
        row_CD1F5.alignment = 'Expand'.upper()
        row_CD1F5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_CD1F5.operator('sna.enable_glares_c9218', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_CD1F5.operator('sna.disable_glares_de435', text='Disable', icon_value=0, emboss=True, depress=False)


class SNA_OT_Operator005_39B40(bpy.types.Operator):
    bl_idname = "sna.operator005_39b40"
    bl_label = "Operator.005"
    bl_description = "Make enabled Lens Dirts appear wet"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_lens_dirt_and_wet_lens():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            wet_lens_node_name = "Wet Lens"
            lens_dirt_node_name = "Lens Dirt"
            # Get the existing nodes
            wet_lens_node = compositor.nodes[wet_lens_node_name]
            lens_dirt_node = compositor.nodes[lens_dirt_node_name]
            # Create links between nodes
            compositor.links.new(wet_lens_node.outputs['Wet Lens'], lens_dirt_node.inputs['Wet Lens'])
        bpy.data.node_groups["Lens Dirt"].nodes["Group.003"].inputs[2].default_value = 1
        bpy.data.node_groups["Lens Dirt"].nodes["Group.005"].inputs[2].default_value = 1
        # Run the function to link the nodes
        link_lens_dirt_and_wet_lens()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator006_2227B(bpy.types.Operator):
    bl_idname = "sna.operator006_2227b"
    bl_label = "Operator.006"
    bl_description = "Disable Wet Lens effect"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def unlink_lens_dirt_and_wet_lens():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            wet_lens_node_name = "Wet Lens"
            lens_dirt_node_name = "Lens Dirt"
            # Get the existing nodes
            wet_lens_node = compositor.nodes[wet_lens_node_name]
            lens_dirt_node = compositor.nodes[lens_dirt_node_name]
            links_to_remove = []
            # Find the links to remove
            for link in compositor.links:
                if link.from_node == wet_lens_node and (link.to_node == lens_dirt_node):
                    links_to_remove.append(link)
            # Remove the identified links
            for link in links_to_remove:
                compositor.links.remove(link)
        # Run the function to unlink the nodes
        unlink_lens_dirt_and_wet_lens()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_LENS_DIRT_D38EB(bpy.types.Panel):
    bl_label = 'Lens Dirt'
    bl_idname = 'SNA_PT_LENS_DIRT_D38EB'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 6
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_5D2AA = layout.row(heading='', align=True)
        row_5D2AA.alert = False
        row_5D2AA.enabled = True
        row_5D2AA.active = True
        row_5D2AA.use_property_split = False
        row_5D2AA.use_property_decorate = False
        row_5D2AA.scale_x = 1.0
        row_5D2AA.scale_y = 1.5
        row_5D2AA.alignment = 'Expand'.upper()
        row_5D2AA.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_5D2AA.operator('sna.operator_9650e', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_5D2AA.operator('sna.operator001_5409d', text='Disable', icon_value=0, emboss=True, depress=False)
        layout.prop(bpy.data.node_groups['Lens Dirt'].nodes['Blur.001'].inputs[1], 'default_value', text='Extra Brightness', icon_value=0, emboss=True)
        col_50D11 = layout.column(heading='', align=True)
        col_50D11.alert = False
        col_50D11.enabled = True
        col_50D11.active = True
        col_50D11.use_property_split = False
        col_50D11.use_property_decorate = False
        col_50D11.scale_x = 1.0
        col_50D11.scale_y = 1.0
        col_50D11.alignment = 'Expand'.upper()
        col_50D11.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_50D11.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.004'].inputs[1], 'default_value', text='Aberration', icon_value=0, emboss=True)
        col_50D11.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.004'].inputs[2], 'default_value', text='Dispersion', icon_value=0, emboss=True)
        box_90256 = layout.box()
        box_90256.alert = False
        box_90256.enabled = True
        box_90256.active = True
        box_90256.use_property_split = False
        box_90256.use_property_decorate = False
        box_90256.alignment = 'Expand'.upper()
        box_90256.scale_x = 1.0
        box_90256.scale_y = 1.0
        if not True: box_90256.operator_context = "EXEC_DEFAULT"
        box_90256.label(text='Lens Dirt 1 - Small Dirts 4K', icon_value=0)
        col_A897C = box_90256.column(heading='', align=True)
        col_A897C.alert = False
        col_A897C.enabled = True
        col_A897C.active = True
        col_A897C.use_property_split = False
        col_A897C.use_property_decorate = False
        col_A897C.scale_x = 1.0
        col_A897C.scale_y = 1.0
        col_A897C.alignment = 'Expand'.upper()
        col_A897C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_A897C.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.013'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)
        col_A897C.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group'].inputs[0], 'default_value', text='Scale', icon_value=0, emboss=True)
        col_A897C.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True, slider=True)
        box_06153 = layout.box()
        box_06153.alert = False
        box_06153.enabled = True
        box_06153.active = True
        box_06153.use_property_split = False
        box_06153.use_property_decorate = False
        box_06153.alignment = 'Expand'.upper()
        box_06153.scale_x = 1.0
        box_06153.scale_y = 1.0
        if not True: box_06153.operator_context = "EXEC_DEFAULT"
        box_06153.label(text='Lens Dirt 2 - Medium Bokeh 4K', icon_value=0)
        col_49DAC = box_06153.column(heading='', align=True)
        col_49DAC.alert = False
        col_49DAC.enabled = True
        col_49DAC.active = True
        col_49DAC.use_property_split = False
        col_49DAC.use_property_decorate = False
        col_49DAC.scale_x = 1.0
        col_49DAC.scale_y = 1.0
        col_49DAC.alignment = 'Expand'.upper()
        col_49DAC.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_49DAC.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.014'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)
        col_49DAC.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.003'].inputs[0], 'default_value', text='Scale', icon_value=0, emboss=True, slider=True)
        col_49DAC.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.003'].inputs[1], 'default_value', text='Extra Bokeh', icon_value=0, emboss=True)
        col_49DAC.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.003'].inputs[2], 'default_value', text='Blur', icon_value=0, emboss=True, slider=True)
        box_9710E = layout.box()
        box_9710E.alert = False
        box_9710E.enabled = True
        box_9710E.active = True
        box_9710E.use_property_split = False
        box_9710E.use_property_decorate = False
        box_9710E.alignment = 'Expand'.upper()
        box_9710E.scale_x = 1.0
        box_9710E.scale_y = 1.0
        if not True: box_9710E.operator_context = "EXEC_DEFAULT"
        box_9710E.label(text='Lens Dirt 3 - Huge Bokeh 4K', icon_value=0)
        col_F2399 = box_9710E.column(heading='', align=True)
        col_F2399.alert = False
        col_F2399.enabled = True
        col_F2399.active = True
        col_F2399.use_property_split = False
        col_F2399.use_property_decorate = False
        col_F2399.scale_x = 1.0
        col_F2399.scale_y = 1.0
        col_F2399.alignment = 'Expand'.upper()
        col_F2399.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_F2399.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.001'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)
        col_F2399.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.005'].inputs[0], 'default_value', text='Scale', icon_value=0, emboss=True)
        col_F2399.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.005'].inputs[1], 'default_value', text='Extra Bokeh', icon_value=0, emboss=True)
        col_F2399.prop(bpy.data.node_groups['Lens Dirt'].nodes['Group.005'].inputs[2], 'default_value', text='Blur', icon_value=0, emboss=True, slider=True)
        col_45140 = layout.column(heading='', align=False)
        col_45140.alert = False
        col_45140.enabled = True
        col_45140.active = True
        col_45140.use_property_split = False
        col_45140.use_property_decorate = False
        col_45140.scale_x = 1.0
        col_45140.scale_y = 0.75
        col_45140.alignment = 'Expand'.upper()
        col_45140.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_45140.label(text='Enabled Glares will have influence on', icon_value=0)
        col_45140.label(text="Lens Dirt's brightness and color", icon_value=0)


class SNA_OT_Operator020_7A6A7(bpy.types.Operator):
    bl_idname = "sna.operator020_7a6a7"
    bl_label = "Operator.020"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1036
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator014_71654(bpy.types.Operator):
    bl_idname = "sna.operator014_71654"
    bl_label = "Operator.014"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1440
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator021_564C0(bpy.types.Operator):
    bl_idname = "sna.operator021_564c0"
    bl_label = "Operator.021"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 4096
        bpy.context.scene.render.resolution_y = 3072
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator022_B4Eef(bpy.types.Operator):
    bl_idname = "sna.operator022_b4eef"
    bl_label = "Operator.022"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1280
        bpy.context.scene.render.resolution_y = 962
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator008_2C684(bpy.types.Operator):
    bl_idname = "sna.operator008_2c684"
    bl_label = "Operator.008"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 4096
        bpy.context.scene.render.resolution_y = 2304
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator009_1Aa7A(bpy.types.Operator):
    bl_idname = "sna.operator009_1aa7a"
    bl_label = "Operator.009"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1280
        bpy.context.scene.render.resolution_y = 720
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator007_C2369(bpy.types.Operator):
    bl_idname = "sna.operator007_c2369"
    bl_label = "Operator.007"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator010_D86Fc(bpy.types.Operator):
    bl_idname = "sna.operator010_d86fc"
    bl_label = "Operator.010"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 854
        bpy.context.scene.render.resolution_y = 480
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator011_325E9(bpy.types.Operator):
    bl_idname = "sna.operator011_325e9"
    bl_label = "Operator.011"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1080
        bpy.context.scene.render.resolution_y = 1080
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator012_A483C(bpy.types.Operator):
    bl_idname = "sna.operator012_a483c"
    bl_label = "Operator.012"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1080
        bpy.context.scene.render.resolution_y = 1350
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator013_19B92(bpy.types.Operator):
    bl_idname = "sna.operator013_19b92"
    bl_label = "Operator.013"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1080
        bpy.context.scene.render.resolution_y = 1920
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator016_29794(bpy.types.Operator):
    bl_idname = "sna.operator016_29794"
    bl_label = "Operator.016"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 4096
        bpy.context.scene.render.resolution_y = 1742
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator017_Cf146(bpy.types.Operator):
    bl_idname = "sna.operator017_cf146"
    bl_label = "Operator.017"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1280
        bpy.context.scene.render.resolution_y = 544
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator015_Aea69(bpy.types.Operator):
    bl_idname = "sna.operator015_aea69"
    bl_label = "Operator.015"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 816
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator019_B1Ef3(bpy.types.Operator):
    bl_idname = "sna.operator019_b1ef3"
    bl_label = "Operator.019"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 1280
        bpy.context.scene.render.resolution_y = 690
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator018_E9C55(bpy.types.Operator):
    bl_idname = "sna.operator018_e9c55"
    bl_label = "Operator.018"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 4096
        bpy.context.scene.render.resolution_y = 2214
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_ASPECT_RATIO__RESOLUTION_4245E(bpy.types.Panel):
    bl_label = 'Aspect Ratio & Resolution'
    bl_idname = 'SNA_PT_ASPECT_RATIO__RESOLUTION_4245E'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 8
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_7E736 = layout.box()
        box_7E736.alert = False
        box_7E736.enabled = True
        box_7E736.active = True
        box_7E736.use_property_split = False
        box_7E736.use_property_decorate = False
        box_7E736.alignment = 'Expand'.upper()
        box_7E736.scale_x = 1.0
        box_7E736.scale_y = 1.0
        if not True: box_7E736.operator_context = "EXEC_DEFAULT"
        col_090D7 = box_7E736.column(heading='', align=True)
        col_090D7.alert = False
        col_090D7.enabled = True
        col_090D7.active = True
        col_090D7.use_property_split = False
        col_090D7.use_property_decorate = False
        col_090D7.scale_x = 1.0
        col_090D7.scale_y = 1.0
        col_090D7.alignment = 'Expand'.upper()
        col_090D7.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_090D7.prop(bpy.data.scenes['Scene'].render, 'resolution_x', text='Resolution X', icon_value=0, emboss=True)
        col_090D7.prop(bpy.data.scenes['Scene'].render, 'resolution_y', text='Resolution Y', icon_value=0, emboss=True)


class SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F(bpy.types.Panel):
    bl_label = 'Aspect Ratio & Resolution'
    bl_idname = 'SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 8
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_3BECB = layout.box()
        box_3BECB.alert = False
        box_3BECB.enabled = True
        box_3BECB.active = True
        box_3BECB.use_property_split = False
        box_3BECB.use_property_decorate = False
        box_3BECB.alignment = 'Expand'.upper()
        box_3BECB.scale_x = 1.0
        box_3BECB.scale_y = 1.0
        if not True: box_3BECB.operator_context = "EXEC_DEFAULT"
        col_43267 = box_3BECB.column(heading='', align=True)
        col_43267.alert = False
        col_43267.enabled = True
        col_43267.active = True
        col_43267.use_property_split = False
        col_43267.use_property_decorate = False
        col_43267.scale_x = 1.0
        col_43267.scale_y = 1.0
        col_43267.alignment = 'Expand'.upper()
        col_43267.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_43267.prop(bpy.data.scenes['Scene'].render, 'resolution_x', text='Resolution X', icon_value=0, emboss=True)
        col_43267.prop(bpy.data.scenes['Scene'].render, 'resolution_y', text='Resolution Y', icon_value=0, emboss=True)


class SNA_OT_Enable_Colorist_264Dc(bpy.types.Operator):
    bl_idname = "sna.enable_colorist_264dc"
    bl_label = "Enable Colorist"
    bl_description = "Enable the compositing tree and add the necessary nodes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Colorist Nodes Blender 4.0.blend') + r'\NodeTree', filename='Colorist Pro', link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_7B570 = None if not new_data else new_data[0]
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Colorist Nodes Blender 4.0.blend') + r'\NodeTree', filename='Film Emulation', link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_CCEE9 = None if not new_data else new_data[0]
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Colorist Nodes Blender 4.0.blend') + r'\NodeTree', filename='Glares', link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_A3316 = None if not new_data else new_data[0]
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Colorist Nodes Blender 4.0.blend') + r'\NodeTree', filename='Lens Dirt', link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_F1029 = None if not new_data else new_data[0]
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Colorist Nodes Blender 4.0.blend') + r'\NodeTree', filename='Lens Flare', link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_C5216 = None if not new_data else new_data[0]
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Colorist Nodes Blender 4.0.blend') + r'\NodeTree', filename='Selective Color', link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_9CDA1 = None if not new_data else new_data[0]
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Colorist Nodes Blender 4.0.blend') + r'\NodeTree', filename='Wet Lens', link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_FB913 = None if not new_data else new_data[0]
        bpy.context.scene.use_nodes = True
        bpy.data.scenes["Scene"].node_tree.use_opencl = True
        bpy.data.scenes["Scene"].node_tree.use_groupnode_buffer = True

        def add_colorist_pro_node():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Clear the current node setup
            for node in compositor.nodes:
                compositor.nodes.remove(node)
            # Add Render Layers node
            render_layers_node = compositor.nodes.new(type='CompositorNodeRLayers')
            render_layers_node.location = (-450, 0)
            render_layers_node.name = "Render Layers - Colorist"
            # Add "Colorist Pro" node group
            colorist_pro_group_name = "Colorist Pro"
            colorist_pro_node = compositor.nodes.new(type='CompositorNodeGroup')
            colorist_pro_node.node_tree = bpy.data.node_groups[colorist_pro_group_name]
            colorist_pro_node.location = (400, 50)
            colorist_pro_node.name = "Colorist Pro"
            selective_color_group_name = "Selective Color"
            selective_color_node = compositor.nodes.new(type='CompositorNodeGroup')
            selective_color_node.node_tree = bpy.data.node_groups[selective_color_group_name]
            selective_color_node.location = (-50, -100)
            selective_color_node.name = "Selective Color"
            lens_flare_group_name = "Lens Flare"
            lens_flare_node = compositor.nodes.new(type='CompositorNodeGroup')
            lens_flare_node.node_tree = bpy.data.node_groups[lens_flare_group_name]
            lens_flare_node.location = (-50, 400)
            lens_flare_node.name = "Lens Flare"
            glares_group_name = "Glares"
            glares_node = compositor.nodes.new(type='CompositorNodeGroup')
            glares_node.node_tree = bpy.data.node_groups[glares_group_name]
            glares_node.location = (-50, 220)
            glares_node.name = "Glares"
            lens_dirt_group_name = "Lens Dirt"
            lens_dirt_node = compositor.nodes.new(type='CompositorNodeGroup')
            lens_dirt_node.node_tree = bpy.data.node_groups[lens_dirt_group_name]
            lens_dirt_node.location = (150, 220)
            lens_dirt_node.name = "Lens Dirt"
            wet_lens_group_name = "Wet Lens"
            wet_lens_node = compositor.nodes.new(type='CompositorNodeGroup')
            wet_lens_node.node_tree = bpy.data.node_groups[wet_lens_group_name]
            wet_lens_node.location = (-50, 100)
            wet_lens_node.name = "Wet Lens"
            film_emulation_group_name = "Film Emulation"
            film_emulation_node = compositor.nodes.new(type='CompositorNodeGroup')
            film_emulation_node.node_tree = bpy.data.node_groups[film_emulation_group_name]
            film_emulation_node.location = (700, -100)
            film_emulation_node.name = "Film Emulation"
            # Add Composite node
            composite_node = compositor.nodes.new(type='CompositorNodeComposite')
            composite_node.location = (1000, 0)
            composite_node.name = "Composite - Colorist"
            viewer_node = compositor.nodes.new(type='CompositorNodeViewer')
            viewer_node.location = (1000, -150)
            viewer_node.name = "Viewer - Colorist"
            # Link the nodes
            compositor.links.new(render_layers_node.outputs['Image'], colorist_pro_node.inputs[0])
            compositor.links.new(render_layers_node.outputs['Image'], lens_flare_node.inputs[0])
            compositor.links.new(render_layers_node.outputs['Image'], glares_node.inputs[0])
            compositor.links.new(render_layers_node.outputs['Image'], lens_dirt_node.inputs[0])
            compositor.links.new(render_layers_node.outputs['Image'], wet_lens_node.inputs[0])
            compositor.links.new(render_layers_node.outputs['Image'], selective_color_node.inputs[0])
            compositor.links.new(colorist_pro_node.outputs[0], film_emulation_node.inputs[0])
            compositor.links.new(colorist_pro_node.outputs[0], composite_node.inputs[0])
            compositor.links.new(colorist_pro_node.outputs[0], viewer_node.inputs[0])
        # Run the function to add the nodes
        add_colorist_pro_node()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Reset_Wb_253Dd(bpy.types.Operator):
    bl_idname = "sna.reset_wb_253dd"
    bl_label = "Reset WB"
    bl_description = "Return WB values to default"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Colorist Pro"].nodes["Math"].inputs[0].default_value = 6.5
        bpy.data.node_groups["Colorist Pro"].nodes["Math.003"].inputs[0].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator002_9Ba85(bpy.types.Operator):
    bl_idname = "sna.operator002_9ba85"
    bl_label = "Operator.002"
    bl_description = "Return Exposure values to default"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Colorist Pro"].nodes["Exposure"].inputs[1].default_value = 0
        bpy.data.node_groups["Colorist Pro"].nodes["Gamma"].inputs[1].default_value = 1
        bpy.data.node_groups["Colorist Pro"].nodes["Bright/Contrast.001"].inputs[2].default_value = 0
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_COLOR_GRADING_8B4C0(bpy.types.Panel):
    bl_label = 'Color Grading'
    bl_idname = 'SNA_PT_COLOR_GRADING_8B4C0'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_05A69 = layout.box()
        box_05A69.alert = False
        box_05A69.enabled = True
        box_05A69.active = True
        box_05A69.use_property_split = False
        box_05A69.use_property_decorate = False
        box_05A69.alignment = 'Expand'.upper()
        box_05A69.scale_x = 1.0
        box_05A69.scale_y = 1.0
        if not True: box_05A69.operator_context = "EXEC_DEFAULT"
        col_87484 = box_05A69.column(heading='', align=True)
        col_87484.alert = False
        col_87484.enabled = True
        col_87484.active = True
        col_87484.use_property_split = True
        col_87484.use_property_decorate = False
        col_87484.scale_x = 1.0
        col_87484.scale_y = 1.0
        col_87484.alignment = 'Expand'.upper()
        col_87484.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_61919 = col_87484.row(heading='', align=False)
        row_61919.alert = False
        row_61919.enabled = True
        row_61919.active = True
        row_61919.use_property_split = False
        row_61919.use_property_decorate = False
        row_61919.scale_x = 1.0
        row_61919.scale_y = 1.0
        row_61919.alignment = 'Expand'.upper()
        row_61919.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_61919.label(text='White Balance', icon_value=299)
        row_61919.separator(factor=1.0)
        row_0F8C9 = row_61919.row(heading='', align=False)
        row_0F8C9.alert = True
        row_0F8C9.enabled = True
        row_0F8C9.active = True
        row_0F8C9.use_property_split = False
        row_0F8C9.use_property_decorate = False
        row_0F8C9.scale_x = 0.8999999761581421
        row_0F8C9.scale_y = 1.0
        row_0F8C9.alignment = 'Expand'.upper()
        row_0F8C9.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_0F8C9.operator('sna.reset_wb_253dd', text='Reset', icon_value=715, emboss=True, depress=False)
        col_87484.separator(factor=2.0)
        col_87484.prop(bpy.data.node_groups['Colorist Pro'].nodes['Math'].inputs[0], 'default_value', text='Temperature', icon_value=0, emboss=True)
        col_87484.prop(bpy.data.node_groups['Colorist Pro'].nodes['Math.003'].inputs[0], 'default_value', text='Tint', icon_value=0, emboss=True)
        box_39E1B = layout.box()
        box_39E1B.alert = False
        box_39E1B.enabled = True
        box_39E1B.active = True
        box_39E1B.use_property_split = False
        box_39E1B.use_property_decorate = False
        box_39E1B.alignment = 'Expand'.upper()
        box_39E1B.scale_x = 1.0
        box_39E1B.scale_y = 1.0
        if not True: box_39E1B.operator_context = "EXEC_DEFAULT"
        row_F0763 = box_39E1B.row(heading='', align=False)
        row_F0763.alert = False
        row_F0763.enabled = True
        row_F0763.active = True
        row_F0763.use_property_split = False
        row_F0763.use_property_decorate = False
        row_F0763.scale_x = 1.0
        row_F0763.scale_y = 1.0
        row_F0763.alignment = 'Expand'.upper()
        row_F0763.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_F0763.label(text='Color', icon_value=54)
        row_F0763.separator(factor=1.0)
        row_997F1 = row_F0763.row(heading='', align=False)
        row_997F1.alert = True
        row_997F1.enabled = True
        row_997F1.active = True
        row_997F1.use_property_split = False
        row_997F1.use_property_decorate = False
        row_997F1.scale_x = 0.8999999761581421
        row_997F1.scale_y = 1.0
        row_997F1.alignment = 'Expand'.upper()
        row_997F1.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_997F1.operator('sna.operator003_68e0d', text='Reset', icon_value=715, emboss=True, depress=False)
        box_39E1B.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group.001'].inputs[1], 'default_value', text='Vibrance', icon_value=0, emboss=True)
        col_64F52 = box_39E1B.column(heading='', align=True)
        col_64F52.alert = False
        col_64F52.enabled = True
        col_64F52.active = True
        col_64F52.use_property_split = False
        col_64F52.use_property_decorate = False
        col_64F52.scale_x = 1.0
        col_64F52.scale_y = 1.0
        col_64F52.alignment = 'Expand'.upper()
        col_64F52.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_64F52.prop(bpy.data.node_groups['Colorist Pro'].nodes['Hue Saturation Value'].inputs[1], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_64F52.prop(bpy.data.node_groups['Colorist Pro'].nodes['Hue Saturation Value'].inputs[2], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        box_94905 = layout.box()
        box_94905.alert = False
        box_94905.enabled = True
        box_94905.active = True
        box_94905.use_property_split = False
        box_94905.use_property_decorate = False
        box_94905.alignment = 'Expand'.upper()
        box_94905.scale_x = 1.0
        box_94905.scale_y = 1.0
        if not True: box_94905.operator_context = "EXEC_DEFAULT"
        row_26A91 = box_94905.row(heading='', align=False)
        row_26A91.alert = False
        row_26A91.enabled = True
        row_26A91.active = True
        row_26A91.use_property_split = False
        row_26A91.use_property_decorate = False
        row_26A91.scale_x = 1.0
        row_26A91.scale_y = 1.0
        row_26A91.alignment = 'Expand'.upper()
        row_26A91.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_26A91.label(text='Exposure', icon_value=239)
        row_26A91.separator(factor=1.0299999713897705)
        row_1DD98 = row_26A91.row(heading='', align=False)
        row_1DD98.alert = True
        row_1DD98.enabled = True
        row_1DD98.active = True
        row_1DD98.use_property_split = False
        row_1DD98.use_property_decorate = False
        row_1DD98.scale_x = 0.8999999761581421
        row_1DD98.scale_y = 1.0
        row_1DD98.alignment = 'Expand'.upper()
        row_1DD98.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_1DD98.operator('sna.operator002_9ba85', text='Reset', icon_value=715, emboss=True, depress=False)
        col_BB1E8 = box_94905.column(heading='', align=True)
        col_BB1E8.alert = False
        col_BB1E8.enabled = True
        col_BB1E8.active = True
        col_BB1E8.use_property_split = False
        col_BB1E8.use_property_decorate = False
        col_BB1E8.scale_x = 1.0
        col_BB1E8.scale_y = 1.0
        col_BB1E8.alignment = 'Expand'.upper()
        col_BB1E8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_BB1E8.prop(bpy.data.node_groups['Colorist Pro'].nodes['Exposure'].inputs[1], 'default_value', text='Exposure', icon_value=0, emboss=True, slider=True)
        col_BB1E8.prop(bpy.data.node_groups['Colorist Pro'].nodes['Gamma'].inputs[1], 'default_value', text='Gamma', icon_value=0, emboss=True, slider=True)
        box_94905.prop(bpy.data.node_groups['Colorist Pro'].nodes['Bright/Contrast.001'].inputs[2], 'default_value', text='Contrast', icon_value=0, emboss=True, slider=True)
        box_34DB9 = layout.box()
        box_34DB9.alert = False
        box_34DB9.enabled = True
        box_34DB9.active = True
        box_34DB9.use_property_split = False
        box_34DB9.use_property_decorate = False
        box_34DB9.alignment = 'Expand'.upper()
        box_34DB9.scale_x = 1.0
        box_34DB9.scale_y = 1.0
        if not True: box_34DB9.operator_context = "EXEC_DEFAULT"
        row_92DB5 = box_34DB9.row(heading='', align=False)
        row_92DB5.alert = False
        row_92DB5.enabled = True
        row_92DB5.active = True
        row_92DB5.use_property_split = False
        row_92DB5.use_property_decorate = False
        row_92DB5.scale_x = 1.0
        row_92DB5.scale_y = 1.0
        row_92DB5.alignment = 'Expand'.upper()
        row_92DB5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_92DB5.label(text='Tone', icon_value=107)
        row_92DB5.separator(factor=1.0299999713897705)
        row_98BB2 = row_92DB5.row(heading='', align=False)
        row_98BB2.alert = True
        row_98BB2.enabled = True
        row_98BB2.active = True
        row_98BB2.use_property_split = False
        row_98BB2.use_property_decorate = False
        row_98BB2.scale_x = 0.8999999761581421
        row_98BB2.scale_y = 1.0
        row_98BB2.alignment = 'Expand'.upper()
        row_98BB2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_98BB2.operator('sna.operator024_25e20', text='Reset', icon_value=715, emboss=True, depress=False)
        col_AE3EE = box_34DB9.column(heading='', align=True)
        col_AE3EE.alert = False
        col_AE3EE.enabled = True
        col_AE3EE.active = True
        col_AE3EE.use_property_split = False
        col_AE3EE.use_property_decorate = False
        col_AE3EE.scale_x = 1.0
        col_AE3EE.scale_y = 1.0
        col_AE3EE.alignment = 'Expand'.upper()
        col_AE3EE.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_D685C = col_AE3EE.row(heading='', align=True)
        row_D685C.alert = False
        row_D685C.enabled = True
        row_D685C.active = True
        row_D685C.use_property_split = False
        row_D685C.use_property_decorate = False
        row_D685C.scale_x = 1.0
        row_D685C.scale_y = 1.0
        row_D685C.alignment = 'Expand'.upper()
        row_D685C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_CDAB7 = row_D685C.row(heading='', align=False)
        row_CDAB7.alert = False
        row_CDAB7.enabled = True
        row_CDAB7.active = True
        row_CDAB7.use_property_split = False
        row_CDAB7.use_property_decorate = False
        row_CDAB7.scale_x = 0.33000001311302185
        row_CDAB7.scale_y = 1.0
        row_CDAB7.alignment = 'Expand'.upper()
        row_CDAB7.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_CDAB7.prop(bpy.data.node_groups['Tonal Range'].nodes['Color Balance'], 'gain', text='', icon_value=0, emboss=True, slider=True)
        row_D685C.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[1], 'default_value', text='Highlight', icon_value=0, emboss=True, slider=True)
        row_45FFF = col_AE3EE.row(heading='', align=True)
        row_45FFF.alert = False
        row_45FFF.enabled = True
        row_45FFF.active = True
        row_45FFF.use_property_split = False
        row_45FFF.use_property_decorate = False
        row_45FFF.scale_x = 1.0
        row_45FFF.scale_y = 1.0
        row_45FFF.alignment = 'Expand'.upper()
        row_45FFF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_3AC26 = row_45FFF.row(heading='', align=False)
        row_3AC26.alert = False
        row_3AC26.enabled = True
        row_3AC26.active = True
        row_3AC26.use_property_split = False
        row_3AC26.use_property_decorate = False
        row_3AC26.scale_x = 0.33000001311302185
        row_3AC26.scale_y = 1.0
        row_3AC26.alignment = 'Expand'.upper()
        row_3AC26.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_3AC26.prop(bpy.data.node_groups['Tonal Range'].nodes['Color Balance'], 'gamma', text='', icon_value=0, emboss=True, slider=True)
        row_45FFF.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[2], 'default_value', text='Midtone', icon_value=0, emboss=True, slider=True)
        row_7718A = col_AE3EE.row(heading='', align=True)
        row_7718A.alert = False
        row_7718A.enabled = True
        row_7718A.active = True
        row_7718A.use_property_split = False
        row_7718A.use_property_decorate = False
        row_7718A.scale_x = 1.0
        row_7718A.scale_y = 1.0
        row_7718A.alignment = 'Expand'.upper()
        row_7718A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_20BB9 = row_7718A.row(heading='', align=False)
        row_20BB9.alert = False
        row_20BB9.enabled = True
        row_20BB9.active = True
        row_20BB9.use_property_split = False
        row_20BB9.use_property_decorate = False
        row_20BB9.scale_x = 0.33000001311302185
        row_20BB9.scale_y = 1.0
        row_20BB9.alignment = 'Expand'.upper()
        row_20BB9.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_20BB9.prop(bpy.data.node_groups['Tonal Range'].nodes['Color Balance'], 'lift', text='', icon_value=0, emboss=True, slider=True)
        row_7718A.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[3], 'default_value', text='Shadow', icon_value=0, emboss=True, slider=True)
        col_5523A = box_34DB9.column(heading='', align=True)
        col_5523A.alert = False
        col_5523A.enabled = True
        col_5523A.active = True
        col_5523A.use_property_split = False
        col_5523A.use_property_decorate = False
        col_5523A.scale_x = 1.0
        col_5523A.scale_y = 1.0
        col_5523A.alignment = 'Expand'.upper()
        col_5523A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_5523A.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[4], 'default_value', text='White', icon_value=0, emboss=True, slider=True)
        col_5523A.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[5], 'default_value', text='Black', icon_value=0, emboss=True, slider=True)
        box_34DB9.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[6], 'default_value', text='Mix', icon_value=0, emboss=True)


class SNA_PT_COLOR_GRADING_FA4B5(bpy.types.Panel):
    bl_label = 'Color Grading'
    bl_idname = 'SNA_PT_COLOR_GRADING_FA4B5'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_64D76 = layout.box()
        box_64D76.alert = False
        box_64D76.enabled = True
        box_64D76.active = True
        box_64D76.use_property_split = False
        box_64D76.use_property_decorate = False
        box_64D76.alignment = 'Expand'.upper()
        box_64D76.scale_x = 1.0
        box_64D76.scale_y = 1.0
        if not True: box_64D76.operator_context = "EXEC_DEFAULT"
        col_4FE67 = box_64D76.column(heading='', align=True)
        col_4FE67.alert = False
        col_4FE67.enabled = True
        col_4FE67.active = True
        col_4FE67.use_property_split = True
        col_4FE67.use_property_decorate = False
        col_4FE67.scale_x = 1.0
        col_4FE67.scale_y = 1.0
        col_4FE67.alignment = 'Expand'.upper()
        col_4FE67.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_95E76 = col_4FE67.row(heading='', align=False)
        row_95E76.alert = False
        row_95E76.enabled = True
        row_95E76.active = True
        row_95E76.use_property_split = False
        row_95E76.use_property_decorate = False
        row_95E76.scale_x = 1.0
        row_95E76.scale_y = 1.0
        row_95E76.alignment = 'Expand'.upper()
        row_95E76.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_95E76.label(text='White Balance', icon_value=299)
        row_95E76.separator(factor=1.0)
        row_7290B = row_95E76.row(heading='', align=False)
        row_7290B.alert = True
        row_7290B.enabled = True
        row_7290B.active = True
        row_7290B.use_property_split = False
        row_7290B.use_property_decorate = False
        row_7290B.scale_x = 0.8999999761581421
        row_7290B.scale_y = 1.0
        row_7290B.alignment = 'Expand'.upper()
        row_7290B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_7290B.operator('sna.reset_wb_253dd', text='Reset', icon_value=715, emboss=True, depress=False)
        col_4FE67.separator(factor=2.0)
        col_4FE67.prop(bpy.data.node_groups['Colorist Pro'].nodes['Math'].inputs[0], 'default_value', text='Temperature', icon_value=0, emboss=True)
        col_4FE67.prop(bpy.data.node_groups['Colorist Pro'].nodes['Math.003'].inputs[0], 'default_value', text='Tint', icon_value=0, emboss=True)
        box_7CC46 = layout.box()
        box_7CC46.alert = False
        box_7CC46.enabled = True
        box_7CC46.active = True
        box_7CC46.use_property_split = False
        box_7CC46.use_property_decorate = False
        box_7CC46.alignment = 'Expand'.upper()
        box_7CC46.scale_x = 1.0
        box_7CC46.scale_y = 1.0
        if not True: box_7CC46.operator_context = "EXEC_DEFAULT"
        row_82723 = box_7CC46.row(heading='', align=False)
        row_82723.alert = False
        row_82723.enabled = True
        row_82723.active = True
        row_82723.use_property_split = False
        row_82723.use_property_decorate = False
        row_82723.scale_x = 1.0
        row_82723.scale_y = 1.0
        row_82723.alignment = 'Expand'.upper()
        row_82723.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_82723.label(text='Color', icon_value=54)
        row_82723.separator(factor=1.0)
        row_2BA45 = row_82723.row(heading='', align=False)
        row_2BA45.alert = True
        row_2BA45.enabled = True
        row_2BA45.active = True
        row_2BA45.use_property_split = False
        row_2BA45.use_property_decorate = False
        row_2BA45.scale_x = 0.8999999761581421
        row_2BA45.scale_y = 1.0
        row_2BA45.alignment = 'Expand'.upper()
        row_2BA45.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_2BA45.operator('sna.operator003_68e0d', text='Reset', icon_value=715, emboss=True, depress=False)
        box_7CC46.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group.001'].inputs[1], 'default_value', text='Vibrance', icon_value=0, emboss=True)
        col_E26FF = box_7CC46.column(heading='', align=True)
        col_E26FF.alert = False
        col_E26FF.enabled = True
        col_E26FF.active = True
        col_E26FF.use_property_split = False
        col_E26FF.use_property_decorate = False
        col_E26FF.scale_x = 1.0
        col_E26FF.scale_y = 1.0
        col_E26FF.alignment = 'Expand'.upper()
        col_E26FF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_E26FF.prop(bpy.data.node_groups['Colorist Pro'].nodes['Hue Saturation Value'].inputs[1], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_E26FF.prop(bpy.data.node_groups['Colorist Pro'].nodes['Hue Saturation Value'].inputs[2], 'default_value', text='Saturation', icon_value=0, emboss=True, slider=True)
        box_FE308 = layout.box()
        box_FE308.alert = False
        box_FE308.enabled = True
        box_FE308.active = True
        box_FE308.use_property_split = False
        box_FE308.use_property_decorate = False
        box_FE308.alignment = 'Expand'.upper()
        box_FE308.scale_x = 1.0
        box_FE308.scale_y = 1.0
        if not True: box_FE308.operator_context = "EXEC_DEFAULT"
        row_6CCC8 = box_FE308.row(heading='', align=False)
        row_6CCC8.alert = False
        row_6CCC8.enabled = True
        row_6CCC8.active = True
        row_6CCC8.use_property_split = False
        row_6CCC8.use_property_decorate = False
        row_6CCC8.scale_x = 1.0
        row_6CCC8.scale_y = 1.0
        row_6CCC8.alignment = 'Expand'.upper()
        row_6CCC8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_6CCC8.label(text='Exposure', icon_value=239)
        row_6CCC8.separator(factor=1.0299999713897705)
        row_3C29F = row_6CCC8.row(heading='', align=False)
        row_3C29F.alert = True
        row_3C29F.enabled = True
        row_3C29F.active = True
        row_3C29F.use_property_split = False
        row_3C29F.use_property_decorate = False
        row_3C29F.scale_x = 0.8999999761581421
        row_3C29F.scale_y = 1.0
        row_3C29F.alignment = 'Expand'.upper()
        row_3C29F.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_3C29F.operator('sna.operator002_9ba85', text='Reset', icon_value=715, emboss=True, depress=False)
        col_1DB22 = box_FE308.column(heading='', align=True)
        col_1DB22.alert = False
        col_1DB22.enabled = True
        col_1DB22.active = True
        col_1DB22.use_property_split = False
        col_1DB22.use_property_decorate = False
        col_1DB22.scale_x = 1.0
        col_1DB22.scale_y = 1.0
        col_1DB22.alignment = 'Expand'.upper()
        col_1DB22.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_1DB22.prop(bpy.data.node_groups['Colorist Pro'].nodes['Exposure'].inputs[1], 'default_value', text='Exposure', icon_value=0, emboss=True, slider=True)
        col_1DB22.prop(bpy.data.node_groups['Colorist Pro'].nodes['Gamma'].inputs[1], 'default_value', text='Gamma', icon_value=0, emboss=True)
        box_FE308.prop(bpy.data.node_groups['Colorist Pro'].nodes['Bright/Contrast.001'].inputs[2], 'default_value', text='Contrast', icon_value=0, emboss=True, slider=True)
        box_E681F = layout.box()
        box_E681F.alert = False
        box_E681F.enabled = True
        box_E681F.active = True
        box_E681F.use_property_split = False
        box_E681F.use_property_decorate = False
        box_E681F.alignment = 'Expand'.upper()
        box_E681F.scale_x = 1.0
        box_E681F.scale_y = 1.0
        if not True: box_E681F.operator_context = "EXEC_DEFAULT"
        row_C785C = box_E681F.row(heading='', align=False)
        row_C785C.alert = False
        row_C785C.enabled = True
        row_C785C.active = True
        row_C785C.use_property_split = False
        row_C785C.use_property_decorate = False
        row_C785C.scale_x = 1.0
        row_C785C.scale_y = 1.0
        row_C785C.alignment = 'Expand'.upper()
        row_C785C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_C785C.label(text='Tone', icon_value=107)
        row_C785C.separator(factor=1.0299999713897705)
        row_F976E = row_C785C.row(heading='', align=False)
        row_F976E.alert = True
        row_F976E.enabled = True
        row_F976E.active = True
        row_F976E.use_property_split = False
        row_F976E.use_property_decorate = False
        row_F976E.scale_x = 0.8999999761581421
        row_F976E.scale_y = 1.0
        row_F976E.alignment = 'Expand'.upper()
        row_F976E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_F976E.operator('sna.operator024_25e20', text='Reset', icon_value=715, emboss=True, depress=False)
        col_6A3A5 = box_E681F.column(heading='', align=True)
        col_6A3A5.alert = False
        col_6A3A5.enabled = True
        col_6A3A5.active = True
        col_6A3A5.use_property_split = False
        col_6A3A5.use_property_decorate = False
        col_6A3A5.scale_x = 1.0
        col_6A3A5.scale_y = 1.0
        col_6A3A5.alignment = 'Expand'.upper()
        col_6A3A5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_CB6BA = col_6A3A5.row(heading='', align=True)
        row_CB6BA.alert = False
        row_CB6BA.enabled = True
        row_CB6BA.active = True
        row_CB6BA.use_property_split = False
        row_CB6BA.use_property_decorate = False
        row_CB6BA.scale_x = 1.0
        row_CB6BA.scale_y = 1.0
        row_CB6BA.alignment = 'Expand'.upper()
        row_CB6BA.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_3D2E5 = row_CB6BA.row(heading='', align=False)
        row_3D2E5.alert = False
        row_3D2E5.enabled = True
        row_3D2E5.active = True
        row_3D2E5.use_property_split = False
        row_3D2E5.use_property_decorate = False
        row_3D2E5.scale_x = 0.33000001311302185
        row_3D2E5.scale_y = 1.0
        row_3D2E5.alignment = 'Expand'.upper()
        row_3D2E5.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_3D2E5.prop(bpy.data.node_groups['Tonal Range'].nodes['Color Balance'], 'gain', text='', icon_value=0, emboss=True, slider=True)
        row_CB6BA.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[1], 'default_value', text='Highlight/Gain', icon_value=0, emboss=True, slider=True)
        row_0090F = col_6A3A5.row(heading='', align=True)
        row_0090F.alert = False
        row_0090F.enabled = True
        row_0090F.active = True
        row_0090F.use_property_split = False
        row_0090F.use_property_decorate = False
        row_0090F.scale_x = 1.0
        row_0090F.scale_y = 1.0
        row_0090F.alignment = 'Expand'.upper()
        row_0090F.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_B1449 = row_0090F.row(heading='', align=False)
        row_B1449.alert = False
        row_B1449.enabled = True
        row_B1449.active = True
        row_B1449.use_property_split = False
        row_B1449.use_property_decorate = False
        row_B1449.scale_x = 0.33000001311302185
        row_B1449.scale_y = 1.0
        row_B1449.alignment = 'Expand'.upper()
        row_B1449.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_B1449.prop(bpy.data.node_groups['Tonal Range'].nodes['Color Balance'], 'gamma', text='', icon_value=0, emboss=True, slider=True)
        row_0090F.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[2], 'default_value', text='Midtone', icon_value=0, emboss=True, slider=True)
        row_F9E0D = col_6A3A5.row(heading='', align=True)
        row_F9E0D.alert = False
        row_F9E0D.enabled = True
        row_F9E0D.active = True
        row_F9E0D.use_property_split = False
        row_F9E0D.use_property_decorate = False
        row_F9E0D.scale_x = 1.0
        row_F9E0D.scale_y = 1.0
        row_F9E0D.alignment = 'Expand'.upper()
        row_F9E0D.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_725ED = row_F9E0D.row(heading='', align=False)
        row_725ED.alert = False
        row_725ED.enabled = True
        row_725ED.active = True
        row_725ED.use_property_split = False
        row_725ED.use_property_decorate = False
        row_725ED.scale_x = 0.33000001311302185
        row_725ED.scale_y = 1.0
        row_725ED.alignment = 'Expand'.upper()
        row_725ED.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_725ED.prop(bpy.data.node_groups['Tonal Range'].nodes['Color Balance'], 'lift', text='', icon_value=0, emboss=True, slider=True)
        row_F9E0D.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[3], 'default_value', text='Shadow', icon_value=0, emboss=True, slider=True)
        col_1D187 = box_E681F.column(heading='', align=True)
        col_1D187.alert = False
        col_1D187.enabled = True
        col_1D187.active = True
        col_1D187.use_property_split = False
        col_1D187.use_property_decorate = False
        col_1D187.scale_x = 1.0
        col_1D187.scale_y = 1.0
        col_1D187.alignment = 'Expand'.upper()
        col_1D187.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_1D187.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[4], 'default_value', text='White', icon_value=0, emboss=True, slider=True)
        col_1D187.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[5], 'default_value', text='Black', icon_value=0, emboss=True, slider=True)
        box_E681F.prop(bpy.data.node_groups['Colorist Pro'].nodes['Group'].inputs[6], 'default_value', text='Mix', icon_value=0, emboss=True)


class SNA_OT_Operator003_68E0D(bpy.types.Operator):
    bl_idname = "sna.operator003_68e0d"
    bl_label = "Operator.003"
    bl_description = "Return Color values to default"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Colorist Pro"].nodes["Group.001"].inputs[1].default_value = 0
        bpy.data.node_groups["Colorist Pro"].nodes["Hue Saturation Value"].inputs[1].default_value = 0.5
        bpy.data.node_groups["Colorist Pro"].nodes["Hue Saturation Value"].inputs[2].default_value = 1
        bpy.data.node_groups["Colorist Pro"].nodes["Hue Saturation Value"].inputs[4].default_value = 1
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_COLOR_MANAGEMENT_A2DC9(bpy.types.Panel):
    bl_label = 'Color Management'
    bl_idname = 'SNA_PT_COLOR_MANAGEMENT_A2DC9'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_46A98 = layout.box()
        box_46A98.alert = False
        box_46A98.enabled = True
        box_46A98.active = True
        box_46A98.use_property_split = False
        box_46A98.use_property_decorate = False
        box_46A98.alignment = 'Expand'.upper()
        box_46A98.scale_x = 1.0
        box_46A98.scale_y = 1.0
        if not True: box_46A98.operator_context = "EXEC_DEFAULT"
        box_46A98.label(text='Color Space Preset', icon_value=0)
        row_BFB5B = box_46A98.row(heading='', align=True)
        row_BFB5B.alert = False
        row_BFB5B.enabled = True
        row_BFB5B.active = True
        row_BFB5B.use_property_split = False
        row_BFB5B.use_property_decorate = False
        row_BFB5B.scale_x = 1.0
        row_BFB5B.scale_y = 1.5
        row_BFB5B.alignment = 'Expand'.upper()
        row_BFB5B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_BFB5B.operator('sna.operator004_5f1e2', text='Blender AGX', icon_value=0, emboss=True, depress=False)
        op = row_BFB5B.operator('sna.operator023_034fc', text='ACES sRGB', icon_value=0, emboss=True, depress=False)
        box_31661 = layout.box()
        box_31661.alert = False
        box_31661.enabled = True
        box_31661.active = True
        box_31661.use_property_split = False
        box_31661.use_property_decorate = False
        box_31661.alignment = 'Expand'.upper()
        box_31661.scale_x = 1.0
        box_31661.scale_y = 1.0
        if not True: box_31661.operator_context = "EXEC_DEFAULT"
        box_31661.label(text='Display Device', icon_value=0)
        box_31661.prop(bpy.data.scenes['Scene'].display_settings, 'display_device', text='', icon_value=0, emboss=True)
        box_E8DDC = layout.box()
        box_E8DDC.alert = False
        box_E8DDC.enabled = True
        box_E8DDC.active = True
        box_E8DDC.use_property_split = False
        box_E8DDC.use_property_decorate = False
        box_E8DDC.alignment = 'Expand'.upper()
        box_E8DDC.scale_x = 1.0
        box_E8DDC.scale_y = 1.0
        if not True: box_E8DDC.operator_context = "EXEC_DEFAULT"
        box_E8DDC.label(text='View Transform', icon_value=0)
        box_E8DDC.prop(bpy.data.scenes['Scene'].view_settings, 'view_transform', text='', icon_value=0, emboss=True)
        box_A612D = layout.box()
        box_A612D.alert = False
        box_A612D.enabled = True
        box_A612D.active = True
        box_A612D.use_property_split = False
        box_A612D.use_property_decorate = False
        box_A612D.alignment = 'Expand'.upper()
        box_A612D.scale_x = 1.0
        box_A612D.scale_y = 1.0
        if not True: box_A612D.operator_context = "EXEC_DEFAULT"
        row_FB51C = box_A612D.row(heading='', align=False)
        row_FB51C.alert = False
        row_FB51C.enabled = True
        row_FB51C.active = True
        row_FB51C.use_property_split = False
        row_FB51C.use_property_decorate = False
        row_FB51C.scale_x = 1.0
        row_FB51C.scale_y = 1.0
        row_FB51C.alignment = 'Expand'.upper()
        row_FB51C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_FB51C.label(text='LUTs (Look)', icon_value=303)
        row_FB51C.separator(factor=1.0)
        row_BAE4A = row_FB51C.row(heading='', align=False)
        row_BAE4A.alert = True
        row_BAE4A.enabled = True
        row_BAE4A.active = True
        row_BAE4A.use_property_split = False
        row_BAE4A.use_property_decorate = False
        row_BAE4A.scale_x = 0.8999999761581421
        row_BAE4A.scale_y = 1.0
        row_BAE4A.alignment = 'Expand'.upper()
        row_BAE4A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_BAE4A.operator('sna.clear_luts_47b32', text='Reset', icon_value=715, emboss=True, depress=False)
        box_A612D.prop(bpy.data.scenes['Scene'].view_settings, 'look', text='', icon_value=0, emboss=True)
        box_A8041 = layout.box()
        box_A8041.alert = False
        box_A8041.enabled = True
        box_A8041.active = True
        box_A8041.use_property_split = False
        box_A8041.use_property_decorate = False
        box_A8041.alignment = 'Expand'.upper()
        box_A8041.scale_x = 1.0
        box_A8041.scale_y = 1.0
        if not True: box_A8041.operator_context = "EXEC_DEFAULT"
        box_A8041.label(text='Sequencer', icon_value=0)
        box_A8041.prop(bpy.data.scenes['Scene'].sequencer_colorspace_settings, 'name', text='', icon_value=0, emboss=True)


class SNA_OT_Operator024_25E20(bpy.types.Operator):
    bl_idname = "sna.operator024_25e20"
    bl_label = "Operator.024"
    bl_description = "Return Tone values to default"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Colorist Pro"].nodes["Group"].inputs[1].default_value = 0
        bpy.data.node_groups["Colorist Pro"].nodes["Group"].inputs[2].default_value = 0
        bpy.data.node_groups["Colorist Pro"].nodes["Group"].inputs[3].default_value = 0
        bpy.data.node_groups["Colorist Pro"].nodes["Group"].inputs[4].default_value = 0
        bpy.data.node_groups["Colorist Pro"].nodes["Group"].inputs[5].default_value = 0
        bpy.data.node_groups["Colorist Pro"].nodes["Group"].inputs[6].default_value = 1
        bpy.data.node_groups["Tonal Range"].nodes["Color Balance"].gain = (1, 1, 1)
        bpy.data.node_groups["Tonal Range"].nodes["Color Balance"].gamma = (1, 1, 1)
        bpy.data.node_groups["Tonal Range"].nodes["Color Balance"].lift = (1, 1, 1)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator004_5F1E2(bpy.types.Operator):
    bl_idname = "sna.operator004_5f1e2"
    bl_label = "Operator.004"
    bl_description = "Change colorspace to Blender's AGX"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.display_settings.display_device = 'sRGB'
        bpy.context.scene.view_settings.view_transform = 'AgX'
        bpy.context.scene.sequencer_colorspace_settings.name = 'sRGB'
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator023_034Fc(bpy.types.Operator):
    bl_idname = "sna.operator023_034fc"
    bl_label = "Operator.023"
    bl_description = "Change colorspace to ACES sRGB"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.display_settings.display_device = 'ACES'
        bpy.context.scene.view_settings.view_transform = 'sRGB'
        bpy.context.scene.sequencer_colorspace_settings.name = 'ACEScg'
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_COLOR_MANAGEMENT_BA963(bpy.types.Panel):
    bl_label = 'Color Management'
    bl_idname = 'SNA_PT_COLOR_MANAGEMENT_BA963'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_5138B = layout.box()
        box_5138B.alert = False
        box_5138B.enabled = True
        box_5138B.active = True
        box_5138B.use_property_split = False
        box_5138B.use_property_decorate = False
        box_5138B.alignment = 'Expand'.upper()
        box_5138B.scale_x = 1.0
        box_5138B.scale_y = 1.0
        if not True: box_5138B.operator_context = "EXEC_DEFAULT"
        box_5138B.label(text='Color Space Preset', icon_value=0)
        row_5A7CD = box_5138B.row(heading='', align=True)
        row_5A7CD.alert = False
        row_5A7CD.enabled = True
        row_5A7CD.active = True
        row_5A7CD.use_property_split = False
        row_5A7CD.use_property_decorate = False
        row_5A7CD.scale_x = 1.0
        row_5A7CD.scale_y = 1.5
        row_5A7CD.alignment = 'Expand'.upper()
        row_5A7CD.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_5A7CD.operator('sna.operator004_5f1e2', text='Blender AGX', icon_value=0, emboss=True, depress=False)
        op = row_5A7CD.operator('sna.operator023_034fc', text='ACES sRGB', icon_value=0, emboss=True, depress=False)
        box_E97BD = layout.box()
        box_E97BD.alert = False
        box_E97BD.enabled = True
        box_E97BD.active = True
        box_E97BD.use_property_split = False
        box_E97BD.use_property_decorate = False
        box_E97BD.alignment = 'Expand'.upper()
        box_E97BD.scale_x = 1.0
        box_E97BD.scale_y = 1.0
        if not True: box_E97BD.operator_context = "EXEC_DEFAULT"
        box_E97BD.label(text='Display Device', icon_value=0)
        box_E97BD.prop(bpy.data.scenes['Scene'].display_settings, 'display_device', text='', icon_value=0, emboss=True)
        box_9687F = layout.box()
        box_9687F.alert = False
        box_9687F.enabled = True
        box_9687F.active = True
        box_9687F.use_property_split = False
        box_9687F.use_property_decorate = False
        box_9687F.alignment = 'Expand'.upper()
        box_9687F.scale_x = 1.0
        box_9687F.scale_y = 1.0
        if not True: box_9687F.operator_context = "EXEC_DEFAULT"
        box_9687F.label(text='View Transform', icon_value=0)
        box_9687F.prop(bpy.data.scenes['Scene'].view_settings, 'view_transform', text='', icon_value=0, emboss=True)
        box_AEEA8 = layout.box()
        box_AEEA8.alert = False
        box_AEEA8.enabled = True
        box_AEEA8.active = True
        box_AEEA8.use_property_split = False
        box_AEEA8.use_property_decorate = False
        box_AEEA8.alignment = 'Expand'.upper()
        box_AEEA8.scale_x = 1.0
        box_AEEA8.scale_y = 1.0
        if not True: box_AEEA8.operator_context = "EXEC_DEFAULT"
        row_8F38C = box_AEEA8.row(heading='', align=False)
        row_8F38C.alert = False
        row_8F38C.enabled = True
        row_8F38C.active = True
        row_8F38C.use_property_split = False
        row_8F38C.use_property_decorate = False
        row_8F38C.scale_x = 1.0
        row_8F38C.scale_y = 1.0
        row_8F38C.alignment = 'Expand'.upper()
        row_8F38C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_8F38C.label(text='LUTs (Look)', icon_value=303)
        row_8F38C.separator(factor=1.0)
        row_905D8 = row_8F38C.row(heading='', align=False)
        row_905D8.alert = True
        row_905D8.enabled = True
        row_905D8.active = True
        row_905D8.use_property_split = False
        row_905D8.use_property_decorate = False
        row_905D8.scale_x = 0.8999999761581421
        row_905D8.scale_y = 1.0
        row_905D8.alignment = 'Expand'.upper()
        row_905D8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_905D8.operator('sna.clear_luts_47b32', text='Reset', icon_value=715, emboss=True, depress=False)
        box_AEEA8.prop(bpy.data.scenes['Scene'].view_settings, 'look', text='', icon_value=0, emboss=True)
        box_499EE = layout.box()
        box_499EE.alert = False
        box_499EE.enabled = True
        box_499EE.active = True
        box_499EE.use_property_split = False
        box_499EE.use_property_decorate = False
        box_499EE.alignment = 'Expand'.upper()
        box_499EE.scale_x = 1.0
        box_499EE.scale_y = 1.0
        if not True: box_499EE.operator_context = "EXEC_DEFAULT"
        box_499EE.label(text='Sequencer', icon_value=0)
        box_499EE.prop(bpy.data.scenes['Scene'].sequencer_colorspace_settings, 'name', text='', icon_value=0, emboss=True)


class SNA_OT_Clear_Luts_47B32(bpy.types.Operator):
    bl_idname = "sna.clear_luts_47b32"
    bl_label = "Clear LUTs"
    bl_description = "Change LUTs to: None"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.view_settings.look = 'None'
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Operator029_0476C(bpy.types.Operator):
    bl_idname = "sna.operator029_0476c"
    bl_label = "Operator.029"
    bl_description = "Unlink Selective Color Node"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_film_emulation_and_composite():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            selective_color_node_name = "Selective Color"
            render_layers_node = "Render Layers - Colorist"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            selective_color_node = compositor.nodes[selective_color_node_name]
            render_layers_node = compositor.nodes[render_layers_node]
            for link in compositor.links:
                if link.from_node == selective_color_node and link.to_node == colorist_pro_node:
                    compositor.links.remove(link)
            compositor.links.new(render_layers_node.outputs[0], (colorist_pro_node.inputs[0]))
        # Run the function to link the nodes
        link_film_emulation_and_composite()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Enable_Film_Bdaed(bpy.types.Operator):
    bl_idname = "sna.enable_film_bdaed"
    bl_label = "Enable Film"
    bl_description = "Link Film Emulation node in Compositor"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_film_emulation_and_composite():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            film_emulation_node_name = "Film Emulation"
            composite_node = "Composite - Colorist"
            viewer_node = "Viewer - Colorist"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            film_emulation_node = compositor.nodes[film_emulation_node_name]
            composite_node = compositor.nodes[composite_node]
            viewer_node = compositor.nodes[viewer_node]
            # Create links between nodes
            compositor.links.new(colorist_pro_node.outputs[0], film_emulation_node.inputs[0])
            for link in compositor.links:
                if link.from_node == colorist_pro_node and link.to_node == composite_node:
                    compositor.links.remove(link)
            compositor.links.new(film_emulation_node.outputs[0], composite_node.inputs[0])
            for link in compositor.links:
                if link.from_node == colorist_pro_node and link.to_node == viewer_node:
                    compositor.links.remove(link)
            compositor.links.new(film_emulation_node.outputs[0], viewer_node.inputs[0])
        # Run the function to link the nodes
        link_film_emulation_and_composite()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Disable_Film_7061A(bpy.types.Operator):
    bl_idname = "sna.disable_film_7061a"
    bl_label = "Disable Film"
    bl_description = "Unlink Film Emulation node"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_film_emulation_and_composite():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            film_emulation_node_name = "Film Emulation"
            composite_node = "Composite - Colorist"
            viewer_node = "Viewer - Colorist"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            film_emulation_node = compositor.nodes[film_emulation_node_name]
            composite_node = compositor.nodes[composite_node]
            viewer_node = compositor.nodes[viewer_node]
            for link in compositor.links:
                if link.from_node == film_emulation_node and link.to_node == colorist_pro_node:
                    compositor.links.remove(link)
            compositor.links.new(colorist_pro_node.outputs[0], composite_node.inputs[0])
            compositor.links.new(colorist_pro_node.outputs[0], viewer_node.inputs[0])
        # Run the function to link the nodes
        link_film_emulation_and_composite()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_FILM_EMULATION_69921(bpy.types.Panel):
    bl_label = 'Film Emulation'
    bl_idname = 'SNA_PT_FILM_EMULATION_69921'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 7
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_38280 = layout.row(heading='', align=True)
        row_38280.alert = False
        row_38280.enabled = True
        row_38280.active = True
        row_38280.use_property_split = False
        row_38280.use_property_decorate = False
        row_38280.scale_x = 1.0
        row_38280.scale_y = 1.5
        row_38280.alignment = 'Expand'.upper()
        row_38280.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_38280.operator('sna.enable_film_bdaed', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_38280.operator('sna.disable_film_7061a', text='Disable', icon_value=0, emboss=True, depress=False)


class SNA_OT_K_Grain_8Bf7C(bpy.types.Operator):
    bl_idname = "sna.k_grain_8bf7c"
    bl_label = "4k Grain"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Film Emulation"].nodes["Texture.002"].texture = bpy.data.textures["RGB Noise"]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Bw_Noise_8B7F2(bpy.types.Operator):
    bl_idname = "sna.bw_noise_8b7f2"
    bl_label = "BW Noise"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Film Emulation"].nodes["Texture.002"].texture = bpy.data.textures["Simple Noise"]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_K_Grain001_52E35(bpy.types.Operator):
    bl_idname = "sna.k_grain001_52e35"
    bl_label = "4k Grain.001"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Film Emulation"].nodes["Texture.002"].texture = bpy.data.textures["RGB Noise"]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Bw_Noise001_0530C(bpy.types.Operator):
    bl_idname = "sna.bw_noise001_0530c"
    bl_label = "BW Noise.001"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.data.node_groups["Film Emulation"].nodes["Texture.002"].texture = bpy.data.textures["Simple Noise"]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_FILM_EMULATION_5D6F8(bpy.types.Panel):
    bl_label = 'Film Emulation'
    bl_idname = 'SNA_PT_FILM_EMULATION_5D6F8'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 7
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_69C19 = layout.row(heading='', align=True)
        row_69C19.alert = False
        row_69C19.enabled = True
        row_69C19.active = True
        row_69C19.use_property_split = False
        row_69C19.use_property_decorate = False
        row_69C19.scale_x = 1.0
        row_69C19.scale_y = 1.5
        row_69C19.alignment = 'Expand'.upper()
        row_69C19.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_69C19.operator('sna.enable_film_bdaed', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_69C19.operator('sna.disable_film_7061a', text='Disable', icon_value=0, emboss=True, depress=False)


class SNA_PT_LENS_FLARE_77473(bpy.types.Panel):
    bl_label = 'Lens Flare'
    bl_idname = 'SNA_PT_LENS_FLARE_77473'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_FE8AF = layout.row(heading='', align=True)
        row_FE8AF.alert = False
        row_FE8AF.enabled = True
        row_FE8AF.active = True
        row_FE8AF.use_property_split = False
        row_FE8AF.use_property_decorate = False
        row_FE8AF.scale_x = 1.0
        row_FE8AF.scale_y = 1.5
        row_FE8AF.alignment = 'Expand'.upper()
        row_FE8AF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_FE8AF.operator('sna.enable_lens_flare_29410', text='Enable', icon_value=0, emboss=True, depress=False)
        op = row_FE8AF.operator('sna.disable_lens_flare_4a654', text='Disable', icon_value=0, emboss=True, depress=False)


class SNA_OT_Enable_Lens_Flare_29410(bpy.types.Operator):
    bl_idname = "sna.enable_lens_flare_29410"
    bl_label = "Enable Lens Flare"
    bl_description = "Link Lens Flare node in Compositor"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def link_colorist_pro_and_lens_flare():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            lens_flare_node_name = "Lens Flare"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            lens_flare_node = compositor.nodes[lens_flare_node_name]
            # Create links between nodes
            compositor.links.new(lens_flare_node.outputs['Lens Flare'], colorist_pro_node.inputs['Lens Flare'])
        # Run the function to link the nodes
        link_colorist_pro_and_lens_flare()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Disable_Lens_Flare_4A654(bpy.types.Operator):
    bl_idname = "sna.disable_lens_flare_4a654"
    bl_label = "Disable Lens Flare"
    bl_description = "Unlink Lens Flare node, press to safe viewport performance"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):

        def unlink_colorist_pro_and_lens_flare():
            # Get the Compositor nodes tree
            compositor = bpy.context.scene.node_tree
            # Replace with the actual names or indices of your nodes
            colorist_pro_node_name = "Colorist Pro"
            lens_flare_node_name = "Lens Flare"
            # Get the existing nodes
            colorist_pro_node = compositor.nodes[colorist_pro_node_name]
            lens_flare_node = compositor.nodes[lens_flare_node_name]
            # Find and remove the links between nodes
            for link in compositor.links:
                if link.from_node == lens_flare_node and link.to_node == colorist_pro_node:
                    compositor.links.remove(link)
        # Run the function to unlink the nodes
        unlink_colorist_pro_and_lens_flare()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_COLORIST_PRO_V111_5161E(bpy.types.Panel):
    bl_label = 'Colorist Pro v1.1.1'
    bl_idname = 'SNA_PT_COLORIST_PRO_V111_5161E'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        col_5A6FB = layout.column(heading='', align=False)
        col_5A6FB.alert = False
        col_5A6FB.enabled = True
        col_5A6FB.active = True
        col_5A6FB.use_property_split = False
        col_5A6FB.use_property_decorate = False
        col_5A6FB.scale_x = 1.0
        col_5A6FB.scale_y = 1.809999942779541
        col_5A6FB.alignment = 'Expand'.upper()
        col_5A6FB.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = col_5A6FB.operator('sna.enable_colorist_264dc', text='Enable Colorist Pro', icon_value=240, emboss=True, depress=False)
        col_CA2E2 = layout.column(heading='', align=False)
        col_CA2E2.alert = False
        col_CA2E2.enabled = True
        col_CA2E2.active = True
        col_CA2E2.use_property_split = False
        col_CA2E2.use_property_decorate = False
        col_CA2E2.scale_x = 1.0
        col_CA2E2.scale_y = 0.46000003814697266
        col_CA2E2.alignment = 'Expand'.upper()
        col_CA2E2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_CA2E2.label(text='Warning: Enabling Colorist Pro will delete', icon_value=0)
        col_CA2E2.label(text='any existing nodes in the compositor', icon_value=0)
        layout.prop(bpy.data.scenes['Scene'], 'use_nodes', text='Use Nodes (Compositor)', icon_value=0, emboss=True)
        row_90C12 = layout.row(heading='', align=False)
        row_90C12.alert = False
        row_90C12.enabled = True
        row_90C12.active = True
        row_90C12.use_property_split = False
        row_90C12.use_property_decorate = False
        row_90C12.scale_x = 3.1599998474121094
        row_90C12.scale_y = 1.0
        row_90C12.alignment = 'Expand'.upper()
        row_90C12.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_90C12.label(text='', icon_value=0)
        row_90C12.label(text='', icon_value=0)
        row_90C12.label(text='Version: 1.1.1', icon_value=0)


class SNA_PT_COLORIST_PRO_V111_BCC9C(bpy.types.Panel):
    bl_label = 'Colorist Pro v1.1.1'
    bl_idname = 'SNA_PT_COLORIST_PRO_V111_BCC9C'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorist'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        col_96AA9 = layout.column(heading='', align=False)
        col_96AA9.alert = False
        col_96AA9.enabled = True
        col_96AA9.active = True
        col_96AA9.use_property_split = False
        col_96AA9.use_property_decorate = False
        col_96AA9.scale_x = 1.0
        col_96AA9.scale_y = 1.809999942779541
        col_96AA9.alignment = 'Expand'.upper()
        col_96AA9.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = col_96AA9.operator('sna.enable_colorist_264dc', text='Enable Colorist Pro', icon_value=240, emboss=True, depress=False)
        col_83C4E = layout.column(heading='', align=False)
        col_83C4E.alert = False
        col_83C4E.enabled = True
        col_83C4E.active = True
        col_83C4E.use_property_split = False
        col_83C4E.use_property_decorate = False
        col_83C4E.scale_x = 1.0
        col_83C4E.scale_y = 0.46000003814697266
        col_83C4E.alignment = 'Expand'.upper()
        col_83C4E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_83C4E.label(text='Warning: Enabling Colorist Pro will delete', icon_value=0)
        col_83C4E.label(text='any existing nodes in the compositor', icon_value=0)
        layout.prop(bpy.data.scenes['Scene'], 'use_nodes', text='Use Nodes (Compositor)', icon_value=0, emboss=True)
        row_7A3DF = layout.row(heading='', align=False)
        row_7A3DF.alert = False
        row_7A3DF.enabled = True
        row_7A3DF.active = True
        row_7A3DF.use_property_split = False
        row_7A3DF.use_property_decorate = False
        row_7A3DF.scale_x = 3.1599998474121094
        row_7A3DF.scale_y = 1.0
        row_7A3DF.alignment = 'Expand'.upper()
        row_7A3DF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_7A3DF.label(text='', icon_value=0)
        row_7A3DF.label(text='', icon_value=0)
        row_7A3DF.label(text='Version: 1.1.1', icon_value=0)


class SNA_PT_panel017_B3899(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel017_B3899'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_FLARE_9C407'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_B5F34 = layout.row(heading='', align=False)
        row_B5F34.alert = False
        row_B5F34.enabled = True
        row_B5F34.active = True
        row_B5F34.use_property_split = False
        row_B5F34.use_property_decorate = False
        row_B5F34.scale_x = 0.9700000286102295
        row_B5F34.scale_y = 1.0
        row_B5F34.alignment = 'Expand'.upper()
        row_B5F34.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_B5F34.label(text='Iris Ghost', icon_value=0)
        row_B5F34.separator(factor=1.4500000476837158)
        row_491A4 = row_B5F34.row(heading='', align=False)
        row_491A4.alert = False
        row_491A4.enabled = True
        row_491A4.active = True
        row_491A4.use_property_split = False
        row_491A4.use_property_decorate = False
        row_491A4.scale_x = 0.9599999785423279
        row_491A4.scale_y = 1.0
        row_491A4.alignment = 'Expand'.upper()
        row_491A4.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_491A4.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.029'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=False)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.028'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_F55D0 = layout.box()
        box_F55D0.alert = False
        box_F55D0.enabled = True
        box_F55D0.active = True
        box_F55D0.use_property_split = False
        box_F55D0.use_property_decorate = False
        box_F55D0.alignment = 'Expand'.upper()
        box_F55D0.scale_x = 1.0
        box_F55D0.scale_y = 1.0
        if not True: box_F55D0.operator_context = "EXEC_DEFAULT"
        box_F55D0.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.023'].inputs[0], 'default_value', text='Iris', icon_value=0, emboss=True)
        box_F55D0.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.024'].inputs[0], 'default_value', text='Soften', icon_value=0, emboss=True, slider=True)
        col_8DD9E = box_F55D0.column(heading='', align=True)
        col_8DD9E.alert = False
        col_8DD9E.enabled = True
        col_8DD9E.active = True
        col_8DD9E.use_property_split = False
        col_8DD9E.use_property_decorate = False
        col_8DD9E.scale_x = 1.0
        col_8DD9E.scale_y = 1.0
        col_8DD9E.alignment = 'Expand'.upper()
        col_8DD9E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_8DD9E.prop(bpy.data.node_groups['Lens Flare'].nodes['Group.002'].inputs[1], 'default_value', text='Distortion', icon_value=0, emboss=True)
        col_8DD9E.prop(bpy.data.node_groups['Lens Flare'].nodes['Group.002'].inputs[2], 'default_value', text='Dispersion', icon_value=0, emboss=True)
        col_8DD9E.prop(bpy.data.node_groups['Lens Flare'].nodes['Hue/Saturation/Value.001'].inputs[2], 'default_value', text='Dispersion Saturation', icon_value=0, emboss=True)
        col_98515 = box_F55D0.column(heading='', align=True)
        col_98515.alert = False
        col_98515.enabled = True
        col_98515.active = True
        col_98515.use_property_split = False
        col_98515.use_property_decorate = False
        col_98515.scale_x = 1.0
        col_98515.scale_y = 1.0
        col_98515.alignment = 'Expand'.upper()
        col_98515.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_98515.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_98515.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'color_modulation', text='Color Module', icon_value=0, emboss=True)
        col_98515.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'threshold', text='Threshold', icon_value=0, emboss=True)


class SNA_PT_ghost_97C8D(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_ghost_97C8D'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_59C9A'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_04F7E = layout.row(heading='', align=False)
        row_04F7E.alert = False
        row_04F7E.enabled = True
        row_04F7E.active = True
        row_04F7E.use_property_split = False
        row_04F7E.use_property_decorate = False
        row_04F7E.scale_x = 1.0
        row_04F7E.scale_y = 1.0
        row_04F7E.alignment = 'Expand'.upper()
        row_04F7E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_04F7E.label(text='Ghost', icon_value=0)
        row_04F7E.separator(factor=4.329999923706055)
        row_8D6DC = row_04F7E.row(heading='', align=False)
        row_8D6DC.alert = False
        row_8D6DC.enabled = True
        row_8D6DC.active = True
        row_8D6DC.use_property_split = False
        row_8D6DC.use_property_decorate = False
        row_8D6DC.scale_x = 0.9299999475479126
        row_8D6DC.scale_y = 1.0
        row_8D6DC.alignment = 'Expand'.upper()
        row_8D6DC.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_8D6DC.prop(bpy.data.node_groups['Glares'].nodes['Mix'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.002'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_3DECC = layout.box()
        box_3DECC.alert = False
        box_3DECC.enabled = True
        box_3DECC.active = True
        box_3DECC.use_property_split = False
        box_3DECC.use_property_decorate = False
        box_3DECC.alignment = 'Expand'.upper()
        box_3DECC.scale_x = 1.0
        box_3DECC.scale_y = 1.0
        if not True: box_3DECC.operator_context = "EXEC_DEFAULT"
        col_D72BF = box_3DECC.column(heading='', align=True)
        col_D72BF.alert = False
        col_D72BF.enabled = True
        col_D72BF.active = True
        col_D72BF.use_property_split = False
        col_D72BF.use_property_decorate = False
        col_D72BF.scale_x = 1.0
        col_D72BF.scale_y = 1.0
        col_D72BF.alignment = 'Expand'.upper()
        col_D72BF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_D72BF.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_D72BF.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'color_modulation', text='Color Modulation', icon_value=0, emboss=True, slider=True)
        col_D72BF.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        box_3DECC.prop(bpy.data.node_groups['Glares'].nodes['Blur.001'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True, slider=False)


class SNA_PT_panel005_95AB8(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel005_95AB8'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_59C9A'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_2E4A1 = layout.row(heading='', align=True)
        row_2E4A1.alert = False
        row_2E4A1.enabled = True
        row_2E4A1.active = True
        row_2E4A1.use_property_split = False
        row_2E4A1.use_property_decorate = False
        row_2E4A1.scale_x = 1.0
        row_2E4A1.scale_y = 1.0
        row_2E4A1.alignment = 'Expand'.upper()
        row_2E4A1.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_2E4A1.label(text='Simple Star', icon_value=0)
        row_2E4A1.separator(factor=2.319999933242798)
        row_2F7CD = row_2E4A1.row(heading='', align=False)
        row_2F7CD.alert = False
        row_2F7CD.enabled = True
        row_2F7CD.active = True
        row_2F7CD.use_property_split = False
        row_2F7CD.use_property_decorate = False
        row_2F7CD.scale_x = 0.9299999475479126
        row_2F7CD.scale_y = 1.0
        row_2F7CD.alignment = 'Expand'.upper()
        row_2F7CD.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_2F7CD.prop(bpy.data.node_groups['Glares'].nodes['Mix.008'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.007'].inputs[2], 'default_value', text='Color', icon_value=0, emboss=True)
        box_083C3 = layout.box()
        box_083C3.alert = False
        box_083C3.enabled = True
        box_083C3.active = True
        box_083C3.use_property_split = False
        box_083C3.use_property_decorate = False
        box_083C3.alignment = 'Expand'.upper()
        box_083C3.scale_x = 1.0
        box_083C3.scale_y = 1.0
        if not True: box_083C3.operator_context = "EXEC_DEFAULT"
        col_724DB = box_083C3.column(heading='', align=False)
        col_724DB.alert = False
        col_724DB.enabled = True
        col_724DB.active = True
        col_724DB.use_property_split = False
        col_724DB.use_property_decorate = False
        col_724DB.scale_x = 1.0
        col_724DB.scale_y = 1.0
        col_724DB.alignment = 'Expand'.upper()
        col_724DB.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_724DB.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_724DB.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        col_724DB.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'fade', text='Fade', icon_value=0, emboss=True, slider=True)
        col_724DB.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'use_rotate_45', text='Rotate 45', icon_value=0, emboss=True)
        box_083C3.prop(bpy.data.node_groups['Glares'].nodes['Blur.004'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True)


class SNA_PT_ghost001_5ED67(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_ghost001_5ED67'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_74542'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_1448A = layout.row(heading='', align=False)
        row_1448A.alert = False
        row_1448A.enabled = True
        row_1448A.active = True
        row_1448A.use_property_split = False
        row_1448A.use_property_decorate = False
        row_1448A.scale_x = 1.0
        row_1448A.scale_y = 1.0
        row_1448A.alignment = 'Expand'.upper()
        row_1448A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_1448A.label(text='Ghost', icon_value=0)
        row_1448A.separator(factor=4.329999923706055)
        row_B285C = row_1448A.row(heading='', align=False)
        row_B285C.alert = False
        row_B285C.enabled = True
        row_B285C.active = True
        row_B285C.use_property_split = False
        row_B285C.use_property_decorate = False
        row_B285C.scale_x = 0.9299999475479126
        row_B285C.scale_y = 1.0
        row_B285C.alignment = 'Expand'.upper()
        row_B285C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_B285C.prop(bpy.data.node_groups['Glares'].nodes['Mix'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.002'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_A0519 = layout.box()
        box_A0519.alert = False
        box_A0519.enabled = True
        box_A0519.active = True
        box_A0519.use_property_split = False
        box_A0519.use_property_decorate = False
        box_A0519.alignment = 'Expand'.upper()
        box_A0519.scale_x = 1.0
        box_A0519.scale_y = 1.0
        if not True: box_A0519.operator_context = "EXEC_DEFAULT"
        col_1FF6C = box_A0519.column(heading='', align=True)
        col_1FF6C.alert = False
        col_1FF6C.enabled = True
        col_1FF6C.active = True
        col_1FF6C.use_property_split = False
        col_1FF6C.use_property_decorate = False
        col_1FF6C.scale_x = 1.0
        col_1FF6C.scale_y = 1.0
        col_1FF6C.alignment = 'Expand'.upper()
        col_1FF6C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_1FF6C.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_1FF6C.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'color_modulation', text='Color Modulation', icon_value=0, emboss=True, slider=True)
        col_1FF6C.prop(bpy.data.node_groups['Glares'].nodes['Glare'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        box_A0519.prop(bpy.data.node_groups['Glares'].nodes['Blur.001'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True, slider=False)


class SNA_PT_panel029_16DD7(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel029_16DD7'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_74542'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_261EF = layout.row(heading='', align=True)
        row_261EF.alert = False
        row_261EF.enabled = True
        row_261EF.active = True
        row_261EF.use_property_split = False
        row_261EF.use_property_decorate = False
        row_261EF.scale_x = 1.0
        row_261EF.scale_y = 1.0
        row_261EF.alignment = 'Expand'.upper()
        row_261EF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_261EF.label(text='Simple Star', icon_value=0)
        row_261EF.separator(factor=2.319999933242798)
        row_F9C69 = row_261EF.row(heading='', align=False)
        row_F9C69.alert = False
        row_F9C69.enabled = True
        row_F9C69.active = True
        row_F9C69.use_property_split = False
        row_F9C69.use_property_decorate = False
        row_F9C69.scale_x = 0.9299999475479126
        row_F9C69.scale_y = 1.0
        row_F9C69.alignment = 'Expand'.upper()
        row_F9C69.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_F9C69.prop(bpy.data.node_groups['Glares'].nodes['Mix.008'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.007'].inputs[2], 'default_value', text='Color', icon_value=0, emboss=True)
        box_00565 = layout.box()
        box_00565.alert = False
        box_00565.enabled = True
        box_00565.active = True
        box_00565.use_property_split = False
        box_00565.use_property_decorate = False
        box_00565.alignment = 'Expand'.upper()
        box_00565.scale_x = 1.0
        box_00565.scale_y = 1.0
        if not True: box_00565.operator_context = "EXEC_DEFAULT"
        col_B4353 = box_00565.column(heading='', align=False)
        col_B4353.alert = False
        col_B4353.enabled = True
        col_B4353.active = True
        col_B4353.use_property_split = False
        col_B4353.use_property_decorate = False
        col_B4353.scale_x = 1.0
        col_B4353.scale_y = 1.0
        col_B4353.alignment = 'Expand'.upper()
        col_B4353.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_B4353.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_B4353.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        col_B4353.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'fade', text='Fade', icon_value=0, emboss=True, slider=True)
        col_B4353.prop(bpy.data.node_groups['Glares'].nodes['Glare.003'], 'use_rotate_45', text='Rotate 45', icon_value=0, emboss=True)
        box_00565.prop(bpy.data.node_groups['Glares'].nodes['Blur.004'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True)


class SNA_PT_panel030_AB64D(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel030_AB64D'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_74542'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_6A93D = layout.row(heading='', align=False)
        row_6A93D.alert = False
        row_6A93D.enabled = True
        row_6A93D.active = True
        row_6A93D.use_property_split = False
        row_6A93D.use_property_decorate = False
        row_6A93D.scale_x = 1.0
        row_6A93D.scale_y = 1.0
        row_6A93D.alignment = 'Expand'.upper()
        row_6A93D.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_6A93D.label(text='Streaks', icon_value=0)
        row_6A93D.separator(factor=2.9799997806549072)
        row_2E7AE = row_6A93D.row(heading='', align=False)
        row_2E7AE.alert = False
        row_2E7AE.enabled = True
        row_2E7AE.active = True
        row_2E7AE.use_property_split = False
        row_2E7AE.use_property_decorate = False
        row_2E7AE.scale_x = 0.9299999475479126
        row_2E7AE.scale_y = 1.0
        row_2E7AE.alignment = 'Expand'.upper()
        row_2E7AE.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_2E7AE.prop(bpy.data.node_groups['Glares'].nodes['Mix.004'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.003'].inputs[2], 'default_value', text='Color', icon_value=0, emboss=True)
        box_58A0A = layout.box()
        box_58A0A.alert = False
        box_58A0A.enabled = True
        box_58A0A.active = True
        box_58A0A.use_property_split = False
        box_58A0A.use_property_decorate = False
        box_58A0A.alignment = 'Expand'.upper()
        box_58A0A.scale_x = 1.0
        box_58A0A.scale_y = 1.0
        if not True: box_58A0A.operator_context = "EXEC_DEFAULT"
        col_AD189 = box_58A0A.column(heading='', align=True)
        col_AD189.alert = False
        col_AD189.enabled = True
        col_AD189.active = True
        col_AD189.use_property_split = False
        col_AD189.use_property_decorate = True
        col_AD189.scale_x = 1.0
        col_AD189.scale_y = 1.0
        col_AD189.alignment = 'Expand'.upper()
        col_AD189.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_AD189.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_AD189.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'color_modulation', text='Color Modulation', icon_value=0, emboss=True, slider=True)
        col_AD189.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        col_AD189.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'streaks', text='Streaks', icon_value=0, emboss=True)
        col_AD189.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'angle_offset', text='Angle Offset', icon_value=0, emboss=True)
        col_AD189.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'fade', text='Fade', icon_value=0, emboss=True, slider=True)
        box_58A0A.prop(bpy.data.node_groups['Glares'].nodes['Blur.002'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True)


class SNA_PT_panel031_34A85(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel031_34A85'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_74542'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_E21C3 = layout.row(heading='', align=False)
        row_E21C3.alert = False
        row_E21C3.enabled = True
        row_E21C3.active = True
        row_E21C3.use_property_split = False
        row_E21C3.use_property_decorate = False
        row_E21C3.scale_x = 1.0
        row_E21C3.scale_y = 1.0
        row_E21C3.alignment = 'Expand'.upper()
        row_E21C3.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_E21C3.label(text='Fog Glow', icon_value=0)
        row_E21C3.separator(factor=1.2699999809265137)
        row_276C0 = row_E21C3.row(heading='', align=False)
        row_276C0.alert = False
        row_276C0.enabled = True
        row_276C0.active = True
        row_276C0.use_property_split = False
        row_276C0.use_property_decorate = False
        row_276C0.scale_x = 0.9299999475479126
        row_276C0.scale_y = 1.0
        row_276C0.alignment = 'Expand'.upper()
        row_276C0.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_276C0.prop(bpy.data.node_groups['Glares'].nodes['Mix.006'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare.002'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.005'].inputs[2], 'default_value', text='Color', icon_value=0, emboss=True)
        box_89813 = layout.box()
        box_89813.alert = False
        box_89813.enabled = True
        box_89813.active = True
        box_89813.use_property_split = False
        box_89813.use_property_decorate = False
        box_89813.alignment = 'Expand'.upper()
        box_89813.scale_x = 1.0
        box_89813.scale_y = 1.0
        if not True: box_89813.operator_context = "EXEC_DEFAULT"
        col_88171 = box_89813.column(heading='', align=True)
        col_88171.alert = False
        col_88171.enabled = True
        col_88171.active = True
        col_88171.use_property_split = False
        col_88171.use_property_decorate = False
        col_88171.scale_x = 1.0
        col_88171.scale_y = 1.0
        col_88171.alignment = 'Expand'.upper()
        col_88171.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_88171.prop(bpy.data.node_groups['Glares'].nodes['Glare.002'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        col_88171.prop(bpy.data.node_groups['Glares'].nodes['Glare.002'], 'size', text='Size', icon_value=0, emboss=True)
        box_89813.prop(bpy.data.node_groups['Glares'].nodes['Blur.003'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True)


class SNA_PT_WET_LENS_0D64E(bpy.types.Panel):
    bl_label = 'Wet Lens'
    bl_idname = 'SNA_PT_WET_LENS_0D64E'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_DIRT_5A957'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_A3284 = layout.row(heading='', align=True)
        row_A3284.alert = False
        row_A3284.enabled = True
        row_A3284.active = True
        row_A3284.use_property_split = False
        row_A3284.use_property_decorate = False
        row_A3284.scale_x = 1.0
        row_A3284.scale_y = 1.8399999141693115
        row_A3284.alignment = 'Expand'.upper()
        row_A3284.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_A3284.operator('sna.operator005_39b40', text='Make It Wet!', icon_value=470, emboss=True, depress=False)
        op = row_A3284.operator('sna.operator006_2227b', text='Dry It!', icon_value=299, emboss=True, depress=False)
        box_7BA66 = layout.box()
        box_7BA66.alert = False
        box_7BA66.enabled = True
        box_7BA66.active = True
        box_7BA66.use_property_split = False
        box_7BA66.use_property_decorate = False
        box_7BA66.alignment = 'Expand'.upper()
        box_7BA66.scale_x = 1.0
        box_7BA66.scale_y = 1.0
        if not True: box_7BA66.operator_context = "EXEC_DEFAULT"
        col_1C6A6 = box_7BA66.column(heading='', align=False)
        col_1C6A6.alert = False
        col_1C6A6.enabled = True
        col_1C6A6.active = True
        col_1C6A6.use_property_split = False
        col_1C6A6.use_property_decorate = False
        col_1C6A6.scale_x = 1.0
        col_1C6A6.scale_y = 1.0
        col_1C6A6.alignment = 'Expand'.upper()
        col_1C6A6.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_1C6A6.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.006'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)


class SNA_PT_WET_LENS_2A174(bpy.types.Panel):
    bl_label = 'Wet Lens'
    bl_idname = 'SNA_PT_WET_LENS_2A174'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_DIRT_D38EB'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row_78260 = layout.row(heading='', align=True)
        row_78260.alert = False
        row_78260.enabled = True
        row_78260.active = True
        row_78260.use_property_split = False
        row_78260.use_property_decorate = False
        row_78260.scale_x = 1.0
        row_78260.scale_y = 1.8399999141693115
        row_78260.alignment = 'Expand'.upper()
        row_78260.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_78260.operator('sna.operator005_39b40', text='Make It Wet!', icon_value=470, emboss=True, depress=False)
        op = row_78260.operator('sna.operator006_2227b', text='Dry It!', icon_value=299, emboss=True, depress=False)
        box_C647F = layout.box()
        box_C647F.alert = False
        box_C647F.enabled = True
        box_C647F.active = True
        box_C647F.use_property_split = False
        box_C647F.use_property_decorate = False
        box_C647F.alignment = 'Expand'.upper()
        box_C647F.scale_x = 1.0
        box_C647F.scale_y = 1.0
        if not True: box_C647F.operator_context = "EXEC_DEFAULT"
        col_4BD22 = box_C647F.column(heading='', align=False)
        col_4BD22.alert = False
        col_4BD22.enabled = True
        col_4BD22.active = True
        col_4BD22.use_property_split = False
        col_4BD22.use_property_decorate = False
        col_4BD22.scale_x = 1.0
        col_4BD22.scale_y = 1.0
        col_4BD22.alignment = 'Expand'.upper()
        col_4BD22.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_4BD22.prop(bpy.data.node_groups['Lens Dirt'].nodes['Mix.006'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)


class SNA_PT_panel026_B0DA7(bpy.types.Panel):
    bl_label = '4:3'
    bl_idname = 'SNA_PT_panel026_B0DA7'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_4245E'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_29021 = layout.box()
        box_29021.alert = False
        box_29021.enabled = True
        box_29021.active = True
        box_29021.use_property_split = False
        box_29021.use_property_decorate = False
        box_29021.alignment = 'Expand'.upper()
        box_29021.scale_x = 1.0
        box_29021.scale_y = 1.0
        if not True: box_29021.operator_context = "EXEC_DEFAULT"
        row_1385B = box_29021.row(heading='', align=False)
        row_1385B.alert = False
        row_1385B.enabled = True
        row_1385B.active = True
        row_1385B.use_property_split = False
        row_1385B.use_property_decorate = False
        row_1385B.scale_x = 1.0
        row_1385B.scale_y = 1.5
        row_1385B.alignment = 'Expand'.upper()
        row_1385B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_1385B.operator('sna.operator021_564c0', text='4:3 4K', icon_value=0, emboss=True, depress=False)
        row_74CCD = box_29021.row(heading='', align=False)
        row_74CCD.alert = False
        row_74CCD.enabled = True
        row_74CCD.active = True
        row_74CCD.use_property_split = False
        row_74CCD.use_property_decorate = False
        row_74CCD.scale_x = 1.0
        row_74CCD.scale_y = 1.5
        row_74CCD.alignment = 'Expand'.upper()
        row_74CCD.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_74CCD.operator('sna.operator022_b4eef', text='4:3 720p', icon_value=0, emboss=True, depress=False)
        op = row_74CCD.operator('sna.operator014_71654', text='4:3 1080p', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel022_FB574(bpy.types.Panel):
    bl_label = '16:9'
    bl_idname = 'SNA_PT_panel022_FB574'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_4245E'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_5DFB8 = layout.box()
        box_5DFB8.alert = False
        box_5DFB8.enabled = True
        box_5DFB8.active = True
        box_5DFB8.use_property_split = False
        box_5DFB8.use_property_decorate = False
        box_5DFB8.alignment = 'Expand'.upper()
        box_5DFB8.scale_x = 1.0
        box_5DFB8.scale_y = 1.0
        if not True: box_5DFB8.operator_context = "EXEC_DEFAULT"
        row_F4F67 = box_5DFB8.row(heading='', align=False)
        row_F4F67.alert = False
        row_F4F67.enabled = True
        row_F4F67.active = True
        row_F4F67.use_property_split = False
        row_F4F67.use_property_decorate = False
        row_F4F67.scale_x = 1.0
        row_F4F67.scale_y = 1.5
        row_F4F67.alignment = 'Expand'.upper()
        row_F4F67.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_F4F67.operator('sna.operator007_c2369', text='16:9 1080p', icon_value=0, emboss=True, depress=False)
        op = row_F4F67.operator('sna.operator008_2c684', text='16:9 4K', icon_value=0, emboss=True, depress=False)
        row_0B4F0 = box_5DFB8.row(heading='', align=False)
        row_0B4F0.alert = False
        row_0B4F0.enabled = True
        row_0B4F0.active = True
        row_0B4F0.use_property_split = False
        row_0B4F0.use_property_decorate = False
        row_0B4F0.scale_x = 1.0
        row_0B4F0.scale_y = 1.5
        row_0B4F0.alignment = 'Expand'.upper()
        row_0B4F0.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_0B4F0.operator('sna.operator009_1aa7a', text='16:9 720p', icon_value=0, emboss=True, depress=False)
        op = row_0B4F0.operator('sna.operator010_d86fc', text='16:9 480p', icon_value=0, emboss=True, depress=False)


class SNA_PT_SOCIAL_MEDIA_DFA8C(bpy.types.Panel):
    bl_label = 'Social Media'
    bl_idname = 'SNA_PT_SOCIAL_MEDIA_DFA8C'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_4245E'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_FBA7F = layout.box()
        box_FBA7F.alert = False
        box_FBA7F.enabled = True
        box_FBA7F.active = True
        box_FBA7F.use_property_split = False
        box_FBA7F.use_property_decorate = False
        box_FBA7F.alignment = 'Expand'.upper()
        box_FBA7F.scale_x = 1.0
        box_FBA7F.scale_y = 1.0
        if not True: box_FBA7F.operator_context = "EXEC_DEFAULT"
        row_48CD9 = box_FBA7F.row(heading='', align=False)
        row_48CD9.alert = False
        row_48CD9.enabled = True
        row_48CD9.active = True
        row_48CD9.use_property_split = False
        row_48CD9.use_property_decorate = False
        row_48CD9.scale_x = 1.0
        row_48CD9.scale_y = 1.5
        row_48CD9.alignment = 'Expand'.upper()
        row_48CD9.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_48CD9.operator('sna.operator011_325e9', text='Insta Square 1:1', icon_value=0, emboss=True, depress=False)
        op = row_48CD9.operator('sna.operator012_a483c', text='Insta Vertical 4:5', icon_value=0, emboss=True, depress=False)
        row_C3018 = box_FBA7F.row(heading='', align=False)
        row_C3018.alert = False
        row_C3018.enabled = True
        row_C3018.active = True
        row_C3018.use_property_split = False
        row_C3018.use_property_decorate = False
        row_C3018.scale_x = 1.0
        row_C3018.scale_y = 1.5
        row_C3018.alignment = 'Expand'.upper()
        row_C3018.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_C3018.operator('sna.operator013_19b92', text='Insta Reels/Tiktok 9:16', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel024_27A4E(bpy.types.Panel):
    bl_label = '2.35:1'
    bl_idname = 'SNA_PT_panel024_27A4E'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_4245E'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_76EFF = layout.box()
        box_76EFF.alert = False
        box_76EFF.enabled = True
        box_76EFF.active = True
        box_76EFF.use_property_split = False
        box_76EFF.use_property_decorate = False
        box_76EFF.alignment = 'Expand'.upper()
        box_76EFF.scale_x = 1.0
        box_76EFF.scale_y = 1.0
        if not True: box_76EFF.operator_context = "EXEC_DEFAULT"
        row_FAF4C = box_76EFF.row(heading='', align=False)
        row_FAF4C.alert = False
        row_FAF4C.enabled = True
        row_FAF4C.active = True
        row_FAF4C.use_property_split = False
        row_FAF4C.use_property_decorate = False
        row_FAF4C.scale_x = 1.0
        row_FAF4C.scale_y = 1.5
        row_FAF4C.alignment = 'Expand'.upper()
        row_FAF4C.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_FAF4C.operator('sna.operator016_29794', text='2.35:1 4K', icon_value=0, emboss=True, depress=False)
        row_EABB6 = box_76EFF.row(heading='', align=False)
        row_EABB6.alert = False
        row_EABB6.enabled = True
        row_EABB6.active = True
        row_EABB6.use_property_split = False
        row_EABB6.use_property_decorate = False
        row_EABB6.scale_x = 1.0
        row_EABB6.scale_y = 1.5
        row_EABB6.alignment = 'Expand'.upper()
        row_EABB6.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_EABB6.operator('sna.operator017_cf146', text='2.35:1 720p', icon_value=0, emboss=True, depress=False)
        op = row_EABB6.operator('sna.operator015_aea69', text='2.35:1 1080p', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel025_32F65(bpy.types.Panel):
    bl_label = '1.85:1'
    bl_idname = 'SNA_PT_panel025_32F65'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_4245E'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_F486B = layout.box()
        box_F486B.alert = False
        box_F486B.enabled = True
        box_F486B.active = True
        box_F486B.use_property_split = False
        box_F486B.use_property_decorate = False
        box_F486B.alignment = 'Expand'.upper()
        box_F486B.scale_x = 1.0
        box_F486B.scale_y = 1.0
        if not True: box_F486B.operator_context = "EXEC_DEFAULT"
        row_2F416 = box_F486B.row(heading='', align=False)
        row_2F416.alert = False
        row_2F416.enabled = True
        row_2F416.active = True
        row_2F416.use_property_split = False
        row_2F416.use_property_decorate = False
        row_2F416.scale_x = 1.0
        row_2F416.scale_y = 1.5
        row_2F416.alignment = 'Expand'.upper()
        row_2F416.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_2F416.operator('sna.operator018_e9c55', text='1.85:1 4K', icon_value=0, emboss=True, depress=False)
        row_F4413 = box_F486B.row(heading='', align=False)
        row_F4413.alert = False
        row_F4413.enabled = True
        row_F4413.active = True
        row_F4413.use_property_split = False
        row_F4413.use_property_decorate = False
        row_F4413.scale_x = 1.0
        row_F4413.scale_y = 1.5
        row_F4413.alignment = 'Expand'.upper()
        row_F4413.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_F4413.operator('sna.operator019_b1ef3', text='1.85:1 720p', icon_value=0, emboss=True, depress=False)
        op = row_F4413.operator('sna.operator020_7a6a7', text='1.85:1 1080p', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel038_03BC6(bpy.types.Panel):
    bl_label = '4:3'
    bl_idname = 'SNA_PT_panel038_03BC6'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_BAC29 = layout.box()
        box_BAC29.alert = False
        box_BAC29.enabled = True
        box_BAC29.active = True
        box_BAC29.use_property_split = False
        box_BAC29.use_property_decorate = False
        box_BAC29.alignment = 'Expand'.upper()
        box_BAC29.scale_x = 1.0
        box_BAC29.scale_y = 1.0
        if not True: box_BAC29.operator_context = "EXEC_DEFAULT"
        row_E6882 = box_BAC29.row(heading='', align=False)
        row_E6882.alert = False
        row_E6882.enabled = True
        row_E6882.active = True
        row_E6882.use_property_split = False
        row_E6882.use_property_decorate = False
        row_E6882.scale_x = 1.0
        row_E6882.scale_y = 1.5
        row_E6882.alignment = 'Expand'.upper()
        row_E6882.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_E6882.operator('sna.operator021_564c0', text='4:3 4K', icon_value=0, emboss=True, depress=False)
        row_2B062 = box_BAC29.row(heading='', align=False)
        row_2B062.alert = False
        row_2B062.enabled = True
        row_2B062.active = True
        row_2B062.use_property_split = False
        row_2B062.use_property_decorate = False
        row_2B062.scale_x = 1.0
        row_2B062.scale_y = 1.5
        row_2B062.alignment = 'Expand'.upper()
        row_2B062.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_2B062.operator('sna.operator022_b4eef', text='4:3 720p', icon_value=0, emboss=True, depress=False)
        op = row_2B062.operator('sna.operator014_71654', text='4:3 1080p', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel039_B1C6B(bpy.types.Panel):
    bl_label = '16:9'
    bl_idname = 'SNA_PT_panel039_B1C6B'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_14C6F = layout.box()
        box_14C6F.alert = False
        box_14C6F.enabled = True
        box_14C6F.active = True
        box_14C6F.use_property_split = False
        box_14C6F.use_property_decorate = False
        box_14C6F.alignment = 'Expand'.upper()
        box_14C6F.scale_x = 1.0
        box_14C6F.scale_y = 1.0
        if not True: box_14C6F.operator_context = "EXEC_DEFAULT"
        row_A8F36 = box_14C6F.row(heading='', align=False)
        row_A8F36.alert = False
        row_A8F36.enabled = True
        row_A8F36.active = True
        row_A8F36.use_property_split = False
        row_A8F36.use_property_decorate = False
        row_A8F36.scale_x = 1.0
        row_A8F36.scale_y = 1.5
        row_A8F36.alignment = 'Expand'.upper()
        row_A8F36.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_A8F36.operator('sna.operator007_c2369', text='16:9 1080p', icon_value=0, emboss=True, depress=False)
        op = row_A8F36.operator('sna.operator008_2c684', text='16:9 4K', icon_value=0, emboss=True, depress=False)
        row_36DFC = box_14C6F.row(heading='', align=False)
        row_36DFC.alert = False
        row_36DFC.enabled = True
        row_36DFC.active = True
        row_36DFC.use_property_split = False
        row_36DFC.use_property_decorate = False
        row_36DFC.scale_x = 1.0
        row_36DFC.scale_y = 1.5
        row_36DFC.alignment = 'Expand'.upper()
        row_36DFC.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_36DFC.operator('sna.operator009_1aa7a', text='16:9 720p', icon_value=0, emboss=True, depress=False)
        op = row_36DFC.operator('sna.operator010_d86fc', text='16:9 480p', icon_value=0, emboss=True, depress=False)


class SNA_PT_SOCIAL_MEDIA_DC603(bpy.types.Panel):
    bl_label = 'Social Media'
    bl_idname = 'SNA_PT_SOCIAL_MEDIA_DC603'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_CE025 = layout.box()
        box_CE025.alert = False
        box_CE025.enabled = True
        box_CE025.active = True
        box_CE025.use_property_split = False
        box_CE025.use_property_decorate = False
        box_CE025.alignment = 'Expand'.upper()
        box_CE025.scale_x = 1.0
        box_CE025.scale_y = 1.0
        if not True: box_CE025.operator_context = "EXEC_DEFAULT"
        row_6D98E = box_CE025.row(heading='', align=False)
        row_6D98E.alert = False
        row_6D98E.enabled = True
        row_6D98E.active = True
        row_6D98E.use_property_split = False
        row_6D98E.use_property_decorate = False
        row_6D98E.scale_x = 1.0
        row_6D98E.scale_y = 1.5
        row_6D98E.alignment = 'Expand'.upper()
        row_6D98E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_6D98E.operator('sna.operator011_325e9', text='Insta Square 1:1', icon_value=0, emboss=True, depress=False)
        op = row_6D98E.operator('sna.operator012_a483c', text='Insta Vertical 4:5', icon_value=0, emboss=True, depress=False)
        row_964BE = box_CE025.row(heading='', align=False)
        row_964BE.alert = False
        row_964BE.enabled = True
        row_964BE.active = True
        row_964BE.use_property_split = False
        row_964BE.use_property_decorate = False
        row_964BE.scale_x = 1.0
        row_964BE.scale_y = 1.5
        row_964BE.alignment = 'Expand'.upper()
        row_964BE.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_964BE.operator('sna.operator013_19b92', text='Insta Reels/Tiktok 9:16', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel041_1FC6C(bpy.types.Panel):
    bl_label = '2.35:1'
    bl_idname = 'SNA_PT_panel041_1FC6C'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_CC918 = layout.box()
        box_CC918.alert = False
        box_CC918.enabled = True
        box_CC918.active = True
        box_CC918.use_property_split = False
        box_CC918.use_property_decorate = False
        box_CC918.alignment = 'Expand'.upper()
        box_CC918.scale_x = 1.0
        box_CC918.scale_y = 1.0
        if not True: box_CC918.operator_context = "EXEC_DEFAULT"
        row_26024 = box_CC918.row(heading='', align=False)
        row_26024.alert = False
        row_26024.enabled = True
        row_26024.active = True
        row_26024.use_property_split = False
        row_26024.use_property_decorate = False
        row_26024.scale_x = 1.0
        row_26024.scale_y = 1.5
        row_26024.alignment = 'Expand'.upper()
        row_26024.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_26024.operator('sna.operator016_29794', text='2.35:1 4K', icon_value=0, emboss=True, depress=False)
        row_93C45 = box_CC918.row(heading='', align=False)
        row_93C45.alert = False
        row_93C45.enabled = True
        row_93C45.active = True
        row_93C45.use_property_split = False
        row_93C45.use_property_decorate = False
        row_93C45.scale_x = 1.0
        row_93C45.scale_y = 1.5
        row_93C45.alignment = 'Expand'.upper()
        row_93C45.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_93C45.operator('sna.operator017_cf146', text='2.35:1 720p', icon_value=0, emboss=True, depress=False)
        op = row_93C45.operator('sna.operator015_aea69', text='2.35:1 1080p', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel042_5FAD5(bpy.types.Panel):
    bl_label = '1.85:1'
    bl_idname = 'SNA_PT_panel042_5FAD5'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        box_7B019 = layout.box()
        box_7B019.alert = False
        box_7B019.enabled = True
        box_7B019.active = True
        box_7B019.use_property_split = False
        box_7B019.use_property_decorate = False
        box_7B019.alignment = 'Expand'.upper()
        box_7B019.scale_x = 1.0
        box_7B019.scale_y = 1.0
        if not True: box_7B019.operator_context = "EXEC_DEFAULT"
        row_C6584 = box_7B019.row(heading='', align=False)
        row_C6584.alert = False
        row_C6584.enabled = True
        row_C6584.active = True
        row_C6584.use_property_split = False
        row_C6584.use_property_decorate = False
        row_C6584.scale_x = 1.0
        row_C6584.scale_y = 1.5
        row_C6584.alignment = 'Expand'.upper()
        row_C6584.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_C6584.operator('sna.operator018_e9c55', text='1.85:1 4K', icon_value=0, emboss=True, depress=False)
        row_7C8F1 = box_7B019.row(heading='', align=False)
        row_7C8F1.alert = False
        row_7C8F1.enabled = True
        row_7C8F1.active = True
        row_7C8F1.use_property_split = False
        row_7C8F1.use_property_decorate = False
        row_7C8F1.scale_x = 1.0
        row_7C8F1.scale_y = 1.5
        row_7C8F1.alignment = 'Expand'.upper()
        row_7C8F1.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_7C8F1.operator('sna.operator019_b1ef3', text='1.85:1 720p', icon_value=0, emboss=True, depress=False)
        op = row_7C8F1.operator('sna.operator020_7a6a7', text='1.85:1 1080p', icon_value=0, emboss=True, depress=False)


class SNA_PT_panel003_2D3AF(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel003_2D3AF'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_59C9A'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_7944B = layout.row(heading='', align=False)
        row_7944B.alert = False
        row_7944B.enabled = True
        row_7944B.active = True
        row_7944B.use_property_split = False
        row_7944B.use_property_decorate = False
        row_7944B.scale_x = 1.0
        row_7944B.scale_y = 1.0
        row_7944B.alignment = 'Expand'.upper()
        row_7944B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_7944B.label(text='Streaks', icon_value=0)
        row_7944B.separator(factor=2.9799997806549072)
        row_96B7B = row_7944B.row(heading='', align=False)
        row_96B7B.alert = False
        row_96B7B.enabled = True
        row_96B7B.active = True
        row_96B7B.use_property_split = False
        row_96B7B.use_property_decorate = False
        row_96B7B.scale_x = 0.9299999475479126
        row_96B7B.scale_y = 1.0
        row_96B7B.alignment = 'Expand'.upper()
        row_96B7B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_96B7B.prop(bpy.data.node_groups['Glares'].nodes['Mix.004'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.003'].inputs[2], 'default_value', text='Color', icon_value=0, emboss=True)
        box_1FBF0 = layout.box()
        box_1FBF0.alert = False
        box_1FBF0.enabled = True
        box_1FBF0.active = True
        box_1FBF0.use_property_split = False
        box_1FBF0.use_property_decorate = False
        box_1FBF0.alignment = 'Expand'.upper()
        box_1FBF0.scale_x = 1.0
        box_1FBF0.scale_y = 1.0
        if not True: box_1FBF0.operator_context = "EXEC_DEFAULT"
        col_15E77 = box_1FBF0.column(heading='', align=True)
        col_15E77.alert = False
        col_15E77.enabled = True
        col_15E77.active = True
        col_15E77.use_property_split = False
        col_15E77.use_property_decorate = True
        col_15E77.scale_x = 1.0
        col_15E77.scale_y = 1.0
        col_15E77.alignment = 'Expand'.upper()
        col_15E77.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_15E77.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_15E77.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'color_modulation', text='Color Modulation', icon_value=0, emboss=True, slider=True)
        col_15E77.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        col_15E77.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'streaks', text='Streaks', icon_value=0, emboss=True)
        col_15E77.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'angle_offset', text='Angle Offset', icon_value=0, emboss=True)
        col_15E77.prop(bpy.data.node_groups['Glares'].nodes['Glare.001'], 'fade', text='Fade', icon_value=0, emboss=True, slider=True)
        box_1FBF0.prop(bpy.data.node_groups['Glares'].nodes['Blur.002'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True)


class SNA_PT_panel004_665CF(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel004_665CF'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_GLARE_59C9A'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_D0F38 = layout.row(heading='', align=False)
        row_D0F38.alert = False
        row_D0F38.enabled = True
        row_D0F38.active = True
        row_D0F38.use_property_split = False
        row_D0F38.use_property_decorate = False
        row_D0F38.scale_x = 1.0
        row_D0F38.scale_y = 1.0
        row_D0F38.alignment = 'Expand'.upper()
        row_D0F38.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_D0F38.label(text='Fog Glow', icon_value=0)
        row_D0F38.separator(factor=1.2699999809265137)
        row_698B8 = row_D0F38.row(heading='', align=False)
        row_698B8.alert = False
        row_698B8.enabled = True
        row_698B8.active = True
        row_698B8.use_property_split = False
        row_698B8.use_property_decorate = False
        row_698B8.scale_x = 0.9299999475479126
        row_698B8.scale_y = 1.0
        row_698B8.alignment = 'Expand'.upper()
        row_698B8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_698B8.prop(bpy.data.node_groups['Glares'].nodes['Mix.006'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Glares'].nodes['Glare.002'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Glares'].nodes['Mix.005'].inputs[2], 'default_value', text='Color', icon_value=0, emboss=True)
        box_A258B = layout.box()
        box_A258B.alert = False
        box_A258B.enabled = True
        box_A258B.active = True
        box_A258B.use_property_split = False
        box_A258B.use_property_decorate = False
        box_A258B.alignment = 'Expand'.upper()
        box_A258B.scale_x = 1.0
        box_A258B.scale_y = 1.0
        if not True: box_A258B.operator_context = "EXEC_DEFAULT"
        col_D37DB = box_A258B.column(heading='', align=True)
        col_D37DB.alert = False
        col_D37DB.enabled = True
        col_D37DB.active = True
        col_D37DB.use_property_split = False
        col_D37DB.use_property_decorate = False
        col_D37DB.scale_x = 1.0
        col_D37DB.scale_y = 1.0
        col_D37DB.alignment = 'Expand'.upper()
        col_D37DB.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_D37DB.prop(bpy.data.node_groups['Glares'].nodes['Glare.002'], 'threshold', text='Threshold', icon_value=0, emboss=True)
        col_D37DB.prop(bpy.data.node_groups['Glares'].nodes['Glare.002'], 'size', text='Size', icon_value=0, emboss=True)
        box_A258B.prop(bpy.data.node_groups['Glares'].nodes['Blur.003'].inputs[1], 'default_value', text='Blur', icon_value=0, emboss=True)


class SNA_PT_panel012_CC8A4(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel012_CC8A4'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_69921'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_E03C6 = layout.row(heading='', align=False)
        row_E03C6.alert = False
        row_E03C6.enabled = True
        row_E03C6.active = True
        row_E03C6.use_property_split = False
        row_E03C6.use_property_decorate = False
        row_E03C6.scale_x = 1.0
        row_E03C6.scale_y = 1.0
        row_E03C6.alignment = 'Expand'.upper()
        row_E03C6.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_E03C6.label(text='Halation', icon_value=0)
        row_E03C6.separator(factor=2.140000104904175)
        row_C0DC4 = row_E03C6.row(heading='', align=False)
        row_C0DC4.alert = False
        row_C0DC4.enabled = True
        row_C0DC4.active = True
        row_C0DC4.use_property_split = False
        row_C0DC4.use_property_decorate = False
        row_C0DC4.scale_x = 0.8999999761581421
        row_C0DC4.scale_y = 1.0
        row_C0DC4.alignment = 'Expand'.upper()
        row_C0DC4.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_C0DC4.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[3], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=True)

    def draw(self, context):
        layout = self.layout
        col_8B31B = layout.column(heading='', align=True)
        col_8B31B.alert = False
        col_8B31B.enabled = True
        col_8B31B.active = True
        col_8B31B.use_property_split = False
        col_8B31B.use_property_decorate = False
        col_8B31B.scale_x = 1.0
        col_8B31B.scale_y = 1.0
        col_8B31B.alignment = 'Expand'.upper()
        col_8B31B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_8B31B.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[5], 'default_value', text='Glow', icon_value=0, emboss=True)
        col_8B31B.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[6], 'default_value', text='Threshold', icon_value=0, emboss=True)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[4], 'default_value', text='Green Channel', icon_value=0, emboss=True, slider=True)
        col_0846F = layout.column(heading='', align=True)
        col_0846F.alert = False
        col_0846F.enabled = True
        col_0846F.active = True
        col_0846F.use_property_split = False
        col_0846F.use_property_decorate = False
        col_0846F.scale_x = 1.0
        col_0846F.scale_y = 1.0
        col_0846F.alignment = 'Expand'.upper()
        col_0846F.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_0846F.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[7], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_0846F.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[8], 'default_value', text='Saturation', icon_value=0, emboss=True)


class SNA_PT_panel_E701A(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel_E701A'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_69921'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='Lens Distortion', icon_value=0)

    def draw(self, context):
        layout = self.layout
        box_A9FDC = layout.box()
        box_A9FDC.alert = False
        box_A9FDC.enabled = True
        box_A9FDC.active = True
        box_A9FDC.use_property_split = False
        box_A9FDC.use_property_decorate = False
        box_A9FDC.alignment = 'Expand'.upper()
        box_A9FDC.scale_x = 1.0
        box_A9FDC.scale_y = 1.0
        if not True: box_A9FDC.operator_context = "EXEC_DEFAULT"
        col_FB565 = box_A9FDC.column(heading='', align=True)
        col_FB565.alert = False
        col_FB565.enabled = True
        col_FB565.active = True
        col_FB565.use_property_split = False
        col_FB565.use_property_decorate = False
        col_FB565.scale_x = 1.0
        col_FB565.scale_y = 1.0
        col_FB565.alignment = 'Expand'.upper()
        col_FB565.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_FB565.prop(bpy.data.node_groups['Film Emulation'].nodes['Lens Distortion'], 'use_projector', text='Projector', icon_value=0, emboss=True)
        col_FB565.prop(bpy.data.node_groups['Film Emulation'].nodes['Lens Distortion'], 'use_jitter', text='Jitter', icon_value=0, emboss=True)
        col_FB565.prop(bpy.data.node_groups['Film Emulation'].nodes['Lens Distortion'], 'use_fit', text='Fit', icon_value=0, emboss=True)
        col_FB565.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[24], 'default_value', text='Distort', icon_value=0, emboss=True)
        col_FB565.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[25], 'default_value', text='Dispersion', icon_value=0, emboss=True)


class SNA_PT_panel015_6D695(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel015_6D695'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_69921'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='RGB Split', icon_value=0)

    def draw(self, context):
        layout = self.layout
        box_FAFE5 = layout.box()
        box_FAFE5.alert = False
        box_FAFE5.enabled = True
        box_FAFE5.active = True
        box_FAFE5.use_property_split = False
        box_FAFE5.use_property_decorate = False
        box_FAFE5.alignment = 'Expand'.upper()
        box_FAFE5.scale_x = 1.0
        box_FAFE5.scale_y = 1.0
        if not True: box_FAFE5.operator_context = "EXEC_DEFAULT"
        col_04395 = box_FAFE5.column(heading='', align=True)
        col_04395.alert = False
        col_04395.enabled = True
        col_04395.active = True
        col_04395.use_property_split = False
        col_04395.use_property_decorate = False
        col_04395.scale_x = 1.0
        col_04395.scale_y = 1.0
        col_04395.alignment = 'Expand'.upper()
        col_04395.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_04395.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[19], 'default_value', text='Red', icon_value=0, emboss=True)
        col_04395.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[20], 'default_value', text='Green', icon_value=0, emboss=True)
        col_04395.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[21], 'default_value', text='Blue', icon_value=0, emboss=True)


class SNA_PT_panel036_8C8DD(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel036_8C8DD'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_5D6F8'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_41361 = layout.row(heading='', align=False)
        row_41361.alert = False
        row_41361.enabled = True
        row_41361.active = True
        row_41361.use_property_split = False
        row_41361.use_property_decorate = False
        row_41361.scale_x = 1.0
        row_41361.scale_y = 1.0
        row_41361.alignment = 'Expand'.upper()
        row_41361.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_41361.label(text='Film Grain', icon_value=0)
        row_41361.separator(factor=0.46000003814697266)
        row_16BFE = row_41361.row(heading='', align=False)
        row_16BFE.alert = False
        row_16BFE.enabled = True
        row_16BFE.active = True
        row_16BFE.use_property_split = False
        row_16BFE.use_property_decorate = False
        row_16BFE.scale_x = 0.8999999761581421
        row_16BFE.scale_y = 1.0
        row_16BFE.alignment = 'Expand'.upper()
        row_16BFE.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_16BFE.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[11], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=True)

    def draw(self, context):
        layout = self.layout
        row_B45B6 = layout.row(heading='', align=True)
        row_B45B6.alert = False
        row_B45B6.enabled = True
        row_B45B6.active = True
        row_B45B6.use_property_split = False
        row_B45B6.use_property_decorate = False
        row_B45B6.scale_x = 1.0
        row_B45B6.scale_y = 1.5
        row_B45B6.alignment = 'Expand'.upper()
        row_B45B6.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_B45B6.operator('sna.bw_noise_8b7f2', text='BW Grain', icon_value=0, emboss=True, depress=False)
        op = row_B45B6.operator('sna.k_grain_8bf7c', text='RGB Grain', icon_value=0, emboss=True, depress=False)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[12], 'default_value', text='Shadow Clumping', icon_value=0, emboss=True, slider=True)
        col_3A175 = layout.column(heading='', align=True)
        col_3A175.alert = False
        col_3A175.enabled = True
        col_3A175.active = True
        col_3A175.use_property_split = False
        col_3A175.use_property_decorate = False
        col_3A175.scale_x = 1.0
        col_3A175.scale_y = 1.0
        col_3A175.alignment = 'Expand'.upper()
        col_3A175.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_3A175.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[13], 'default_value', text='Soften Grain', icon_value=0, emboss=True, slider=True)
        col_3A175.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[14], 'default_value', text='Scale', icon_value=0, emboss=True, slider=True)
        col_3A175.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[15], 'default_value', text='RGB Grain Saturation', icon_value=0, emboss=True)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[16], 'default_value', text='Animate (0/1)', icon_value=0, emboss=True)


class SNA_PT_panel037_3EEE5(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel037_3EEE5'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_5D6F8'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_C4C8E = layout.row(heading='', align=False)
        row_C4C8E.alert = False
        row_C4C8E.enabled = True
        row_C4C8E.active = True
        row_C4C8E.use_property_split = False
        row_C4C8E.use_property_decorate = False
        row_C4C8E.scale_x = 1.0
        row_C4C8E.scale_y = 1.0
        row_C4C8E.alignment = 'Expand'.upper()
        row_C4C8E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_C4C8E.label(text='Halation', icon_value=0)
        row_C4C8E.separator(factor=2.140000104904175)
        row_EFF9B = row_C4C8E.row(heading='', align=False)
        row_EFF9B.alert = False
        row_EFF9B.enabled = True
        row_EFF9B.active = True
        row_EFF9B.use_property_split = False
        row_EFF9B.use_property_decorate = False
        row_EFF9B.scale_x = 0.8999999761581421
        row_EFF9B.scale_y = 1.0
        row_EFF9B.alignment = 'Expand'.upper()
        row_EFF9B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_EFF9B.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[3], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=True)

    def draw(self, context):
        layout = self.layout
        col_63A13 = layout.column(heading='', align=True)
        col_63A13.alert = False
        col_63A13.enabled = True
        col_63A13.active = True
        col_63A13.use_property_split = False
        col_63A13.use_property_decorate = False
        col_63A13.scale_x = 1.0
        col_63A13.scale_y = 1.0
        col_63A13.alignment = 'Expand'.upper()
        col_63A13.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_63A13.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[5], 'default_value', text='Glow', icon_value=0, emboss=True)
        col_63A13.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[6], 'default_value', text='Threshold', icon_value=0, emboss=True)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[4], 'default_value', text='Green Channel', icon_value=0, emboss=True, slider=True)
        col_31103 = layout.column(heading='', align=True)
        col_31103.alert = False
        col_31103.enabled = True
        col_31103.active = True
        col_31103.use_property_split = False
        col_31103.use_property_decorate = False
        col_31103.scale_x = 1.0
        col_31103.scale_y = 1.0
        col_31103.alignment = 'Expand'.upper()
        col_31103.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_31103.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[7], 'default_value', text='Hue', icon_value=0, emboss=True)
        col_31103.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[8], 'default_value', text='Saturation', icon_value=0, emboss=True)


class SNA_PT_panel045_C078A(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel045_C078A'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_5D6F8'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='Lens Distortion', icon_value=0)

    def draw(self, context):
        layout = self.layout
        box_23EFB = layout.box()
        box_23EFB.alert = False
        box_23EFB.enabled = True
        box_23EFB.active = True
        box_23EFB.use_property_split = False
        box_23EFB.use_property_decorate = False
        box_23EFB.alignment = 'Expand'.upper()
        box_23EFB.scale_x = 1.0
        box_23EFB.scale_y = 1.0
        if not True: box_23EFB.operator_context = "EXEC_DEFAULT"
        col_C3DF6 = box_23EFB.column(heading='', align=True)
        col_C3DF6.alert = False
        col_C3DF6.enabled = True
        col_C3DF6.active = True
        col_C3DF6.use_property_split = False
        col_C3DF6.use_property_decorate = False
        col_C3DF6.scale_x = 1.0
        col_C3DF6.scale_y = 1.0
        col_C3DF6.alignment = 'Expand'.upper()
        col_C3DF6.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_C3DF6.prop(bpy.data.node_groups['Film Emulation'].nodes['Lens Distortion'], 'use_projector', text='Projector', icon_value=0, emboss=True)
        col_C3DF6.prop(bpy.data.node_groups['Film Emulation'].nodes['Lens Distortion'], 'use_jitter', text='Jitter', icon_value=0, emboss=True)
        col_C3DF6.prop(bpy.data.node_groups['Film Emulation'].nodes['Lens Distortion'], 'use_fit', text='Fit', icon_value=0, emboss=True)
        col_C3DF6.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[24], 'default_value', text='Distort', icon_value=0, emboss=True)
        col_C3DF6.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[25], 'default_value', text='Dispersion', icon_value=0, emboss=True)


class SNA_PT_panel046_A473D(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel046_A473D'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_5D6F8'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='RGB Split', icon_value=0)

    def draw(self, context):
        layout = self.layout
        box_54293 = layout.box()
        box_54293.alert = False
        box_54293.enabled = True
        box_54293.active = True
        box_54293.use_property_split = False
        box_54293.use_property_decorate = False
        box_54293.alignment = 'Expand'.upper()
        box_54293.scale_x = 1.0
        box_54293.scale_y = 1.0
        if not True: box_54293.operator_context = "EXEC_DEFAULT"
        col_76751 = box_54293.column(heading='', align=True)
        col_76751.alert = False
        col_76751.enabled = True
        col_76751.active = True
        col_76751.use_property_split = False
        col_76751.use_property_decorate = False
        col_76751.scale_x = 1.0
        col_76751.scale_y = 1.0
        col_76751.alignment = 'Expand'.upper()
        col_76751.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_76751.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[19], 'default_value', text='Red', icon_value=0, emboss=True)
        col_76751.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[20], 'default_value', text='Green', icon_value=0, emboss=True)
        col_76751.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[21], 'default_value', text='Blue', icon_value=0, emboss=True)


class SNA_PT_panel008_50F63(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel008_50F63'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_FLARE_77473'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_03694 = layout.row(heading='', align=False)
        row_03694.alert = False
        row_03694.enabled = True
        row_03694.active = True
        row_03694.use_property_split = False
        row_03694.use_property_decorate = False
        row_03694.scale_x = 0.9700000286102295
        row_03694.scale_y = 1.0
        row_03694.alignment = 'Expand'.upper()
        row_03694.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_03694.label(text='Iris Ghost', icon_value=0)
        row_03694.separator(factor=1.4500000476837158)
        row_A86AD = row_03694.row(heading='', align=False)
        row_A86AD.alert = False
        row_A86AD.enabled = True
        row_A86AD.active = True
        row_A86AD.use_property_split = False
        row_A86AD.use_property_decorate = False
        row_A86AD.scale_x = 0.9599999785423279
        row_A86AD.scale_y = 1.0
        row_A86AD.alignment = 'Expand'.upper()
        row_A86AD.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_A86AD.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.029'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=False)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.028'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_6DEB8 = layout.box()
        box_6DEB8.alert = False
        box_6DEB8.enabled = True
        box_6DEB8.active = True
        box_6DEB8.use_property_split = False
        box_6DEB8.use_property_decorate = False
        box_6DEB8.alignment = 'Expand'.upper()
        box_6DEB8.scale_x = 1.0
        box_6DEB8.scale_y = 1.0
        if not True: box_6DEB8.operator_context = "EXEC_DEFAULT"
        box_6DEB8.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.023'].inputs[0], 'default_value', text='Iris', icon_value=0, emboss=True)
        box_6DEB8.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.024'].inputs[0], 'default_value', text='Soften', icon_value=0, emboss=True, slider=True)
        col_C565B = box_6DEB8.column(heading='', align=True)
        col_C565B.alert = False
        col_C565B.enabled = True
        col_C565B.active = True
        col_C565B.use_property_split = False
        col_C565B.use_property_decorate = False
        col_C565B.scale_x = 1.0
        col_C565B.scale_y = 1.0
        col_C565B.alignment = 'Expand'.upper()
        col_C565B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_C565B.prop(bpy.data.node_groups['Lens Flare'].nodes['Group.002'].inputs[1], 'default_value', text='Distortion', icon_value=0, emboss=True)
        col_C565B.prop(bpy.data.node_groups['Lens Flare'].nodes['Group.002'].inputs[2], 'default_value', text='Dispersion', icon_value=0, emboss=True)
        col_C565B.prop(bpy.data.node_groups['Lens Flare'].nodes['Hue/Saturation/Value.001'].inputs[2], 'default_value', text='Dispersion Saturation', icon_value=0, emboss=True)
        col_D4159 = box_6DEB8.column(heading='', align=True)
        col_D4159.alert = False
        col_D4159.enabled = True
        col_D4159.active = True
        col_D4159.use_property_split = False
        col_D4159.use_property_decorate = False
        col_D4159.scale_x = 1.0
        col_D4159.scale_y = 1.0
        col_D4159.alignment = 'Expand'.upper()
        col_D4159.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_D4159.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'iterations', text='Iterations', icon_value=0, emboss=True)
        col_D4159.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'color_modulation', text='Color Module', icon_value=0, emboss=True)
        col_D4159.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.005'], 'threshold', text='Threshold', icon_value=0, emboss=True)


class SNA_PT_panel011_89433(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel011_89433'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_FLARE_77473'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_380BF = layout.row(heading='', align=False)
        row_380BF.alert = False
        row_380BF.enabled = True
        row_380BF.active = True
        row_380BF.use_property_split = False
        row_380BF.use_property_decorate = False
        row_380BF.scale_x = 0.9699999690055847
        row_380BF.scale_y = 1.0
        row_380BF.alignment = 'Expand'.upper()
        row_380BF.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_380BF.label(text='Simple Hoop', icon_value=0)
        row_96189 = row_380BF.row(heading='', align=False)
        row_96189.alert = False
        row_96189.enabled = True
        row_96189.active = True
        row_96189.use_property_split = False
        row_96189.use_property_decorate = False
        row_96189.scale_x = 0.9599999785423279
        row_96189.scale_y = 1.0
        row_96189.alignment = 'Expand'.upper()
        row_96189.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_96189.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.037'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.008'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.021'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_B9D43 = layout.box()
        box_B9D43.alert = False
        box_B9D43.enabled = True
        box_B9D43.active = True
        box_B9D43.use_property_split = False
        box_B9D43.use_property_decorate = False
        box_B9D43.alignment = 'Expand'.upper()
        box_B9D43.scale_x = 1.0
        box_B9D43.scale_y = 1.0
        if not True: box_B9D43.operator_context = "EXEC_DEFAULT"
        col_864FB = box_B9D43.column(heading='', align=True)
        col_864FB.alert = False
        col_864FB.enabled = True
        col_864FB.active = True
        col_864FB.use_property_split = False
        col_864FB.use_property_decorate = False
        col_864FB.scale_x = 1.0
        col_864FB.scale_y = 1.0
        col_864FB.alignment = 'Expand'.upper()
        col_864FB.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_864FB.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.034'].inputs[0], 'default_value', text='Iris', icon_value=0, emboss=True)
        col_864FB.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.035'].inputs[0], 'default_value', text='Soften', icon_value=0, emboss=True)
        col_864FB.prop(bpy.data.node_groups['Lens Flare'].nodes['Hue/Saturation/Value.003'].inputs[2], 'default_value', text='Dispersion Saturation', icon_value=0, emboss=True)
        box_B9D43.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.008'], 'threshold', text='Threshold', icon_value=0, emboss=True)


class SNA_PT_panel027_E8B95(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel027_E8B95'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_FLARE_9C407'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_88FE4 = layout.row(heading='', align=False)
        row_88FE4.alert = False
        row_88FE4.enabled = True
        row_88FE4.active = True
        row_88FE4.use_property_split = False
        row_88FE4.use_property_decorate = False
        row_88FE4.scale_x = 0.9700000286102295
        row_88FE4.scale_y = 1.0
        row_88FE4.alignment = 'Expand'.upper()
        row_88FE4.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_88FE4.label(text='Hoop Flare', icon_value=0)
        row_88FE4.separator(factor=0.3100000023841858)
        row_D81F2 = row_88FE4.row(heading='', align=False)
        row_D81F2.alert = False
        row_D81F2.enabled = True
        row_D81F2.active = True
        row_D81F2.use_property_split = False
        row_D81F2.use_property_decorate = False
        row_D81F2.scale_x = 0.9599999785423279
        row_D81F2.scale_y = 1.0
        row_D81F2.alignment = 'Expand'.upper()
        row_D81F2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_D81F2.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.033'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.007'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.025'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_D63B3 = layout.box()
        box_D63B3.alert = False
        box_D63B3.enabled = True
        box_D63B3.active = True
        box_D63B3.use_property_split = False
        box_D63B3.use_property_decorate = False
        box_D63B3.alignment = 'Expand'.upper()
        box_D63B3.scale_x = 1.0
        box_D63B3.scale_y = 1.0
        if not True: box_D63B3.operator_context = "EXEC_DEFAULT"
        col_C3743 = box_D63B3.column(heading='', align=True)
        col_C3743.alert = False
        col_C3743.enabled = True
        col_C3743.active = True
        col_C3743.use_property_split = False
        col_C3743.use_property_decorate = False
        col_C3743.scale_x = 1.0
        col_C3743.scale_y = 1.0
        col_C3743.alignment = 'Expand'.upper()
        col_C3743.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_C3743.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.030'].inputs[0], 'default_value', text='Iris', icon_value=0, emboss=True)
        col_C3743.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.031'].inputs[0], 'default_value', text='Soften', icon_value=0, emboss=True)
        col_C3743.prop(bpy.data.node_groups['Lens Flare'].nodes['Hue/Saturation/Value.002'].inputs[2], 'default_value', text='Dispersion Saturation', icon_value=0, emboss=True)
        box_D63B3.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.007'], 'threshold', text='Threshold', icon_value=0, emboss=True)


class SNA_PT_panel018_444C5(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel018_444C5'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_FLARE_9C407'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_13A43 = layout.row(heading='', align=False)
        row_13A43.alert = False
        row_13A43.enabled = True
        row_13A43.active = True
        row_13A43.use_property_split = False
        row_13A43.use_property_decorate = False
        row_13A43.scale_x = 0.9699999690055847
        row_13A43.scale_y = 1.0
        row_13A43.alignment = 'Expand'.upper()
        row_13A43.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_13A43.label(text='Simple Hoop', icon_value=0)
        row_67BD7 = row_13A43.row(heading='', align=False)
        row_67BD7.alert = False
        row_67BD7.enabled = True
        row_67BD7.active = True
        row_67BD7.use_property_split = False
        row_67BD7.use_property_decorate = False
        row_67BD7.scale_x = 0.9599999785423279
        row_67BD7.scale_y = 1.0
        row_67BD7.alignment = 'Expand'.upper()
        row_67BD7.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_67BD7.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.037'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.008'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.021'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_94938 = layout.box()
        box_94938.alert = False
        box_94938.enabled = True
        box_94938.active = True
        box_94938.use_property_split = False
        box_94938.use_property_decorate = False
        box_94938.alignment = 'Expand'.upper()
        box_94938.scale_x = 1.0
        box_94938.scale_y = 1.0
        if not True: box_94938.operator_context = "EXEC_DEFAULT"
        col_81185 = box_94938.column(heading='', align=True)
        col_81185.alert = False
        col_81185.enabled = True
        col_81185.active = True
        col_81185.use_property_split = False
        col_81185.use_property_decorate = False
        col_81185.scale_x = 1.0
        col_81185.scale_y = 1.0
        col_81185.alignment = 'Expand'.upper()
        col_81185.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_81185.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.034'].inputs[0], 'default_value', text='Iris', icon_value=0, emboss=True)
        col_81185.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.035'].inputs[0], 'default_value', text='Soften', icon_value=0, emboss=True)
        col_81185.prop(bpy.data.node_groups['Lens Flare'].nodes['Hue/Saturation/Value.003'].inputs[2], 'default_value', text='Dispersion Saturation', icon_value=0, emboss=True)
        box_94938.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.008'], 'threshold', text='Threshold', icon_value=0, emboss=True)


class SNA_PT_panel013_A1AAA(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel013_A1AAA'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_FILM_EMULATION_69921'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_ACA52 = layout.row(heading='', align=False)
        row_ACA52.alert = False
        row_ACA52.enabled = True
        row_ACA52.active = True
        row_ACA52.use_property_split = False
        row_ACA52.use_property_decorate = False
        row_ACA52.scale_x = 1.0
        row_ACA52.scale_y = 1.0
        row_ACA52.alignment = 'Expand'.upper()
        row_ACA52.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_ACA52.label(text='Film Grain', icon_value=0)
        row_ACA52.separator(factor=0.46000003814697266)
        row_26849 = row_ACA52.row(heading='', align=False)
        row_26849.alert = False
        row_26849.enabled = True
        row_26849.active = True
        row_26849.use_property_split = False
        row_26849.use_property_decorate = False
        row_26849.scale_x = 0.8999999761581421
        row_26849.scale_y = 1.0
        row_26849.alignment = 'Expand'.upper()
        row_26849.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_26849.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[11], 'default_value', text='Opacity', icon_value=0, emboss=True, slider=True)

    def draw(self, context):
        layout = self.layout
        row_35C4B = layout.row(heading='', align=True)
        row_35C4B.alert = False
        row_35C4B.enabled = True
        row_35C4B.active = True
        row_35C4B.use_property_split = False
        row_35C4B.use_property_decorate = False
        row_35C4B.scale_x = 1.0
        row_35C4B.scale_y = 1.5
        row_35C4B.alignment = 'Expand'.upper()
        row_35C4B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = row_35C4B.operator('sna.bw_noise_8b7f2', text='BW Grain', icon_value=0, emboss=True, depress=False)
        op = row_35C4B.operator('sna.k_grain_8bf7c', text='RGB Grain', icon_value=0, emboss=True, depress=False)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[12], 'default_value', text='Shadow Clumping', icon_value=0, emboss=True, slider=True)
        col_E10A2 = layout.column(heading='', align=True)
        col_E10A2.alert = False
        col_E10A2.enabled = True
        col_E10A2.active = True
        col_E10A2.use_property_split = False
        col_E10A2.use_property_decorate = False
        col_E10A2.scale_x = 1.0
        col_E10A2.scale_y = 1.0
        col_E10A2.alignment = 'Expand'.upper()
        col_E10A2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_E10A2.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[13], 'default_value', text='Soften Grain', icon_value=0, emboss=True, slider=True)
        col_E10A2.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[14], 'default_value', text='Scale', icon_value=0, emboss=True, slider=True)
        col_E10A2.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[15], 'default_value', text='RGB Grain Saturation', icon_value=0, emboss=True)
        layout.prop(bpy.data.scenes['Scene'].node_tree.nodes['Film Emulation'].inputs[16], 'default_value', text='Animate (0/1)', icon_value=0, emboss=True)


class SNA_PT_panel010_83136(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_panel010_83136'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'SNA_PT_LENS_FLARE_77473'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        row_BA7F3 = layout.row(heading='', align=False)
        row_BA7F3.alert = False
        row_BA7F3.enabled = True
        row_BA7F3.active = True
        row_BA7F3.use_property_split = False
        row_BA7F3.use_property_decorate = False
        row_BA7F3.scale_x = 0.9700000286102295
        row_BA7F3.scale_y = 1.0
        row_BA7F3.alignment = 'Expand'.upper()
        row_BA7F3.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_BA7F3.label(text='Hoop Flare', icon_value=0)
        row_BA7F3.separator(factor=0.3100000023841858)
        row_A6EA8 = row_BA7F3.row(heading='', align=False)
        row_A6EA8.alert = False
        row_A6EA8.enabled = True
        row_A6EA8.active = True
        row_A6EA8.use_property_split = False
        row_A6EA8.use_property_decorate = False
        row_A6EA8.scale_x = 0.9599999785423279
        row_A6EA8.scale_y = 1.0
        row_A6EA8.alignment = 'Expand'.upper()
        row_A6EA8.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        row_A6EA8.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.033'].inputs[0], 'default_value', text='Opacity', icon_value=0, emboss=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.007'], 'quality', text='Quality', icon_value=0, emboss=True)
        layout.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.025'].inputs[2], 'default_value', text='Color Overlay', icon_value=0, emboss=True)
        box_ECB78 = layout.box()
        box_ECB78.alert = False
        box_ECB78.enabled = True
        box_ECB78.active = True
        box_ECB78.use_property_split = False
        box_ECB78.use_property_decorate = False
        box_ECB78.alignment = 'Expand'.upper()
        box_ECB78.scale_x = 1.0
        box_ECB78.scale_y = 1.0
        if not True: box_ECB78.operator_context = "EXEC_DEFAULT"
        col_CF305 = box_ECB78.column(heading='', align=True)
        col_CF305.alert = False
        col_CF305.enabled = True
        col_CF305.active = True
        col_CF305.use_property_split = False
        col_CF305.use_property_decorate = False
        col_CF305.scale_x = 1.0
        col_CF305.scale_y = 1.0
        col_CF305.alignment = 'Expand'.upper()
        col_CF305.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        col_CF305.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.030'].inputs[0], 'default_value', text='Iris', icon_value=0, emboss=True)
        col_CF305.prop(bpy.data.node_groups['Lens Flare'].nodes['Mix.031'].inputs[0], 'default_value', text='Soften', icon_value=0, emboss=True)
        col_CF305.prop(bpy.data.node_groups['Lens Flare'].nodes['Hue/Saturation/Value.002'].inputs[2], 'default_value', text='Dispersion Saturation', icon_value=0, emboss=True)
        box_ECB78.prop(bpy.data.node_groups['Lens Flare'].nodes['Glare.007'], 'threshold', text='Threshold', icon_value=0, emboss=True)


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.utils.register_class(SNA_OT_Operator026_2Ac7B)
    bpy.utils.register_class(SNA_OT_Operator027_E268C)
    bpy.utils.register_class(SNA_PT_SELECTIVE_COLOR_6B020)
    bpy.utils.register_class(SNA_OT_Operator028_D6556)
    bpy.utils.register_class(SNA_OT_Operator030_D0C31)
    bpy.utils.register_class(SNA_OT_Operator031_Bb8C9)
    bpy.utils.register_class(SNA_OT_Operator032_Fba2A)
    bpy.utils.register_class(SNA_OT_Operator033_1E2A6)
    bpy.utils.register_class(SNA_PT_SELECTIVE_COLOR_A0FCA)
    bpy.utils.register_class(SNA_PT_LENS_FLARE_9C407)
    bpy.utils.register_class(SNA_OT_Enable_Glares_C9218)
    bpy.utils.register_class(SNA_OT_Disable_Glares_De435)
    bpy.utils.register_class(SNA_PT_GLARE_59C9A)
    bpy.utils.register_class(SNA_OT_Operator001_5409D)
    bpy.utils.register_class(SNA_OT_Operator_9650E)
    bpy.utils.register_class(SNA_PT_LENS_DIRT_5A957)
    bpy.utils.register_class(SNA_PT_GLARE_74542)
    bpy.utils.register_class(SNA_OT_Operator005_39B40)
    bpy.utils.register_class(SNA_OT_Operator006_2227B)
    bpy.utils.register_class(SNA_PT_LENS_DIRT_D38EB)
    bpy.utils.register_class(SNA_OT_Operator020_7A6A7)
    bpy.utils.register_class(SNA_OT_Operator014_71654)
    bpy.utils.register_class(SNA_OT_Operator021_564C0)
    bpy.utils.register_class(SNA_OT_Operator022_B4Eef)
    bpy.utils.register_class(SNA_OT_Operator008_2C684)
    bpy.utils.register_class(SNA_OT_Operator009_1Aa7A)
    bpy.utils.register_class(SNA_OT_Operator007_C2369)
    bpy.utils.register_class(SNA_OT_Operator010_D86Fc)
    bpy.utils.register_class(SNA_OT_Operator011_325E9)
    bpy.utils.register_class(SNA_OT_Operator012_A483C)
    bpy.utils.register_class(SNA_OT_Operator013_19B92)
    bpy.utils.register_class(SNA_OT_Operator016_29794)
    bpy.utils.register_class(SNA_OT_Operator017_Cf146)
    bpy.utils.register_class(SNA_OT_Operator015_Aea69)
    bpy.utils.register_class(SNA_OT_Operator019_B1Ef3)
    bpy.utils.register_class(SNA_OT_Operator018_E9C55)
    bpy.utils.register_class(SNA_PT_ASPECT_RATIO__RESOLUTION_4245E)
    bpy.utils.register_class(SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F)
    bpy.utils.register_class(SNA_OT_Enable_Colorist_264Dc)
    bpy.utils.register_class(SNA_OT_Reset_Wb_253Dd)
    bpy.utils.register_class(SNA_OT_Operator002_9Ba85)
    bpy.utils.register_class(SNA_PT_COLOR_GRADING_8B4C0)
    bpy.utils.register_class(SNA_PT_COLOR_GRADING_FA4B5)
    bpy.utils.register_class(SNA_OT_Operator003_68E0D)
    bpy.utils.register_class(SNA_PT_COLOR_MANAGEMENT_A2DC9)
    bpy.utils.register_class(SNA_OT_Operator024_25E20)
    bpy.utils.register_class(SNA_OT_Operator004_5F1E2)
    bpy.utils.register_class(SNA_OT_Operator023_034Fc)
    bpy.utils.register_class(SNA_PT_COLOR_MANAGEMENT_BA963)
    bpy.utils.register_class(SNA_OT_Clear_Luts_47B32)
    bpy.utils.register_class(SNA_OT_Operator029_0476C)
    bpy.utils.register_class(SNA_OT_Enable_Film_Bdaed)
    bpy.utils.register_class(SNA_OT_Disable_Film_7061A)
    bpy.utils.register_class(SNA_PT_FILM_EMULATION_69921)
    bpy.utils.register_class(SNA_OT_K_Grain_8Bf7C)
    bpy.utils.register_class(SNA_OT_Bw_Noise_8B7F2)
    bpy.utils.register_class(SNA_OT_K_Grain001_52E35)
    bpy.utils.register_class(SNA_OT_Bw_Noise001_0530C)
    bpy.utils.register_class(SNA_PT_FILM_EMULATION_5D6F8)
    bpy.utils.register_class(SNA_PT_LENS_FLARE_77473)
    bpy.utils.register_class(SNA_OT_Enable_Lens_Flare_29410)
    bpy.utils.register_class(SNA_OT_Disable_Lens_Flare_4A654)
    bpy.utils.register_class(SNA_PT_COLORIST_PRO_V111_5161E)
    bpy.utils.register_class(SNA_PT_COLORIST_PRO_V111_BCC9C)
    bpy.utils.register_class(SNA_PT_panel017_B3899)
    bpy.utils.register_class(SNA_PT_ghost_97C8D)
    bpy.utils.register_class(SNA_PT_panel005_95AB8)
    bpy.utils.register_class(SNA_PT_ghost001_5ED67)
    bpy.utils.register_class(SNA_PT_panel029_16DD7)
    bpy.utils.register_class(SNA_PT_panel030_AB64D)
    bpy.utils.register_class(SNA_PT_panel031_34A85)
    bpy.utils.register_class(SNA_PT_WET_LENS_0D64E)
    bpy.utils.register_class(SNA_PT_WET_LENS_2A174)
    bpy.utils.register_class(SNA_PT_panel026_B0DA7)
    bpy.utils.register_class(SNA_PT_panel022_FB574)
    bpy.utils.register_class(SNA_PT_SOCIAL_MEDIA_DFA8C)
    bpy.utils.register_class(SNA_PT_panel024_27A4E)
    bpy.utils.register_class(SNA_PT_panel025_32F65)
    bpy.utils.register_class(SNA_PT_panel038_03BC6)
    bpy.utils.register_class(SNA_PT_panel039_B1C6B)
    bpy.utils.register_class(SNA_PT_SOCIAL_MEDIA_DC603)
    bpy.utils.register_class(SNA_PT_panel041_1FC6C)
    bpy.utils.register_class(SNA_PT_panel042_5FAD5)
    bpy.utils.register_class(SNA_PT_panel003_2D3AF)
    bpy.utils.register_class(SNA_PT_panel004_665CF)
    bpy.utils.register_class(SNA_PT_panel012_CC8A4)
    bpy.utils.register_class(SNA_PT_panel_E701A)
    bpy.utils.register_class(SNA_PT_panel015_6D695)
    bpy.utils.register_class(SNA_PT_panel036_8C8DD)
    bpy.utils.register_class(SNA_PT_panel037_3EEE5)
    bpy.utils.register_class(SNA_PT_panel045_C078A)
    bpy.utils.register_class(SNA_PT_panel046_A473D)
    bpy.utils.register_class(SNA_PT_panel008_50F63)
    bpy.utils.register_class(SNA_PT_panel011_89433)
    bpy.utils.register_class(SNA_PT_panel027_E8B95)
    bpy.utils.register_class(SNA_PT_panel018_444C5)
    bpy.utils.register_class(SNA_PT_panel013_A1AAA)
    bpy.utils.register_class(SNA_PT_panel010_83136)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(SNA_OT_Operator026_2Ac7B)
    bpy.utils.unregister_class(SNA_OT_Operator027_E268C)
    bpy.utils.unregister_class(SNA_PT_SELECTIVE_COLOR_6B020)
    bpy.utils.unregister_class(SNA_OT_Operator028_D6556)
    bpy.utils.unregister_class(SNA_OT_Operator030_D0C31)
    bpy.utils.unregister_class(SNA_OT_Operator031_Bb8C9)
    bpy.utils.unregister_class(SNA_OT_Operator032_Fba2A)
    bpy.utils.unregister_class(SNA_OT_Operator033_1E2A6)
    bpy.utils.unregister_class(SNA_PT_SELECTIVE_COLOR_A0FCA)
    bpy.utils.unregister_class(SNA_PT_LENS_FLARE_9C407)
    bpy.utils.unregister_class(SNA_OT_Enable_Glares_C9218)
    bpy.utils.unregister_class(SNA_OT_Disable_Glares_De435)
    bpy.utils.unregister_class(SNA_PT_GLARE_59C9A)
    bpy.utils.unregister_class(SNA_OT_Operator001_5409D)
    bpy.utils.unregister_class(SNA_OT_Operator_9650E)
    bpy.utils.unregister_class(SNA_PT_LENS_DIRT_5A957)
    bpy.utils.unregister_class(SNA_PT_GLARE_74542)
    bpy.utils.unregister_class(SNA_OT_Operator005_39B40)
    bpy.utils.unregister_class(SNA_OT_Operator006_2227B)
    bpy.utils.unregister_class(SNA_PT_LENS_DIRT_D38EB)
    bpy.utils.unregister_class(SNA_OT_Operator020_7A6A7)
    bpy.utils.unregister_class(SNA_OT_Operator014_71654)
    bpy.utils.unregister_class(SNA_OT_Operator021_564C0)
    bpy.utils.unregister_class(SNA_OT_Operator022_B4Eef)
    bpy.utils.unregister_class(SNA_OT_Operator008_2C684)
    bpy.utils.unregister_class(SNA_OT_Operator009_1Aa7A)
    bpy.utils.unregister_class(SNA_OT_Operator007_C2369)
    bpy.utils.unregister_class(SNA_OT_Operator010_D86Fc)
    bpy.utils.unregister_class(SNA_OT_Operator011_325E9)
    bpy.utils.unregister_class(SNA_OT_Operator012_A483C)
    bpy.utils.unregister_class(SNA_OT_Operator013_19B92)
    bpy.utils.unregister_class(SNA_OT_Operator016_29794)
    bpy.utils.unregister_class(SNA_OT_Operator017_Cf146)
    bpy.utils.unregister_class(SNA_OT_Operator015_Aea69)
    bpy.utils.unregister_class(SNA_OT_Operator019_B1Ef3)
    bpy.utils.unregister_class(SNA_OT_Operator018_E9C55)
    bpy.utils.unregister_class(SNA_PT_ASPECT_RATIO__RESOLUTION_4245E)
    bpy.utils.unregister_class(SNA_PT_ASPECT_RATIO__RESOLUTION_2BE9F)
    bpy.utils.unregister_class(SNA_OT_Enable_Colorist_264Dc)
    bpy.utils.unregister_class(SNA_OT_Reset_Wb_253Dd)
    bpy.utils.unregister_class(SNA_OT_Operator002_9Ba85)
    bpy.utils.unregister_class(SNA_PT_COLOR_GRADING_8B4C0)
    bpy.utils.unregister_class(SNA_PT_COLOR_GRADING_FA4B5)
    bpy.utils.unregister_class(SNA_OT_Operator003_68E0D)
    bpy.utils.unregister_class(SNA_PT_COLOR_MANAGEMENT_A2DC9)
    bpy.utils.unregister_class(SNA_OT_Operator024_25E20)
    bpy.utils.unregister_class(SNA_OT_Operator004_5F1E2)
    bpy.utils.unregister_class(SNA_OT_Operator023_034Fc)
    bpy.utils.unregister_class(SNA_PT_COLOR_MANAGEMENT_BA963)
    bpy.utils.unregister_class(SNA_OT_Clear_Luts_47B32)
    bpy.utils.unregister_class(SNA_OT_Operator029_0476C)
    bpy.utils.unregister_class(SNA_OT_Enable_Film_Bdaed)
    bpy.utils.unregister_class(SNA_OT_Disable_Film_7061A)
    bpy.utils.unregister_class(SNA_PT_FILM_EMULATION_69921)
    bpy.utils.unregister_class(SNA_OT_K_Grain_8Bf7C)
    bpy.utils.unregister_class(SNA_OT_Bw_Noise_8B7F2)
    bpy.utils.unregister_class(SNA_OT_K_Grain001_52E35)
    bpy.utils.unregister_class(SNA_OT_Bw_Noise001_0530C)
    bpy.utils.unregister_class(SNA_PT_FILM_EMULATION_5D6F8)
    bpy.utils.unregister_class(SNA_PT_LENS_FLARE_77473)
    bpy.utils.unregister_class(SNA_OT_Enable_Lens_Flare_29410)
    bpy.utils.unregister_class(SNA_OT_Disable_Lens_Flare_4A654)
    bpy.utils.unregister_class(SNA_PT_COLORIST_PRO_V111_5161E)
    bpy.utils.unregister_class(SNA_PT_COLORIST_PRO_V111_BCC9C)
    bpy.utils.unregister_class(SNA_PT_panel017_B3899)
    bpy.utils.unregister_class(SNA_PT_ghost_97C8D)
    bpy.utils.unregister_class(SNA_PT_panel005_95AB8)
    bpy.utils.unregister_class(SNA_PT_ghost001_5ED67)
    bpy.utils.unregister_class(SNA_PT_panel029_16DD7)
    bpy.utils.unregister_class(SNA_PT_panel030_AB64D)
    bpy.utils.unregister_class(SNA_PT_panel031_34A85)
    bpy.utils.unregister_class(SNA_PT_WET_LENS_0D64E)
    bpy.utils.unregister_class(SNA_PT_WET_LENS_2A174)
    bpy.utils.unregister_class(SNA_PT_panel026_B0DA7)
    bpy.utils.unregister_class(SNA_PT_panel022_FB574)
    bpy.utils.unregister_class(SNA_PT_SOCIAL_MEDIA_DFA8C)
    bpy.utils.unregister_class(SNA_PT_panel024_27A4E)
    bpy.utils.unregister_class(SNA_PT_panel025_32F65)
    bpy.utils.unregister_class(SNA_PT_panel038_03BC6)
    bpy.utils.unregister_class(SNA_PT_panel039_B1C6B)
    bpy.utils.unregister_class(SNA_PT_SOCIAL_MEDIA_DC603)
    bpy.utils.unregister_class(SNA_PT_panel041_1FC6C)
    bpy.utils.unregister_class(SNA_PT_panel042_5FAD5)
    bpy.utils.unregister_class(SNA_PT_panel003_2D3AF)
    bpy.utils.unregister_class(SNA_PT_panel004_665CF)
    bpy.utils.unregister_class(SNA_PT_panel012_CC8A4)
    bpy.utils.unregister_class(SNA_PT_panel_E701A)
    bpy.utils.unregister_class(SNA_PT_panel015_6D695)
    bpy.utils.unregister_class(SNA_PT_panel036_8C8DD)
    bpy.utils.unregister_class(SNA_PT_panel037_3EEE5)
    bpy.utils.unregister_class(SNA_PT_panel045_C078A)
    bpy.utils.unregister_class(SNA_PT_panel046_A473D)
    bpy.utils.unregister_class(SNA_PT_panel008_50F63)
    bpy.utils.unregister_class(SNA_PT_panel011_89433)
    bpy.utils.unregister_class(SNA_PT_panel027_E8B95)
    bpy.utils.unregister_class(SNA_PT_panel018_444C5)
    bpy.utils.unregister_class(SNA_PT_panel013_A1AAA)
    bpy.utils.unregister_class(SNA_PT_panel010_83136)

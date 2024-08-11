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
    "name" : "Bender",
    "author" : "Blender Bash", 
    "description" : "Bend Anything",
    "blender" : (3, 4, 0),
    "version" : (1, 1, 4),
    "location" : "3D Viewport - Side Panel - BB Tools",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "3D View" 
}


import bpy
import bpy.utils.previews
import os


addon_keymaps = {}
_icons = None
number_of_targets = {'sna_list': [], }
operators = {'sna_helplistsetenum': [], 'sna_helplistbendapply': [], }
_item_map = dict()


def make_enum_item(_id, name, descr, preview_id, uid):
    lookup = str(_id)+"\0"+str(name)+"\0"+str(descr)+"\0"+str(preview_id)+"\0"+str(uid)
    if not lookup in _item_map:
        _item_map[lookup] = (_id, name, descr, preview_id, uid)
    return _item_map[lookup]


def property_exists(prop_path, glob, loc):
    try:
        eval(prop_path, glob, loc)
        return True
    except:
        return False


def sna_update_sna_bends_D2E14(self, context):
    sna_updated_prop = self.sna_bends
    sna_set_gizmo_37264()


def load_preview_icon(path):
    global _icons
    if not path in _icons:
        if os.path.exists(path):
            _icons.load(path, path, "IMAGE")
        else:
            return 0
    return _icons[path].icon_id


def sna_function_execute2_D864C():
    number_of_targets['sna_list'] = []
    for i_43438 in range(len(list(bpy.context.active_object.modifiers))):
        if 'Bend.0' in str(list(bpy.context.active_object.modifiers)[i_43438]):
            number_of_targets['sna_list'].append([list(bpy.context.active_object.modifiers)[i_43438].name, list(bpy.context.active_object.modifiers)[i_43438].name, '', 0])
    return number_of_targets['sna_list']


def sna_bends_enum_items(self, context):
    enum_items = sna_function_execute2_D864C()
    return [make_enum_item(item[0], item[1], item[2], item[3], i) for i, item in enumerate(enum_items)]


class SNA_OT_No_Bend_Limit_Op_92Ded(bpy.types.Operator):
    bl_idname = "sna.no_bend_limit_op_92ded"
    bl_label = "No Bend Limit OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value = False
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Hide_Gizmo_Op_3Ea44(bpy.types.Operator):
    bl_idname = "sna.hide_gizmo_op_3ea44"
    bl_label = "Hide Gizmo OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value = False
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Show_Gizmo_Op_822Ec(bpy.types.Operator):
    bl_idname = "sna.show_gizmo_op_822ec"
    bl_label = "Show Gizmo OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Apply_This_Bend_Op_D2B63(bpy.types.Operator):
    bl_idname = "sna.apply_this_bend_op_d2b63"
    bl_label = "Apply This Bend OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value = False
        bpy.ops.object.modifier_apply('INVOKE_DEFAULT', modifier=bpy.context.view_layer.objects.active.sna_bends)
        sna_set_gizmo_37264()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Bend_Limit_Op_C6880(bpy.types.Operator):
    bl_idname = "sna.bend_limit_op_c6880"
    bl_label = "Bend Limit OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Both_Sides_Op_4C454(bpy.types.Operator):
    bl_idname = "sna.both_sides_op_4c454"
    bl_label = "Both Sides OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[7].default_value = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_One_Side_Op_3D9F1(bpy.types.Operator):
    bl_idname = "sna.one_side_op_3d9f1"
    bl_label = "One Side OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[7].default_value = False
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Bypass_Bend_Op_C95E5(bpy.types.Operator):
    bl_idname = "sna.bypass_bend_op_c95e5"
    bl_label = "BYpass Bend OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.active_object.modifiers[bpy.context.view_layer.objects.active.sna_bends].show_viewport = False
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Enable_Bend_Op_51E3E(bpy.types.Operator):
    bl_idname = "sna.enable_bend_op_51e3e"
    bl_label = "Enable Bend OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.active_object.modifiers[bpy.context.view_layer.objects.active.sna_bends].show_viewport = True
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_set_gizmo_37264():
    for i_894BB in range(len(bpy.context.active_object.modifiers)):
        if 'Bend.0' in bpy.context.active_object.modifiers[i_894BB].name:
            if ('Bend.0' in bpy.context.active_object.modifiers[i_894BB].name == bpy.context.view_layer.objects.active.sna_bends):
                list(bpy.context.active_object.modifiers[i_894BB].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value = True
            else:
                list(bpy.context.active_object.modifiers[i_894BB].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value = False


def sna_removebendfunction_9B50A():
    bpy.ops.object.modifier_remove('INVOKE_DEFAULT', modifier=bpy.context.view_layer.objects.active.sna_bends)
    sna_set_bend_mod_enum_5D9C3()


class SNA_OT_Remove_Bend_Op_77499(bpy.types.Operator):
    bl_idname = "sna.remove_bend_op_77499"
    bl_label = "Remove Bend OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_removebendfunction_9B50A()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Apply_All_Bends_Op_Fce4D(bpy.types.Operator):
    bl_idname = "sna.apply_all_bends_op_fce4d"
    bl_label = "Apply All Bends OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        operators['sna_helplistbendapply'] = []
        for i_24B88 in range(len(bpy.context.active_object.modifiers)):
            if 'Bend.0' in bpy.context.active_object.modifiers[i_24B88].name:
                operators['sna_helplistbendapply'].append(bpy.context.active_object.modifiers[i_24B88].name)
        for i_744F0 in range(len(operators['sna_helplistbendapply'])):
            if bpy.context.view_layer.objects.active.modifiers[operators['sna_helplistbendapply'][i_744F0]].show_viewport:
                list(bpy.context.active_object.modifiers.active.id_data.modifiers[operators['sna_helplistbendapply'][i_744F0]].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value = False
                bpy.ops.object.modifier_apply('INVOKE_DEFAULT', modifier=operators['sna_helplistbendapply'][i_744F0])
            else:
                bpy.ops.object.modifier_remove('INVOKE_DEFAULT', modifier=operators['sna_helplistbendapply'][i_744F0])
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Refresh_Op_5B04A(bpy.types.Operator):
    bl_idname = "sna.refresh_op_5b04a"
    bl_label = "Refresh OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_set_bend_mod_enum_5D9C3()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_set_bend_mod_enum_5D9C3():
    operators['sna_helplistsetenum'] = []
    if (bpy.context.active_object.modifiers.active != None):
        for i_FB3B3 in range(len(bpy.context.active_object.modifiers)):
            if 'Bend.0' in bpy.context.active_object.modifiers[i_FB3B3].name:
                operators['sna_helplistsetenum'].append(bpy.context.active_object.modifiers[i_FB3B3].name)
        if (len(operators['sna_helplistsetenum']) != 0):
            bpy.context.view_layer.objects.active.sna_bends = operators['sna_helplistsetenum'][int(len(operators['sna_helplistsetenum']) - 1.0)]


class SNA_OT_Bend_Op_99Eec(bpy.types.Operator):
    bl_idname = "sna.bend_op_99eec"
    bl_label = "Bend OP"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if 'Bend.0' in str(bpy.context.object.modifiers.active):
            bpy.context.active_object.modifiers.active.node_group.nodes['Group'].inputs[8].default_value = False
        if (property_exists("bpy.data.node_groups", globals(), locals()) and 'BB.Bend.Geonode' in bpy.data.node_groups):
            pass
        else:
            before_data = list(bpy.data.node_groups)
            bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'bend_asset.blend') + r'\NodeTree', filename='BB.Bend.Geonode', link=False)
            new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
            appended_0CCB9 = None if not new_data else new_data[0]
        if (property_exists("bpy.data.node_groups", globals(), locals()) and 'BB_Bend' in bpy.data.node_groups):
            pass
        else:
            before_data = list(bpy.data.node_groups)
            bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'bend_asset.blend') + r'\NodeTree', filename='BB_Bend', link=True)
            new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
            appended_48ABA = None if not new_data else new_data[0]
        bpy.ops.object.modifier_add('INVOKE_DEFAULT', type='NODES')
        bpy.context.active_object.modifiers.active.name = 'Bend.001'
        bpy.context.active_object.modifiers.active.node_group = bpy.data.node_groups[bpy.data.node_groups.find('BB.Bend.Geonode')]
        bpy.data.node_groups['BB.Bend.Geonode'].nodes['Group'].node_tree = bpy.data.node_groups[bpy.data.node_groups.find('BB_Bend')]
        link_CDE4A = bpy.data.node_groups['BB.Bend.Geonode'].links.new(input=bpy.data.node_groups['BB.Bend.Geonode'].nodes['Group'].outputs[0], output=bpy.data.node_groups['BB.Bend.Geonode'].nodes['Group Output'].inputs[0], )
        bpy.ops.object.geometry_node_tree_copy_assign('INVOKE_DEFAULT', )
        bpy.data.node_groups.remove(tree=bpy.data.node_groups[bpy.data.node_groups.find('BB.Bend.Geonode')], )
        bpy.data.node_groups.remove(tree=bpy.data.node_groups[bpy.data.node_groups.find('_help_bend')], )
        sna_set_bend_mod_enum_5D9C3()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class BB_TOOLS_PARENT_PT(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'BB_TOOLS_PARENT_PT'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'BB Tools'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='BB Tools', icon_value=load_preview_icon(os.path.join(os.path.dirname(__file__), 'assets', 'BB_logo48.png')))

    def draw(self, context):
        layout = self.layout


class SNA_PT_bend_panel_C5BD7(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_bend_panel_C5BD7'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'BB_TOOLS_PARENT_PT'
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='Bender', icon_value=load_preview_icon(os.path.join(os.path.dirname(__file__), 'assets', 'icon_bend.png')))

    def draw(self, context):
        layout = self.layout
        if (bpy.context.view_layer.objects.active.sna_bends != ''):
            col_8C944 = layout.column(heading='', align=False)
            col_8C944.alert = False
            col_8C944.enabled = True
            col_8C944.active = True
            col_8C944.use_property_split = False
            col_8C944.use_property_decorate = False
            col_8C944.scale_x = 1.0
            col_8C944.scale_y = 1.0
            col_8C944.alignment = 'Center'.upper()
            if not True: col_8C944.operator_context = "EXEC_DEFAULT"
            if (len(number_of_targets['sna_list']) > 1):
                split_A977C = col_8C944.split(factor=0.6000000238418579, align=False)
                split_A977C.alert = False
                split_A977C.enabled = True
                split_A977C.active = True
                split_A977C.use_property_split = False
                split_A977C.use_property_decorate = False
                split_A977C.scale_x = 1.0
                split_A977C.scale_y = 1.0
                split_A977C.alignment = 'Center'.upper()
                if not True: split_A977C.operator_context = "EXEC_DEFAULT"
                row_7F02B = split_A977C.row(heading='', align=False)
                row_7F02B.alert = False
                row_7F02B.enabled = True
                row_7F02B.active = True
                row_7F02B.use_property_split = False
                row_7F02B.use_property_decorate = False
                row_7F02B.scale_x = 1.0
                row_7F02B.scale_y = 0.0
                row_7F02B.alignment = 'Right'.upper()
                if not True: row_7F02B.operator_context = "EXEC_DEFAULT"
                row_7F02B.label(text='Select Your Bend', icon_value=0)
                split_A977C.prop(bpy.context.view_layer.objects.active, 'sna_bends', text='', icon_value=0, emboss=True)
            split_24FD2 = col_8C944.split(factor=0.6000000238418579, align=False)
            split_24FD2.alert = False
            split_24FD2.enabled = True
            split_24FD2.active = True
            split_24FD2.use_property_split = False
            split_24FD2.use_property_decorate = False
            split_24FD2.scale_x = 1.0
            split_24FD2.scale_y = 1.0
            split_24FD2.alignment = 'Center'.upper()
            if not True: split_24FD2.operator_context = "EXEC_DEFAULT"
            row_ECD1F = split_24FD2.row(heading='', align=False)
            row_ECD1F.alert = False
            row_ECD1F.enabled = True
            row_ECD1F.active = True
            row_ECD1F.use_property_split = False
            row_ECD1F.use_property_decorate = False
            row_ECD1F.scale_x = 1.0
            row_ECD1F.scale_y = 0.0
            row_ECD1F.alignment = 'Right'.upper()
            if not True: row_ECD1F.operator_context = "EXEC_DEFAULT"
            row_ECD1F.label(text='Bend Angle', icon_value=0)
            split_24FD2.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[2], 'default_value', text='', icon_value=0, emboss=True)
            split_A8DEF = col_8C944.split(factor=0.6000000238418579, align=False)
            split_A8DEF.alert = False
            split_A8DEF.enabled = True
            split_A8DEF.active = True
            split_A8DEF.use_property_split = False
            split_A8DEF.use_property_decorate = False
            split_A8DEF.scale_x = 1.0
            split_A8DEF.scale_y = 1.0
            split_A8DEF.alignment = 'Center'.upper()
            if not True: split_A8DEF.operator_context = "EXEC_DEFAULT"
            row_689C2 = split_A8DEF.row(heading='', align=False)
            row_689C2.alert = False
            row_689C2.enabled = True
            row_689C2.active = True
            row_689C2.use_property_split = False
            row_689C2.use_property_decorate = False
            row_689C2.scale_x = 1.0
            row_689C2.scale_y = 0.0
            row_689C2.alignment = 'Right'.upper()
            if not True: row_689C2.operator_context = "EXEC_DEFAULT"
            row_689C2.label(text='Position Center', icon_value=0)
            split_A8DEF.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[3], 'default_value', text='', icon_value=0, emboss=True)
            split_4B40B = col_8C944.split(factor=0.6000000238418579, align=False)
            split_4B40B.alert = False
            split_4B40B.enabled = True
            split_4B40B.active = True
            split_4B40B.use_property_split = False
            split_4B40B.use_property_decorate = False
            split_4B40B.scale_x = 1.0
            split_4B40B.scale_y = 1.0
            split_4B40B.alignment = 'Center'.upper()
            if not True: split_4B40B.operator_context = "EXEC_DEFAULT"
            row_648D9 = split_4B40B.row(heading='', align=False)
            row_648D9.alert = False
            row_648D9.enabled = True
            row_648D9.active = True
            row_648D9.use_property_split = False
            row_648D9.use_property_decorate = False
            row_648D9.scale_x = 1.0
            row_648D9.scale_y = 0.0
            row_648D9.alignment = 'Right'.upper()
            if not True: row_648D9.operator_context = "EXEC_DEFAULT"
            row_648D9.label(text='Bend Plane Normal', icon_value=0)
            split_4B40B.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[4], 'default_value', text='', icon_value=0, emboss=True)
            split_1721C = col_8C944.split(factor=0.6000000238418579, align=False)
            split_1721C.alert = False
            split_1721C.enabled = True
            split_1721C.active = True
            split_1721C.use_property_split = False
            split_1721C.use_property_decorate = False
            split_1721C.scale_x = 1.0
            split_1721C.scale_y = 1.0
            split_1721C.alignment = 'Center'.upper()
            if not True: split_1721C.operator_context = "EXEC_DEFAULT"
            row_384BC = split_1721C.row(heading='', align=False)
            row_384BC.alert = False
            row_384BC.enabled = True
            row_384BC.active = True
            row_384BC.use_property_split = False
            row_384BC.use_property_decorate = False
            row_384BC.scale_x = 1.0
            row_384BC.scale_y = 0.0
            row_384BC.alignment = 'Right'.upper()
            if not True: row_384BC.operator_context = "EXEC_DEFAULT"
            row_384BC.label(text='Rotation Bend Plane', icon_value=0)
            split_1721C.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[5], 'default_value', text='', icon_value=0, emboss=True)
            split_E8B50 = col_8C944.split(factor=0.5, align=False)
            split_E8B50.alert = False
            split_E8B50.enabled = True
            split_E8B50.active = True
            split_E8B50.use_property_split = False
            split_E8B50.use_property_decorate = False
            split_E8B50.scale_x = 1.0
            split_E8B50.scale_y = 1.0
            split_E8B50.alignment = 'Center'.upper()
            if not True: split_E8B50.operator_context = "EXEC_DEFAULT"
            op = split_E8B50.operator('sna.bend_limit_op_c6880', text='Limit Bend', icon_value=0, emboss=True, depress=list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value)
            op = split_E8B50.operator('sna.no_bend_limit_op_92ded', text='No Limit Bend', icon_value=0, emboss=True, depress=(not list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value))
            if list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value:
                split_7545D = col_8C944.split(factor=0.6000000238418579, align=False)
                split_7545D.alert = False
                split_7545D.enabled = True
                split_7545D.active = True
                split_7545D.use_property_split = False
                split_7545D.use_property_decorate = False
                split_7545D.scale_x = 1.0
                split_7545D.scale_y = 1.0
                split_7545D.alignment = 'Center'.upper()
                if not True: split_7545D.operator_context = "EXEC_DEFAULT"
                row_E5DE0 = split_7545D.row(heading='', align=False)
                row_E5DE0.alert = False
                row_E5DE0.enabled = True
                row_E5DE0.active = True
                row_E5DE0.use_property_split = False
                row_E5DE0.use_property_decorate = False
                row_E5DE0.scale_x = 1.0
                row_E5DE0.scale_y = 0.0
                row_E5DE0.alignment = 'Right'.upper()
                if not True: row_E5DE0.operator_context = "EXEC_DEFAULT"
                row_E5DE0.label(text='Limit Z distance', icon_value=0)
                split_7545D.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[10], 'default_value', text='', icon_value=0, emboss=True)
            if list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value:
                split_27C4E = col_8C944.split(factor=0.6000000238418579, align=False)
                split_27C4E.alert = False
                split_27C4E.enabled = True
                split_27C4E.active = True
                split_27C4E.use_property_split = False
                split_27C4E.use_property_decorate = False
                split_27C4E.scale_x = 1.0
                split_27C4E.scale_y = 1.0
                split_27C4E.alignment = 'Center'.upper()
                if not True: split_27C4E.operator_context = "EXEC_DEFAULT"
                row_C68C8 = split_27C4E.row(heading='', align=False)
                row_C68C8.alert = False
                row_C68C8.enabled = True
                row_C68C8.active = True
                row_C68C8.use_property_split = False
                row_C68C8.use_property_decorate = False
                row_C68C8.scale_x = 1.0
                row_C68C8.scale_y = 0.0
                row_C68C8.alignment = 'Right'.upper()
                if not True: row_C68C8.operator_context = "EXEC_DEFAULT"
                row_C68C8.label(text='Limit X distance', icon_value=0)
                split_27C4E.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[11], 'default_value', text='', icon_value=0, emboss=True)
            if list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value:
                split_26855 = col_8C944.split(factor=0.6000000238418579, align=False)
                split_26855.alert = False
                split_26855.enabled = True
                split_26855.active = True
                split_26855.use_property_split = False
                split_26855.use_property_decorate = False
                split_26855.scale_x = 1.0
                split_26855.scale_y = 1.0
                split_26855.alignment = 'Center'.upper()
                if not True: split_26855.operator_context = "EXEC_DEFAULT"
                row_40058 = split_26855.row(heading='', align=False)
                row_40058.alert = False
                row_40058.enabled = True
                row_40058.active = True
                row_40058.use_property_split = False
                row_40058.use_property_decorate = False
                row_40058.scale_x = 1.0
                row_40058.scale_y = 0.0
                row_40058.alignment = 'Right'.upper()
                if not True: row_40058.operator_context = "EXEC_DEFAULT"
                row_40058.label(text='Limit Y distance', icon_value=0)
                split_26855.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[12], 'default_value', text='', icon_value=0, emboss=True)
            split_F9052 = col_8C944.split(factor=0.5, align=False)
            split_F9052.alert = False
            split_F9052.enabled = True
            split_F9052.active = True
            split_F9052.use_property_split = False
            split_F9052.use_property_decorate = False
            split_F9052.scale_x = 1.0
            split_F9052.scale_y = 1.0
            split_F9052.alignment = 'Center'.upper()
            if not True: split_F9052.operator_context = "EXEC_DEFAULT"
            op = split_F9052.operator('sna.one_side_op_3d9f1', text='Bend One Side', icon_value=0, emboss=True, depress= not list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[7].default_value)
            op = split_F9052.operator('sna.both_sides_op_4c454', text='Bend Both Sides', icon_value=0, emboss=True, depress=list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[7].default_value)
            split_70654 = col_8C944.split(factor=0.5, align=False)
            split_70654.alert = False
            split_70654.enabled = True
            split_70654.active = True
            split_70654.use_property_split = False
            split_70654.use_property_decorate = False
            split_70654.scale_x = 1.0
            split_70654.scale_y = 1.0
            split_70654.alignment = 'Center'.upper()
            if not True: split_70654.operator_context = "EXEC_DEFAULT"
            op = split_70654.operator('sna.show_gizmo_op_822ec', text='Show Gizmo', icon_value=0, emboss=True, depress=list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value)
            op = split_70654.operator('sna.hide_gizmo_op_3ea44', text='Hide Gizmo', icon_value=0, emboss=True, depress=(not list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value))
            if (list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value and (not list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[9].default_value)):
                split_C5772 = col_8C944.split(factor=0.6000000238418579, align=False)
                split_C5772.alert = False
                split_C5772.enabled = True
                split_C5772.active = True
                split_C5772.use_property_split = False
                split_C5772.use_property_decorate = False
                split_C5772.scale_x = 1.0
                split_C5772.scale_y = 1.0
                split_C5772.alignment = 'Center'.upper()
                if not True: split_C5772.operator_context = "EXEC_DEFAULT"
                row_694FF = split_C5772.row(heading='', align=False)
                row_694FF.alert = False
                row_694FF.enabled = True
                row_694FF.active = True
                row_694FF.use_property_split = False
                row_694FF.use_property_decorate = False
                row_694FF.scale_x = 1.0
                row_694FF.scale_y = 0.0
                row_694FF.alignment = 'Right'.upper()
                if not True: row_694FF.operator_context = "EXEC_DEFAULT"
                row_694FF.label(text='Size Gizmo', icon_value=0)
                split_C5772.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[6], 'default_value', text='', icon_value=0, emboss=True)
            if list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[8].default_value:
                split_26306 = col_8C944.split(factor=0.6000000238418579, align=False)
                split_26306.alert = False
                split_26306.enabled = True
                split_26306.active = True
                split_26306.use_property_split = False
                split_26306.use_property_decorate = False
                split_26306.scale_x = 1.0
                split_26306.scale_y = 1.0
                split_26306.alignment = 'Center'.upper()
                if not True: split_26306.operator_context = "EXEC_DEFAULT"
                row_034F4 = split_26306.row(heading='', align=False)
                row_034F4.alert = False
                row_034F4.enabled = True
                row_034F4.active = True
                row_034F4.use_property_split = False
                row_034F4.use_property_decorate = False
                row_034F4.scale_x = 1.0
                row_034F4.scale_y = 0.0
                row_034F4.alignment = 'Right'.upper()
                if not True: row_034F4.operator_context = "EXEC_DEFAULT"
                row_034F4.label(text='Gizmo Grid Spacing', icon_value=0)
                split_26306.prop(list(bpy.context.active_object.modifiers.active.id_data.modifiers[bpy.context.view_layer.objects.active.sna_bends].node_group.inputs['Geometry'].id_data.nodes['Group'].inputs)[13], 'default_value', text='', icon_value=0, emboss=True)
            split_9BDD6 = col_8C944.split(factor=0.5, align=False)
            split_9BDD6.alert = False
            split_9BDD6.enabled = True
            split_9BDD6.active = True
            split_9BDD6.use_property_split = False
            split_9BDD6.use_property_decorate = False
            split_9BDD6.scale_x = 1.0
            split_9BDD6.scale_y = 1.0
            split_9BDD6.alignment = 'Center'.upper()
            if not True: split_9BDD6.operator_context = "EXEC_DEFAULT"
            op = split_9BDD6.operator('sna.enable_bend_op_51e3e', text='Bend Enabled', icon_value=0, emboss=True, depress=bpy.context.active_object.modifiers[bpy.context.view_layer.objects.active.sna_bends].show_viewport)
            op = split_9BDD6.operator('sna.bypass_bend_op_c95e5', text='Bend Bypassed', icon_value=0, emboss=True, depress=(not bpy.context.active_object.modifiers[bpy.context.view_layer.objects.active.sna_bends].show_viewport))
            if (len(number_of_targets['sna_list']) > 1):
                split_FCABA = col_8C944.split(factor=0.5, align=False)
                split_FCABA.alert = False
                split_FCABA.enabled = True
                split_FCABA.active = True
                split_FCABA.use_property_split = False
                split_FCABA.use_property_decorate = False
                split_FCABA.scale_x = 1.0
                split_FCABA.scale_y = 1.0
                split_FCABA.alignment = 'Center'.upper()
                if not True: split_FCABA.operator_context = "EXEC_DEFAULT"
                op = split_FCABA.operator('sna.apply_this_bend_op_d2b63', text='APPLY This Bend', icon_value=0, emboss=True, depress=False)
                op = split_FCABA.operator('sna.apply_all_bends_op_fce4d', text='APPLY All Bends', icon_value=0, emboss=True, depress=False)
            else:
                op = col_8C944.operator('sna.apply_this_bend_op_d2b63', text='Apply The Bend', icon_value=0, emboss=True, depress=False)
            op = col_8C944.operator('sna.remove_bend_op_77499', text='Remove This Bend', icon_value=0, emboss=True, depress=False)
        if (len(number_of_targets['sna_list']) > 0):
            col_C7DF9 = layout.column(heading='', align=False)
            col_C7DF9.alert = False
            col_C7DF9.enabled = True
            col_C7DF9.active = True
            col_C7DF9.use_property_split = False
            col_C7DF9.use_property_decorate = False
            col_C7DF9.scale_x = 1.0
            col_C7DF9.scale_y = 1.0
            col_C7DF9.alignment = 'Expand'.upper()
            if not True: col_C7DF9.operator_context = "EXEC_DEFAULT"
            op = col_C7DF9.operator('sna.refresh_op_5b04a', text='Refresh', icon_value=0, emboss=True, depress=False)
            row_6B786 = col_C7DF9.row(heading='', align=False)
            row_6B786.alert = False
            row_6B786.enabled = True
            row_6B786.active = True
            row_6B786.use_property_split = False
            row_6B786.use_property_decorate = False
            row_6B786.scale_x = 1.0
            row_6B786.scale_y = 0.6100000143051147
            row_6B786.alignment = 'Center'.upper()
            if not True: row_6B786.operator_context = "EXEC_DEFAULT"
            row_6B786.label(text='or...', icon_value=0)
        if (len(number_of_targets['sna_list']) > 0):
            op = layout.operator('sna.bend_op_99eec', text='Bend It Again', icon_value=0, emboss=True, depress=False)
        else:
            op = layout.operator('sna.bend_op_99eec', text='Bend It', icon_value=0, emboss=True, depress=False)


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.types.Object.sna_bends = bpy.props.EnumProperty(name='Bends', description='', items=sna_bends_enum_items, update=sna_update_sna_bends_D2E14)
    bpy.utils.register_class(SNA_OT_No_Bend_Limit_Op_92Ded)
    bpy.utils.register_class(SNA_OT_Hide_Gizmo_Op_3Ea44)
    bpy.utils.register_class(SNA_OT_Show_Gizmo_Op_822Ec)
    bpy.utils.register_class(SNA_OT_Apply_This_Bend_Op_D2B63)
    bpy.utils.register_class(SNA_OT_Bend_Limit_Op_C6880)
    bpy.utils.register_class(SNA_OT_Both_Sides_Op_4C454)
    bpy.utils.register_class(SNA_OT_One_Side_Op_3D9F1)
    bpy.utils.register_class(SNA_OT_Bypass_Bend_Op_C95E5)
    bpy.utils.register_class(SNA_OT_Enable_Bend_Op_51E3E)
    bpy.utils.register_class(SNA_OT_Remove_Bend_Op_77499)
    bpy.utils.register_class(SNA_OT_Apply_All_Bends_Op_Fce4D)
    bpy.utils.register_class(SNA_OT_Refresh_Op_5B04A)
    bpy.utils.register_class(SNA_OT_Bend_Op_99Eec)
    bpy.utils.register_class(BB_TOOLS_PARENT_PT)
    bpy.utils.register_class(SNA_PT_bend_panel_C5BD7)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    del bpy.types.Object.sna_bends
    bpy.utils.unregister_class(SNA_OT_No_Bend_Limit_Op_92Ded)
    bpy.utils.unregister_class(SNA_OT_Hide_Gizmo_Op_3Ea44)
    bpy.utils.unregister_class(SNA_OT_Show_Gizmo_Op_822Ec)
    bpy.utils.unregister_class(SNA_OT_Apply_This_Bend_Op_D2B63)
    bpy.utils.unregister_class(SNA_OT_Bend_Limit_Op_C6880)
    bpy.utils.unregister_class(SNA_OT_Both_Sides_Op_4C454)
    bpy.utils.unregister_class(SNA_OT_One_Side_Op_3D9F1)
    bpy.utils.unregister_class(SNA_OT_Bypass_Bend_Op_C95E5)
    bpy.utils.unregister_class(SNA_OT_Enable_Bend_Op_51E3E)
    bpy.utils.unregister_class(SNA_OT_Remove_Bend_Op_77499)
    bpy.utils.unregister_class(SNA_OT_Apply_All_Bends_Op_Fce4D)
    bpy.utils.unregister_class(SNA_OT_Refresh_Op_5B04A)
    bpy.utils.unregister_class(SNA_OT_Bend_Op_99Eec)
    bpy.utils.unregister_class(BB_TOOLS_PARENT_PT)
    bpy.utils.unregister_class(SNA_PT_bend_panel_C5BD7)

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
    "name" : "Real Damage Lite",
    "author" : "Andrey Repnikov", 
    "description" : "",
    "blender" : (3, 5, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "3D View" 
}


import bpy
import bpy.utils.previews
import os
import random


addon_keymaps = {}
_icons = None
visual_scripting_editor = {'sna_selectedobjects': [], }


def sna_pop_message_272A6_B1848(Header, Message, NamedIcon):
    Headers = Header
    Messagers = Message
    Iconers = NamedIcon

    def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
    #Shows a message box with a message, custom title, and a specific icon
    ShowMessageBox(Messagers, Headers, Iconers)
    return


def property_exists(prop_path, glob, loc):
    try:
        eval(prop_path, glob, loc)
        return True
    except:
        return False


def sna_true_deselect__all_C6336_690A9():
    if (bpy.context.view_layer.objects.selected or bpy.context.view_layer.objects.active):
        exec('bpy.context.view_layer.objects.active = None')
        exec("bpy.ops.object.select_all(action='DESELECT')")


def random_integer(min, max, seed):
    random.seed(seed)
    return random.randint(int(min), int(max))


def random_float(min, max, seed):
    random.seed(seed)
    return random.uniform(min, max)


class SNA_OT_Apply_Modifer_92C02(bpy.types.Operator):
    bl_idname = "sna.apply_modifer_92c02"
    bl_label = "Apply Modifer"
    bl_description = "Add modifer to objects"
    bl_options = {"REGISTER", "UNDO"}
    sna_modifer: bpy.props.StringProperty(name='modifer', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (len(list(bpy.context.view_layer.objects.selected)) > 0):
            visual_scripting_editor['sna_selectedobjects'] = []
            for i_265A2 in range(len(bpy.context.view_layer.objects.selected)):
                if bpy.context.view_layer.objects.selected[i_265A2].type == 'MESH':
                    visual_scripting_editor['sna_selectedobjects'].append(bpy.context.view_layer.objects.selected[i_265A2])
            if property_exists("bpy.data.node_groups[self.sna_modifer]", globals(), locals()):
                pass
            else:
                before_data = list(bpy.data.node_groups)
                bpy.ops.wm.append(directory=os.path.join(os.path.dirname(__file__), 'assets', 'Damage39 New Lite.blend') + r'\NodeTree', filename=self.sna_modifer, link=False)
                new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
                appended_3FD41 = None if not new_data else new_data[0]
            sna_true_deselect__all_C6336_690A9()
            for i_4902B in range(len(visual_scripting_editor['sna_selectedobjects'])):
                modifier_9D005 = visual_scripting_editor['sna_selectedobjects'][i_4902B].modifiers.new(name='DamagePro_', type='NODES', )
                modifier_9D005.node_group = bpy.data.node_groups[self.sna_modifer]
            for i_B525C in range(len(visual_scripting_editor['sna_selectedobjects'])):
                visual_scripting_editor['sna_selectedobjects'][i_B525C].select_set(state=True, )
                visual_scripting_editor['sna_selectedobjects'][i_B525C].modifiers['DamagePro_']['Input_14'] = random_integer(1.0, 40.0, None)
                visual_scripting_editor['sna_selectedobjects'][i_B525C].modifiers['DamagePro_']['Input_42'] = random_float(0.004999999888241291, 0.00800000037997961, None)
                visual_scripting_editor['sna_selectedobjects'][i_B525C].modifiers['DamagePro_']['Input_40'] = random_float(1.0, 360.0, None)
        else:
            sna_pop_message_272A6_B1848('Warning', 'No selected objects', 'ERROR')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_REAL_DAMAGE_3F792(bpy.types.Panel):
    bl_label = 'Real Damage'
    bl_idname = 'SNA_PT_REAL_DAMAGE_3F792'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Real Damage'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        op = layout.operator('sna.apply_modifer_92c02', text='Add Damage', icon_value=892, emboss=True, depress=False)
        op.sna_modifer = 'DamagePro2'
        attr_DC527 = '["' + str('Input_4' + '"]') 
        layout.prop(bpy.context.view_layer.objects.active.modifiers['DamagePro_'], attr_DC527, text='Depth', icon_value=0, emboss=False)
        attr_C5415 = '["' + str('Input_41' + '"]') 
        layout.prop(bpy.context.view_layer.objects.active.modifiers['DamagePro_'], attr_C5415, text='Density', icon_value=0, emboss=False)
        attr_355AA = '["' + str('Input_42' + '"]') 
        layout.prop(bpy.context.view_layer.objects.active.modifiers['DamagePro_'], attr_355AA, text='Scale', icon_value=0, emboss=False)
        attr_4C24C = '["' + str('Input_44' + '"]') 
        layout.prop(bpy.context.view_layer.objects.active.modifiers['DamagePro_'], attr_4C24C, text='Detail', icon_value=0, emboss=False)
        attr_5A0FC = '["' + str('Input_40' + '"]') 
        layout.prop(bpy.context.view_layer.objects.active.modifiers['DamagePro_'], attr_5A0FC, text='Angle', icon_value=0, emboss=False)


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.types.Scene.sna_new_property = bpy.props.PointerProperty(name='New Property', description='', type=bpy.types.Material)
    bpy.types.Scene.sna_new_property_001 = bpy.props.PointerProperty(name='New Property 001', description='', type=bpy.types.Material)
    bpy.types.Scene.sna_new_property_002 = bpy.props.PointerProperty(name='New Property 002', description='', type=bpy.types.Material)
    bpy.utils.register_class(SNA_OT_Apply_Modifer_92C02)
    bpy.utils.register_class(SNA_PT_REAL_DAMAGE_3F792)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    del bpy.types.Scene.sna_new_property_002
    del bpy.types.Scene.sna_new_property_001
    del bpy.types.Scene.sna_new_property
    bpy.utils.unregister_class(SNA_OT_Apply_Modifer_92C02)
    bpy.utils.unregister_class(SNA_PT_REAL_DAMAGE_3F792)

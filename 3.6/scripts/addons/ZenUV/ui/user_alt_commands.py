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

""" User alternative commands and "Magic Button" module """
import bpy
from ZenUV.ui.labels import ZuvLabels


class BaseCollectionItem(bpy.types.PropertyGroup):
    pass

pie_menus: bpy.props.CollectionProperty(type=BaseCollectionItem)

MAX_STR_LEN = 1024

ED_DATA = (
    ('PMENU', "Pie Menu", 'MOD_SUBSURF'),
    ('RMENU', "Regular Menu", 'MOD_BOOLEAN'),
    ('DIALOG', "Popup Dialog", 'MOD_BUILD'),
    ('SCRIPT', "Stack Key", 'MOD_MIRROR'),
    ('PANEL', "Panel Group", 'MOD_MULTIRES'),
    ('HPANEL', "Hidden Panel Group", 'MOD_TRIANGULATE'),
    ('STICKY', "Sticky Key", 'MOD_WARP'),
    ('MACRO', "Macro Operator", 'MOD_ARRAY'),
    ('MODAL', "Modal Operator", 'MOD_BEVEL'),
    ('PROPERTY', "Property", 'MOD_SCREW'),
)

PM_ITEMS_M = tuple(
    (id, name, "", icon, 1 << i)
    for i, (id, name, icon) in enumerate(ED_DATA)
)


# def prop_name(data, property, default=None):
#     prop = data.bl_rna.properties[property]
#     return prop.name or default or prop
    
# def btn_operator(text="", icon='NONE', icon_value=0):
#     p = PLayout.real_operator(
#         PME_OT_btn_hide.bl_idname, text,
#         icon=ic(icon), icon_value=icon_value)
#     p.idx = PLayout.idx
#     p.item_id = PLayout.item_id

def utitle(text):
    words = [word[0].upper() + word[1:] for word in text.split("_") if word]
    return " ".join(words)


def get_bl_command(op):
    if isinstance(op, str):
        try:
            eval("bpy.ops.%s" % op)
        except:
            return None

    return ("bpy.ops.%s()" % op)


def get_rna_type(op):
    if isinstance(op, str):
        try:
            op = eval("bpy.ops.%s" % op)
        except:
            return None

    if hasattr(op, "get_rna"):
        return op.get_rna().rna_type
    else:
        return op.get_rna_type()


class ZUV_OT_search_operator(bpy.types.Operator):
    bl_idname = "zenuv.search_operator"
    bl_label = "Search and Select Menu"
    bl_description = "Search and select menu"
    bl_options = {'INTERNAL'}
    bl_property = "item"

    enum_items = None

    def get_items(self, context):
        items = []
        for op_module_name in dir(bpy.ops):
            op_module = getattr(bpy.ops, op_module_name)
            for op_submodule_name in dir(op_module):
                op = getattr(op_module, op_submodule_name)
                op_name = get_rna_type(op).bl_rna.name

                label = op_name or op_submodule_name
                label = "%s|%s" % (utitle(label), op_module_name.upper())

                items.append((
                    "%s.%s" % (op_module_name, op_submodule_name),
                    label, ""))

        ZUV_OT_search_operator.items = items

        return items
    sector: bpy.props.StringProperty(default="")
    item: bpy.props.EnumProperty(items=get_items)



    def execute(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        # print("Selected", self.item)
        # addon_prefs.operator_prop
        addon_prefs.operator = get_bl_command(self.item)
        if self.sector:
            addon_prefs[self.sector] = get_bl_command(self.item)
        # if addon_prefs.operator:
        #     addon_prefs.operator_prop.items = get_rna_type(self.item)
        # print(get_rna_type(self.item))
        # print(get_bl_command(self.item))
        # bpy.ops.wm.zuv_select(pm_name=self.item)
        ZUV_OT_search_operator.enum_items = None
        return {'FINISHED'}

    def invoke(self, context, event):
        ZUV_OT_search_operator.enum_items = None
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

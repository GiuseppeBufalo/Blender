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
    "name" : "Alt Tab Colorful",
    "author" : "Alt Tab & SkdSam", 
    "description" : "Alt Tab Colorful",
    "blender" : (3, 0, 0),
    "version" : (1, 0, 0),
    "location" : "N-Panel",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "3D View" 
}


import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper
import shutil
import json
import sys


addon_keymaps = {}
_icons = None
nodetree = {'sna_convertz': [], 'sna_c_namez': [], 'sna_c_col_rgb': [], 'sna_rand': 0, 'sna_col_master_list': [], 'sna_combined_col_save': [], 'sna_col_capture_amount_collection': 0, 'sna_enum_menu': [], 'sna_fine_tune_random': [], 'sna_fine_tune_delete': [], }
pallette_generator = {'sna_listnamess': [], 'sna_enumfunlist': [], 'sna_integerscroller': 0, }
_item_map = dict()


def make_enum_item(_id, name, descr, preview_id, uid):
    lookup = str(_id)+"\0"+str(name)+"\0"+str(descr)+"\0"+str(preview_id)+"\0"+str(uid)
    if not lookup in _item_map:
        _item_map[lookup] = (_id, name, descr, preview_id, uid)
    return _item_map[lookup]


def sna_update_sna_pallet_list_07097(self, context):
    sna_updated_prop = self.sna_pallet_list
    bpy.context.scene.sna_indexalt = 0
    bpy.context.scene.sna_pallettoload = bpy.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'pallets') + '\\' + sna_updated_prop + '.json')
    sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)


def display_collection_id(uid, vars):
    id = f"coll_{uid}"
    for var in vars.keys():
        if var.startswith("i_"):
            id += f"_{var}_{vars[var]}"
    return id


class SNA_UL_display_collection_list_4750A(bpy.types.UIList):

    def draw_item(self, context, layout, data, item_4750A, icon, active_data, active_propname, index_4750A):
        row = layout
        if bpy.context.scene.sna_show_names:
            row_B01A7 = layout.row(heading='', align=False)
            row_B01A7.alert = False
            row_B01A7.enabled = False
            row_B01A7.active = False
            row_B01A7.use_property_split = False
            row_B01A7.use_property_decorate = False
            row_B01A7.scale_x = 0.6690000295639038
            row_B01A7.scale_y = 1.0
            row_B01A7.alignment = 'Left'.upper()
            if not True: row_B01A7.operator_context = "EXEC_DEFAULT"
            row_B01A7.prop(item_4750A, 'name', text='', icon_value=0, emboss=False, expand=False, slider=False, toggle=False, invert_checkbox=False)
        row_DF159 = layout.row(heading='', align=True)
        row_DF159.alert = False
        row_DF159.enabled = True
        row_DF159.active = True
        row_DF159.use_property_split = False
        row_DF159.use_property_decorate = False
        row_DF159.scale_x = 1.0
        row_DF159.scale_y = 1.0
        row_DF159.alignment = 'Expand'.upper()
        if not True: row_DF159.operator_context = "EXEC_DEFAULT"
        for i_D8469 in range(item_4750A.colmount):
            if str(i_D8469) == "0":
                row_DF159.prop(item_4750A, 'col1r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
            elif str(i_D8469) == "1":
                row_DF159.prop(item_4750A, 'col2r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
            elif str(i_D8469) == "2":
                row_DF159.prop(item_4750A, 'col3r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
            elif str(i_D8469) == "3":
                row_DF159.prop(item_4750A, 'col4r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
            elif str(i_D8469) == "4":
                row_DF159.prop(item_4750A, 'col5r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
            else:
                pass
        col_9FAED = row_DF159.column(heading='', align=False)
        col_9FAED.alert = False
        col_9FAED.enabled = True
        col_9FAED.active = True
        col_9FAED.use_property_split = False
        col_9FAED.use_property_decorate = False
        col_9FAED.scale_x = 1.0
        col_9FAED.scale_y = 1.0
        col_9FAED.alignment = 'Right'.upper()
        if not True: col_9FAED.operator_context = "EXEC_DEFAULT"
        row_7EB66 = col_9FAED.row(heading='', align=True)
        row_7EB66.alert = False
        row_7EB66.enabled = True
        row_7EB66.active = True
        row_7EB66.use_property_split = False
        row_7EB66.use_property_decorate = False
        row_7EB66.scale_x = 1.0
        row_7EB66.scale_y = 1.0
        row_7EB66.alignment = 'Right'.upper()
        if not True: row_7EB66.operator_context = "EXEC_DEFAULT"
        op = row_7EB66.operator('sna.apply_random_color_bd01c', text='', icon_value=470, emboss=True, depress=False)
        op.sna_colindex = index_4750A
        op.sna_applyint = 0
        if bpy.context.scene.sna_show_edit_buttons:
            row_66478 = row_7EB66.row(heading='', align=False)
            row_66478.alert = False
            row_66478.enabled = True
            row_66478.active = True
            row_66478.use_property_split = False
            row_66478.use_property_decorate = False
            row_66478.scale_x = 1.0
            row_66478.scale_y = 1.0
            row_66478.alignment = 'Right'.upper()
            if not True: row_66478.operator_context = "EXEC_DEFAULT"
            op = row_66478.operator('sna.edit_palette_2c0da', text='', icon_value=107, emboss=True, depress=False)
            op.sna_openeditname = index_4750A
        if bpy.context.scene.sna_show_delete_buttons:
            row_0B4E6 = row_7EB66.row(heading='', align=False)
            row_0B4E6.alert = True
            row_0B4E6.enabled = True
            row_0B4E6.active = True
            row_0B4E6.use_property_split = False
            row_0B4E6.use_property_decorate = False
            row_0B4E6.scale_x = 1.0
            row_0B4E6.scale_y = 1.0
            row_0B4E6.alignment = 'Right'.upper()
            if not True: row_0B4E6.operator_context = "EXEC_DEFAULT"
            op = row_0B4E6.operator('sna.delete_palette_0980f', text='', icon_value=32, emboss=True, depress=False)
            op.sna_name = item_4750A.name

    def filter_items(self, context, data, propname):
        flt_flags = []
        for item in getattr(data, propname):
            if not self.filter_name or self.filter_name.lower() in item.name.lower():
                if True:
                    flt_flags.append(self.bitflag_filter_item)
                else:
                    flt_flags.append(0)
            else:
                flt_flags.append(0)
        return flt_flags, []


def sna_pop_message_272A6_41AB5(Header, Message, NamedIcon):
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


def sna_pop_message_272A6_5CB98(Header, Message, NamedIcon):
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


def sna_pop_message_272A6_EA733(Header, Message, NamedIcon):
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


def sna_pop_message_272A6_DA480(Header, Message, NamedIcon):
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


def sna_pop_message_272A6_0C6FA(Header, Message, NamedIcon):
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


def sna_pop_message_272A6_3E8A9(Header, Message, NamedIcon):
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


def sna_update_sna_main_color_6F9DB(self, context):
    sna_updated_prop = self.sna_main_color
    CCC = sna_updated_prop
    cColor = None
    import colorsys
    COLOR_V = CCC

    def complementary_color(rgba):
        """Calculate the complementary color."""
        hsv = colorsys.rgb_to_hsv(rgba[0], rgba[1], rgba[2])
        new_hue = (hsv[0] + 0.5) % 1.0  # Shift hue by 180 degrees (0.5 in normalized hue) to get the complementary color
        rgb = colorsys.hsv_to_rgb(new_hue, hsv[1], hsv[2])
        return (rgb[0], rgb[1], rgb[2], rgba[3])
    # Calculate the complementary color for COLOR_V
    cColor = complementary_color(COLOR_V)
    print("Original Color:", COLOR_V)
    print("Complementary Color:", cColor)
    bpy.context.scene.sna_complcolor = cColor


def sna_update_sna_main_color_06851(self, context):
    sna_updated_prop = self.sna_main_color
    CCC = sna_updated_prop
    tColor1 = None
    tColor2 = None
    import colorsys
    COLOR_V = CCC  # Replace with your desired RGBA color

    def triadic_colors(rgba, shifts=[120.0, -120.0]):
        """Calculate a list of triadic colors by shifting the hue."""
        triadic = []
        for shift in shifts:
            hsv = colorsys.rgb_to_hsv(rgba[0], rgba[1], rgba[2])
            new_hue = (hsv[0] + shift/360.0) % 1.0  # Shift hue and wrap around if it goes beyond 1
            rgb = colorsys.hsv_to_rgb(new_hue, hsv[1], hsv[2])
            triadic.append((rgb[0], rgb[1], rgb[2], rgba[3]))
        return triadic
    # Calculate the triadic colors for COLOR_V
    tColor1, tColor2 = triadic_colors(COLOR_V)
    bpy.context.scene.sna_triad_1 = tColor1
    bpy.context.scene.sna_triad_2 = tColor2


def sna_update_sna_main_color_6DF7D(self, context):
    sna_updated_prop = self.sna_main_color
    CCC = sna_updated_prop
    sColor1 = None
    sColor2 = None
    import colorsys
    COLOR_V = CCC

    def split_complementary_colors(rgba, shifts=[-30.0, 30.0]):
        """Calculate a list of split complementary colors by shifting the hue of the complementary color."""
        split_complementary = []
        hsv = colorsys.rgb_to_hsv(rgba[0], rgba[1], rgba[2])
        complementary_hue = (hsv[0] + 0.5) % 1.0  # Shift by 180 degrees (0.5 in normalized hue) to get the complementary color
        for shift in shifts:
            new_hue = (complementary_hue + shift/360.0) % 1.0  # Shift hue and wrap around if it goes beyond 1
            rgb = colorsys.hsv_to_rgb(new_hue, hsv[1], hsv[2])
            split_complementary.append((rgb[0], rgb[1], rgb[2], rgba[3]))
        return split_complementary
    # Calculate the split complementary colors for COLOR_V
    sColor1, sColor2 = split_complementary_colors(COLOR_V)
    bpy.context.scene.sna_split1 = sColor1
    bpy.context.scene.sna_split2 = sColor2


def sna_update_sna_main_color_5B960(self, context):
    sna_updated_prop = self.sna_main_color
    CCC = sna_updated_prop
    sqColor1 = None
    sqColor2 = None
    sqColor3 = None
    import colorsys
    COLOR_V = CCC

    def square_colors(rgba, shifts=[90.0, 180.0, 270.0]):
        """Calculate a list of square colors by shifting the hue."""
        square = []
        for shift in shifts:
            hsv = colorsys.rgb_to_hsv(rgba[0], rgba[1], rgba[2])
            new_hue = (hsv[0] + shift/360.0) % 1.0  # Shift hue and wrap around if it goes beyond 1
            rgb = colorsys.hsv_to_rgb(new_hue, hsv[1], hsv[2])
            square.append((rgb[0], rgb[1], rgb[2], rgba[3]))
        return square
    # Calculate the square colors for COLOR_V
    sqColor1, sqColor2, sqColor3 = square_colors(COLOR_V)
    bpy.context.scene.sna_square1 = sqColor1
    bpy.context.scene.sna_square2 = sqColor2
    bpy.context.scene.sna_square3 = sqColor3


def sna_update_sna_main_color_ABB92(self, context):
    sna_updated_prop = self.sna_main_color
    CCC = sna_updated_prop
    tColor1 = None
    tColor2 = None
    tColor3 = None
    import colorsys
    COLOR_V = CCC

    def tetradic_colors(rgba):
        """Calculate a list of tetradic colors."""
        tetradic = []
        hsv = colorsys.rgb_to_hsv(rgba[0], rgba[1], rgba[2])
        # Define shifts for the tetradic colors: 90, 180, and 270 degrees
        shifts = [-25.0, -180.0, -205.0]
        for shift in shifts:
            new_hue = (hsv[0] + shift/360.0) % 1.0  # Shift hue and wrap around if it goes beyond 1
            rgb = colorsys.hsv_to_rgb(new_hue, hsv[1], hsv[2])
            tetradic.append((rgb[0], rgb[1], rgb[2], rgba[3]))
        return tetradic
    # Calculate the tetradic colors for COLOR_V
    tColor1, tColor2, tColor3 = tetradic_colors(COLOR_V)
    bpy.context.scene.sna_tetradc1 = tColor1
    bpy.context.scene.sna_tetradc2 = tColor2
    bpy.context.scene.sna_tetradc3 = tColor3


def sna_update_sna_main_color_68793(self, context):
    sna_updated_prop = self.sna_main_color
    CCC = sna_updated_prop
    mColor1 = None
    mColor2 = None
    mColor3 = None
    mColor4 = None
    import colorsys
    COLOR_V = CCC

    def monochromatic_colors(rgba, variations=[(0.9, 1.1), (0.75, 1.25), (0.6, 1.4), (0.5, 1.5)]):
        """Calculate a list of monochromatic colors by varying saturation and value."""
        monochromatic = []
        hsv = colorsys.rgb_to_hsv(rgba[0], rgba[1], rgba[2])
        for sat_mult, val_mult in variations:
            new_sat = min(1.0, hsv[1] * sat_mult)
            new_val = min(1.0, hsv[2] * val_mult)
            rgb = colorsys.hsv_to_rgb(hsv[0], new_sat, new_val)
            monochromatic.append((rgb[0], rgb[1], rgb[2], rgba[3]))
        return monochromatic
    # Calculate the monochromatic colors for COLOR_V
    mColor1, mColor2, mColor3, mColor4 = monochromatic_colors(COLOR_V)
    bpy.context.scene.sna_mono1 = mColor1
    bpy.context.scene.sna_mono2 = mColor2
    bpy.context.scene.sna_mono3 = mColor3
    bpy.context.scene.sna_mono4 = mColor4


def sna_update_sna_main_color_04464(self, context):
    sna_updated_prop = self.sna_main_color
    CCC = sna_updated_prop
    aColor1 = None
    aColor2 = None
    aColor3 = None
    aColor4 = None
    import colorsys
    COLOR_V = CCC

    def analogous_colors(rgba, shifts=[-75.0, -55.0, -35.0, -15.0]):
        """Calculate a list of analogous colors by shifting the hue."""
        analogous = []
        hsv = colorsys.rgb_to_hsv(rgba[0], rgba[1], rgba[2])
        for shift in shifts:
            new_hue = (hsv[0] + shift/360.0) % 1.0  # Shift hue and wrap around if it goes beyond 1
            rgb = colorsys.hsv_to_rgb(new_hue, hsv[1], hsv[2])
            analogous.append((rgb[0], rgb[1], rgb[2], rgba[3]))
        return analogous
    # Calculate the analogous colors for COLOR_V
    aColor1, aColor2, aColor3, aColor4 = analogous_colors(COLOR_V)
    bpy.context.scene.sna_analog1 = aColor4
    bpy.context.scene.sna_analog2 = aColor3
    bpy.context.scene.sna_analog3 = aColor2
    bpy.context.scene.sna_analog4 = aColor1


def sna_update_sna_enumscroller_26CB5(self, context):
    sna_updated_prop = self.sna_enumscroller
    bpy.context.scene.sna_enumselector = sna_updated_prop


def sna_pop_message_272A6_B08ED(Header, Message, NamedIcon):
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


class SNA_OT_Delete_Color_1_9Bd49(bpy.types.Operator):
    bl_idname = "sna.delete_color_1_9bd49"
    bl_label = "Delete Color 1"
    bl_description = "*"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        bpy.context.scene.sna_col_del_tog_1 = True
        bpy.ops.sna.fine_tune_delete_35613('INVOKE_DEFAULT', sna_pallet_name_fine=bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name)
        sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Delete_Color_2_A6B7D(bpy.types.Operator):
    bl_idname = "sna.delete_color_2_a6b7d"
    bl_label = "Delete Color 2"
    bl_description = "*"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        bpy.context.scene.sna_col_del_tog_2 = True
        bpy.ops.sna.fine_tune_delete_35613('INVOKE_DEFAULT', sna_pallet_name_fine=bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name)
        sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Delete_Color_4_75Ab8(bpy.types.Operator):
    bl_idname = "sna.delete_color_4_75ab8"
    bl_label = "Delete Color 4"
    bl_description = "*"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        bpy.context.scene.sna_col_del_tog_4 = True
        bpy.ops.sna.fine_tune_delete_35613('INVOKE_DEFAULT', sna_pallet_name_fine=bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name)
        sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Delete_Color_5_D27A6(bpy.types.Operator):
    bl_idname = "sna.delete_color_5_d27a6"
    bl_label = "Delete Color 5"
    bl_description = "*"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        bpy.context.scene.sna_col_del_tog_5 = True
        bpy.ops.sna.fine_tune_delete_35613('INVOKE_DEFAULT', sna_pallet_name_fine=bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name)
        sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Delete_Color_3_B4Bee(bpy.types.Operator):
    bl_idname = "sna.delete_color_3_b4bee"
    bl_label = "Delete Color 3"
    bl_description = "*"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        bpy.context.scene.sna_col_del_tog_3 = True
        bpy.ops.sna.fine_tune_delete_35613('INVOKE_DEFAULT', sna_pallet_name_fine=bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name)
        sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


@persistent
def load_post_handler_27CC8(dummy):
    sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)


class SNA_OT_Load_Colours_E77Af(bpy.types.Operator):
    bl_idname = "sna.load_colours_e77af"
    bl_label = "Load Colours"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Export_2B6A0(bpy.types.Operator, ExportHelper):
    bl_idname = "sna.export_2b6a0"
    bl_label = "Export"
    bl_description = "Export Current Palette Library"
    bl_options = {"REGISTER", "UNDO"}
    filter_glob: bpy.props.StringProperty( default='*.json', options={'HIDDEN'} )
    filename_ext = '.json'
    sna_filename: bpy.props.StringProperty(name='filename', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        OldLocation = bpy.context.scene.sna_pallettoload
        SaveLocation = self.filepath
        namez = None
        src_path = OldLocation
        dst_path = SaveLocation
        shutil.copy(src_path, dst_path)
        return {"FINISHED"}


class SNA_PT_ALT_TAB_COLORFUL_10BBC(bpy.types.Panel):
    bl_label = 'Alt Tab Colorful'
    bl_idname = 'SNA_PT_ALT_TAB_COLORFUL_10BBC'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorful'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        op = layout.operator('wm.url_open', text='Start', icon_value=126, emboss=True, depress=False)
        op.url = 'https://coolors.co/5bbdd9-5ebec1-61bea8-64bf90-67bf77'
        op = layout.operator('sna.copy_pallet_eab95', text='Sync from URL', icon_value=692, emboss=True, depress=False)
        op.sna_new_property = ''
        if (len(nodetree['sna_col_master_list']) == 0):
            pass
        else:
            box_506C5 = layout.box()
            box_506C5.alert = False
            box_506C5.enabled = True
            box_506C5.active = True
            box_506C5.use_property_split = False
            box_506C5.use_property_decorate = False
            box_506C5.alignment = 'Expand'.upper()
            box_506C5.scale_x = 1.0
            box_506C5.scale_y = 1.7999999523162842
            if not True: box_506C5.operator_context = "EXEC_DEFAULT"
            row_B76BE = box_506C5.row(heading='', align=True)
            row_B76BE.alert = False
            row_B76BE.enabled = True
            row_B76BE.active = True
            row_B76BE.use_property_split = False
            row_B76BE.use_property_decorate = False
            row_B76BE.scale_x = 2.0
            row_B76BE.scale_y = 1.0
            row_B76BE.alignment = 'Expand'.upper()
            if not True: row_B76BE.operator_context = "EXEC_DEFAULT"
            op = row_B76BE.operator('sna.paint_selected_objects_e873b', text='', icon_value=182, emboss=True, depress=False)
            for i_B8A45 in range(len(nodetree['sna_col_master_list'])):
                if str(i_B8A45) == "0":
                    row_B76BE.prop(bpy.context.scene, 'sna_c1', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
                elif str(i_B8A45) == "1":
                    row_B76BE.prop(bpy.context.scene, 'sna_c2', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
                elif str(i_B8A45) == "2":
                    row_B76BE.prop(bpy.context.scene, 'sna_c3', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
                elif str(i_B8A45) == "3":
                    row_B76BE.prop(bpy.context.scene, 'sna_c4', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
                elif str(i_B8A45) == "4":
                    row_B76BE.prop(bpy.context.scene, 'sna_c5', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=False, invert_checkbox=False)
                else:
                    pass
            op = row_B76BE.operator('sna.save_palette_04046', text='', icon_value=706, emboss=True, depress=False)
            op.sna_whattosave = ''


class SNA_OT_Importer_E712B(bpy.types.Operator, ImportHelper):
    bl_idname = "sna.importer_e712b"
    bl_label = "Importer"
    bl_description = "Import a palette library from a JSON file"
    bl_options = {"REGISTER", "UNDO"}
    filter_glob: bpy.props.StringProperty( default='*.json', options={'HIDDEN'} )

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        LOCATION = os.path.join(os.path.dirname(__file__), 'assets', 'pallets')
        namer = self.filepath
        new_file_name_without_extension = None
        import json
        #Absolute path to the file you want to save
        source_file_path = namer
        #Directory where you want to save the JSON file
        output_directory = LOCATION
        #Extract the file name from the source file path
        file_name = os.path.basename(source_file_path)
        #Check if the file already exists in the output directory
        if os.path.exists(os.path.join(output_directory, file_name)):
            # Find the next available filename with an incremented prefix
            i = 1
            while True:
                base_name, extension = os.path.splitext(file_name)
                new_file_name = f"{base_name}{i}{extension}"
                if not os.path.exists(os.path.join(output_directory, new_file_name)):
                    break
                i += 1
        else:
            new_file_name = file_name
        #Copy the source file to the output directory with the new name
        shutil.copy(source_file_path, os.path.join(output_directory, new_file_name))
        #Return the new file name without the extension
        new_file_name_without_extension = os.path.splitext(new_file_name)[0]
        print(new_file_name_without_extension)
        bpy.context.scene.sna_pallettoload = bpy.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'pallets') + '\\' + new_file_name_without_extension + '.json')
        sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
        bpy.context.scene.sna_pallet_list = new_file_name_without_extension
        return {"FINISHED"}


def sna_pallet_list_enum_items(self, context):
    enum_items = sna_pallets_65030()
    return [make_enum_item(item[0], item[1], item[2], item[3], i) for i, item in enumerate(enum_items)]


def sna_pallets_65030():
    nodetree['sna_enum_menu'] = []
    for i_B26BB in range(len([os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f) for f in os.listdir(os.path.join(os.path.dirname(__file__), 'assets', 'pallets')) if os.path.isfile(os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f))])-1,-1,-1):
        nodetree['sna_enum_menu'].append([[os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f) for f in os.listdir(os.path.join(os.path.dirname(__file__), 'assets', 'pallets')) if os.path.isfile(os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f))][i_B26BB].replace(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), '').replace('\\', '').replace('.json', ''), [os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f) for f in os.listdir(os.path.join(os.path.dirname(__file__), 'assets', 'pallets')) if os.path.isfile(os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f))][i_B26BB].replace(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), '').replace('\\', '').replace('.json', ''), [os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f) for f in os.listdir(os.path.join(os.path.dirname(__file__), 'assets', 'pallets')) if os.path.isfile(os.path.join(os.path.join(os.path.dirname(__file__), 'assets', 'pallets'), f))][i_B26BB], 0])
    return nodetree['sna_enum_menu']


class SNA_PT_colour001_F183C(bpy.types.Panel):
    bl_label = ''
    bl_idname = 'SNA_PT_colour001_F183C'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorful'
    bl_order = 1
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='Palette Library', icon_value=54)

    def draw(self, context):
        layout = self.layout
        row_286BB = layout.row(heading='', align=False)
        row_286BB.alert = False
        row_286BB.enabled = True
        row_286BB.active = True
        row_286BB.use_property_split = False
        row_286BB.use_property_decorate = False
        row_286BB.scale_x = 1.2000000476837158
        row_286BB.scale_y = 1.399999976158142
        row_286BB.alignment = 'Expand'.upper()
        if not True: row_286BB.operator_context = "EXEC_DEFAULT"
        op = row_286BB.operator('sna.create_collection_7b813', text='', icon_value=22, emboss=True, depress=False)
        op.sna_filetoname = ''
        row_286BB.prop(bpy.context.scene, 'sna_pallet_list', text='', icon_value=0, emboss=True)
        op = row_286BB.operator('sna.delete_palette_collection_52cd8', text='', icon_value=21, emboss=True, depress=False)
        op.sna_deletename = ''
        box_BF1EB = layout.box()
        box_BF1EB.alert = False
        box_BF1EB.enabled = True
        box_BF1EB.active = True
        box_BF1EB.use_property_split = False
        box_BF1EB.use_property_decorate = False
        box_BF1EB.alignment = 'Expand'.upper()
        box_BF1EB.scale_x = 1.0
        box_BF1EB.scale_y = 1.0
        if not True: box_BF1EB.operator_context = "EXEC_DEFAULT"
        row_79DC4 = box_BF1EB.row(heading='', align=True)
        row_79DC4.alert = False
        row_79DC4.enabled = True
        row_79DC4.active = True
        row_79DC4.use_property_split = False
        row_79DC4.use_property_decorate = False
        row_79DC4.scale_x = 1.0
        row_79DC4.scale_y = bpy.context.scene.sna_ui_row_h
        row_79DC4.alignment = 'Expand'.upper()
        if not True: row_79DC4.operator_context = "EXEC_DEFAULT"
        coll_id = display_collection_id('4750A', locals())
        row_79DC4.template_list('SNA_UL_display_collection_list_4750A', coll_id, bpy.context.scene, 'sna_collectionscolours', bpy.context.scene, 'sna_indexalt', rows=0)
        row_D085C = layout.row(heading='', align=False)
        row_D085C.alert = False
        row_D085C.enabled = True
        row_D085C.active = True
        row_D085C.use_property_split = False
        row_D085C.use_property_decorate = False
        row_D085C.scale_x = 1.1100000143051147
        row_D085C.scale_y = 1.1100000143051147
        row_D085C.alignment = 'Center'.upper()
        if not True: row_D085C.operator_context = "EXEC_DEFAULT"
        row_D085C.prop(bpy.context.scene, 'sna_show_names', text='', icon_value=742, emboss=True, toggle=True)
        row_D085C.prop(bpy.context.scene, 'sna_show_edit_buttons', text='', icon_value=(92 if bpy.context.scene.sna_show_edit_buttons else 92), emboss=True, toggle=True)
        row_D085C.prop(bpy.context.scene, 'sna_show_delete_buttons', text='', icon_value=21, emboss=True, toggle=True)


class SNA_OT_Delete_Palette_Collection_52Cd8(bpy.types.Operator):
    bl_idname = "sna.delete_palette_collection_52cd8"
    bl_label = "Delete Palette Collection"
    bl_description = "Deletes the currently selected collection"
    bl_options = {"REGISTER", "UNDO"}
    sna_deletename: bpy.props.StringProperty(name='DeleteName', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (len(sna_pallets_65030()) == 1):
            sna_pop_message_272A6_41AB5('Unable to delete palette library!', 'Minimum one palette library.', 'ERROR')
        else:
            PalleteToDelete = bpy.context.scene.sna_pallettoload
            json_file_path = PalleteToDelete
            if os.path.exists(json_file_path):
                os.remove(json_file_path)
            else:
                print(f"JSON file not found at: {json_file_path}")
            bpy.context.scene.sna_pallettoload = sna_pallets_65030()[0][2]
            sna_create_collections_6E2A3(sna_pallets_65030()[0][2])
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class SNA_OT_Copy_Pallet_Eab95(bpy.types.Operator):
    bl_idname = "sna.copy_pallet_eab95"
    bl_label = "Copy Pallet"
    bl_description = "Sync palette from a website link"
    bl_options = {"REGISTER", "UNDO"}
    sna_new_property: bpy.props.StringProperty(name='New Property', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        nodetree['sna_convertz'] = []
        nodetree['sna_col_master_list'] = []
        if 'https://coolors.co/' in bpy.context.window_manager.clipboard:
            for i_DC499 in range(len(bpy.context.window_manager.clipboard.replace('https://coolors.co/', '').replace('palette/', '').split('-'))):
                nodetree['sna_col_master_list'].append(bpy.context.window_manager.clipboard.replace('https://coolors.co/', '').replace('palette/', '').split('-')[i_DC499])
                hex_color_code = bpy.context.window_manager.clipboard.replace('https://coolors.co/', '').replace('palette/', '').split('-')[i_DC499]
                rgb_color = None

                def hex_to_srgb(hex_value):
                    # Remove the '#' if present
                    hex_value = hex_value.lstrip('#')
                    # Convert hex to RGB
                    r = int(hex_value[0:2], 16) / 255.0
                    g = int(hex_value[2:4], 16) / 255.0
                    b = int(hex_value[4:6], 16) / 255.0

                    def gamma_correct(color):
                        if color <= 0.04045:
                            return color / 12.92
                        else:
                            return ((color + 0.055) / 1.055) ** 2.4
                    # Apply gamma correction
                    r_srgb = gamma_correct(r)
                    g_srgb = gamma_correct(g)
                    b_srgb = gamma_correct(b)
                    return (r_srgb, g_srgb, b_srgb)
                # Call the function to convert to RGB
                rgb_color = hex_to_srgb(hex_color_code)
                nodetree['sna_convertz'].append(rgb_color)
            for i_EC7DD in range(len(nodetree['sna_col_master_list'])):
                if str(i_EC7DD) == "0":
                    bpy.context.scene.sna_c1 = (nodetree['sna_convertz'][0][0], nodetree['sna_convertz'][0][1], nodetree['sna_convertz'][0][2], 1.0)
                elif str(i_EC7DD) == "1":
                    bpy.context.scene.sna_c2 = (nodetree['sna_convertz'][1][0], nodetree['sna_convertz'][1][1], nodetree['sna_convertz'][1][2], 1.0)
                elif str(i_EC7DD) == "2":
                    bpy.context.scene.sna_c3 = (nodetree['sna_convertz'][2][0], nodetree['sna_convertz'][2][1], nodetree['sna_convertz'][2][2], 1.0)
                elif str(i_EC7DD) == "3":
                    bpy.context.scene.sna_c4 = (nodetree['sna_convertz'][3][0], nodetree['sna_convertz'][3][1], nodetree['sna_convertz'][3][2], 1.0)
                elif str(i_EC7DD) == "4":
                    bpy.context.scene.sna_c5 = (nodetree['sna_convertz'][4][0], nodetree['sna_convertz'][4][1], nodetree['sna_convertz'][4][2], 1.0)
                else:
                    pass
        else:
            sna_pop_message_272A6_5CB98('No colour data', 'Copy website link from Coolors.co (CTRL + E  shortcut in browser)', 'CANCEL')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Save_Palette_04046(bpy.types.Operator):
    bl_idname = "sna.save_palette_04046"
    bl_label = "Save Palette"
    bl_description = "Save to Palette Library"
    bl_options = {"REGISTER", "UNDO"}
    sna_whattosave: bpy.props.StringProperty(name='whatToSave', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        sna_load_palette_default_4F3BD()
        nodetree['sna_combined_col_save'] = []
        for i_E1267 in range(len(nodetree['sna_col_master_list'])):
            if str(i_E1267) == "0":
                nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_c1[0], bpy.context.scene.sna_c1[1], bpy.context.scene.sna_c1[2], 1.0))
            elif str(i_E1267) == "1":
                nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_c2[0], bpy.context.scene.sna_c2[1], bpy.context.scene.sna_c2[2], 1.0))
            elif str(i_E1267) == "2":
                nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_c3[0], bpy.context.scene.sna_c3[1], bpy.context.scene.sna_c3[2], 1.0))
            elif str(i_E1267) == "3":
                nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_c4[0], bpy.context.scene.sna_c4[1], bpy.context.scene.sna_c4[2], 1.0))
            elif str(i_E1267) == "4":
                nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_c5[0], bpy.context.scene.sna_c5[1], bpy.context.scene.sna_c5[2], 1.0))
            else:
                pass
        assetsz = bpy.context.scene.sna_pallettoload
        colours_lister = nodetree['sna_combined_col_save']
        namerz = bpy.context.scene.sna_save_name
        import json

        def natural_sort_key(name):
            parts = name.split('_')
            numeric_part = []
            non_numeric_part = []
            for part in parts:
                if part.isdigit():
                    numeric_part.append(int(part))
                else:
                    non_numeric_part.append(part)
            return (non_numeric_part, numeric_part)

        def save_color_palette(palette_name, colors):
            json_file_path = assetsz
            existing_data = {}
            # Try to open the JSON file and load existing data
            try:
                with open(json_file_path, "r") as json_file:
                    existing_data = json.load(json_file)
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                # If the file doesn't exist or is empty, create an empty dictionary
                existing_data = {}
            if palette_name in existing_data:
                suffix = 1
                while f"{palette_name}_{suffix}" in existing_data:
                    suffix += 1
                palette_name = f"{palette_name}_{suffix}"
            existing_data[palette_name] = colors
            # Sort the dictionary keys naturally
            sorted_data = {key: existing_data[key] for key in sorted(existing_data, key=natural_sort_key)}
            with open(json_file_path, "w") as json_file:
                json.dump(sorted_data, json_file, indent=4)
        # Example color palette
        palette_name = namerz
        colors = colours_lister
        save_color_palette(palette_name, colors)
        sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
        sna_reset_boolean_D465A()
        sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text='Pallet Name', icon_value=0)
        layout.prop(bpy.context.scene, 'sna_save_name', text='', icon_value=0, emboss=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class SNA_OT_Apply_Random_Color_Bd01C(bpy.types.Operator):
    bl_idname = "sna.apply_random_color_bd01c"
    bl_label = "Apply Random Color"
    bl_description = "Apply the palette to selected objects."
    bl_options = {"REGISTER", "UNDO"}
    sna_colindex: bpy.props.IntProperty(name='colIndex', description='', options={'HIDDEN'}, default=0, subtype='NONE')
    sna_applyint: bpy.props.IntProperty(name='APPLYINT', description='', options={'HIDDEN'}, default=0, subtype='NONE')

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        assetsz = bpy.context.scene.sna_pallettoload
        pallete_name = bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name
        CC1 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col1r
        CC2 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col2r
        CC3 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col3r
        CC4 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col4r
        CC5 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col5r

        def update_json_colors(json_file_path, palette_name, new_colors):
            # Convert bpy_prop_array to standard Python list and filter out (0.0, 0.0, 0.0, 0.0)
            new_colors_list = [list(color) for color in new_colors if tuple(color) != (0.0, 0.0, 0.0, 0.0)]
            # Load the current data from the JSON file
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            # Check if the palette name exists in the JSON data
            if palette_name in data:
                # Update the colors for the given palette name
                data[palette_name] = new_colors_list
                # Write the updated data back to the JSON file
                with open(json_file_path, 'w') as file:
                    json.dump(data, file, indent=4)
            else:
                print(f"Palette '{palette_name}' not found in the JSON file.")
        # Variables
        json_file_path = assetsz
        palette_name = pallete_name
        new_colors = [CC1, CC2, CC3, CC4, CC5]
        # Call the function to update the JSON file
        update_json_colors(json_file_path, palette_name, new_colors)
        bpy.context.scene.sna_indexalt = self.sna_applyint
        if (len(list(bpy.context.view_layer.objects.selected)) > 0):
            for i_56478 in range(len(bpy.context.view_layer.objects.selected)):
                if (bpy.context.view_layer.objects.selected[i_56478].type == 'ARMATURE' or bpy.context.view_layer.objects.selected[i_56478].type == 'VOLUME' or bpy.context.view_layer.objects.selected[i_56478].type == 'POINTCLOUD' or bpy.context.view_layer.objects.selected[i_56478].type == 'LATTICE' or bpy.context.view_layer.objects.selected[i_56478].type == 'META' or bpy.context.view_layer.objects.selected[i_56478].type == 'FONT' or bpy.context.view_layer.objects.selected[i_56478].type == 'SURFACE' or bpy.context.view_layer.objects.selected[i_56478].type == 'CURVE' or bpy.context.view_layer.objects.selected[i_56478].type == 'MESH'):
                    if bpy.context.view_layer.objects.selected[i_56478].type == 'ARMATURE':
                        pass
                    else:
                        obxx = bpy.context.view_layer.objects.selected[i_56478]
                        assetsz = bpy.context.scene.sna_pallettoload
                        pallete_name = bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name
                        import random
                        # Variables from another script
                        json_file_path = assetsz
                        entry_to_read_from = pallete_name
                        # Load the JSON file
                        with open(json_file_path, "r") as file:
                            data = json.load(file)
                        colors_from_json = data.get(entry_to_read_from, [])
                        # Ensure colors_from_json is a list
                        if not isinstance(colors_from_json, list):
                            colors_from_json = [colors_from_json]
                        colors = colors_from_json
                        # Ensure obxx is a list or collection of objects
                        if isinstance(obxx, bpy.types.Object):
                            objects_list = [obxx]
                        else:
                            objects_list = obxx

                        def set_shader_color(material, color):
                            """Set the color of the shader in the material."""
                            for node in material.node_tree.nodes:
                                if node.type == 'BSDF_PRINCIPLED':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_DIFFUSE':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_GLOSSY':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_TRANSPARENT':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_TOON':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_REFRACTION':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_TRANSLUCENT':
                                    node.inputs[0].default_value = color
                                elif node.type == 'EMISSION':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_GLASS':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_HAIR':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_HAIR_PRINCIPLED':
                                    node.inputs[0].default_value = color
                                elif node.type == 'BSDF_VELVET':
                                    node.inputs[0].default_value = color
                            # Add more shader types as needed
                        for obj in objects_list:
                            if not obj.material_slots:
                                # Create a new material
                                material_name = "Material_" + obj.name
                                material = bpy.data.materials.new(name=material_name)
                                obj.data.materials.append(material)
                                material.use_nodes = True
                                nodes = material.node_tree.nodes
                                nodes.clear()
                                # Create Principled BSDF node
                                principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                                color = random.choice(colors)
                                principled_bsdf.inputs[0].default_value = color
                                # Create Material Output node
                                material_output = nodes.new(type='ShaderNodeOutputMaterial')
                                # Link Principled BSDF to Material Output
                                links = material.node_tree.links
                                link = links.new(principled_bsdf.outputs[0], material_output.inputs[0])
                            else:
                                for mat_slot in obj.material_slots:
                                    material = mat_slot.material
                                    if material and material.use_nodes:
                                        color = random.choice(colors)
                                        set_shader_color(material, color)
        else:
            sna_pop_message_272A6_EA733('We need objects! ', 'No objects selected', 'ERROR')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def sna_create_collections_6E2A3(fileToLoad):
    nodetree['sna_c_namez'] = []
    nodetree['sna_c_col_rgb'] = []
    bpy.context.scene.sna_collectionscolours.clear()
    assetsz = fileToLoad
    import json

    def load_color_palettes(json_file_path):
        try:
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            data = {}
        palette_names =  nodetree['sna_c_namez']
        palette_colors = nodetree['sna_c_col_rgb']
        for palette_name, colors in data.items():
            palette_names.append(palette_name)
            palette_colors.append(colors)
        return palette_names, palette_colors
    json_file_path = assetsz
    palette_names, palette_colors = load_color_palettes(json_file_path)
    for i_9C094 in range(len(nodetree['sna_c_col_rgb'])):
        nodetree['sna_col_capture_amount_collection'] = 0
        item_E3F74 = bpy.context.scene.sna_collectionscolours.add()
        nodetree['sna_col_capture_amount_collection'] = len(nodetree['sna_c_col_rgb'][i_9C094])
        item_E3F74.name = nodetree['sna_c_namez'][i_9C094]
        for i_C1056 in range(len(nodetree['sna_c_col_rgb'][i_9C094])):
            if str(i_C1056) == "0":
                item_E3F74.col1r = nodetree['sna_c_col_rgb'][i_9C094][0]
            elif str(i_C1056) == "1":
                item_E3F74.col2r = nodetree['sna_c_col_rgb'][i_9C094][1]
            elif str(i_C1056) == "2":
                item_E3F74.col3r = nodetree['sna_c_col_rgb'][i_9C094][2]
            elif str(i_C1056) == "3":
                item_E3F74.col4r = nodetree['sna_c_col_rgb'][i_9C094][3]
            elif str(i_C1056) == "4":
                item_E3F74.col5r = nodetree['sna_c_col_rgb'][i_9C094][4]
            else:
                pass
        item_E3F74.colmount = nodetree['sna_col_capture_amount_collection']
    return


class SNA_OT_Create_Collection_7B813(bpy.types.Operator):
    bl_idname = "sna.create_collection_7b813"
    bl_label = "Create Collection"
    bl_description = "This creates a new palette collection"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = 'sna_filetoname'
    sna_filetoname: bpy.props.StringProperty(name='fileToName', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if ('' == self.sna_filetoname):
            pass
        else:
            SaveLoction = os.path.join(os.path.dirname(__file__), 'assets', 'pallets')
            namer = self.sna_filetoname
            # Sample JSON structure as a string
            data = '''
            {
                "Palette 1": [
                    [
                        1.0,
                        1.0,
                        1.0,
                        1.0
                    ],
                    [
                        1.0,
                        1.0,
                        1.0,
                        1.0
                    ],
                    [
                        1.0,
                        1.0,
                        1.0,
                        1.0
                    ],
                    [
                        1.0,
                        1.0,
                        1.0,
                        1.0
                    ],
                    [
                        1.0,
                        1.0,
                        1.0,
                        1.0
                    ]
                ]
            }
            '''
            # File name and location
            filename = namer + ".json"
            location = SaveLoction
            # Combine the file name and location to get the full path
            file_path = os.path.join(location, filename)
            # Parse the JSON string into a Python dictionary
            json_data = json.loads(data)
            # Write the JSON data to the file
            with open(file_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            bpy.context.scene.sna_pallettoload = bpy.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'pallets') + '\\' + self.sna_filetoname + '.json')
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            bpy.context.scene.sna_pallet_list = self.sna_filetoname
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text='Name your pallet', icon_value=0)
        layout.prop(self, 'sna_filetoname', text='', icon_value=0, emboss=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class SNA_OT_Edit_Palette_2C0Da(bpy.types.Operator):
    bl_idname = "sna.edit_palette_2c0da"
    bl_label = "Edit Palette"
    bl_description = "Remove unwanted colors from a palette"
    bl_options = {"REGISTER", "UNDO"}
    sna_openeditname: bpy.props.IntProperty(name='OpenEditName', description='', options={'HIDDEN'}, default=0, subtype='NONE')

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        bpy.context.scene.sna_indexalt = self.sna_openeditname
        bpy.ops.wm.call_panel(name="SNA_PT_POPUPPANEL_2CC19", keep_open=True)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_POPUPPANEL_2CC19(bpy.types.Panel):
    bl_label = 'PopupPanel'
    bl_idname = 'SNA_PT_POPUPPANEL_2CC19'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_context = ''
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        col_81AFF = layout.column(heading='', align=True)
        col_81AFF.alert = False
        col_81AFF.enabled = True
        col_81AFF.active = True
        col_81AFF.use_property_split = True
        col_81AFF.use_property_decorate = False
        col_81AFF.scale_x = 1.0
        col_81AFF.scale_y = 1.0
        col_81AFF.alignment = 'Expand'.upper()
        if not True: col_81AFF.operator_context = "EXEC_DEFAULT"
        box_E80E2 = col_81AFF.box()
        box_E80E2.alert = False
        box_E80E2.enabled = True
        box_E80E2.active = True
        box_E80E2.use_property_split = True
        box_E80E2.use_property_decorate = False
        box_E80E2.alignment = 'Expand'.upper()
        box_E80E2.scale_x = 1.0
        box_E80E2.scale_y = 1.0
        if not True: box_E80E2.operator_context = "EXEC_DEFAULT"
        row_B1181 = box_E80E2.row(heading='', align=False)
        row_B1181.alert = False
        row_B1181.enabled = True
        row_B1181.active = True
        row_B1181.use_property_split = False
        row_B1181.use_property_decorate = False
        row_B1181.scale_x = 1.0
        row_B1181.scale_y = 1.0
        row_B1181.alignment = 'Center'.upper()
        if not True: row_B1181.operator_context = "EXEC_DEFAULT"
        row_B1181.label(text='Palette: ' + bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name, icon_value=0)
        row_BBCF2 = box_E80E2.row(heading='', align=True)
        row_BBCF2.alert = False
        row_BBCF2.enabled = True
        row_BBCF2.active = True
        row_BBCF2.use_property_split = True
        row_BBCF2.use_property_decorate = False
        row_BBCF2.scale_x = 1.0
        row_BBCF2.scale_y = 1.0
        row_BBCF2.alignment = 'Expand'.upper()
        if not True: row_BBCF2.operator_context = "EXEC_DEFAULT"
        for i_80EFE in range(bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].colmount):
            if str(i_80EFE) == "0":
                col_8A3B2 = row_BBCF2.column(heading='', align=True)
                col_8A3B2.alert = False
                col_8A3B2.enabled = True
                col_8A3B2.active = True
                col_8A3B2.use_property_split = False
                col_8A3B2.use_property_decorate = False
                col_8A3B2.scale_x = 2.0
                col_8A3B2.scale_y = 1.5
                col_8A3B2.alignment = 'Expand'.upper()
                if not True: col_8A3B2.operator_context = "EXEC_DEFAULT"
                col_8A3B2.prop(bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt], 'col1r', text='', icon_value=0, emboss=True, expand=False, toggle=True, invert_checkbox=True)
                op = col_8A3B2.operator('sna.delete_color_1_9bd49', text='', icon_value=32, emboss=True, depress=False)
            elif str(i_80EFE) == "1":
                col_267AD = row_BBCF2.column(heading='', align=True)
                col_267AD.alert = False
                col_267AD.enabled = True
                col_267AD.active = True
                col_267AD.use_property_split = False
                col_267AD.use_property_decorate = False
                col_267AD.scale_x = 2.0
                col_267AD.scale_y = 1.5
                col_267AD.alignment = 'Expand'.upper()
                if not True: col_267AD.operator_context = "EXEC_DEFAULT"
                col_267AD.prop(bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt], 'col2r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=True, invert_checkbox=False)
                op = col_267AD.operator('sna.delete_color_2_a6b7d', text='', icon_value=32, emboss=True, depress=False)
            elif str(i_80EFE) == "2":
                col_18CD7 = row_BBCF2.column(heading='', align=True)
                col_18CD7.alert = False
                col_18CD7.enabled = True
                col_18CD7.active = True
                col_18CD7.use_property_split = False
                col_18CD7.use_property_decorate = False
                col_18CD7.scale_x = 2.0
                col_18CD7.scale_y = 1.5
                col_18CD7.alignment = 'Expand'.upper()
                if not True: col_18CD7.operator_context = "EXEC_DEFAULT"
                col_18CD7.prop(bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt], 'col3r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=True, invert_checkbox=False)
                op = col_18CD7.operator('sna.delete_color_3_b4bee', text='', icon_value=32, emboss=True, depress=False)
            elif str(i_80EFE) == "3":
                col_9DB48 = row_BBCF2.column(heading='', align=True)
                col_9DB48.alert = False
                col_9DB48.enabled = True
                col_9DB48.active = True
                col_9DB48.use_property_split = False
                col_9DB48.use_property_decorate = False
                col_9DB48.scale_x = 2.0
                col_9DB48.scale_y = 1.5
                col_9DB48.alignment = 'Expand'.upper()
                if not True: col_9DB48.operator_context = "EXEC_DEFAULT"
                col_9DB48.prop(bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt], 'col4r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=True, invert_checkbox=False)
                op = col_9DB48.operator('sna.delete_color_4_75ab8', text='', icon_value=32, emboss=True, depress=False)
            elif str(i_80EFE) == "4":
                col_B47FE = row_BBCF2.column(heading='', align=True)
                col_B47FE.alert = False
                col_B47FE.enabled = True
                col_B47FE.active = True
                col_B47FE.use_property_split = False
                col_B47FE.use_property_decorate = False
                col_B47FE.scale_x = 2.0
                col_B47FE.scale_y = 1.5
                col_B47FE.alignment = 'Expand'.upper()
                if not True: col_B47FE.operator_context = "EXEC_DEFAULT"
                col_B47FE.prop(bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt], 'col5r', text='', icon_value=0, emboss=True, expand=False, slider=False, toggle=True, invert_checkbox=False)
                op = col_B47FE.operator('sna.delete_color_5_d27a6', text='', icon_value=32, emboss=True, depress=False)
            else:
                pass


def sna_reset_boolean_D465A():
    bpy.context.scene.sna_col_del_tog_1 = False
    bpy.context.scene.sna_col_del_tog_2 = False
    bpy.context.scene.sna_col_del_tog_3 = False
    bpy.context.scene.sna_col_del_tog_4 = False
    bpy.context.scene.sna_col_del_tog_5 = False


class SNA_OT_Delete_Palette_0980F(bpy.types.Operator):
    bl_idname = "sna.delete_palette_0980f"
    bl_label = "Delete Palette"
    bl_description = "Delete the colour pallet"
    bl_options = {"REGISTER", "UNDO"}
    sna_name: bpy.props.StringProperty(name='Name', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        assetsz = bpy.context.scene.sna_pallettoload
        itemz = self.sna_name
        warning_printed = None
        import json
        import io

        def remove_color_palette(json_file_path, palette_name):
            try:
                with open(json_file_path, "r") as json_file:
                    data = json.load(json_file)
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                data = {}
            warning_printed = False  # Initialize a variable to track if the warning was printed
            if palette_name in data:
                if len(data) == 1:
                    warning_printed = True
                if not warning_printed:
                    del data[palette_name]
                    with open(json_file_path, "w") as json_file:
                        json.dump(data, json_file, indent=4)
            else:
                print(f"Palette '{palette_name}' not found in the JSON file.")
            return warning_printed  # Return True if the warning was printed, False otherwise
        # usage:
        json_file_path = assetsz
        palette_name_to_remove = itemz
        warning_printed = remove_color_palette(json_file_path, palette_name_to_remove)
        bpy.context.scene.sna_indexalt = 0
        if warning_printed:
            sna_pop_message_272A6_DA480('Unable to delete palette!', 'Minimum one palette in a palette library.', 'ERROR')
        sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
        sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Fine_Tune_Delete_35613(bpy.types.Operator):
    bl_idname = "sna.fine_tune_delete_35613"
    bl_label = "Fine tune Delete"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    sna_pallet_name_fine: bpy.props.StringProperty(name='pallet_name_fine', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        nodetree['sna_fine_tune_delete'] = []
        if (True == bpy.context.scene.sna_col_del_tog_1):
            nodetree['sna_fine_tune_delete'].append(0)
        if (True == bpy.context.scene.sna_col_del_tog_2):
            nodetree['sna_fine_tune_delete'].append(1)
        if (True == bpy.context.scene.sna_col_del_tog_3):
            nodetree['sna_fine_tune_delete'].append(2)
        if (True == bpy.context.scene.sna_col_del_tog_4):
            nodetree['sna_fine_tune_delete'].append(3)
        if (True == bpy.context.scene.sna_col_del_tog_5):
            nodetree['sna_fine_tune_delete'].append(4)
        assetsz = bpy.context.scene.sna_pallettoload
        colours_list_remove = nodetree['sna_fine_tune_delete']
        pallete_name = bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name
        has_only_one_color = None
        # Path to your JSON file
        json_file_path = assetsz
        # Named entry to check for number of elements (colors)
        palette_name = pallete_name
        # Load and parse the JSON file
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
        # Initialize boolean property
        has_only_one_color = False
        # Check if the named palette exists in the JSON data
        if palette_name in json_data:
            palette_colors = json_data[palette_name]
            # Check if the palette has only one color
            if len(palette_colors) == 1:
                has_only_one_color = True
        print(f"Does the palette '{palette_name}' have only one color? {has_only_one_color}")
        if has_only_one_color:
            sna_pop_message_272A6_0C6FA('Unable to remove a single color', 'To remove this color, delete this palette row.', 'ERROR')
        else:
            assetsz = bpy.context.scene.sna_pallettoload
            colours_list_remove = nodetree['sna_fine_tune_delete']
            pallete_name = bpy.context.scene.sna_collectionscolours[bpy.context.scene.sna_indexalt].name
            status_message = None
            # Path to your JSON file
            json_file_path = assetsz
            # Named entry to remove elements from
            entry_to_remove_from = pallete_name
            # List of integers to match and remove
            integers_to_remove = colours_list_remove
            # Load and parse the JSON file
            with open(json_file_path, 'r') as f:
                json_data = json.load(f)
            # Check if the named entry exists in the JSON data
            if entry_to_remove_from in json_data:
                entry_list = json_data[entry_to_remove_from]
                # Reverse the integers to remove so we remove them in reverse order
                integers_to_remove.reverse()
                # Remove elements at the provided reversed indices
                for i in integers_to_remove:
                    if i < len(entry_list):
                        entry_list.pop(i)
                # Print the elements that will be removed
                print("Elements to be removed:")
                for i in integers_to_remove:
                    if i < len(entry_list):
                        print(entry_list[i])
                # Update the JSON data with the modified list
                json_data[entry_to_remove_from] = entry_list
                # Save the updated JSON data back to the file
                with open(json_file_path, 'w') as f:
                    json.dump(json_data, f, indent=4)
            else:
                print(f"The named entry '{entry_to_remove_from}' was not found in the JSON data.")
            sna_reset_boolean_D465A()
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


@persistent
def save_post_handler_21F4E(dummy):
    for i_18D0F in range(len(bpy.context.scene.sna_collectionscolours)):
        assetsz = bpy.context.scene.sna_pallettoload
        CC1 = bpy.context.scene.sna_collectionscolours[i_18D0F].col1r
        CC2 = bpy.context.scene.sna_collectionscolours[i_18D0F].col2r
        CC3 = bpy.context.scene.sna_collectionscolours[i_18D0F].col3r
        CC4 = bpy.context.scene.sna_collectionscolours[i_18D0F].col4r
        CC5 = bpy.context.scene.sna_collectionscolours[i_18D0F].col5r
        INDEXS = [i_18D0F]

        def update_json_colors(json_file_path, new_colors, palette_indices):
            # Convert bpy_prop_array to standard Python list and filter out (0.0, 0.0, 0.0, 0.0)
            new_colors_list = [list(color) for color in new_colors if tuple(color) != (0.0, 0.0, 0.0, 0.0)]
            # Load the current data from the JSON file
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            # Loop through the provided palette indices and update their colors
            for index in palette_indices:
                palette_name = list(data.keys())[index]
                data[palette_name] = new_colors_list
            # Write the updated data back to the JSON file
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)
        # Variables
        json_file_path = assetsz  # Assuming 'assetsz' is the correct path to your JSON file
        new_colors = [CC1, CC2, CC3, CC4, CC5]  # Assuming CC1, CC2, etc. are defined elsewhere in your script
        palette_indices = INDEXS
        # Call the function to update the JSON file
        update_json_colors(json_file_path, new_colors, palette_indices)


def sna_updatejsondata_7DF1D():
    for i_3D2E7 in range(len(bpy.context.scene.sna_collectionscolours)):
        assetsz = bpy.context.scene.sna_pallettoload
        CC1 = bpy.context.scene.sna_collectionscolours[i_3D2E7].col1r
        CC2 = bpy.context.scene.sna_collectionscolours[i_3D2E7].col2r
        CC3 = bpy.context.scene.sna_collectionscolours[i_3D2E7].col3r
        CC4 = bpy.context.scene.sna_collectionscolours[i_3D2E7].col4r
        CC5 = bpy.context.scene.sna_collectionscolours[i_3D2E7].col5r
        INDEXS = [i_3D2E7]

        def update_json_colors(json_file_path, new_colors, palette_indices):
            # Convert bpy_prop_array to standard Python list and filter out (0.0, 0.0, 0.0, 0.0)
            new_colors_list = [list(color) for color in new_colors if tuple(color) != (0.0, 0.0, 0.0, 0.0)]
            # Load the current data from the JSON file
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            # Loop through the provided palette indices and update their colors
            for index in palette_indices:
                palette_name = list(data.keys())[index]
                data[palette_name] = new_colors_list
            # Write the updated data back to the JSON file
            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)
        # Variables
        json_file_path = assetsz  # Assuming 'assetsz' is the correct path to your JSON file
        new_colors = [CC1, CC2, CC3, CC4, CC5]  # Assuming CC1, CC2, etc. are defined elsewhere in your script
        palette_indices = INDEXS
        # Call the function to update the JSON file
        update_json_colors(json_file_path, new_colors, palette_indices)


def sna_load_palette_default_4F3BD():
    if property_exists("bpy.context.scene.sna_pallet_list", globals(), locals()):
        if (bpy.context.scene.sna_pallet_list == 'Palette Library'):
            bpy.context.scene.sna_pallettoload = os.path.join(os.path.dirname(__file__), 'assets', 'pallets') + '\\' + bpy.context.scene.sna_pallet_list + '.json'
            sna_create_collections_6E2A3(os.path.join(os.path.dirname(__file__), 'assets', 'pallets') + '\\' + bpy.context.scene.sna_pallet_list + '.json')
            return


class SNA_OT_Paint_Selected_Objects_E873B(bpy.types.Operator):
    bl_idname = "sna.paint_selected_objects_e873b"
    bl_label = "Paint Selected Objects"
    bl_description = "Paint all selected objects with this palette."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        if (len(list(bpy.context.view_layer.objects.selected)) > 0):
            for i_35D08 in range(len(bpy.context.view_layer.objects.selected)):
                if (bpy.context.view_layer.objects.selected[i_35D08].type == 'ARMATURE' or bpy.context.view_layer.objects.selected[i_35D08].type == 'VOLUME' or bpy.context.view_layer.objects.selected[i_35D08].type == 'POINTCLOUD' or bpy.context.view_layer.objects.selected[i_35D08].type == 'LATTICE' or bpy.context.view_layer.objects.selected[i_35D08].type == 'META' or bpy.context.view_layer.objects.selected[i_35D08].type == 'FONT' or bpy.context.view_layer.objects.selected[i_35D08].type == 'SURFACE' or bpy.context.view_layer.objects.selected[i_35D08].type == 'CURVE' or bpy.context.view_layer.objects.selected[i_35D08].type == 'MESH'):
                    if bpy.context.view_layer.objects.selected[i_35D08].type == 'ARMATURE':
                        pass
                    else:
                        obxx = bpy.context.view_layer.objects.selected[i_35D08]
                        C1 = bpy.context.scene.sna_c1
                        C2 = bpy.context.scene.sna_c2
                        C3 = bpy.context.scene.sna_c3
                        C4 = bpy.context.scene.sna_c4
                        C5 = bpy.context.scene.sna_c5
                        import random

                        def set_shader_color(material, color):
                            """Set the color of the shader in the material."""
                            for node in material.node_tree.nodes:
                                if node.type in ['BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'BSDF_GLOSSY', 'BSDF_TRANSPARENT', 'BSDF_TOON', 'BSDF_REFRACTION', 'SUBSURFACE_SCATTERING', 'BSDF_TRANSLUCENT', 'EMISSION', 'BSDF_GLASS', 'BSDF_HAIR', 'BSDF_HAIR_PRINCIPLED', 'BSDF_VELVET']:
                                    node.inputs[0].default_value = color
                        # Assuming you bring in the objects_list and colors like this:
                        objects_list = obxx
                        colors = [C1, C2, C3, C4, C5]
                        objects_list = [obxx] if isinstance(obxx, bpy.types.Object) else obxx
                        # For the sake of example, I'll define dummy values for objects_list and colors:
                        #objects_list = bpy.context.selected_objects
                        #colors = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1), (0, 1, 1, 1)]  # RGBA values for Red, Green, Blue, Yellow, Cyan
                        for obj in objects_list:
                            if not obj.material_slots:
                                # Create a new material
                                material_name = "Material_" + obj.name
                                material = bpy.data.materials.new(name=material_name)
                                obj.data.materials.append(material)
                                material.use_nodes = True
                                nodes = material.node_tree.nodes
                                nodes.clear()
                                # Create Principled BSDF node
                                principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                                color = random.choice(colors)
                                principled_bsdf.inputs[0].default_value = color
                                # Create Material Output node
                                material_output = nodes.new(type='ShaderNodeOutputMaterial')
                                # Link Principled BSDF to Material Output
                                links = material.node_tree.links
                                link = links.new(principled_bsdf.outputs[0], material_output.inputs[0])
                            else:
                                for mat_slot in obj.material_slots:
                                    material = mat_slot.material
                                    if material and material.use_nodes:
                                        color = random.choice(colors)
                                        set_shader_color(material, color)
        else:
            sna_pop_message_272A6_3E8A9('We need objects! ', 'No objects selected', 'ERROR')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


@persistent
def load_post_handler_E9244(dummy):
    bpy.context.scene.sna_main_color = (0.63729327917099, 1.0, 0.15341612696647644, 1.0)


class SNA_PT_COLOR_SCHEMES_C37D9(bpy.types.Panel):
    bl_label = 'Color Schemes'
    bl_idname = 'SNA_PT_COLOR_SCHEMES_C37D9'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorful'
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
        row_7AA96 = layout.row(heading='', align=False)
        row_7AA96.alert = False
        row_7AA96.enabled = True
        row_7AA96.active = True
        row_7AA96.use_property_split = False
        row_7AA96.use_property_decorate = False
        row_7AA96.scale_x = 3.0
        row_7AA96.scale_y = 1.5
        row_7AA96.alignment = 'Center'.upper()
        if not True: row_7AA96.operator_context = "EXEC_DEFAULT"
        op = row_7AA96.operator('sna.cyclecolorscheme_b6ff5', text='', icon_value=6, emboss=True, depress=False)
        op.sna_scrolldirection = 'MINUS'
        box_9BA46 = row_7AA96.box()
        box_9BA46.alert = False
        box_9BA46.enabled = True
        box_9BA46.active = True
        box_9BA46.use_property_split = False
        box_9BA46.use_property_decorate = False
        box_9BA46.alignment = 'Expand'.upper()
        box_9BA46.scale_x = 2.4000000953674316
        box_9BA46.scale_y = 0.7000000476837158
        if not True: box_9BA46.operator_context = "EXEC_DEFAULT"
        box_9BA46.label(text=bpy.context.scene.sna_enumscroller, icon_value=0)
        op = row_7AA96.operator('sna.cyclecolorscheme_b6ff5', text='', icon_value=4, emboss=True, depress=False)
        op.sna_scrolldirection = 'PLUS'
        box_86804 = layout.box()
        box_86804.alert = False
        box_86804.enabled = True
        box_86804.active = True
        box_86804.use_property_split = False
        box_86804.use_property_decorate = False
        box_86804.alignment = 'Expand'.upper()
        box_86804.scale_x = 1.0
        box_86804.scale_y = 1.0
        if not True: box_86804.operator_context = "EXEC_DEFAULT"
        row_FAE6F = box_86804.row(heading='', align=False)
        row_FAE6F.alert = False
        row_FAE6F.enabled = True
        row_FAE6F.active = True
        row_FAE6F.use_property_split = False
        row_FAE6F.use_property_decorate = False
        row_FAE6F.scale_x = 1.0
        row_FAE6F.scale_y = 1.7000000476837158
        row_FAE6F.alignment = 'Expand'.upper()
        if not True: row_FAE6F.operator_context = "EXEC_DEFAULT"
        if bpy.context.scene.sna_enumselector == "Complementary":
            row_81B85 = row_FAE6F.row(heading='', align=False)
            row_81B85.alert = False
            row_81B85.enabled = True
            row_81B85.active = True
            row_81B85.use_property_split = False
            row_81B85.use_property_decorate = False
            row_81B85.scale_x = 1.0
            row_81B85.scale_y = 1.0
            row_81B85.alignment = 'Expand'.upper()
            if not True: row_81B85.operator_context = "EXEC_DEFAULT"
            row_81B85.label(text='', icon_value=495)
            row_81B85.prop(bpy.context.scene, 'sna_main_color', text='', icon_value=0, emboss=True)
            row_81B85.prop(bpy.context.scene, 'sna_complcolor', text='', icon_value=0, emboss=True)
        elif bpy.context.scene.sna_enumselector == "Split Complementary":
            row_CB2BE = row_FAE6F.row(heading='', align=False)
            row_CB2BE.alert = False
            row_CB2BE.enabled = True
            row_CB2BE.active = True
            row_CB2BE.use_property_split = False
            row_CB2BE.use_property_decorate = False
            row_CB2BE.scale_x = 1.0
            row_CB2BE.scale_y = 1.0
            row_CB2BE.alignment = 'Expand'.upper()
            if not True: row_CB2BE.operator_context = "EXEC_DEFAULT"
            row_CB2BE.label(text='', icon_value=495)
            row_CB2BE.prop(bpy.context.scene, 'sna_main_color', text='', icon_value=0, emboss=True)
            row_CB2BE.prop(bpy.context.scene, 'sna_split1', text='', icon_value=0, emboss=True)
            row_CB2BE.prop(bpy.context.scene, 'sna_split2', text='', icon_value=0, emboss=True)
        elif bpy.context.scene.sna_enumselector == "Triad":
            row_7CD42 = row_FAE6F.row(heading='', align=False)
            row_7CD42.alert = False
            row_7CD42.enabled = True
            row_7CD42.active = True
            row_7CD42.use_property_split = False
            row_7CD42.use_property_decorate = False
            row_7CD42.scale_x = 1.0
            row_7CD42.scale_y = 1.0
            row_7CD42.alignment = 'Expand'.upper()
            if not True: row_7CD42.operator_context = "EXEC_DEFAULT"
            row_7CD42.label(text='', icon_value=495)
            row_7CD42.prop(bpy.context.scene, 'sna_main_color', text='', icon_value=0, emboss=True)
            row_7CD42.prop(bpy.context.scene, 'sna_triad_1', text='', icon_value=0, emboss=True)
            row_7CD42.prop(bpy.context.scene, 'sna_triad_2', text='', icon_value=0, emboss=True)
        elif bpy.context.scene.sna_enumselector == "Tetrad":
            row_AB049 = row_FAE6F.row(heading='', align=False)
            row_AB049.alert = False
            row_AB049.enabled = True
            row_AB049.active = True
            row_AB049.use_property_split = False
            row_AB049.use_property_decorate = False
            row_AB049.scale_x = 1.0
            row_AB049.scale_y = 1.0
            row_AB049.alignment = 'Expand'.upper()
            if not True: row_AB049.operator_context = "EXEC_DEFAULT"
            row_AB049.label(text='', icon_value=495)
            row_AB049.prop(bpy.context.scene, 'sna_main_color', text='', icon_value=0, emboss=True)
            row_AB049.prop(bpy.context.scene, 'sna_tetradc1', text='', icon_value=0, emboss=True)
            row_AB049.prop(bpy.context.scene, 'sna_tetradc2', text='', icon_value=0, emboss=True)
            row_AB049.prop(bpy.context.scene, 'sna_tetradc3', text='', icon_value=0, emboss=True)
        elif bpy.context.scene.sna_enumselector == "Square":
            row_95EC6 = row_FAE6F.row(heading='', align=False)
            row_95EC6.alert = False
            row_95EC6.enabled = True
            row_95EC6.active = True
            row_95EC6.use_property_split = False
            row_95EC6.use_property_decorate = False
            row_95EC6.scale_x = 1.0
            row_95EC6.scale_y = 1.0
            row_95EC6.alignment = 'Expand'.upper()
            if not True: row_95EC6.operator_context = "EXEC_DEFAULT"
            row_95EC6.label(text='', icon_value=495)
            row_95EC6.prop(bpy.context.scene, 'sna_main_color', text='', icon_value=0, emboss=True)
            row_95EC6.prop(bpy.context.scene, 'sna_square1', text='', icon_value=0, emboss=True)
            row_95EC6.prop(bpy.context.scene, 'sna_square2', text='', icon_value=0, emboss=True)
            row_95EC6.prop(bpy.context.scene, 'sna_square3', text='', icon_value=0, emboss=True)
        elif bpy.context.scene.sna_enumselector == "Analogous":
            row_C51F9 = row_FAE6F.row(heading='', align=False)
            row_C51F9.alert = False
            row_C51F9.enabled = True
            row_C51F9.active = True
            row_C51F9.use_property_split = False
            row_C51F9.use_property_decorate = False
            row_C51F9.scale_x = 1.0
            row_C51F9.scale_y = 1.0
            row_C51F9.alignment = 'Expand'.upper()
            if not True: row_C51F9.operator_context = "EXEC_DEFAULT"
            row_C51F9.label(text='', icon_value=495)
            row_C51F9.prop(bpy.context.scene, 'sna_main_color', text='', icon_value=0, emboss=True)
            row_C51F9.prop(bpy.context.scene, 'sna_analog1', text='', icon_value=0, emboss=True)
            row_C51F9.prop(bpy.context.scene, 'sna_analog2', text='', icon_value=0, emboss=True)
            row_C51F9.prop(bpy.context.scene, 'sna_analog3', text='', icon_value=0, emboss=True)
            row_C51F9.prop(bpy.context.scene, 'sna_analog4', text='', icon_value=0, emboss=True)
        elif bpy.context.scene.sna_enumselector == "Monochromatic":
            row_66B3E = row_FAE6F.row(heading='', align=False)
            row_66B3E.alert = False
            row_66B3E.enabled = True
            row_66B3E.active = True
            row_66B3E.use_property_split = False
            row_66B3E.use_property_decorate = False
            row_66B3E.scale_x = 1.0
            row_66B3E.scale_y = 1.0
            row_66B3E.alignment = 'Expand'.upper()
            if not True: row_66B3E.operator_context = "EXEC_DEFAULT"
            row_66B3E.label(text='', icon_value=495)
            row_66B3E.prop(bpy.context.scene, 'sna_main_color', text='', icon_value=0, emboss=True)
            row_66B3E.prop(bpy.context.scene, 'sna_mono1', text='', icon_value=0, emboss=True)
            row_66B3E.prop(bpy.context.scene, 'sna_mono2', text='', icon_value=0, emboss=True)
            row_66B3E.prop(bpy.context.scene, 'sna_mono3', text='', icon_value=0, emboss=True)
            row_66B3E.prop(bpy.context.scene, 'sna_mono4', text='', icon_value=0, emboss=True)
        else:
            pass
        row_25119 = box_86804.row(heading='', align=False)
        row_25119.alert = False
        row_25119.enabled = True
        row_25119.active = True
        row_25119.use_property_split = False
        row_25119.use_property_decorate = False
        row_25119.scale_x = 1.0
        row_25119.scale_y = 1.5
        row_25119.alignment = 'Expand'.upper()
        if not True: row_25119.operator_context = "EXEC_DEFAULT"
        op = row_25119.operator('sna.save_json_pallete_814b1', text='Save ', icon_value=706, emboss=True, depress=False)
        op.sna_whattosave = ''


class SNA_OT_Save_Json_Pallete_814B1(bpy.types.Operator):
    bl_idname = "sna.save_json_pallete_814b1"
    bl_label = "Save Json pallete"
    bl_description = "Save color palette to collection."
    bl_options = {"REGISTER", "UNDO"}
    sna_whattosave: bpy.props.StringProperty(name='whatToSave', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        sna_updatejsondata_7DF1D()
        nodetree['sna_combined_col_save'] = []
        if bpy.context.scene.sna_enumselector == "Complementary":
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_main_color[0], bpy.context.scene.sna_main_color[1], bpy.context.scene.sna_main_color[2], bpy.context.scene.sna_main_color[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_complcolor[0], bpy.context.scene.sna_complcolor[1], bpy.context.scene.sna_complcolor[2], bpy.context.scene.sna_complcolor[3]))
            assetsz = bpy.context.scene.sna_pallettoload
            colours_lister = nodetree['sna_combined_col_save']
            namerz = self.sna_whattosave
            import json

            def save_color_palette(palette_name, colors):
                json_file_path = assetsz
                existing_data = {}
                # Try to open the JSON file and load existing data
                try:
                    with open(json_file_path, "r") as json_file:
                        existing_data = json.load(json_file)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    # If the file doesn't exist or is empty, create an empty dictionary
                    existing_data = {}
                if palette_name in existing_data:
                    suffix = 1
                    while f"{palette_name}_{suffix}" in existing_data:
                        suffix += 1
                    palette_name = f"{palette_name}_{suffix}"
                existing_data[palette_name] = colors
                # Sort the dictionary keys in alphanumeric order
                sorted_data = {key: existing_data[key] for key in sorted(existing_data)}
                with open(json_file_path, "w") as json_file:
                    json.dump(sorted_data, json_file, indent=4)
            # Example color palette
            palette_name = namerz
            colors = colours_lister
            save_color_palette(palette_name, colors)
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        elif bpy.context.scene.sna_enumselector == "Split Complementary":
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_main_color[0], bpy.context.scene.sna_main_color[1], bpy.context.scene.sna_main_color[2], bpy.context.scene.sna_main_color[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_split1[0], bpy.context.scene.sna_split1[1], bpy.context.scene.sna_split1[2], bpy.context.scene.sna_split1[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_split2[0], bpy.context.scene.sna_split2[1], bpy.context.scene.sna_split2[2], bpy.context.scene.sna_split2[3]))
            assetsz = bpy.context.scene.sna_pallettoload
            colours_lister = nodetree['sna_combined_col_save']
            namerz = self.sna_whattosave
            import json

            def save_color_palette(palette_name, colors):
                json_file_path = assetsz
                existing_data = {}
                # Try to open the JSON file and load existing data
                try:
                    with open(json_file_path, "r") as json_file:
                        existing_data = json.load(json_file)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    # If the file doesn't exist or is empty, create an empty dictionary
                    existing_data = {}
                if palette_name in existing_data:
                    suffix = 1
                    while f"{palette_name}_{suffix}" in existing_data:
                        suffix += 1
                    palette_name = f"{palette_name}_{suffix}"
                existing_data[palette_name] = colors
                # Sort the dictionary keys in alphanumeric order
                sorted_data = {key: existing_data[key] for key in sorted(existing_data)}
                with open(json_file_path, "w") as json_file:
                    json.dump(sorted_data, json_file, indent=4)
            # Example color palette
            palette_name = namerz
            colors = colours_lister
            save_color_palette(palette_name, colors)
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        elif bpy.context.scene.sna_enumselector == "Tetrad":
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_main_color[0], bpy.context.scene.sna_main_color[1], bpy.context.scene.sna_main_color[2], bpy.context.scene.sna_main_color[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_tetradc1[0], bpy.context.scene.sna_tetradc1[1], bpy.context.scene.sna_tetradc1[2], bpy.context.scene.sna_tetradc1[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_tetradc2[0], bpy.context.scene.sna_tetradc2[1], bpy.context.scene.sna_tetradc2[2], bpy.context.scene.sna_tetradc2[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_tetradc3[0], bpy.context.scene.sna_tetradc3[1], bpy.context.scene.sna_tetradc3[2], bpy.context.scene.sna_tetradc3[3]))
            assetsz = bpy.context.scene.sna_pallettoload
            colours_lister = nodetree['sna_combined_col_save']
            namerz = self.sna_whattosave
            import json

            def save_color_palette(palette_name, colors):
                json_file_path = assetsz
                existing_data = {}
                # Try to open the JSON file and load existing data
                try:
                    with open(json_file_path, "r") as json_file:
                        existing_data = json.load(json_file)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    # If the file doesn't exist or is empty, create an empty dictionary
                    existing_data = {}
                if palette_name in existing_data:
                    suffix = 1
                    while f"{palette_name}_{suffix}" in existing_data:
                        suffix += 1
                    palette_name = f"{palette_name}_{suffix}"
                existing_data[palette_name] = colors
                # Sort the dictionary keys in alphanumeric order
                sorted_data = {key: existing_data[key] for key in sorted(existing_data)}
                with open(json_file_path, "w") as json_file:
                    json.dump(sorted_data, json_file, indent=4)
            # Example color palette
            palette_name = namerz
            colors = colours_lister
            save_color_palette(palette_name, colors)
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        elif bpy.context.scene.sna_enumselector == "Triad":
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_main_color[0], bpy.context.scene.sna_main_color[1], bpy.context.scene.sna_main_color[2], bpy.context.scene.sna_main_color[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_triad_1[0], bpy.context.scene.sna_triad_1[1], bpy.context.scene.sna_triad_1[2], bpy.context.scene.sna_triad_1[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_triad_2[0], bpy.context.scene.sna_triad_2[1], bpy.context.scene.sna_triad_2[2], bpy.context.scene.sna_triad_2[3]))
            assetsz = bpy.context.scene.sna_pallettoload
            colours_lister = nodetree['sna_combined_col_save']
            namerz = self.sna_whattosave
            import json

            def save_color_palette(palette_name, colors):
                json_file_path = assetsz
                existing_data = {}
                # Try to open the JSON file and load existing data
                try:
                    with open(json_file_path, "r") as json_file:
                        existing_data = json.load(json_file)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    # If the file doesn't exist or is empty, create an empty dictionary
                    existing_data = {}
                if palette_name in existing_data:
                    suffix = 1
                    while f"{palette_name}_{suffix}" in existing_data:
                        suffix += 1
                    palette_name = f"{palette_name}_{suffix}"
                existing_data[palette_name] = colors
                # Sort the dictionary keys in alphanumeric order
                sorted_data = {key: existing_data[key] for key in sorted(existing_data)}
                with open(json_file_path, "w") as json_file:
                    json.dump(sorted_data, json_file, indent=4)
            # Example color palette
            palette_name = namerz
            colors = colours_lister
            save_color_palette(palette_name, colors)
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        elif bpy.context.scene.sna_enumselector == "Square":
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_main_color[0], bpy.context.scene.sna_main_color[1], bpy.context.scene.sna_main_color[2], bpy.context.scene.sna_main_color[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_square1[0], bpy.context.scene.sna_square1[1], bpy.context.scene.sna_square1[2], bpy.context.scene.sna_square1[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_square2[0], bpy.context.scene.sna_square2[1], bpy.context.scene.sna_square2[2], bpy.context.scene.sna_square2[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_square3[0], bpy.context.scene.sna_square3[1], bpy.context.scene.sna_square3[2], bpy.context.scene.sna_square3[3]))
            assetsz = bpy.context.scene.sna_pallettoload
            colours_lister = nodetree['sna_combined_col_save']
            namerz = self.sna_whattosave
            import json

            def save_color_palette(palette_name, colors):
                json_file_path = assetsz
                existing_data = {}
                # Try to open the JSON file and load existing data
                try:
                    with open(json_file_path, "r") as json_file:
                        existing_data = json.load(json_file)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    # If the file doesn't exist or is empty, create an empty dictionary
                    existing_data = {}
                if palette_name in existing_data:
                    suffix = 1
                    while f"{palette_name}_{suffix}" in existing_data:
                        suffix += 1
                    palette_name = f"{palette_name}_{suffix}"
                existing_data[palette_name] = colors
                # Sort the dictionary keys in alphanumeric order
                sorted_data = {key: existing_data[key] for key in sorted(existing_data)}
                with open(json_file_path, "w") as json_file:
                    json.dump(sorted_data, json_file, indent=4)
            # Example color palette
            palette_name = namerz
            colors = colours_lister
            save_color_palette(palette_name, colors)
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        elif bpy.context.scene.sna_enumselector == "Analogous":
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_main_color[0], bpy.context.scene.sna_main_color[1], bpy.context.scene.sna_main_color[2], bpy.context.scene.sna_main_color[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_analog1[0], bpy.context.scene.sna_analog1[1], bpy.context.scene.sna_analog1[2], bpy.context.scene.sna_analog1[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_analog2[0], bpy.context.scene.sna_analog2[1], bpy.context.scene.sna_analog2[2], bpy.context.scene.sna_analog2[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_analog3[0], bpy.context.scene.sna_analog3[1], bpy.context.scene.sna_analog3[2], bpy.context.scene.sna_analog3[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_analog4[0], bpy.context.scene.sna_analog4[1], bpy.context.scene.sna_analog4[2], bpy.context.scene.sna_analog4[3]))
            assetsz = bpy.context.scene.sna_pallettoload
            colours_lister = nodetree['sna_combined_col_save']
            namerz = self.sna_whattosave
            import json

            def save_color_palette(palette_name, colors):
                json_file_path = assetsz
                existing_data = {}
                # Try to open the JSON file and load existing data
                try:
                    with open(json_file_path, "r") as json_file:
                        existing_data = json.load(json_file)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    # If the file doesn't exist or is empty, create an empty dictionary
                    existing_data = {}
                if palette_name in existing_data:
                    suffix = 1
                    while f"{palette_name}_{suffix}" in existing_data:
                        suffix += 1
                    palette_name = f"{palette_name}_{suffix}"
                existing_data[palette_name] = colors
                # Sort the dictionary keys in alphanumeric order
                sorted_data = {key: existing_data[key] for key in sorted(existing_data)}
                with open(json_file_path, "w") as json_file:
                    json.dump(sorted_data, json_file, indent=4)
            # Example color palette
            palette_name = namerz
            colors = colours_lister
            save_color_palette(palette_name, colors)
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        elif bpy.context.scene.sna_enumselector == "Monochromatic":
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_main_color[0], bpy.context.scene.sna_main_color[1], bpy.context.scene.sna_main_color[2], bpy.context.scene.sna_main_color[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_mono1[0], bpy.context.scene.sna_mono1[1], bpy.context.scene.sna_mono1[2], bpy.context.scene.sna_mono1[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_mono2[0], bpy.context.scene.sna_mono2[1], bpy.context.scene.sna_mono2[2], bpy.context.scene.sna_mono2[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_mono3[0], bpy.context.scene.sna_mono3[1], bpy.context.scene.sna_mono3[2], bpy.context.scene.sna_mono3[3]))
            nodetree['sna_combined_col_save'].append((bpy.context.scene.sna_mono4[0], bpy.context.scene.sna_mono4[1], bpy.context.scene.sna_mono4[2], bpy.context.scene.sna_mono4[3]))
            assetsz = bpy.context.scene.sna_pallettoload
            colours_lister = nodetree['sna_combined_col_save']
            namerz = self.sna_whattosave
            import json

            def save_color_palette(palette_name, colors):
                json_file_path = assetsz
                existing_data = {}
                # Try to open the JSON file and load existing data
                try:
                    with open(json_file_path, "r") as json_file:
                        existing_data = json.load(json_file)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    # If the file doesn't exist or is empty, create an empty dictionary
                    existing_data = {}
                if palette_name in existing_data:
                    suffix = 1
                    while f"{palette_name}_{suffix}" in existing_data:
                        suffix += 1
                    palette_name = f"{palette_name}_{suffix}"
                existing_data[palette_name] = colors
                # Sort the dictionary keys in alphanumeric order
                sorted_data = {key: existing_data[key] for key in sorted(existing_data)}
                with open(json_file_path, "w") as json_file:
                    json.dump(sorted_data, json_file, indent=4)
            # Example color palette
            palette_name = namerz
            colors = colours_lister
            save_color_palette(palette_name, colors)
            sna_create_collections_6E2A3(bpy.context.scene.sna_pallettoload)
            sna_updatejsondata_7DF1D()
        else:
            pass
        sna_reset_boolean_D465A()
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text='Pallet Name', icon_value=0)
        layout.prop(self, 'sna_whattosave', text='', icon_value=0, emboss=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


def sna_enumfunction_18E61():
    pallette_generator['sna_listnamess'] = []
    pallette_generator['sna_enumfunlist'] = []
    for i_F436C in range(len(['Complementary', 'Split Complementary', 'Triad', 'Tetrad', 'Square', 'Analogous', 'Monochromatic'])):
        pallette_generator['sna_enumfunlist'].append([['Complementary', 'Split Complementary', 'Triad', 'Tetrad', 'Square', 'Analogous', 'Monochromatic'][i_F436C], ['Complementary', 'Split Complementary', 'Triad', 'Tetrad', 'Square', 'Analogous', 'Monochromatic'][i_F436C], ['Complementary', 'Split Complementary', 'Triad', 'Tetrad', 'Square', 'Analogous', 'Monochromatic'][i_F436C], 0])
        pallette_generator['sna_listnamess'].append(['Complementary', 'Split Complementary', 'Triad', 'Tetrad', 'Square', 'Analogous', 'Monochromatic'][i_F436C])
    return [pallette_generator['sna_enumfunlist'], pallette_generator['sna_listnamess']]


def sna_enumscroller_enum_items(self, context):
    enum_items = sna_enumfunction_18E61()[0]
    return [make_enum_item(item[0], item[1], item[2], item[3], i) for i, item in enumerate(enum_items)]


class SNA_OT_Cyclecolorscheme_B6Ff5(bpy.types.Operator):
    bl_idname = "sna.cyclecolorscheme_b6ff5"
    bl_label = "CycleColorScheme"
    bl_description = "Cycles the color scheme."
    bl_options = {"REGISTER", "UNDO"}
    sna_scrolldirection: bpy.props.StringProperty(name='scrolldirection', description='', options={'HIDDEN'}, default='', subtype='NONE', maxlen=0)

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        pallette_generator['sna_integerscroller'] = 0
        for i_A0ED3 in range(len(pallette_generator['sna_enumfunlist'])):
            for i_CA274 in range(len(pallette_generator['sna_enumfunlist'][i_A0ED3])):
                if (pallette_generator['sna_enumfunlist'][i_A0ED3][i_CA274] == bpy.context.scene.sna_enumscroller):
                    pallette_generator['sna_integerscroller'] = i_A0ED3
        if self.sna_scrolldirection == "MINUS":
            if (pallette_generator['sna_integerscroller'] == 0):
                bpy.context.scene.sna_enumscroller = pallette_generator['sna_listnamess'][int(len(pallette_generator['sna_listnamess']) - 1.0)]
            else:
                bpy.context.scene.sna_enumscroller = pallette_generator['sna_listnamess'][int(pallette_generator['sna_integerscroller'] - 1.0)]
        elif self.sna_scrolldirection == "PLUS":
            if (pallette_generator['sna_integerscroller'] == int(len(pallette_generator['sna_listnamess']) - 1.0)):
                bpy.context.scene.sna_enumscroller = pallette_generator['sna_listnamess'][0]
            else:
                bpy.context.scene.sna_enumscroller = pallette_generator['sna_listnamess'][int(pallette_generator['sna_integerscroller'] + 1.0)]
        else:
            pass
        if bpy.context and bpy.context.screen:
            for a in bpy.context.screen.areas:
                a.tag_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Apply_Tester_29884(bpy.types.Operator):
    bl_idname = "sna.apply_tester_29884"
    bl_label = "APPLY TESTER"
    bl_description = "Add random colour to objects"
    bl_options = {"REGISTER", "UNDO"}
    sna_colindex: bpy.props.IntProperty(name='colIndex', description='', options={'HIDDEN'}, default=0, subtype='NONE')

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (len(list(bpy.context.view_layer.objects.selected)) > 0):
            for i_FAC7E in range(len(bpy.context.view_layer.objects.selected)):
                if bpy.context.view_layer.objects.selected[i_FAC7E].type == 'ARMATURE':
                    pass
                else:
                    if (bpy.context.view_layer.objects.selected[i_FAC7E].type == 'ARMATURE' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'VOLUME' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'POINTCLOUD' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'LATTICE' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'META' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'FONT' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'SURFACE' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'CURVE' or bpy.context.view_layer.objects.selected[i_FAC7E].type == 'MESH'):
                        nodetree['sna_fine_tune_random'] = []
                        if (True == bpy.context.scene.sna_col_apply_tog_1):
                            nodetree['sna_fine_tune_random'].append(1)
                        if (True == bpy.context.scene.sna_col_apply_tog_2):
                            nodetree['sna_fine_tune_random'].append(2)
                        if (True == bpy.context.scene.sna_col_apply_tog_3):
                            nodetree['sna_fine_tune_random'].append(3)
                        if (True == bpy.context.scene.sna_col_apply_tog_4):
                            nodetree['sna_fine_tune_random'].append(4)
                        if (True == bpy.context.scene.sna_col_apply_tog_5):
                            nodetree['sna_fine_tune_random'].append(5)
                        obxx = bpy.context.view_layer.objects.selected[i_FAC7E]
                        CC1 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col1r
                        CC2 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col2r
                        CC3 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col3r
                        CC4 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col4r
                        CC5 = bpy.context.scene.sna_collectionscolours[self.sna_colindex].col5r
                        tuned_list = nodetree['sna_fine_tune_random']
                        import random
                        # List of colors you provide
                        COL1 = CC1
                        COL2 = CC2
                        COL3 = CC3
                        COL4 = CC4
                        COL5 = CC5
                        colors = [COL1, COL2, COL3, COL4, COL5]
                        # Assuming SELECTED_COLOR_INDICES is a global variable or property that contains the indices of the selected colors
                        SELECTED_COLOR_INDICES = []
                        SELECTED_COLOR_INDICES = tuned_list
                        selected_colors = [colors[i-1] for i in SELECTED_COLOR_INDICES]  # Convert indices to actual colors
                        # List of objects you want to check
                        objects_list = bpy.context.selected_objects
                        for obj in objects_list:
                            if not obj.material_slots:
                                # Create a new material
                                material_name = "Material_" + obj.name
                                material = bpy.data.materials.new(name=material_name)
                                obj.data.materials.append(material)
                                material.use_nodes = True
                                nodes = material.node_tree.nodes
                                nodes.clear()
                                # Create Principled BSDF node
                                principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                                color = random.choice(selected_colors)
                                principled_bsdf.inputs[0].default_value = color
                                # Create Material Output node
                                material_output = nodes.new(type='ShaderNodeOutputMaterial')
                                # Link Principled BSDF to Material Output
                                links = material.node_tree.links
                                link = links.new(principled_bsdf.outputs[0], material_output.inputs[0])
                            else:
                                for mat_slot in obj.material_slots:
                                    material = mat_slot.material
                                    if material and material.use_nodes:
                                        principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
                                        if principled_bsdf:
                                            color = random.choice(selected_colors)
                                            principled_bsdf.inputs[0].default_value = color
        else:
            sna_pop_message_272A6_B08ED('We need objects! ', 'No objects selected', 'ERROR')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_PT_UTILITIES_C38BC(bpy.types.Panel):
    bl_label = 'Utilities'
    bl_idname = 'SNA_PT_UTILITIES_C38BC'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Colorful'
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
        row_5B075 = layout.row(heading='', align=False)
        row_5B075.alert = False
        row_5B075.enabled = True
        row_5B075.active = True
        row_5B075.use_property_split = False
        row_5B075.use_property_decorate = False
        row_5B075.scale_x = 1.0
        row_5B075.scale_y = 1.0
        row_5B075.alignment = 'Expand'.upper()
        if not True: row_5B075.operator_context = "EXEC_DEFAULT"
        op = row_5B075.operator('sna.importer_e712b', text='Import Palette', icon_value=70, emboss=True, depress=False)
        op = row_5B075.operator('sna.export_2b6a0', text='Export Palette', icon_value=722, emboss=True, depress=False)
        op.sna_filename = 'pallet.json'
        box_B852F = layout.box()
        box_B852F.alert = False
        box_B852F.enabled = True
        box_B852F.active = True
        box_B852F.use_property_split = False
        box_B852F.use_property_decorate = False
        box_B852F.alignment = 'Expand'.upper()
        box_B852F.scale_x = 1.0
        box_B852F.scale_y = 1.0
        if not True: box_B852F.operator_context = "EXEC_DEFAULT"
        box_B852F.label(text='UI Settings:', icon_value=0)
        row_74E73 = box_B852F.row(heading='', align=False)
        row_74E73.alert = False
        row_74E73.enabled = True
        row_74E73.active = True
        row_74E73.use_property_split = False
        row_74E73.use_property_decorate = False
        row_74E73.scale_x = 1.0
        row_74E73.scale_y = 1.0
        row_74E73.alignment = 'Expand'.upper()
        if not True: row_74E73.operator_context = "EXEC_DEFAULT"
        row_74E73.prop(bpy.context.scene, 'sna_ui_row_h', text='Library Row Height', icon_value=0, emboss=True)


class SNA_GROUP_sna_colprops(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='Name', description='', default='', subtype='NONE', maxlen=0)
    col1r: bpy.props.FloatVectorProperty(name='col1r', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    col2r: bpy.props.FloatVectorProperty(name='col2r', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    col3r: bpy.props.FloatVectorProperty(name='col3r', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    col4r: bpy.props.FloatVectorProperty(name='col4r', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    col5r: bpy.props.FloatVectorProperty(name='col5r', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    colmount: bpy.props.IntProperty(name='colmount', description='', default=0, subtype='NONE')


class SNA_GROUP_sna_group_stored(bpy.types.PropertyGroup):
    pointer: bpy.props.PointerProperty(name='Pointer', description='', type=bpy.types.Object)


def sna_update_sna_main_color(self, context):
    sna_update_sna_main_color_6F9DB(self, context)
    sna_update_sna_main_color_5B960(self, context)
    sna_update_sna_main_color_68793(self, context)
    sna_update_sna_main_color_04464(self, context)
    sna_update_sna_main_color_6DF7D(self, context)
    sna_update_sna_main_color_06851(self, context)
    sna_update_sna_main_color_ABB92(self, context)


def sna_map_enum_enum_items(self, context):
    return [("No Items", "No Items", "No generate enum items node found to create items!", "ERROR", 0)]


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    bpy.utils.register_class(SNA_GROUP_sna_colprops)
    bpy.utils.register_class(SNA_GROUP_sna_group_stored)
    bpy.types.Scene.sna_c1 = bpy.props.FloatVectorProperty(name='c1', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_c2 = bpy.props.FloatVectorProperty(name='c2', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_c3 = bpy.props.FloatVectorProperty(name='c3', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_c4 = bpy.props.FloatVectorProperty(name='c4', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_c5 = bpy.props.FloatVectorProperty(name='c5', description='', size=4, default=(0.0, 0.0, 0.0, 0.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_save_name = bpy.props.StringProperty(name='save_name', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_save_name_pallete = bpy.props.StringProperty(name='save_name_pallete', description='', default='', subtype='NONE', maxlen=0)
    bpy.types.Scene.sna_collectionscolours = bpy.props.CollectionProperty(name='CollectionsColours', description='', type=SNA_GROUP_sna_colprops)
    bpy.types.Scene.sna_indexalt = bpy.props.IntProperty(name='indexalt', description='', default=0, subtype='NONE')
    bpy.types.Scene.sna_show_names = bpy.props.BoolProperty(name='Show Names', description='', default=False)
    bpy.types.Scene.sna_pallet_list = bpy.props.EnumProperty(name='Pallet List', description='', items=sna_pallet_list_enum_items, update=sna_update_sna_pallet_list_07097)
    bpy.types.Scene.sna_pallettoload = bpy.props.StringProperty(name='PalletToLoad', description='', default='', subtype='FILE_PATH', maxlen=0)
    bpy.types.Scene.sna_enumselector = bpy.props.EnumProperty(name='EnumSelector', description='', items=[('Complementary', 'Complementary', 'Complementary', 0, 0), ('Split Complementary', 'Split Complementary', 'Split Complementary', 0, 1), ('Triad', 'Triad', 'Triad', 0, 2), ('Tetrad', 'Tetrad', 'Tetrad', 0, 3), ('Square', 'Square', 'Square', 0, 4), ('Analogous', 'Analogous', 'Analogus', 0, 5), ('Monochromatic', 'Monochromatic', 'Monochromatic', 0, 6)])
    bpy.types.Scene.sna_main_color = bpy.props.FloatVectorProperty(name='Main Color', description='', size=4, default=(1.0, 1.0, 1.0, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6, update=sna_update_sna_main_color)
    bpy.types.Scene.sna_complcolor = bpy.props.FloatVectorProperty(name='ComplColor', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_triad_1 = bpy.props.FloatVectorProperty(name='Triad 1', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_triad_2 = bpy.props.FloatVectorProperty(name='Triad 2', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_square1 = bpy.props.FloatVectorProperty(name='Square1', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_square2 = bpy.props.FloatVectorProperty(name='Square2', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_square3 = bpy.props.FloatVectorProperty(name='Square3', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_mono1 = bpy.props.FloatVectorProperty(name='Mono1', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_mono2 = bpy.props.FloatVectorProperty(name='Mono2', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_mono3 = bpy.props.FloatVectorProperty(name='Mono3', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_analog1 = bpy.props.FloatVectorProperty(name='Analog1', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_analog2 = bpy.props.FloatVectorProperty(name='Analog2', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_analog3 = bpy.props.FloatVectorProperty(name='Analog3', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_split1 = bpy.props.FloatVectorProperty(name='Split1', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_split2 = bpy.props.FloatVectorProperty(name='Split2', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_split3 = bpy.props.FloatVectorProperty(name='Split3', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_map_enum = bpy.props.EnumProperty(name='MAP ENUM', description='', items=sna_map_enum_enum_items)
    bpy.types.Scene.sna_settings_switcher = bpy.props.BoolProperty(name='settings_switcher', description='', default=False)
    bpy.types.Scene.sna_col_apply_tog_1 = bpy.props.BoolProperty(name='col_apply_tog_1', description='', default=True)
    bpy.types.Scene.sna_col_apply_tog_2 = bpy.props.BoolProperty(name='col_apply_tog_2', description='', default=True)
    bpy.types.Scene.sna_col_apply_tog_3 = bpy.props.BoolProperty(name='col_apply_tog_3', description='', default=True)
    bpy.types.Scene.sna_col_apply_tog_4 = bpy.props.BoolProperty(name='col_apply_tog_4', description='', default=True)
    bpy.types.Scene.sna_col_apply_tog_5 = bpy.props.BoolProperty(name='col_apply_tog_5', description='', default=True)
    bpy.types.Scene.sna_col_del_tog_1 = bpy.props.BoolProperty(name='col_del_tog_1', description='', default=False)
    bpy.types.Scene.sna_col_del_tog_2 = bpy.props.BoolProperty(name='col_del_tog_2', description='', default=False)
    bpy.types.Scene.sna_col_del_tog_3 = bpy.props.BoolProperty(name='col_del_tog_3', description='', default=False)
    bpy.types.Scene.sna_col_del_tog_4 = bpy.props.BoolProperty(name='col_del_tog_4', description='', default=False)
    bpy.types.Scene.sna_col_del_tog_5 = bpy.props.BoolProperty(name='col_del_tog_5', description='', default=False)
    bpy.types.Scene.sna_show_delete_buttons = bpy.props.BoolProperty(name='Show Delete Buttons', description='', default=False)
    bpy.types.Scene.sna_show_edit_buttons = bpy.props.BoolProperty(name='Show Edit Buttons', description='', default=False)
    bpy.types.Scene.sna_ui_row_h = bpy.props.FloatProperty(name='UI_ROW_H', description='', default=1.0, subtype='NONE', unit='NONE', min=0.5, max=36.900001525878906, step=3, precision=2)
    bpy.types.Scene.sna_enumscroller = bpy.props.EnumProperty(name='ENUMSCROLLER', description='', items=sna_enumscroller_enum_items, update=sna_update_sna_enumscroller_26CB5)
    bpy.types.Scene.sna_tetradc1 = bpy.props.FloatVectorProperty(name='TetradC1', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_tetradc2 = bpy.props.FloatVectorProperty(name='TetradC2', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_tetradc3 = bpy.props.FloatVectorProperty(name='TetradC3', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_analog4 = bpy.props.FloatVectorProperty(name='Analog4', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', step=3, precision=6)
    bpy.types.Scene.sna_mono4 = bpy.props.FloatVectorProperty(name='Mono4', description='', size=4, default=(0.0262410007417202, 0.0262410007417202, 0.0262410007417202, 1.0), subtype='COLOR', unit='NONE', min=0.0, max=1.0, step=3, precision=6)
    bpy.types.Scene.sna_collection_stored = bpy.props.CollectionProperty(name='Collection Stored', description='', type=SNA_GROUP_sna_group_stored)
    bpy.utils.register_class(SNA_OT_Delete_Color_1_9Bd49)
    bpy.utils.register_class(SNA_OT_Delete_Color_2_A6B7D)
    bpy.utils.register_class(SNA_OT_Delete_Color_4_75Ab8)
    bpy.utils.register_class(SNA_OT_Delete_Color_5_D27A6)
    bpy.utils.register_class(SNA_OT_Delete_Color_3_B4Bee)
    bpy.app.handlers.load_post.append(load_post_handler_27CC8)
    bpy.utils.register_class(SNA_OT_Load_Colours_E77Af)
    bpy.utils.register_class(SNA_OT_Export_2B6A0)
    bpy.utils.register_class(SNA_PT_ALT_TAB_COLORFUL_10BBC)
    bpy.utils.register_class(SNA_OT_Importer_E712B)
    bpy.utils.register_class(SNA_PT_colour001_F183C)
    bpy.utils.register_class(SNA_UL_display_collection_list_4750A)
    bpy.utils.register_class(SNA_OT_Delete_Palette_Collection_52Cd8)
    bpy.utils.register_class(SNA_OT_Copy_Pallet_Eab95)
    bpy.utils.register_class(SNA_OT_Save_Palette_04046)
    bpy.utils.register_class(SNA_OT_Apply_Random_Color_Bd01C)
    bpy.utils.register_class(SNA_OT_Create_Collection_7B813)
    bpy.utils.register_class(SNA_OT_Edit_Palette_2C0Da)
    bpy.utils.register_class(SNA_PT_POPUPPANEL_2CC19)
    bpy.utils.register_class(SNA_OT_Delete_Palette_0980F)
    bpy.utils.register_class(SNA_OT_Fine_Tune_Delete_35613)
    bpy.app.handlers.save_post.append(save_post_handler_21F4E)
    bpy.utils.register_class(SNA_OT_Paint_Selected_Objects_E873B)
    bpy.app.handlers.load_post.append(load_post_handler_E9244)
    bpy.utils.register_class(SNA_PT_COLOR_SCHEMES_C37D9)
    bpy.utils.register_class(SNA_OT_Save_Json_Pallete_814B1)
    bpy.utils.register_class(SNA_OT_Cyclecolorscheme_B6Ff5)
    bpy.utils.register_class(SNA_OT_Apply_Tester_29884)
    bpy.utils.register_class(SNA_PT_UTILITIES_C38BC)


def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    del bpy.types.Scene.sna_collection_stored
    del bpy.types.Scene.sna_mono4
    del bpy.types.Scene.sna_analog4
    del bpy.types.Scene.sna_tetradc3
    del bpy.types.Scene.sna_tetradc2
    del bpy.types.Scene.sna_tetradc1
    del bpy.types.Scene.sna_enumscroller
    del bpy.types.Scene.sna_ui_row_h
    del bpy.types.Scene.sna_show_edit_buttons
    del bpy.types.Scene.sna_show_delete_buttons
    del bpy.types.Scene.sna_col_del_tog_5
    del bpy.types.Scene.sna_col_del_tog_4
    del bpy.types.Scene.sna_col_del_tog_3
    del bpy.types.Scene.sna_col_del_tog_2
    del bpy.types.Scene.sna_col_del_tog_1
    del bpy.types.Scene.sna_col_apply_tog_5
    del bpy.types.Scene.sna_col_apply_tog_4
    del bpy.types.Scene.sna_col_apply_tog_3
    del bpy.types.Scene.sna_col_apply_tog_2
    del bpy.types.Scene.sna_col_apply_tog_1
    del bpy.types.Scene.sna_settings_switcher
    del bpy.types.Scene.sna_map_enum
    del bpy.types.Scene.sna_split3
    del bpy.types.Scene.sna_split2
    del bpy.types.Scene.sna_split1
    del bpy.types.Scene.sna_analog3
    del bpy.types.Scene.sna_analog2
    del bpy.types.Scene.sna_analog1
    del bpy.types.Scene.sna_mono3
    del bpy.types.Scene.sna_mono2
    del bpy.types.Scene.sna_mono1
    del bpy.types.Scene.sna_square3
    del bpy.types.Scene.sna_square2
    del bpy.types.Scene.sna_square1
    del bpy.types.Scene.sna_triad_2
    del bpy.types.Scene.sna_triad_1
    del bpy.types.Scene.sna_complcolor
    del bpy.types.Scene.sna_main_color
    del bpy.types.Scene.sna_enumselector
    del bpy.types.Scene.sna_pallettoload
    del bpy.types.Scene.sna_pallet_list
    del bpy.types.Scene.sna_show_names
    del bpy.types.Scene.sna_indexalt
    del bpy.types.Scene.sna_collectionscolours
    del bpy.types.Scene.sna_save_name_pallete
    del bpy.types.Scene.sna_save_name
    del bpy.types.Scene.sna_c5
    del bpy.types.Scene.sna_c4
    del bpy.types.Scene.sna_c3
    del bpy.types.Scene.sna_c2
    del bpy.types.Scene.sna_c1
    bpy.utils.unregister_class(SNA_GROUP_sna_group_stored)
    bpy.utils.unregister_class(SNA_GROUP_sna_colprops)
    bpy.utils.unregister_class(SNA_OT_Delete_Color_1_9Bd49)
    bpy.utils.unregister_class(SNA_OT_Delete_Color_2_A6B7D)
    bpy.utils.unregister_class(SNA_OT_Delete_Color_4_75Ab8)
    bpy.utils.unregister_class(SNA_OT_Delete_Color_5_D27A6)
    bpy.utils.unregister_class(SNA_OT_Delete_Color_3_B4Bee)
    bpy.app.handlers.load_post.remove(load_post_handler_27CC8)
    bpy.utils.unregister_class(SNA_OT_Load_Colours_E77Af)
    bpy.utils.unregister_class(SNA_OT_Export_2B6A0)
    bpy.utils.unregister_class(SNA_PT_ALT_TAB_COLORFUL_10BBC)
    bpy.utils.unregister_class(SNA_OT_Importer_E712B)
    bpy.utils.unregister_class(SNA_PT_colour001_F183C)
    bpy.utils.unregister_class(SNA_UL_display_collection_list_4750A)
    bpy.utils.unregister_class(SNA_OT_Delete_Palette_Collection_52Cd8)
    bpy.utils.unregister_class(SNA_OT_Copy_Pallet_Eab95)
    bpy.utils.unregister_class(SNA_OT_Save_Palette_04046)
    bpy.utils.unregister_class(SNA_OT_Apply_Random_Color_Bd01C)
    bpy.utils.unregister_class(SNA_OT_Create_Collection_7B813)
    bpy.utils.unregister_class(SNA_OT_Edit_Palette_2C0Da)
    bpy.utils.unregister_class(SNA_PT_POPUPPANEL_2CC19)
    bpy.utils.unregister_class(SNA_OT_Delete_Palette_0980F)
    bpy.utils.unregister_class(SNA_OT_Fine_Tune_Delete_35613)
    bpy.app.handlers.save_post.remove(save_post_handler_21F4E)
    bpy.utils.unregister_class(SNA_OT_Paint_Selected_Objects_E873B)
    bpy.app.handlers.load_post.remove(load_post_handler_E9244)
    bpy.utils.unregister_class(SNA_PT_COLOR_SCHEMES_C37D9)
    bpy.utils.unregister_class(SNA_OT_Save_Json_Pallete_814B1)
    bpy.utils.unregister_class(SNA_OT_Cyclecolorscheme_B6Ff5)
    bpy.utils.unregister_class(SNA_OT_Apply_Tester_29884)
    bpy.utils.unregister_class(SNA_PT_UTILITIES_C38BC)

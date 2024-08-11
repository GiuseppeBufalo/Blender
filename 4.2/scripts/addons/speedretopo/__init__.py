# -*- coding:utf-8 -*-

# SpeedRetopo Add-on
# Copyright (C) 2016 Cedric Lepiller aka Pitiwazou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# <pep8 compliant>

bl_info = {
    "name": "SpeedRetopo",
    "description": "Addon for retopology",
    "author": "Cedric Lepiller, EWOC for Laprelax",
    "version": (0, 2, 7),
    "blender": (4, 1, 0),
    "location": "Property Panel, Press N in the 3DView",
    "wiki_url": "https://youtu.be/cKhZNOFc4Us",
    "category": "Object"}

import bpy
from mathutils import *
from bpy.types import Operator, Menu, AddonPreferences, PropertyGroup
from bpy.types import Object
from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatVectorProperty,
                       FloatProperty,
                       EnumProperty,
                       IntProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty)
import rna_keymap_ui
from .ui import SPEEDRETOPO_PT_ui
from .icon.icons import *
# from .operators import smooth_flat_shading

# Import des modules
if "bpy" in locals():
    import importlib
    reloadable_modules = ["operators","ui","documentation"]
    for module in reloadable_modules:
        if module in locals():
            importlib.reload(locals()[module])

from . import  (operators,ui,documentation)

# -----------------------------------------------------------------------------
#    Preferences
# -----------------------------------------------------------------------------

keymaps_items_dict = {"Speedretopo": ['object.speedretopo_ot_start_or_edit', None,
                                      '3D View ''Generic', 'VIEW_3D', 'WINDOW',
                                      'RIGHTMOUSE', 'PRESS', True, True, True]}

def update_speedretopo_category(self, context):
    is_panel = hasattr(bpy.types, 'SPEEDRETOPO_PT_ui')
    prefs = bpy.context.preferences.addons[__name__].preferences

    if is_panel:
        try:
            bpy.utils.unregister_class(bpy.types.SPEEDRETOPO_PT_ui)
        except:
            pass

    ui.SPEEDRETOPO_PT_ui.bl_category = self.category
    bpy.utils.register_class(ui.SPEEDRETOPO_PT_ui)

# Preferences
class SPEEDRETOPO_MT_addon_preferences(AddonPreferences):
    bl_idname = __name__

    prefs_tabs: EnumProperty(
        items=(('info', "Info", "ADDON INFO"),
               ('options', "Options", "ADDON OPTIONS"),
               ('keymaps', "Keymaps", "CHANGE KEYMAPS"),
               ('links', "Links", "LINKS")),
        default='options')

    hidden_wire: BoolProperty(name="Hidden Wire", default=True,
                              description="Hide Faces to see through the mesh")

    retopology_shading: BoolProperty(name="Hidden Wire", default=True,
                              description="Hide Faces to see through the mesh")
    icons = load_icons()

    icon1 = icons.get("icon_bsurface")
    icon2 = icons.get("icon_vertex")
    icon3 = icons.get("icon_polybuild")
    icon4 = icons.get("icon_face")


    start_from: EnumProperty(
        items=(
               ('VERTEX', "Vertex", "Use a single Vertex to start the retopology", icon2.icon_id, 2),
               ('FACE', "face", "Use a single Face to start the retopology", icon4.icon_id, 4),
               ('BSURFACE', "BSurface", "Use Bsurface Addon, Press D, old and draw the lines", icon1.icon_id, 1),
               ('POLYBUILD', "Polybuild", "Use Polybuild Tool", icon3.icon_id, 3),),
        default='FACE',
        description="")

    use_menu_or_pie_menu: EnumProperty(
        items=(('menu', "Menu", "Use Menu instead of Pie Menus"),
               ('pie_menus', "Pie Menus", "Use Pie Menus instead of Menu" )),
        default='pie_menus',
        description="Choose Menu Type")

    auto_add_mirror: BoolProperty(name="Auto Add Mirror", default=True, description="Add a Mirror Modifier to your retopology.")
    auto_add_shrinkwrap: BoolProperty(name="Auto Add Shrinkwrap", default=True, description="Add a Shrinkwrap Modifier to your retopology.")
    use_in_front: BoolProperty(name="Use In Front Setting", default=True,
                                   description="See the Retopo Mesh in front of the Reference Mesh")
    use_wireframe: BoolProperty(name="Use Wireframe", default=True,
                                   description="Show Object Wireframe")
    use_color_shader: BoolProperty(name="Use Color Shader", default=False,
                                   description="Add a Color to you mesh")
    obj_color: FloatVectorProperty(name="", default=(0, 0.65, 1, 0.5), min=0, max=1, size=4, subtype='COLOR_GAMMA',
                                   description="Choose a Color to you mesh")
    mirror_axis: BoolVectorProperty(default=[True, False, False], size=3, name="")
    mirror_clipping: BoolProperty(name="Use Mirror Clipping", default=False,
                                   description="Add a Color to you mesh")
    buttons_size: FloatProperty(name="", default=1, min=1, max=2, precision=3)
    smooth_shading: BoolProperty(name="Smooth Shading", default=True,description="Use smooth shading with Auto Smooth")
    change_selection_tool: BoolProperty(default=True, description="Use the tewak tool")
    category: StringProperty(description="Choose a name for the category of the panel", default="SpeedRetopo",
                             update=update_speedretopo_category)

    # QUAD REMESH
    # quad_use_mesh_symmetry : BoolProperty(name="Use Mesh Symmetry", default=True,
    #                                      description="Generate a symmetrical mesh using the mesh symmetry configuration.")
    # quad_use_preserve_sharp : BoolProperty(name="Use Preserve Sharp", default=True, description="Try to preserve Sharph features on the mesh.")
    # quad_use_preserve_boundary : BoolProperty(name="Use Preserve Boundary", default=True,description="Try to preserve Boundary on the mesh.")
    # quad_preserve_paint_mask : BoolProperty(name="Use Preserve Paint Mask", default=False, description="Reproject the paint mask onto the new mesh.")
    # quad_smooth_normals : BoolProperty(name="Smooth Normals", default=True,description="Smooth the Normals of the mesh")
    # quad_mode : EnumProperty(
    #     items=(('FACES', "FACES", ""),
    #            ('RATIO', "RATIO", "" ),
    #            ('EDGE', "EDGE", "" )),
    #     default='FACES',
    #     description="Specify the amount of detail for the new mesh.")
    # quad_target_ratio : FloatProperty(name="Ratio", default=0.5, min=0.01, max=1, precision=3, description="Relative Number of Faces compared to the current Mesh.")
    # quad_target_edge_length : FloatProperty(name="Length", default=0.1, min=0.01, max=1, precision=3, description="Edges Length")
    # quad_target_faces : IntProperty(name="Number of Faces", default=1000, min=1, max=100000, description="Number of Faces")
    # quad_mesh_area : FloatProperty(name="Quad Mesh Area", default=-1, min=-1, max=1, precision=3, description="Old Object Face Area, This property is only used to cache the object area for later calculations.")
    # quad_seed : IntProperty(name="Seed", default=0, min=0, max=255, description="Random Seed to use with the Solver")

    show_start_menu: BoolProperty(default=True, description="Show/Hide Start Menu")
    show_retopo_settings_menu: BoolProperty(default=True, description="Show/Hide Retopo Settings")
    show_modifiers_menu: BoolProperty(default=True, description="Show/Hide Modifiers")
    show_tools_menu: BoolProperty(default=True, description="Show/Hide Tools")
    show_shading_menu: BoolProperty(default=True, description="Show/Hide Shadind")
    show_quadriflow_menu: BoolProperty(default=False, description="Show/Hide Quadriflow")
    show_freeze_unfreeze: BoolProperty(default=False, description="Show/Hide Freezing tools")
    show_center_tools: BoolProperty(default=True, description="Show/Hide Center tools")


    show_hide_menu_settings: BoolProperty(default=True, description="Show/Hide Menus Settings")
    show_hide_retopo_settings: BoolProperty(default=True, description="Show/Hide Retopology Settings")
    show_hide_quadremesh_settings: BoolProperty(default=False, description="Show/Hide Quad Remesh Settings")
    show_hide_mirror_modifiers_settings: BoolProperty(default=False, description="Show/Hide Mirror Modifiers Settings")
    show_hide_shrinkwrap_modifiers_settings: BoolProperty(default=False, description="Show/Hide Shrinkwrap Modifiers Settings")
    show_hide_subsurf_modifiers_settings: BoolProperty(default=False, description="Show/Hide Subsurf Modifiers Settings")

    show_help_buttons: BoolProperty(default=True, description="Show Help Buttons")
    reference_nbf : IntProperty(name="Number of Faces for the Reference Object", default=100000, min=10, max=500000, description="Number of Faces for the Reference Object.")


    # MIRROR SETTINGS
    use_axis_x: BoolProperty(name="",default=True,description="Use Mirror X Axis")
    use_axis_y: BoolProperty(name="",default=False,description="Use Mirror Y Axis")
    use_axis_z: BoolProperty(name="",default=False,description="Use Mirror Z Axis")

    use_bisect_axis_x: BoolProperty(name="",default=False,description="Use Mirror X Bisect Axis")
    use_bisect_axis_y: BoolProperty(name="",default=False,description="Use Mirror Y Bisect Axis")
    use_bisect_axis_z: BoolProperty(name="",default=False,description="Use Mirror Z Bisect Axis")

    use_bisect_flip_axis_x: BoolProperty(name="",default=False,description="Use Mirror X Bisect Flip Axis")
    use_bisect_flip_axis_y: BoolProperty(name="",default=False,description="Use Mirror Y Bisect Flip Axis")
    use_bisect_flip_axis_z: BoolProperty(name="",default=False,description="Use Mirror Z Bisect Flip Axis")

    use_clip: BoolProperty(name="",default=True,description="Use Clip")
    use_mirror_merge: BoolProperty(name="",default=True,description="Use Mirror Merge")
    use_merge: BoolProperty(name="",default=True,description="Use Mirror Merge")
    merge_threshold: FloatProperty(name="Merge Threshold", default=0.001)
    use_mirror_vertex_groups: BoolProperty(name="",default=True,description="Use Mirror Vertex Group")
    center_empty_ref: BoolProperty(name="", default=False, description="Center the Empty to the scene origin")
    show_on_cage: BoolProperty(name="", default=True)
    show_options_mirror: BoolProperty(default=False)

    # SHRINKWRAP SETTINGS
    shrinkwrap_axis: BoolVectorProperty(default=[True, False, False], size=3)

    shrinkwrap_axis_x: BoolProperty(name="",default=False,description="Use Shrinkwrap X Axis")
    shrinkwrap_axis_y: BoolProperty(name="",default=False,description="Use Shrinkwrap Y Axis")
    shrinkwrap_axis_z: BoolProperty(name="",default=False,description="Use Shrinkwrap Z Axis")


    shrinkwrap_offset : FloatProperty(name="Offset",default=0.03,description="Offset")
    wrap_method : EnumProperty(
        items=(('NEAREST_SURFACEPOINT', "NEAREST_SURFACEPOINT", ""),
               ('PROJECT', "PROJECT", ""),
               ('NEAREST_VERTEX', "NEAREST_VERTEX", ""),
               ('TARGET_PROJECT', "TARGET_PROJECT", "")),
        default='PROJECT')

    snap_mode: EnumProperty(
        items=(('ON_SURFACE', "ON_SURFACE", ""),
               ("INSIDE", "INSIDE", ""),
               ("OUTSIDE", "OUTSIDE", ""),
               ("OUTSIDE_SURFACE", "OUTSIDE_SURFACE", ""),
               ("ABOVE_SURFACE", "ABOVE_SURFACE", "")),
        default='ABOVE_SURFACE')

    shrinkwrap_subsurf_levels: IntProperty(name="Subsurf Levels",default=0, min=0, max=6,description="Subsurf Levels")
    project_limit: FloatProperty(name="Project Limit",default=0, min=0, max=100, precision=3,description="Project Limit")
    use_negative_direction: BoolProperty(name="Negative",default=True,description="Negative")
    use_positive_direction: BoolProperty(name="Positive",default=True,description="Positive")
    use_invert_cull: BoolProperty(name="Invert Cull",default=False,description="Invert Cull")
    mirror_axis: BoolVectorProperty(default=[False, False, False], size=3, name="")
    cull_face: EnumProperty(
        items=(('OFF', "OFF", ""),
               ("FRONT", "FRONT", ""),
               ("BACK", "BACK", "")),
        default='OFF')

    # SUBSURF SETTINGS
    subsurf_levels: IntProperty(name="",default=0, min=0, max=6,description="Subsurf Levels")
    show_only_control_edges: BoolProperty(name="",default=True,description="Optimal Display")

    info: BoolProperty(
        name="",
        default=False,
        description="INFO")

    def draw(self, context):
        layout = self.layout
        icons = load_icons()

        row = layout.row(align=True)
        row.prop(self, "prefs_tabs", expand=True)
        row.scale_y = 1.5
        if self.prefs_tabs == 'info':
            box = layout.box()
            icon = icons.get("icon_discord")
            row = box.row(align=True)
            row.scale_y = 2
            row.operator("wm.url_open", text="SUPPORT ON DISCORD FOR CUSTOMERS",
                         icon_value=icon.icon_id).url = "https://discord.gg/ctQAdbY"
            row.scale_x = 2
            row.prop(self, 'info', icon='INFO')
            if self.info:
                box = layout.box()
                split = box.split()
                col = split.column()
                row = col.row(align=True)
                row.label(text="Join our Discord community for customer support! As a valued customer, you’ll gain access to exclusive benefits:")
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.label(text="1. Add-on Support Channel: To access this channel, simply send us a copy of your receipt to our email address below.")
                row = col.row(align=True)
                row.label(text="2. Latest Builds: Stay up-to-date with the latest builds of our add-ons.")
                row = col.row(align=True)
                row.label(text="3. Feature Requests: Have a feature in mind? Feel free to ask—we’re here to listen!")
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.label(text="🔗 Discord Invite Link: https://discord.gg/ctQAdbY")
                row = col.row(align=True)
                row.label(text="📧 Email: mail.blscripts@gmail.com")
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.label(text="Thank you for supporting our work! If you haven’t purchased the add-on yet, ")
                row = col.row(align=True)
                row.label(text="consider doing so it helps sustain years of effort and support for all our add-ons.")

            box = layout.box()
            box.label(text="Welcome to SpeedRetopo, this addon allows you to make easy and Fast Retopology.")
            box.label(text="The addon was made from profesionnal for you and is really simple to use.")
            box.label(text="It gives you all the necessary tools to work on your retopology.")

            box = layout.box()
            box.label(text="The Documentation is located in the Active tool ", icon='HELP')
            box.label(text="and Workspace Settings of the Property Editor.")
            box.label(text="Video Documentation")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=30"

            box = layout.box()
            box.label(text="RETOPO MT", icon='UV_VERTEXSEL')
            box.label(text="Retopo MT isn't my addon, so, it's not shipped with Speedretopo.")
            box.label(text="You can download it on this link.")
            icon = icons.get("icon_web")
            box.operator("wm.url_open", text="CLICK HERE",
                         icon_value=icon.icon_id).url = "https://www.dropbox.com/s/bp2bggryk2tlm3a/retopo_mt_2_1_2.py?dl=0"

        if self.prefs_tabs == 'options':
            box = layout.box()
            row = box.row(align=True)
            row.scale_y = 1.5
            row.label(text="",icon='MENU_PANEL')
            row.prop(self, "show_hide_menu_settings", text="MENUS SETTINGS",
                     icon='TRIA_UP' if self.show_hide_menu_settings else 'TRIA_RIGHT')
            if self.show_hide_menu_settings:

                row = box.row(align=True)
                row.label(text="Panel Category:")
                row.prop(self, "category", text="")

                row = box.row(align=True)
                row.label(text="Choose Menu Type")
                row.prop(self, "use_menu_or_pie_menu", text="")

                row = box.row(align=True)
                row.label(text="Buttons Size")
                row.prop(self, "buttons_size")

                row = box.row(align=True)
                row.label(text="Always show Modifiers menu")
                row.prop(self, "show_modifiers_menu", text="      ")

                row = box.row(align=True)
                row.label(text="Always show Tools menu")
                row.prop(self, "show_tools_menu", text="      ")

                row = box.row(align=True)
                row.label(text="Always show Shading menu")
                row.prop(self, "show_shading_menu", text="      ")

                row = box.row(align=True)
                row.label(text="Number of Faces for the Reference Object")
                row.prop(self, "reference_nbf", text="      ")

                row = box.row(align=True)
                row.label(text="Show Help in the UI")
                row.prop(self, "show_help_buttons", text="      ")

            # RETOPO
            box = layout.box()
            row = box.row(align=True)
            row.scale_y = 1.5
            icon = icons.get("icon_polybuild")
            row.label(text="", icon_value=icon.icon_id)
            row.prop(self, "show_hide_retopo_settings", text="RETOPOLOGY SETTINGS",
                     icon='TRIA_UP' if self.show_hide_retopo_settings else 'TRIA_RIGHT')

            if self.show_hide_retopo_settings:
                row = box.row(align=True)
                row.label(text="Start Retopo From")
                row.prop(self, "start_from", text="")

                row = box.row(align=True)
                row.label(text="Auto Add Mirror")
                row.prop(self, "auto_add_mirror", text="      ")

                if not self.start_from == 'POLYBUILD':
                    row = box.row(align=True)
                    row.label(text="Auto Add Shrinkwrap")
                    row.prop(self, "auto_add_shrinkwrap", text="      ")

                row = box.row(align=True)
                row.label(text="Use Tweak Tool")
                row.prop(self, "change_selection_tool", text="      ")

                row = box.row(align=True)
                row.label(text="Use Smooth Shading")
                row.prop(self, "smooth_shading", text="      ")

                if bpy.app.version < (3, 6, 0):
                    row = box.row(align=True)
                    row.label(text="Use Hidden Wire")
                    row.prop(self, "hidden_wire", text="      ")
                else:
                    row = box.row(align=True)
                    row.label(text="Use Retopology Shading")
                    row.prop(self, "retopology_shading", text="      ")

                row = box.row(align=True)
                row.label(text="Use Wireframe")
                row.prop(self, "use_wireframe", text="      ")

                row = box.row(align=True)
                row.label(text="Use In Front")
                row.prop(self, "use_in_front", text="      ")

                row = box.row(align=True)
                row.label(text="Use Color")
                row.prop(self, "use_color_shader", text="      ")


                if self.use_color_shader:
                    row = box.row(align=True)
                    row.label(text="Color")
                    row.prop(self, "obj_color")

                # MIRROR
                row = box.row(align=True)
                row.scale_y = 1.5
                row.label(text="", icon='MOD_MIRROR')
                row.prop(self, "show_hide_mirror_modifiers_settings", text="MIRROR MODIFIER",
                         icon='TRIA_UP' if self.show_hide_mirror_modifiers_settings else 'TRIA_RIGHT')
                if self.show_hide_mirror_modifiers_settings:
                    split = box.split()
                    col1 = split.column()
                    col1.label(text="Axis")
                    col1.label(text="Bisect Axis")
                    col1.label(text="Bisect Flip Axis")

                    col2 = split.column()
                    row = col2.row(align=True)
                    row.prop(self, "use_axis_x", text="X", expand=True)
                    row.prop(self, "use_axis_y", text="Y", expand=True)
                    row.prop(self, "use_axis_z", text="Z", expand=True)

                    row = col2.row(align=True)
                    row.prop(self, "use_bisect_axis_x", text="X", expand=True)
                    row.prop(self, "use_bisect_axis_y", text="Y", expand=True)
                    row.prop(self, "use_bisect_axis_z", text="Z", expand=True)

                    row = col2.row(align=True)
                    row.prop(self, "use_bisect_flip_axis_x", text="X", expand=True)
                    row.prop(self, "use_bisect_flip_axis_y", text="Y", expand=True)
                    row.prop(self, "use_bisect_flip_axis_z", text="Z", expand=True)

                    row = box.row(align=True)
                    row.label(text="Clipping")
                    row.prop(self, "use_clip", text="      ")

                    row = box.row(align=True)
                    row.label(text="Merge")
                    row.prop(self, "use_merge", text="      ")
                    if self.use_merge:
                        row = box.row(align=True)
                        row.label(text="Merge Threshold")
                        row.prop(self, "merge_threshold")

                # SHRINKWRAP
                row = box.row(align=True)
                row.scale_y = 1.5
                row.label(text="", icon='MOD_SHRINKWRAP')
                row.prop(self, "show_hide_shrinkwrap_modifiers_settings", text="SHRINKWRAP MODIFIER",
                         icon='TRIA_UP' if self.show_hide_shrinkwrap_modifiers_settings else 'TRIA_RIGHT')
                if self.show_hide_shrinkwrap_modifiers_settings:
                    split = box.split()
                    col = split.column()

                    row = col.row(align=True)
                    row.label(text="Wrap Method")
                    row.prop(self, "wrap_method", text="")

                    if self.wrap_method in {'NEAREST_SURFACEPOINT', 'TARGET_PROJECT', 'NEAREST_VERTEX'}:
                        row = box.row(align=True)
                        row.label(text="Snap Mode")
                        row.prop(self, "snap_mode", text="")

                    elif self.wrap_method == 'PROJECT':
                        row = box.row(align=True)
                        row.label(text="Snap Mode")
                        row.prop(self, "snap_mode", text="")

                        split = box.split()
                        col = split.column()
                        col.label(text="Project Limit:")
                        col = split.column(align=True)
                        col.prop(self, 'project_limit', expand=True)

                        split = box.split()
                        col = split.column()
                        col.label(text="Subdivision Levels:")
                        col = split.column(align=True)
                        col.prop(self, 'shrinkwrap_subsurf_levels', expand=True)

                        split = box.split()
                        col1 = split.column()
                        col1.label(text="Axis")
                        col2 = split.column()
                        row = col2.row(align=True)
                        row.prop(self, "shrinkwrap_axis_x", text="X", expand=True)
                        row.prop(self, "shrinkwrap_axis_y", text="Y", expand=True)
                        row.prop(self, "shrinkwrap_axis_z", text="Z", expand=True)

                        split = box.split()
                        col = split.column()
                        row = col.row(align=True)
                        row.label(text="Negative")
                        row.prop(self, "use_negative_direction", text="      ")

                        split = box.split()
                        col = split.column()
                        row = col.row(align=True)
                        row.label(text="Positive")
                        row.prop(self, "use_positive_direction", text="      ")

                        split = box.split()
                        col = split.column()
                        row = col.row(align=True)
                        row.label(text="Cull Faces:")
                        row.prop(self, "cull_face", text="")

                        if self.cull_face in {'FRONT', 'BACK'}:
                            split = box.split()
                            col = split.column()
                            row = col.row(align=True)
                            row.label(text="Invert Cull")
                            row.prop(self, "use_invert_cull", text="      ")

                    split = box.split()
                    col = split.column()
                    col.label(text="Offset:")
                    col = split.column(align=True)
                    col.prop(self, 'shrinkwrap_offset', expand=True)

                # SUBSURF
                row = box.row(align=True)
                row.scale_y = 1.5
                row.label(text="", icon='MOD_SUBSURF')
                row.prop(self, "show_hide_subsurf_modifiers_settings", text="SUBSURF MODIFIER",
                         icon='TRIA_UP' if self.show_hide_subsurf_modifiers_settings else 'TRIA_RIGHT')
                if self.show_hide_subsurf_modifiers_settings:
                    split = box.split()
                    col = split.column()
                    col.label(text="Subdivision Levels:")
                    col = split.column(align=True)
                    col.prop(self, 'subsurf_levels', expand=True)

                    split = box.split()
                    col = split.column()
                    row = col.row(align=True)
                    row.label(text="Optimal Display")
                    row.prop(self, "show_only_control_edges", text="      ")

        # KEYMAPS
        if self.prefs_tabs == 'keymaps':
            wm = bpy.context.window_manager
            draw_keymap_items(wm, layout)

        # Links
        if self.prefs_tabs == 'links':

            # TUTORIALS
            box = layout.box()
            row = box.row(align=True)
            row.label(text="TUTORIALS & ADD-ONS")

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_gumroad")
            row.operator("wm.url_open", text="GUMROAD",
                         icon_value=icon.icon_id).url = "https://pitiwazou-1.gumroad.com/"

            row = box.row(align=True)
            row.scale_y = 1.3
            row.operator("wm.url_open", text="GUMROAD - SPEEDFLOW",
                         icon_value=icon.icon_id).url = "https://pitiwazou.gumroad.com/"

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_market")
            row.operator("wm.url_open", text="MARKET",
                         icon_value=icon.icon_id).url = "https://blendermarket.com/creators/pitiwazou"

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_artstation")
            row.scale_y = 1.3
            row.operator("wm.url_open", text="ARTSTATION",
                         icon_value=icon.icon_id).url = "https://www.artstation.com/a/651436"

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_flipped_normals")
            row.operator("wm.url_open", text="FLIPPED NORMALS",
                         icon_value=icon.icon_id).url = "https://flippednormals.com/creator/pitiwazou?tagIds=1"

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_youtube")
            row.operator("wm.url_open", text="YOUTUBE",
                         icon_value=icon.icon_id).url = "https://www.youtube.com/user/pitiwazou"

            # LINKS
            box = layout.box()
            row = box.row(align=True)
            row.label(text="SOCIAL")

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_web")
            row.operator("wm.url_open", text="PITIWAZOU.COM",
                         icon_value=icon.icon_id).url = "http://www.pitiwazou.com/"

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_artstation")
            row.operator("wm.url_open", text="ARTSTATION",
                         icon_value=icon.icon_id).url = "https://www.artstation.com/artist/pitiwazou"

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_twitter")
            row.operator("wm.url_open", text="TWITTER",
                         icon_value=icon.icon_id).url = "https://twitter.com/#!/pitiwazou"

            row = box.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_facebook")
            row.operator("wm.url_open", text="FACEBOOK",
                         icon_value=icon.icon_id).url = "https://www.facebook.com/Pitiwazou-C%C3%A9dric-Lepiller-120591657966584/"

# -----------------------------------------------------------------------------
#    Keymap
# -----------------------------------------------------------------------------
addon_keymaps = []

def draw_keymap_items(wm, layout):
    kc = wm.keyconfigs.user

    for name, items in keymaps_items_dict.items():
        kmi_name, kmi_value, km_name = items[:3]
        box = layout.box()
        split = box.split()
        col = split.column()
        col.label(text=name)
        col.separator()
        km = kc.keymaps[km_name]
        get_hotkey_entry_item(kc, km, kmi_name, kmi_value, col)

def get_hotkey_entry_item(kc, km, kmi_name, kmi_value, col):
    # for menus and pie_menu
    if kmi_value:
        for km_item in km.keymap_items:
            if km_item.idname == kmi_name and km_item.properties.name == kmi_value:
                col.context_pointer_set('keymap', km)
                rna_keymap_ui.draw_kmi([], kc, km, km_item, col, 0)
                return

        col.label(text=f"No hotkey entry found for {kmi_value}")
        col.operator(SPEEDRETOPO_OT_Add_Hotkey.bl_idname, icon='ADD')

    # for operators
    else:
        if km.keymap_items.get(kmi_name):
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi(
                [], kc, km, km.keymap_items[kmi_name], col, 0)
        else:
            col.label(text=f"No hotkey entry found for {kmi_name}")
            col.operator(SPEEDRETOPO_OT_Add_Hotkey.bl_idname, icon='ADD')

class SPEEDRETOPO_OT_Add_Hotkey(Operator):
    ''' Add hotkey entry '''
    bl_idname = "template_rmb.add_hotkey"
    bl_label = "Add Hotkeys"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        add_hotkey()

        self.report({'INFO'},
                    "Hotkey added in User Preferences -> Input -> Screen -> Screen (Global)")
        return {'FINISHED'}

def add_hotkey():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if not kc:
        return

    for items in keymaps_items_dict.values():
        kmi_name, kmi_value, km_name, space_type, region_type = items[:5]
        eventType, eventValue, ctrl, shift, alt = items[5:]
        km = kc.keymaps.new(name=km_name, space_type=space_type,
                            region_type=region_type)

        kmi = km.keymap_items.new(kmi_name, eventType,
                                  eventValue, ctrl=ctrl, shift=shift,
                                  alt=alt

                                  )
        if kmi_value:
            kmi.properties.name = kmi_value

        kmi.active = True

    addon_keymaps.append((km, kmi))

def remove_hotkey():
    ''' clears all addon level keymap hotkeys stored in addon_keymaps '''

    kmi_values = [item[1] for item in keymaps_items_dict.values() if item]
    kmi_names = [item[0] for item in keymaps_items_dict.values() if item not in ['wm.call_menu', 'wm.call_menu_pie']]

    for km, kmi in addon_keymaps:
        # remove addon keymap for menu and pie menu
        if hasattr(kmi.properties, 'name'):
            if kmi_values:
                if kmi.properties.name in kmi_values:
                    km.keymap_items.remove(kmi)

        # remove addon_keymap for operators
        else:
            if kmi_names:
                if kmi.name in kmi_names:
                    km.keymap_items.remove(kmi)

    addon_keymaps.clear()

# -----------------------------------------------------------------------------
#    PROPERTYGROUP
# -----------------------------------------------------------------------------
class SPEEDRETOPO_PropertyGroup(PropertyGroup):
    show_doc_intro: BoolProperty(default=True, description="Show/Hide Introduction")
    show_doc_start: BoolProperty(default=True, description="Show/Hide Starting Your Retopology")
    show_doc_ref: BoolProperty(default=True, description="Show/Hide Reference Object")
    show_doc_modifiers: BoolProperty(default=False, description="Show/Hide Modifiers")
    show_doc_tools: BoolProperty(default=False, description="Show/Hide Tools")
    show_doc_shading: BoolProperty(default=False, description="Show/Hide Shading")
    show_doc_start_cont_fin: BoolProperty(default=False, description="Show/Hide Start Continue Finalize")
    show_doc_prefs: BoolProperty(default=False, description="Show/Hide Preferences")

CLASSES =  [SPEEDRETOPO_MT_addon_preferences,
            SPEEDRETOPO_OT_Add_Hotkey,
            SPEEDRETOPO_PropertyGroup]

# -----------------------------------------------------
# REGISTERS
# -----------------------------------------------------
def register():
    operators.register()
    ui.register()
    documentation.register()

    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except:
            print(f"{cls.__name__} already registred")

    # Update Category
    context = bpy.context
    prefs = context.preferences.addons[__name__].preferences
    update_speedretopo_category(prefs, context)

    # PropertyGroup
    Object.speedretopo_ref_object = PointerProperty(name="", type=Object)
    bpy.types.WindowManager.speedretopo_PropertyGroup = PointerProperty(type=SPEEDRETOPO_PropertyGroup)

    add_hotkey()


def unregister():
    operators.unregister()
    ui.unregister()
    documentation.unregister()

    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    remove_hotkey()


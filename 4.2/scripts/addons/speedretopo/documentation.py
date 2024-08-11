# -*- coding:utf-8 -*-

# SPEEDRETOPO Add-on
# Copyright (C) 2018 Cedric Lepiller aka Pitiwazou
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

import bpy
from bpy.types import Menu, Panel
from .icon.icons import load_icons

#Panel
class SPEEDRETOPO_PT_documentation(Panel):
    bl_label = "Speedretopo Documentation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        speedretopo_PropertyGroup = context.window_manager.speedretopo_PropertyGroup

        icons = load_icons()
        layout = self.layout
        icon = icons.get("icon_polybuild")
        layout.label(text="SPEEDRETOPO DOCUMENTATION", icon_value=icon.icon_id)

#-------INTRODUCTION
        box = layout.box()
        box.prop(speedretopo_PropertyGroup, "show_doc_intro", text="INTRODUCTION", icon='TRIA_UP' if speedretopo_PropertyGroup.show_doc_intro else 'TRIA_DOWN')
        if speedretopo_PropertyGroup.show_doc_intro:
            box.label(text="SpeeRetopo Addon's helps you to make easy and Fast Retopology.")
            box.label(text="The addon was made for beginners and is really simple to use.")
            box.label(text="It gives you all the necessary tools to work on your retopology.")
            box.label(text="The addon is made by a freelance artist for all blender artists.")

            box.label(text="Video Documentation")
            icon = icons.get("icon_youtube")
            box.operator("wm.url_open", text="VIDEO", icon_value=icon.icon_id).url = "https://youtu.be/cKhZNOFc4Us?t=30"

#-------STARTING YOUR FIRST RETOPOLOGY
        box = layout.box()
        box.prop(speedretopo_PropertyGroup, "show_doc_start", text="STARTING YOUR FIRST RETOPOLOGY",
                 icon='TRIA_UP' if speedretopo_PropertyGroup.show_doc_start else 'TRIA_DOWN')
        if speedretopo_PropertyGroup.show_doc_start:
            box.label(text="To start your Retopology, you need to select the reference object first.")
            box.label(text="Note: This object will be connected to your Retopo Object.", icon='WORDWRAP_ON')

            box.separator()
            icon = icons.get("icon_decimate")
            box.label(text="DECIMATE", icon_value=icon.icon_id)
            box.label(text="If you object has too many vertices, it can decrease performances.")
            box.label(text="Then, you can Decimate it with the Decimate Modifier.")
            box.label(text="Click on the button en set the ratio to something lighter.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=2111"


            box.separator()
            box.label(text="You will now see a menu to Start the Retopology.")
            box.operator("wm.url_open", text="IMAGE",
                         icon='IMAGE_DATA').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_001.jpg"
            box.label(text="You will be able to choose the tool you want to use.")
            box.operator("wm.url_open", text="IMAGE",
                         icon='IMAGE_DATA').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_002.jpg"

            box.separator()
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us"

            box.separator()
            icon = icons.get("icon_vertex")
            box.label(text="VERTEX", icon_value=icon.icon_id)
            box.label(text="That Vertex tool is a simple vertex, as simple as that!")
            box.label(text="You can place it where you want on your reference mesh.")
            box.label(text="After that you just have to extrude it and use normal poly editing tools.")

            box.separator()
            icon = icons.get("icon_face")
            box.label(text="face", icon_value=icon.icon_id)
            box.label(text="That Face tool is a simple face, as simple as that!")
            box.label(text="You can place it where you want on your reference mesh.")
            box.label(text="After that you just have to extrude it and use normal poly editing tools.")

            box.separator()
            icon = icons.get("icon_bsurface")
            box.label(text="BSURFACE", icon_value=icon.icon_id)
            box.label(text="Bsurface is a well known Addon that allows you")
            box.label(text="to draw lines and create faces on your Retopology.")
            box.label(text="By pressing D key and draw, you will create lines.")
            box.label(text="Once your lines are created, you can press Add Bsurface button in the Menu.")
            box.label(text="That will create the first faces of your retopology.")

            box.separator()
            icon = icons.get("icon_polybuild")
            box.label(text="POLYBUILD", icon_value=icon.icon_id)
            box.label(text="Polybuild is an inside tool from Blender to help you create and edit your retopology.")
            box.label(text="It's a several in one tool using shortcuts to extrude faces and move vertices")

            box.separator()
            box.label(text="SpeedRetopo automatize things for you,")
            box.label(text="it will automatically create modifiers like Mirror and Shrinkwrap.")
            box.label(text="You just have to start and edit your retopology.")
            box.separator()
            box.label(text="So, when you have created your first faces with the tool of you choice, you will have the edit menu.")
            box.label(text="With it, you will be able to edit modifiers and your mesh.")


#-------REFERENCE OBJECT
        box = layout.box()
        box.prop(speedretopo_PropertyGroup, "show_doc_ref", text="REFERENCE OBJECT",
                 icon='TRIA_UP' if speedretopo_PropertyGroup.show_doc_ref else 'TRIA_DOWN')
        if speedretopo_PropertyGroup.show_doc_ref:
            box.label(text="The reference object is connected to your retopo object.")
            box.label(text="It is used as reference for the modifiers, Mirror and Shrinkwrap.")
            box.label(text="You can remove it and change it.")
            box.label(text="Note: The addon needs it to use modifiers.", icon='WORDWRAP_ON')
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_reference_object.mp4"

#-------MODIFIERS
        box = layout.box()
        box.prop(speedretopo_PropertyGroup, "show_doc_modifiers", text="MODIFIERS",
                 icon='TRIA_UP' if speedretopo_PropertyGroup.show_doc_modifiers else 'TRIA_DOWN')
        if speedretopo_PropertyGroup.show_doc_modifiers:
            box.label(text="You will be able to edit the modifiers.")
            box.label(text="Apply them, remove them and add them again if necessary.")
            box.label(text="You will be able to align the center Vertices to .")

            box.separator()
            box.label(text="MIRROR", icon='MOD_MIRROR')
            box.label(text="The Mirror Modifiers create a mirror of your object on the X axis.")
            box.label(text="You can Apply it, remove it, use the clipping setting")
            box.label(text="to keep the middle vertices at the center of the scene.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_mirror_modifier.mp4"

            box.separator()
            box.label(text="SHRINKWRAP", icon='MOD_SHRINKWRAP')
            box.label(text="The Shrinkwrap Modifiers projects your retopology on the surface")
            box.label(text="of the reference object.")
            box.label(text="You can Apply it, remove it and update it.")
            box.label(text="Note: This Modifiers needs to be updated regularly to be efficient.", icon='WORDWRAP_ON')
            box.label(text="Note2: The modifier auto align to center the vertices you have setted as center.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_shrinkwrap_modifier.mp4"

            box.separator()
            box.label(text="SUBSURF", icon='MOD_SUBSURF')
            box.label(text="The Subsurf Modifiers subdivide your surface")
            box.label(text="it's useful to see if the retopology is correct.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_subsurf_modifier.mp4"

#-------TOOLS
        box = layout.box()
        box.prop(speedretopo_PropertyGroup, "show_doc_tools", text="TOOLS",
                 icon='TRIA_UP' if speedretopo_PropertyGroup.show_doc_tools else 'TRIA_DOWN')
        if speedretopo_PropertyGroup.show_doc_tools:
            box.label(text="In Edit Mode you have differents tools.")

            box.separator()
            icon = icons.get("icon_bsurface")
            box.label(text="BSURFACE", icon_value=icon.icon_id)
            box.label(text="Listed previously, allow you to draw lines to create faces.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=899"

            box.separator()
            icon = icons.get("icon_align_to_x")
            box.label(text="ALING TO X", icon_value=icon.icon_id)
            box.label(text="Align the center vertices to the center of the scene.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_align_to_x.mp4"

            box.separator()
            icon = icons.get("icon_retopomt")
            box.label(text="RETOPO MT", icon_value=icon.icon_id)
            box.label(text="Special tool for retopology.")
            box.label(text="Note: You need to activate it in the preferences.", icon='WORDWRAP_ON')
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_retopo_mt.mp4"

            box.separator()
            icon = icons.get("icon_space")
            box.label(text="SPACE", icon_value=icon.icon_id)
            box.label(text="This tool keep the vertices on a loop at the same space.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_space_tool.mp4"

            box.separator()
            icon = icons.get("icon_relax")
            box.label(text="RELAX", icon_value=icon.icon_id)
            box.label(text="Relax the selection to make it better.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_relax_tool.mp4"

            box.separator()
            icon = icons.get("icon_gstretch")
            box.label(text="GSTRETCH", icon_value=icon.icon_id)
            box.label(text="This tool aligns vertices with grease pencil lines.")
            box.label(text="Note: Seems not to work on latest builds of blender.", icon='WORDWRAP_ON')
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_gstretch_tool.mp4"

            box.separator()
            icon = icons.get("icon_curve")
            box.label(text="CURVE", icon_value=icon.icon_id)
            box.label(text="This tool creates a curve on 3 points selection on a loop.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_curve_tool.mp4"

            box.separator()
            icon = icons.get("icon_bridge")
            box.label(text="BRIDGE", icon_value=icon.icon_id)
            box.label(text="This tool creates faces between too selected loops.")
            box.label(text="Note: Better to have the same amount of vertices.", icon='WORDWRAP_ON')
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_bridge_tool.mp4"

            box.separator()
            icon = icons.get("icon_gridfill")
            box.label(text="GRIDFILL", icon_value=icon.icon_id)
            box.label(text="This tool creates faces in holes.")
            box.label(text="you need to select 2 loops with the same number of vertices.")
            box.label(text="Note: Check the looptools documentation to learn more about it.", icon='WORDWRAP_ON')
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_bridge_tool.mp4"

            box.separator()
            icon = icons.get("icon_recalculate_normals")
            box.label(text="RECALCULATE NORMALS", icon_value=icon.icon_id)
            box.label(text="This tool flips the normals of the mesh outside.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_recalculate_normals.mp4"

            box.separator()
            icon = icons.get("icon_flip_normals")
            box.label(text="FLIP NORMALS", icon_value=icon.icon_id)
            box.label(text="This tool flips the normals of the selected faces.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_flip_normals.mp4"

            box.separator()
            box.label(text="CENTER TOOLS", icon='THREE_DOTS')
            box.label(text="Center tools allows you too set some vertices as center.")
            box.label(text="That's mean, those vertices will always be at the center of the grid when you will")
            box.label(text="update the Shrinkwrap modifier.")
            box.separator()
            box.label(text="You can set or Unset the selection.")
            box.label(text="Also Select and clear the entire set to remove all vertices from the set.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_center_tools.mp4"

            box.separator()
            box.label(text="FREEZING TOOLS", icon='FREEZE')
            box.label(text="Freezing tools allows you too freeze some vertices.")
            box.label(text="That's mean, those vertices will be used for the Shrinkwrap modifier.")
            box.separator()
            box.label(text="You can Freeze or Unfreeze the selection.")
            box.label(text="Also Select and clear the entire set to remove all vertices from the set.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_freezing_tools.mp4"

#-------SHADING
        box = layout.box()
        box.prop(speedretopo_PropertyGroup, "show_doc_shading", text="SHADING",
                 icon='TRIA_UP' if speedretopo_PropertyGroup.show_doc_shading else 'TRIA_DOWN')
        if speedretopo_PropertyGroup.show_doc_shading:
            box.label(text="The shading part help you to better see your retopology")
            box.label(text="on the reference object.")
            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_shading.mp4"

            box.separator()
            box.label(text="HIDDEN WIRE")
            box.label(text="Will hide faces to only see the wireframe of your object.")

            box.separator()
            box.label(text="IN FRONT")
            box.label(text="You will always see the retopo object on top of the reference object.")

            box.separator()
            box.label(text="WIREFRAME")
            box.label(text="Will show the wireframe of your object.")

            box.separator()
            box.label(text="BACK FACE CULLING")
            box.label(text="You will see through the back of the faces of your object.")

            box.separator()
            box.label(text="COLOR")
            box.label(text="It will add a color shader with transparency to your object.")
            box.label(text="You can change the color and remove it.")
            box.label(text="Note: It will disable the Hidden Wire option.", icon='WORDWRAP_ON')

#-------PREFERENCES
        box = layout.box()
        box.prop(speedretopo_PropertyGroup, "show_doc_prefs", text="PREFERENCES",
                 icon='TRIA_UP' if speedretopo_PropertyGroup.show_doc_prefs else 'TRIA_DOWN')
        if speedretopo_PropertyGroup.show_doc_prefs:
            box.label(text="MENU SETTINGS")
            box.separator()
            box.label(text="The addon gives you tools in the preferences to set your settings.")
            box.label(text="You can the category of the UI menu.")
            box.label(text="You can use a menu, or a pie menu.")
            box.label(text="You can change the button size of the UI menu.")
            box.label(text="You can expand or not the tabs in the UI menu.")

            box.separator()
            box.label(text="RETOPOLOGY SETTINGS")
            box.separator()
            box.label(text="You can set the settings for your retopology.")
            box.label(text="Choose the tool you always want to use and the shading, color, etc.")

            box.separator()
            box.label(text="KEYMAPS")
            box.separator()
            box.label(text="You can change the keymaps to call the menu/pie menu.")

            box.operator("wm.url_open", text="VIDEO",
                         icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=74"


# -----------------------------------------------------
# REGISTER/UNREGISTER
# -----------------------------------------------------
CLASSES =  [SPEEDRETOPO_PT_documentation]

def register():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except:
            print(f"{cls.__name__} already registred")


def unregister():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    # for cls in CLASSES :
    #     if hasattr(bpy.types, cls.__name__):
    #         bpy.utils.unregister_class(cls)
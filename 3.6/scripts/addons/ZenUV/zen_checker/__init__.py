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

""" Init Zen Checker """

from bpy.utils import register_class, unregister_class
import bpy
# from bpy.types import StringProperty, PropertyGroup, IntProperty, CollectionProperty
from ZenUV.zen_checker.panel import ZenUVCheckerPopover
from ZenUV.zen_checker.checker import (
    ZUVChecker_OT_CheckerToggle,
    ZUVChecker_OT_Reset,
    ZUVChecker_OT_Remove,
    ZUVChecker_OT_OpenEditor,
    ZUVChecker_OT_ResetPath
)
from ZenUV.zen_checker.files import (
    ZUVChecker_OT_CollectImages,
    ZUVChecker_OT_AppendFile
)
from ZenUV.zen_checker.stretch_map import (
    ZUV_OT_SelectStretchedIslands,
    ZUV_OT_StretchMapSwitch,
)


classes = [
    ZUVChecker_OT_CollectImages,
    ZUVChecker_OT_CheckerToggle,
    ZUVChecker_OT_Reset,
    ZUVChecker_OT_Remove,
    ZUVChecker_OT_OpenEditor,
    ZUVChecker_OT_AppendFile,
    ZUVChecker_OT_ResetPath,
    ZenUVCheckerPopover,
    ZUV_OT_SelectStretchedIslands,
    ZUV_OT_StretchMapSwitch
]

addon_keymaps = []


class ZUV_CheckerProperties(bpy.types.PropertyGroup):

    bl_idname = "ZenUvChecker"
    prev_color_type: bpy.props.StringProperty(name="Color Type", default='MATERIAL')


def register():
    """ Register classes """
    for cl in classes:
        register_class(cl)
        # print("Register class: ", cl)

    register_class(ZUV_CheckerProperties)
    bpy.types.Scene.zen_uv_checker = bpy.props.PointerProperty(type=ZUV_CheckerProperties)

    # wm = bpy.context.window_manager
    # if wm.keyconfigs.addon:
    #     km = wm.keyconfigs.addon.keymaps.new(name='Window', space_type='EMPTY')
    #     kmi = km.keymap_items.new('view3d.zch_toggle', 'T', 'PRESS', alt=True)
    #     addon_keymaps.append((km, kmi))


def unregister():
    """ Unregister classes """
    for cl in classes:
        unregister_class(cl)

    unregister_class(ZUV_CheckerProperties)

    del bpy.types.Scene.zen_uv_checker

    # wm = bpy.context.window_manager
    # kc = wm.keyconfigs.addon
    # if kc:
    #     for km, kmi in addon_keymaps:
    #         km.keymap_items.remove(kmi)
    # addon_keymaps.clear()


if __name__ == "__main__":
    pass

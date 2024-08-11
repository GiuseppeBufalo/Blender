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

# (c) 2022 Jakub Uhlik

from . import shaders
from . import widgets
from . import infobox
from . import grid
from . import theme

import bpy

classes = shaders.classes + widgets.classes + infobox.classes + grid.classes + theme.classes


# NOTE: module status
# grid -------- ok
# infobox ----- ok
# shaders ----- remove `ui_overlay.*` shader, it is used by `widgets.widgets.ToolOverlay` which is obsolete and only used in `curve.draw_bezier_area` where is disabled.. otherwise ok
# theme ------- ok
# widgets ----- ok (only remove ToolOverlay when manual.tools is merged)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

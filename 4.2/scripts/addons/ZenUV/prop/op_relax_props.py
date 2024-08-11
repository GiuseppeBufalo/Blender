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


import bpy
from ZenUV.ui.labels import ZuvLabels


class ZUV_RelaxOpProps(bpy.types.PropertyGroup):

    method: bpy.props.EnumProperty(
        name=ZuvLabels.PROP_RELAX_METHOD_LABEL,
        description=ZuvLabels.PROP_RELAX_METHOD_DESC,
        items=[
            ("ZENRELAX", "Zen Relax", ""),
            ("ANGLE_BASED", "Angle Based", ""),
            ("CONFORMAL", "Conformal", ""),
        ]
    )
    select: bpy.props.BoolProperty(
        name="Select",
        description="Select relaxed Island",
        default=False
    )
    relax: bpy.props.BoolProperty(
        name="Relax",
        description="Relax",
        default=True,
        options={'HIDDEN'}
    )
    show_log: bpy.props.BoolProperty(
        name="Show Log",
        description="Show Log",
        default=True,
        options={'HIDDEN'}
    )

    relax_mode: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    use_zensets: bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def draw_relax_props(self, layout, context):
        layout.prop(self, "method")
        layout.prop(self, "select")

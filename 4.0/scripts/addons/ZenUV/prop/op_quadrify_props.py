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
from bpy.props import BoolProperty, EnumProperty
from ZenUV.ui.labels import ZuvLabels


class ZUV_QuadrifyOpProps(bpy.types.PropertyGroup):

    # Quadrify property group. context.scene.zen_uv.op_quadrify_props

    packAfQuadrify: BoolProperty(
        name=ZuvLabels.PREF_PACK_AF_QUADRIFY_LABEL,
        description=ZuvLabels.PREF_PACK_AF_QUADRIFY_DESC,
        default=False)

    TagFinished: BoolProperty(
        name=ZuvLabels.PREF_QUADRIFY_TAG_FINISHED_LABEL,
        description=ZuvLabels.PREF_QUADRIFY_TAG_FINISHED_DESC,
        default=False)

    quadrifyOrientToWorld: BoolProperty(
        name=ZuvLabels.PREF_ORIENT_TO_WORLD_QUADRIFY_LABEL,
        description=ZuvLabels.PREF_ORIENT_TO_WORLD_QUADRIFY_DESC,
        default=False,
        options={'HIDDEN'}
        )

    QuadrifyBySelected: BoolProperty(
        name=ZuvLabels.PREF_QUADRIFY_BY_SELECTED_EDGES_LABEL,
        description=ZuvLabels.PREF_QUADRIFY_BY_SELECTED_EDGES_DESC,
        default=True)

    autoPinQuadrified: BoolProperty(
        name=ZuvLabels.PREF_AUTO_PIN_QUADRIFIED_LABEL,
        description=ZuvLabels.PREF_AUTO_PIN_QUADRIFIED_DESC,
        default=False)

    mark_borders: BoolProperty(
        name=ZuvLabels.PREF_UPD_SEAMS_AF_QUADRIFY_LABEL,
        description=ZuvLabels.PREF_UPD_SEAMS_AF_QUADRIFY_DESC,
        default=True)

    mark_seams: bpy.props.BoolProperty(name="Mark Seams", default=True, description="Mark seam in case Mark Borders is on")
    mark_sharp: bpy.props.BoolProperty(name="Mark Sharp", default=False, description="Mark sharp in case Mark Borders is on")

    average_td: BoolProperty(
        name="Average Texel Density",
        description="Averaging the size for the processed islands",
        default=True
    )

    orient: EnumProperty(
        name="Orient to",
        description="Orient Quadrified Islands",
        items=[
            ("INITIAL", "Initial", "Leave orientation as is"),
            ("VERTICAL", "Vertical", "Set orientation vertical"),
            ("HORIZONTAL", "Horizontal", "Set orientation horizontal")
        ],
        default="INITIAL"
    )

    def draw_quadrify_props(self, layout, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout.prop(self, "QuadrifyBySelected")

        # Mark Section
        self.draw_mark_section(layout, addon_prefs)

        layout.prop(self, "orient")
        layout.prop(self, "average_td")

        # Post Process
        layout.label(text="Post Process:")
        p_box = layout.box()
        p_box.prop(self, "packAfQuadrify")
        p_box.prop(self, "autoPinQuadrified")
        p_box.prop(self, "TagFinished")

    def draw_mark_section(self, layout, addon_prefs):
        mark_box = layout.box()
        s_mark_settings = 'Mark Settings'
        s_mark_settings += ' (Global Mode)' if addon_prefs.useGlobalMarkSettings else ' (Local Mode)'
        mark_box.label(text=s_mark_settings)

        row = mark_box.row(align=True)
        row.prop(self, "mark_borders")
        sub_row = row.row(align=True)
        sub_row.enabled = self.mark_borders
        if not addon_prefs.useGlobalMarkSettings:
            sub_row.prop(self, "mark_seams")
            sub_row.prop(self, "mark_sharp")
        else:
            sub_row.enabled = False
            sub_row.prop(addon_prefs, "markSeamEdges")
            sub_row.prop(addon_prefs, "markSharpEdges")

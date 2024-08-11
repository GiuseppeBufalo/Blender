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

""" Hard Ops Popup Menu """

import bpy
from ZenUV.ui.labels import ZuvLabels


class ZUV_MT_HOPS_Popup(bpy.types.Menu):
    bl_label = "Zen UV"
    bl_idname = "ZUV_MT_HOPS_Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        layout = self.layout
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout.label(text="Nothing has changed.")
        layout.label(text="It looks like HOps addon")
        layout.label(text="is not installed on your system.")
        layout.separator()
        layout.label(text="To disable the notification ")
        layout.label(text="turn off option:")
        layout.prop(addon_prefs, "hops_uv_activate")
        layout.label(text="Or install the addon")
        layout.operator("wm.url_open",
                        text="Buy HOps addon",
                        icon="HELP").url = "https://gumroad.com/l/hardops"


def draw_zensets_popup(self, context):
    layout = self.layout
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    layout.label(text="Nothing has displayed.")
    layout.label(text="It looks like Zen Sets addon")
    layout.label(text="is not installed on your system.")
    layout.separator()
    layout.label(text="To disable the notification ")
    layout.label(text="turn off option:")
    layout.prop(addon_prefs, "use_zensets")
    layout.label(text="Or install the addon")
    layout.operator("wm.url_open",
                    text="Buy Zen Sets addon",
                    icon="HELP").url = "https://gumroad.com/l/ZenSets"


class ZUV_MT_ZenSets_Popup(bpy.types.Menu):
    bl_label = "Zen UV"
    bl_idname = "ZUV_MT_ZenSets_Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        draw_zensets_popup(self, context)

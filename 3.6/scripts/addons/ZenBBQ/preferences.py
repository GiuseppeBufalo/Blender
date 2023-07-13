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

# Copyright 2022, Dmitry Aleksandrovich Maslov (ABTOMAT)

import bpy

from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, BoolProperty, FloatProperty, IntProperty, StringProperty, EnumProperty, FloatVectorProperty

from . import globals as ZBBQ_Globals

from .blender_zen_utils import ZenLocks
from .draw_sets import ZBBQ_EdgeLayerManager, mark_groups_modified
from .ico import ZBBQ_Icons
from .labels import ZBBQ_Labels
from .colors import ZBBQ_Colors
from .commonFunc import ZBBQ_CommonFunc
from .consts import ZBBQ_Consts
from .units import ZBBQ_Unit, ZBBQ_UnitSystemsForEnumProperty, ZBBQ_Units, ZBBQ_UnitsForEnumPropertyConsideringUnitSystem
from .keymap_manager import draw_keymaps


def ZBBQ_RebuildColoredEdges(self, context):

    # ZBBQ_Overlay.ColoredEdgesRebuildForObjectsInModeIfDisplayed()

    try:
        ZenLocks.lock_depsgraph_update()

        for obj in context.objects_in_mode:
            if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                continue
            mark_groups_modified(ZBBQ_EdgeLayerManager, obj)

    finally:
        ZenLocks.unlock_depsgraph_update()
    pass


class ZBBQ_Pref_BevelPreset(PropertyGroup):

    radius: FloatProperty(
            name=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_Radius_Name,
            description=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_Radius_Desc,
            default=0.1,
            min=0,
            subtype="UNSIGNED",
            update=ZBBQ_RebuildColoredEdges
            # precision=3
    )

    unitSystem: EnumProperty(  # Yes, we need it here as well to check out which units we may include to Enum
            name=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_UnitSystem_Name,
            description=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_UnitSystem_Desc,
            items=ZBBQ_UnitSystemsForEnumProperty,
            default="METRIC"
    )

    units: EnumProperty(
            name=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_Units_Name,
            description=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_Units_Desc,
            items=lambda self, context: ZBBQ_UnitsForEnumPropertyConsideringUnitSystem(self.unitSystem),
            update=ZBBQ_RebuildColoredEdges
            # items=ZBBQ_UnitsForEnumProperty,
            # default="MILLIMETERS"
    )

    # To-Do: Remove this and make icon-generation from Color Vector

    colorId: StringProperty(
           name=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_ColorId_Name,
           description=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_ColorId_Desc,
           default="Blue"
    )

    color: FloatVectorProperty(
           name=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_Color_Name,
           description=ZBBQ_Labels.ZBBQ_Pref_BevelPreset_Prop_Color_Desc,
           subtype='COLOR_GAMMA',
           size=3,
           min=0, max=1
    )

    def iconId(self):
        return ZBBQ_Colors[self.colorId].iconId()

    def getUnitInfo(self):
        return ZBBQ_Units[self.units]

    def unitAndSceneScaleMultiplier(self):
        return ZBBQ_Unit.unitAndSceneScaleMultiplierByUnitsName(self.units)


class ZBBQ_Pref_BevelPresetGroup(PropertyGroup):

    title: StringProperty(
           name=ZBBQ_Labels.ZBBQ_Pref_BevelPresetGroup_Prop_Title_Name,
           description=ZBBQ_Labels.ZBBQ_Pref_BevelPresetGroup_Prop_Title_Desc,
           default="Untitled"
    )

    unitSystem: EnumProperty(
            name=ZBBQ_Labels.ZBBQ_Pref_BevelPresetGroup_Prop_UnitSystem_Name,
            description=ZBBQ_Labels.ZBBQ_Pref_BevelPresetGroup_Prop_UnitSystem_Desc,
            items=ZBBQ_UnitSystemsForEnumProperty,
            default="METRIC"
    )

    bevelPresets: CollectionProperty(type=ZBBQ_Pref_BevelPreset)
    bevelPresetsIndex: IntProperty(
            name=ZBBQ_Labels.ZBBQ_Pref_BevelPresetGroup_Prop_BevelPresetsIndex_Title,
            description=ZBBQ_Labels.ZBBQ_Pref_BevelPresetGroup_Prop_BevelPresetsIndex_Desc,
            default=0)

    def GetActiveBevelPreset(self):
        return self.bevelPresets[self.bevelPresetsIndex]


def ZBBQ_BevelPresetGroupsForDropdown():
    result = [(str(i), bpg.title, "") for i, bpg in enumerate(ZBBQ_CommonFunc.GetPrefs().bevelPresetGroups)]
    if ZBBQ_Globals.displaySceneIncludedBevelPresets:
        result.append((str(len(ZBBQ_CommonFunc.GetPrefs().bevelPresetGroups)), "[Scene Data] "+bpy.context.scene.ZBBQ_PresetsIncluded.title, ""))
    return result


class ZBBQ_Prefs(bpy.types.AddonPreferences):
    bl_idname = ZBBQ_Consts.addonId

    bevelPresetGroups: CollectionProperty(type=ZBBQ_Pref_BevelPresetGroup)

    bevelPresetGroupsDropdown: EnumProperty(
            name=ZBBQ_Labels.ZBBQ_Prefs_Prop_BevelPresetGroupsDropdown_Name,
            description=ZBBQ_Labels.ZBBQ_Prefs_Prop_BevelPresetGroupsDropdown_Desc,
            # items=lambda self, context: [(str(i), bpg.title+(" ("+ZBBQ_Units[bpg.units].shortTitle+")" if ZBBQ_Units[bpg.units].shortTitle != '' else ''), "") for i, bpg in enumerate(ZBBQ_CommonFunc.GetPrefs().bevelPresetGroups)]
            items=lambda self, context: ZBBQ_BevelPresetGroupsForDropdown(),
            update=ZBBQ_RebuildColoredEdges
    )

    smartSelectRadiusThreshold: FloatProperty(
            name=ZBBQ_Labels.ZBBQ_Prefs_Prop_SmartSelectRadiusThreshold_Name,
            description=ZBBQ_Labels.ZBBQ_Prefs_Prop_SmartSelectRadiusThreshold_Desc,
            default=ZBBQ_Consts.smartSelectRadiusThresholdDefault,
            min=0,
            max=20,
            # max=150,
            # soft_max=20,
            subtype='PERCENTAGE')

    cyclesActivatingConfirmation: BoolProperty(
            name=ZBBQ_Labels.ZBBQ_Prefs_Prop_CyclesActivatingConfirmation_Name,
            description=ZBBQ_Labels.ZBBQ_Prefs_Prop_CyclesActivatingConfirmation_Desc,
            default=True)

    polygonBoundaryLoopOnly: BoolProperty(
            name=ZBBQ_Labels.ZBBQ_Prefs_Prop_PolygonBoundaryLoopOnly_Name,
            description=ZBBQ_Labels.ZBBQ_Prefs_Prop_PolygonBoundaryLoopOnly_Desc,
            default=False)  # Default: False

    tabs: bpy.props.EnumProperty(
        items=[
            ("COMMON", "Common", ""),
            ("KEYMAP", "Keymap", ""),
            ("HELP", "Help", ""),
        ],
        default="COMMON"
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "tabs", expand=True)

        if self.tabs == 'COMMON':

            layout.label(text="Settings")

            box = layout.box()
            box.prop(self, 'smartSelectRadiusThreshold')
            box.prop(self, 'polygonBoundaryLoopOnly')
            box.prop(self, 'cyclesActivatingConfirmation')

            layout.label(text="Cleanup / Repair")

            box = layout.box()

            box.operator("global.zen_bbq_reset_preferences")
            box.operator("global.zen_bbq_materials_repair")
            box.operator("global.zen_bbq_addon_cleanup")
            # box.operator("object.zen_bbq_addon_cleanup", icon="PANEL_CLOSE")
            # box.operator("global.zen_bbq_addon_cleanup", icon="TRASH")
            # box.operator("global.zen_bbq_reset_preferences", icon="LOOP_BACK")

        elif self.tabs == 'KEYMAP':
            draw_keymaps(context, layout)

        elif self.tabs == 'HELP':

            col = layout.column(align=False)

            row = col.row(align=True)
            row.operator(
                "wm.url_open",
                text=ZBBQ_Labels.PANEL_HELP_DOC_LABEL,
                icon="HELP"
            ).url = ZBBQ_Labels.PANEL_HELP_DOC_LINK
            row = col.row(align=True)
            row.operator(
                "wm.url_open",
                text=ZBBQ_Labels.PANEL_HELP_DISCORD_LABEL,
                icon_value=ZBBQ_Icons['Discord-Logo-White_32'].id()
            ).url = ZBBQ_Labels.PANEL_HELP_DISCORD_LINK

        box_products = layout.box()
        box_products.label(text='Zen Add-ons')
        box_products.operator(
            "wm.url_open",
            text=ZBBQ_Labels.PREF_ZEN_SETS_URL_DESC,
            icon_value=ZBBQ_Icons['zen-sets_32'].id()
        ).url = ZBBQ_Labels.PREF_ZEN_SETS_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZBBQ_Labels.PREF_ZEN_UV_URL_DESC,
            icon_value=ZBBQ_Icons['zen-uv_32'].id()
        ).url = ZBBQ_Labels.PREF_ZEN_UV_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZBBQ_Labels.PREF_ZEN_UV_CHECKER_URL_DESC,
            icon_value=ZBBQ_Icons['checker_32'].id()
        ).url = ZBBQ_Labels.PREF_ZEN_UV_CHECKER_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZBBQ_Labels.PREF_ZEN_UV_TOPMOST_URL_DESC,
            # icon_value=ZBBQ_Icons['checker_32'].id()
        ).url = ZBBQ_Labels.PREF_ZEN_UV_TOPMOST_URL_LINK


classes = (

    ZBBQ_Pref_BevelPreset,
    ZBBQ_Pref_BevelPresetGroup,

    ZBBQ_Prefs,

)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

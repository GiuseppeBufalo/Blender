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

""" Zen UV Init UI module """

import bpy
from bpy.utils import register_class, unregister_class
from ZenUV.ops.pt_uv_texture_advanced import DATA_PT_uv_texture_advanced, DATA_PT_UVL_uv_texture_advanced
from ZenUV.ui import main_popup, main_panel, ots_local_props
from ZenUV.zen_checker.panel import ZUV_PT_Checker, ZUV_PT_Checker_UVL
from ZenUV.ui import ui_call
# from ZenUV.ui import callers
# from ZenUV.ui import zen_unwrap_popup
from ZenUV.ui import zen_pack_popup
from ZenUV.ui import zen_mark_popup
from ZenUV.ui import zen_checker_popup
from ZenUV.ui import keymap_operator
from ZenUV.ui import uv_panel
from ZenUV.ops import seam_groups
from ZenUV.stacks import manual_stacks
# from ZenUV.ui.user_alt_commands import ZUV_OT_search_operator
from ZenUV.ui import third_party_popups
from ZenUV.ui import manual_map
from ZenUV.ui.pie import ZsPieFactory

main_panel_classes = (
    # main_panel.ZUV_PT_Global,
    DATA_PT_uv_texture_advanced,
    seam_groups.ZUV_PT_ZenSeamsGroups,
    main_panel.ZUV_PT_Unwrap,
    main_panel.SYSTEM_PT_Finished,
    main_panel.ZUV_PT_Select,
    main_panel.ZUV_PT_Pack,
    main_panel.PROPS_PT_Packer,
    main_panel.ZUV_PT_PackObjMode,
    ZUV_PT_Checker,
    main_panel.ZUV_PT_Texel_Density,
    main_panel.ZUV_PT_Texel_DensityObjMode,
    main_panel.ZUV_PT_3DV_Transform,
    main_panel.ZUV_PT_Stack,
    main_panel.ZUV_PT_Preferences,
    main_panel.ZUV_PT_PreferencesObjMode,
    main_panel.ZUV_OT_resetPreferences,
    # main_panel.DATA_PT_Setup,
    main_panel.DATA_PT_ZDisplay,
    main_panel.DATA_PT_Panels_Switch,
    main_panel.ZUV_PT_Help,
    main_panel.ZUV_PT_ZenCore,
)

uv_panel_classes = (
    DATA_PT_UVL_uv_texture_advanced,
    uv_panel.ZUV_PT_UVL_Unwrap,
    uv_panel.ZUV_PT_UVL_Select,
    uv_panel.ZUV_PT_UVL_Transform,
    uv_panel.ZUV_PT_UVL_Texel_Density,
    uv_panel.ZUV_PT_UVL_Pack,
    ZUV_PT_Checker_UVL,
    uv_panel.PROPS_PT_UVL_Packer,
    uv_panel.ZUV_PT_UVL_Stack,
    uv_panel.ZUV_PT_UVL_Preferences,
    uv_panel.DATA_PT_UVL_Panels_Switch,
    uv_panel.SYSTEM_PT_Finished_UV,
    # uv_panel.SYSTEM_PT_FitRegion_UV

)

classes = (
    manual_stacks.ZUV_PT_ZenManualStack,
    manual_stacks.ZUV_PT_UVL_ZenManualStack,
    # ots_local_props.ZENUNWRAP_PT_Properties,
    ots_local_props.MARK_PT_Properties,
    ots_local_props.FINISHED_PT_Properties,
    ots_local_props.QUADRIFY_PT_Properties,
    ots_local_props.RELAX_PT_Properties,
    # ots_local_props.PACK_PT_Properties,
    ots_local_props.TD_PT_Properties,
    ots_local_props.TD_PT_Checker_Properties,
    ots_local_props.TR_PT_Properties,
    ots_local_props.STACK_PT_Properties,
    ots_local_props.STACK_PT_DrawProperties,
    # main_pie.ZUV_OT_StretchMapSwitch,
    # main_pie.ZUV_MT_Main_Pie,
    # main_pie.ZUV_OT_Pie_Caller,
    main_popup.ZenUV_MT_Main_Popup,
    # ui_call.ZUV_OT_Main_Pie_call,
    ui_call.ZUV_OT_Main_Popup_call,
    third_party_popups.ZUV_MT_HOPS_Popup,
    # callers.ZUV_OT_Caller_Sector_9,
    # callers.ZUV_OT_Caller_Sector_4,
    # callers.ZUV_OT_Caller_Sector_7,
    # callers.ZUV_OT_Caller_Sector_3,
    # callers.ZUV_OT_Caller_Sector_6,
    # callers.ZUV_OT_Caller_Sector_8,
    # callers.ZUV_OT_Caller_Sector_2,
    # callers.ZUV_OT_Caller_Sector_1,
    # zen_unwrap_popup.ZenUV_MT_ZenUnwrap_Popup,
    zen_pack_popup.ZUV_MT_ZenPack_Uvp_Popup,
    zen_pack_popup.ZUV_MT_ZenPack_Uvpacker_Popup,
    zen_mark_popup.ZenUV_MT_ZenMark_Popup,
    zen_checker_popup.ZenUV_MT_ZenChecker_Popup,
    keymap_operator.ZUV_OT_Keymaps

)


def register():
    # Main Panel registration
    for cls in main_panel_classes:
        register_class(cls)

    # UV Panel registration
    for cls in uv_panel_classes:
        register_class(cls)

    # Pie menu
    for cl in ZsPieFactory.classes:
        register_class(cl)

    for cls in classes:
        register_class(cls)

    manual_map.register()

    # register_class(ZUV_OT_search_operator)


def unregister():

    for cls in main_panel_classes:
        unregister_class(cls)

    # Unregister UV Panel
    for cls in uv_panel_classes:
        unregister_class(cls)

    # Pie menu
    for cl in ZsPieFactory.classes:
        unregister_class(cl)

    for cls in classes:
        unregister_class(cls)

    if hasattr(bpy.types, "ZUV_PT_System"):
        unregister_class(bpy.types.ZUV_PT_System)
    if hasattr(bpy.types, "ZUV_PT_System_UVL"):
        unregister_class(bpy.types.ZUV_PT_System_UVL)
    # unregister_class(ZUV_OT_search_operator)

    manual_map.unregister()


if __name__ == "__main__":
    pass

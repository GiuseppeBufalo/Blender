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

""" Zen UV Addon Properties module """
import os
import sys
from json import loads, dumps
import bpy
import addon_utils
from bpy.types import AddonPreferences
from bpy.props import (
    BoolProperty,
    FloatProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
    FloatVectorProperty,
    PointerProperty
)
from ZenUV.zen_checker.files import update_files_info, load_checker_image
from ZenUV.utils.messages import zen_message
from ZenUV.zen_checker.checker import zen_checker_image_update, \
    get_materials_with_overrider, ZUVChecker_OT_CheckerToggle
from ZenUV.ico import icon_get
from ZenUV.ui.labels import ZuvLabels
from ZenUV.zen_checker.zen_checker_labels import ZCheckerLabels as label
from ZenUV.utils.generic import get_padding_in_pct, get_padding_in_px

from ZenUV.ui import ui_call
from ZenUV.ui.pie import ZUV_OT_PieMenu
from ZenUV.ui.keymap_manager import draw_key
from ZenUV.utils.clib.lib_init import StackSolver, get_zenlib_name, get_zenlib_version, is_zenlib_present

from ZenUV.sticky_uv_editor.stk_uv_props import UVEditorSettings, draw_sticky_editor_settings

from ZenUV.ops.zen_unwrap.props import ZUV_ZenUnwrapOpAddonProps

resolutions_x = []
resolutions_y = []
values_x = []
values_y = []


_CACHE_ADDON_VERSION = None


def get_addon_version():
    global _CACHE_ADDON_VERSION
    if _CACHE_ADDON_VERSION is None:
        for addon in addon_utils.modules():
            if addon.bl_info['name'] == 'Zen UV':
                ver = addon.bl_info['version']
                _CACHE_ADDON_VERSION = '%i.%i.%i' % (ver[0], ver[1], ver[2])
                break

    return _CACHE_ADDON_VERSION if _CACHE_ADDON_VERSION else '0.0.0'


def get_prefs():
    """ Return Zen UV Properties obj """
    return bpy.context.preferences.addons[ZuvLabels.ADDON_NAME].preferences


def get_name():
    """Get Name"""
    return os.path.basename(get_path())


def get_path():
    """Get the path of Addon"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


uv_enblr = {
    "enable_pt_adv_uv_map": {"view3d": True, "uv": True},
    "enable_pt_seam_group": {"view3d": True, "uv": False},
    "enable_pt_unwrap": {"view3d": True, "uv": True},
    "enable_pt_select": {"view3d": True, "uv": True},
    "enable_pt_pack": {"view3d": True, "uv": True},
    "enable_pt_checker_map": {"view3d": True, "uv": True},
    "enable_pt_texel_density": {"view3d": True, "uv": True},
    "enable_pt_transform": {"view3d": True, "uv": True},
    "enable_pt_help": {"view3d": True, "uv": False},
    "enable_pt_stack": {"view3d": True, "uv": True},
    "enable_pt_preferences": {"view3d": True, "uv": True},
}


def draw_panels_enabler(self, context, layout, viewport):
    addon_prefs = get_prefs()

    if viewport == "view3d":
        suf = ""
        align_left = False
    else:
        suf = "uv_"
        align_left = False

    box = layout.box()
    # box.use_property_split = align_left
    # box.use_property_decorate = False

    for pref, switch in uv_enblr.items():
        enb = box.row(align=True)
        if align_left:
            enb.alignment = 'RIGHT'
        enb.enabled = switch[viewport]
        enb.prop(addon_prefs, suf + pref)


def draw_alt_commands(self):
    box = self.layout.box()
    addon_prefs = self
    box.label(text="Pie Menu commands that will be executed in combination with the SHIFT key.")
    row = box.row(align=True)
    row.prop(addon_prefs, 's8', icon="TRIA_UP")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's8'
    row = box.row(align=True)
    row.prop(addon_prefs, 's9')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's9'
    row.enabled = False
    row = box.row(align=True)
    row.prop(addon_prefs, 's6', icon="TRIA_RIGHT")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's6'
    row = box.row(align=True)
    row.prop(addon_prefs, 's3')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's3'
    row = box.row(align=True)
    row.prop(addon_prefs, 's2', icon="TRIA_DOWN")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's2'
    row = box.row(align=True)
    row.prop(addon_prefs, 's1')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's1'
    row = box.row(align=True)
    row.prop(addon_prefs, 's4', icon="TRIA_LEFT")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's4'
    row = box.row(align=True)
    row.prop(addon_prefs, 's7')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's7'


class ZUV_AddonPreferences(AddonPreferences):

    bl_idname = ZuvLabels.ADDON_NAME  # "ZenUV"

    def draw(self, context):
        layout = self.layout
        self.draw_update_note(layout)

        row = layout.row()
        row.prop(self, "tabs", expand=True)

        if self.tabs == 'KEYMAP':
            keys = [('Window', ZUVChecker_OT_CheckerToggle.bl_idname, None),
                    ('Mesh', ZUV_OT_PieMenu.bl_idname, None),
                    ('Mesh', ui_call.ZUV_OT_Main_Popup_call.bl_idname, None),
                    ('UV Editor', ZUV_OT_PieMenu.bl_idname, None),
                    ('UV Editor', ui_call.ZUV_OT_Main_Popup_call.bl_idname, None),
                    ('Window', 'wm.sticky_uv_editor', None),
                    ('Window', 'wm.sticky_uv_editor_split', None)
                    ]
            layout.prop(self, "zen_key_modifier")
            draw_key(layout, keys)

        # if self.tabs == 'PIE_MENU':
        #     draw_alt_commands(self)
        if self.tabs == 'PANELS':
            layout = self.layout
            pie_box = layout.box()
            pie_box.label(text="Pie Menu: ")
            pie_box.prop(self, "pie_assist")
            pie_box.prop(self, "pie_assist_font_size")
            row = layout.row()
            col = row.column()
            # col.alignment = 'RIGHT'
            # draw_uv_panels_enabler(self, context, row)
            title_box = col.box()
            title_box.label(text="UV Editor", icon="UV")
            draw_panels_enabler(self, context, col, "uv")
            col = row.column()
            title_box = col.box()
            title_box.label(text="3D Viewport", icon="VIEW3D")
            draw_panels_enabler(self, context, col, "view3d")

        if self.tabs == 'HELP':
            box = layout.box()
            box.operator(
                "wm.url_open",
                text=ZuvLabels.PANEL_HELP_DOC_LABEL,
                icon="HELP"
            ).url = ZuvLabels.PANEL_HELP_DOC_LINK
            box.operator(
                "wm.url_open",
                text=ZuvLabels.PANEL_HELP_DISCORD_LABEL,
                icon_value=icon_get(ZuvLabels.PANEL_HELP_DISCORD_ICO)
            ).url = ZuvLabels.PANEL_HELP_DISCORD_LINK
        if self.tabs == 'MODULES':
            self.draw_modules_tab(layout)
        if self.tabs == 'STK_UV_EDITOR':
            draw_sticky_editor_settings(self, context)

        box_products = layout.box()
        box_products.label(text='Zen Add-ons')
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_SETS_URL_DESC,
            icon_value=icon_get(ZuvLabels.AddonZenSets)
        ).url = ZuvLabels.PREF_ZEN_SETS_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_UV_BBQ_URL_DESC,
            icon_value=icon_get(ZuvLabels.AddonZenBBQ)
        ).url = ZuvLabels.PREF_ZEN_UV_BBQ_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_UV_CHECKER_URL_DESC,
            icon_value=icon_get(ZuvLabels.AddonZenChecker)
        ).url = ZuvLabels.PREF_ZEN_UV_CHECKER_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_UV_TOPMOST_URL_DESC,
            icon='WINDOW',
        ).url = ZuvLabels.PREF_ZEN_UV_TOPMOST_URL_LINK

    def draw_modules_tab(self, layout):
        box = layout.box()
        if not StackSolver():
            b_is_zenlib_present = is_zenlib_present()
            row = box.row()
            row.alert = True
            row.label(text=ZuvLabels.CLIB_NAME + (": not installed" if not b_is_zenlib_present else ": not registered"))
            box.operator(
                    "wm.url_open",
                    text=ZuvLabels.PREF_ZEN_CORE_URL_DESC,

                ).url = ZuvLabels.PREF_ZEN_CORE_URL_LINK

            s_label = ("Register " if b_is_zenlib_present else "Install ") + ZuvLabels.CLIB_NAME
            box.operator("view3d.zenuv_install_library", text=s_label)
        else:
            result = get_zenlib_version()

            box.label(text=ZuvLabels.CLIB_NAME + f": {result[0]}.{result[1]}.{result[2]} ({get_zenlib_name()})" + ' is installed.')
            box.operator("uv.zenuv_unregister_library")
            box.label(text=ZuvLabels.UPDATE_WARNING_UNREGISTER)

    def draw_update_note(self, layout):
        upd_box = layout.box()
        # col.label(text=ZuvLabels.UPDATE_MESSAGE_SHORT)
        if StackSolver():
            # col = upd_box.column()
            # col.alert = True
            upd_box.label(text='NOTE', icon='ERROR')
            mes_box = upd_box.box()
            mes_box.label(text=ZuvLabels.UPDATE_WARNING_MAIN_01)
            mes_box.label(text=ZuvLabels.UPDATE_WARNING_MAIN_02)
        row = upd_box.row()
        row.operator("uv.zenuv_update_addon")

    def pack_eng_callback(self, context):
        return (
            ("BLDR", ZuvLabels.PREF_PACK_ENGINE_BLDR_LABEL, ZuvLabels.PREF_PACK_ENGINE_BLDR_DESC),
            ("UVP", ZuvLabels.PREF_PACK_ENGINE_UVP_LABEL, ZuvLabels.PREF_PACK_ENGINE_UVP_DESC),
            ("UVPACKER", ZuvLabels.PREF_PACK_ENGINE_UVPACKER_LABEL, ZuvLabels.PREF_PACK_ENGINE_UVPACKER_DESC)
            # ("CUSTOM", ZuvLabels.PREF_PACK_CUSTOM_LABEL, ZuvLabels.PREF_PACK_CUSTOM_DESC)
        )

    def mark_update_function(self, context):
        if not self.markSharpEdges and not self.markSeamEdges:
            zen_message(
                context,
                message=ZuvLabels.PREF_MARK_WARN_MES,
                title=ZuvLabels.PREF_MARK_WARN_TITLE)

    def update_margin_px(self, context):
        self.margin = get_padding_in_pct(context, self.margin_px)

    def update_margin_show_in_px(self, context):
        if self.margin_show_in_px:
            self.margin_px = get_padding_in_px(context, self.margin)
        else:
            self.margin = get_padding_in_pct(context, self.margin_px)

    def image_size_update_function(self, context):
        if self.td_im_size_presets.isdigit():
            self.TD_TextureSizeX = self.TD_TextureSizeY = int(self.td_im_size_presets)
        self.margin = get_padding_in_pct(context, self.margin_px)

    op_zen_unwrap_props: bpy.props.PointerProperty(type=ZUV_ZenUnwrapOpAddonProps)

    pie_assist: bpy.props.BoolProperty(
        name=ZuvLabels.PROP_DISPLAY_PIE_ASSIST_LABEL,
        description=ZuvLabels.PROP_DISPLAY_PIE_ASSIST_DESC,
        default=True
    )

    pie_assist_font_size: IntProperty(
        name=ZuvLabels.PROP_PIE_ASSIST_FONT_SIZE_LABEL,
        description=ZuvLabels.PROP_PIE_ASSIST_FONT_SIZE_DESC,
        min=8,
        max=16,
        default=11,
    )

    # Stack Preferences
    StackedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.PREF_ST_STACKED_COLOR_LABEL,
        description=ZuvLabels.PREF_ST_STACKED_COLOR_DESC,
        subtype='COLOR',
        default=[0.325, 0.65, 0.0, 0.35],
        size=4,
        min=0,
        max=1
    )

    st_stack_mode: EnumProperty(
        name=ZuvLabels.PREF_ST_STACK_MODE_LABEL,
        description=ZuvLabels.PREF_ST_STACK_MODE_DESC,
        items=[
            (
                'ALL',
                ZuvLabels.PREF_ST_STACK_MODE_ALL_LABEL,
                ZuvLabels.PREF_ST_STACK_MODE_ALL_DESC
            ),
            (
                'SELECTED',
                ZuvLabels.PREF_ST_STACK_MODE_SEL_LABEL,
                ZuvLabels.PREF_ST_STACK_MODE_SEL_DESC
            ),
            (
                'SIMPLE',
                ZuvLabels.PREF_ST_STACK_MODE_SIMPLE_LABEL,
                ZuvLabels.PREF_ST_STACK_MODE_SIMPLE_DESC
            ),
        ],
        default="ALL"
    )

    unstack_direction: FloatVectorProperty(
        name="Direction",
        size=2,
        default=(1.0, 0.0),
        subtype='XYZ'
    )

    stack_offset: FloatVectorProperty(
        name="Direction",
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ'
    )

    stackMoveOnly: BoolProperty(
        name=ZuvLabels.PREF_STACK_MOVE_ONLY_LABEL,
        default=False,
        description=ZuvLabels.PREF_STACK_MOVE_ONLY_DESC,
        )

    # Panel Enabler Preferences
    enable_pt_adv_uv_map: BoolProperty(name=ZuvLabels.PT_ADV_UV_MAPS_LABEL, default=True)
    enable_pt_seam_group: BoolProperty(name=ZuvLabels.PT_SEAMS_GROUP_LABEL, default=True)
    enable_pt_unwrap: BoolProperty(name=ZuvLabels.PANEL_UNWRAP_LABEL, default=True)
    enable_pt_select: BoolProperty(name=ZuvLabels.PANEL_SELECT_LABEL, default=True)
    enable_pt_pack: BoolProperty(name=ZuvLabels.PANEL_PACK_LABEL, default=True)
    enable_pt_checker_map: BoolProperty(name=ZuvLabels.PANEL_CHECKER_LABEL, default=True)
    enable_pt_texel_density: BoolProperty(name=ZuvLabels.TEXEL_DENSITY_LABEL, default=True)
    enable_pt_transform: BoolProperty(name=ZuvLabels.PANEL_TRANSFORM_LABEL, default=True)
    enable_pt_help: BoolProperty(name=ZuvLabels.PANEL_HELP_LABEL, default=True)
    enable_pt_stack: BoolProperty(name=ZuvLabels.PANEL_STACK_LABEL, default=True)
    enable_pt_preferences: BoolProperty(name=ZuvLabels.PANEL_PREFERENCES_LABEL, default=True)

    # UV Panel Enabler Preferences
    uv_enable_pt_adv_uv_map: BoolProperty(name=ZuvLabels.PT_ADV_UV_MAPS_LABEL, default=True)
    uv_enable_pt_seam_group: BoolProperty(name=ZuvLabels.PT_SEAMS_GROUP_LABEL, default=False)
    uv_enable_pt_unwrap: BoolProperty(name=ZuvLabels.PANEL_UNWRAP_LABEL, default=True)
    uv_enable_pt_select: BoolProperty(name=ZuvLabels.PANEL_SELECT_LABEL, default=True)
    uv_enable_pt_pack: BoolProperty(name=ZuvLabels.PANEL_PACK_LABEL, default=True)
    uv_enable_pt_checker_map: BoolProperty(name=ZuvLabels.PANEL_CHECKER_LABEL, default=False)
    uv_enable_pt_texel_density: BoolProperty(name=ZuvLabels.TEXEL_DENSITY_LABEL, default=True)
    uv_enable_pt_transform: BoolProperty(name=ZuvLabels.PANEL_TRANSFORM_LABEL, default=True)
    uv_enable_pt_help: BoolProperty(name=ZuvLabels.PANEL_HELP_LABEL, default=False)
    uv_enable_pt_stack: BoolProperty(name=ZuvLabels.PANEL_STACK_LABEL, default=True)
    uv_enable_pt_preferences: BoolProperty(name=ZuvLabels.PANEL_PREFERENCES_LABEL, default=True)

    # Alt Commands Preferences
    s8: StringProperty(name="Sector 8", default='')
    s9: StringProperty(name="Sector 9", default='')
    s6: StringProperty(name="Sector 6", default='')
    s3: StringProperty(name="Sector 3", default='')
    s2: StringProperty(name="Sector 2", default='')
    s1: StringProperty(name="Sector 1", default='')
    s4: StringProperty(name="Sector 4", default='')
    s7: StringProperty(name="Sector 7", default='bpy.ops.uv.zenuv_select_similar()')

    operator: StringProperty(
        name="Operator",
        default=''
    )

    # Zen UV Preferences
    hops_uv_activate: BoolProperty(
        name=ZuvLabels.HOPS_UV_ACTIVATE_LABEL,
        description=ZuvLabels.HOPS_UV_ACTIVATE_DESC,
        default=False,
    )
    hops_uv_context: BoolProperty(
        name=ZuvLabels.HOPS_UV_CONTEXT_LABEL,
        description=ZuvLabels.HOPS_UV_CONTEXT_DESC,
        default=True,
    )
    tabs: EnumProperty(
        items=[
            ("KEYMAP", "Keymap", ""),
            ("PANELS", "Panels", ""),
            # ("PIE_MENU", "Pie Menu", ""),
            ("MODULES", "Modules", ""),
            ("STK_UV_EDITOR", "Sticky UV Editor", ""),
            ("HELP", "Help", ""),
        ],
        default="MODULES"
    )
    # Zen UV UI Key modifier
    zen_key_modifier: EnumProperty(
        items=[
            ("ALT", "Alt", "Alt"),
            ("CTRL", "Ctrl", "Ctrl"),
            ("SHIFT", "Shift", "Shift")
        ],
        default="ALT",
        description=ZuvLabels.ZEN_MODIFIER_KEY_DESC,
        name=ZuvLabels.ZEN_MODIFIER_KEY_LABEL,

    )
    # Tabs for Sticky UV Editor Setup
    stk_tabs: EnumProperty(
        items=[
            ("GENERAL", "General", ""),
            ("OVERLAY", "Overlay", ""),
            ("VIEW", "View", ""),
            ("ABOUT", "About", "")
        ],
        default="GENERAL"
    )

    useGlobalMarkSettings: BoolProperty(
        name=ZuvLabels.PREF_USE_GLOBAL_MARK_LABEL,
        description=ZuvLabels.PREF_USE_GLOBAL_MARK_DESC,
        default=True
    )

    markSharpEdges: BoolProperty(
        name=ZuvLabels.PREF_MARK_SHARP_EDGES_LABEL,
        description=ZuvLabels.PREF_MARK_SHARP_EDGES_DESC,
        default=False,
        update=mark_update_function)

    markSeamEdges: BoolProperty(
        name=ZuvLabels.PREF_MARK_SEAM_EDGES_LABEL,
        description=ZuvLabels.PREF_MARK_SEAM_EDGES_DESC,
        default=True,
        update=mark_update_function)

    # MarkUnwrapped: BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_SEAMS_WITH_UNWRAP_LABEL,
    #     description=ZuvLabels.PREF_AUTO_SEAMS_WITH_UNWRAP_DESC,
    #     default=True)

    # packAfUnwrap: BoolProperty(
    #     name=ZuvLabels.PREF_PACK_AF_UNWRAP_LABEL,
    #     description=ZuvLabels.PREF_PACK_AF_UNWRAP_DESC,
    #     default=True)

    # Quadrify Props ------------------------------------------------

    # autoPinQuadrified: BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_PIN_QUADRIFIED_LABEL,
    #     description=ZuvLabels.PREF_AUTO_PIN_QUADRIFIED_DESC,
    #     default=False)

    # quadrifyOrientToWorld: BoolProperty(
    #     name=ZuvLabels.PREF_ORIENT_TO_WORLD_QUADRIFY_LABEL,
    #     description=ZuvLabels.PREF_ORIENT_TO_WORLD_QUADRIFY_DESC,
    #     default=False)

    # mark_borders: BoolProperty(
    #     name=ZuvLabels.PREF_UPD_SEAMS_AF_QUADRIFY_LABEL,
    #     description=ZuvLabels.PREF_UPD_SEAMS_AF_QUADRIFY_DESC,
    #     default=True)

    # QuadrifyBySelected: BoolProperty(
    #     name=ZuvLabels.PREF_QUADRIFY_BY_SELECTED_EDGES_LABEL,
    #     description=ZuvLabels.PREF_QUADRIFY_BY_SELECTED_EDGES_DESC,
    #     default=True)

    # packAfQuadrify: BoolProperty(
    #     name=ZuvLabels.PREF_PACK_AF_QUADRIFY_LABEL,
    #     description=ZuvLabels.PREF_PACK_AF_QUADRIFY_DESC,
    #     default=False)

    # Quadrify Props END --------------------------------------------

    packEngine: EnumProperty(
        items=pack_eng_callback,
        name=ZuvLabels.PREF_PACK_ENGINE_LABEL,
        description=ZuvLabels.PREF_PACK_ENGINE_DESC,
        default=None
        )

    # customEngine: StringProperty(
    #     default="bpy.ops.uvpackeroperator.packbtn()",
    #     description="Custom Pack Command"
    # )

    averageBeforePack: BoolProperty(
        name=ZuvLabels.PREF_AVERAGE_BEFORE_PACK_LABEL,
        description=ZuvLabels.PREF_AVERAGE_BEFORE_PACK_DESC,
        default=True)

    rotateOnPack: BoolProperty(
        name=ZuvLabels.PREF_ROTATE_ON_PACK_LABEL,
        description=ZuvLabels.PREF_ROTATE_ON_PACK_DESC,
        default=True)

    # keepStacked: BoolProperty(
    #     name=ZuvLabels.PREF_KEEP_STACKED_LABEL,
    #     description=ZuvLabels.PREF_KEEP_STACKED_DESC,
    #     default=True)

    def update_lock_ovelap_enbl(self, context):
        if self.lock_overlapping_mode == '0':
            self.lock_overlapping_enable = False
        else:
            self.lock_overlapping_enable = True

    lock_overlapping_mode: EnumProperty(
        items=[
            ('0', 'Disabled', ZuvLabels.LOCK_OVERLAPPING_MODE_DISABLED_DESC),
            ('1', 'Any Part', ZuvLabels.LOCK_OVERLAPPING_MODE_ANY_PART_DESC),
            ('2', 'Exact', ZuvLabels.LOCK_OVERLAPPING_MODE_EXACT_DESC)
        ],
        name=ZuvLabels.LOCK_OVERLAPPING_MODE_NAME,
        description=ZuvLabels.LOCK_OVERLAPPING_MODE_DESC,
        update=update_lock_ovelap_enbl
    )

    lock_overlapping_enable: BoolProperty(
        name=ZuvLabels.LOCK_OVERLAPPING_ENABLE_NAME,
        description=ZuvLabels.LOCK_OVERLAPPING_ENABLE_DESC,
    )

    packFixedScale: BoolProperty(
        name=ZuvLabels.PREF_FIXED_SCALE_LABEL,
        description=ZuvLabels.PREF_FIXED_SCALE_DESC,
        default=False)

    autoFitUV: BoolProperty(
        name=ZuvLabels.PREF_AUTO_FIT_UV_LABEL,
        description=ZuvLabels.PREF_AUTO_FIT_UV_DESC,
        default=False)

    # unwrapAutoSorting: BoolProperty(
    #     name=ZuvLabels.PREF_ZEN_UNWRAP_SORT_ISLANDS_LABEL,
    #     description=ZuvLabels.PREF_ZEN_UNWRAP_SORT_ISLANDS_DESC,
    #     default=False)

    sortAutoSorting: BoolProperty(
        name=ZuvLabels.PREF_ZEN_SORT_ISLANDS_LABEL,
        description=ZuvLabels.PREF_ZEN_SORT_ISLANDS_DESC,
        default=True)

    autoPinnedAsFinished: BoolProperty(
        name=ZuvLabels.PREF_AUTO_PINNED_AS_FINISHED_LABEL,
        description=ZuvLabels.PREF_AUTO_PINNED_AS_FINISHED_DESC,
        default=True)

    autoFinishedToPinned: BoolProperty(
        name=ZuvLabels.PREF_AUTO_FINISHED_TO_PINNED_LABEL,
        description=ZuvLabels.PREF_AUTO_FINISHED_TO_PINNED_DESC,
        default=False)

    # autoTagFinished: BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_TAG_FINISHED_LABEL,
    #     description=ZuvLabels.PREF_AUTO_TAG_FINISHED_DESC,
    #     default=False)

    margin: FloatProperty(
        name=ZuvLabels.PREF_MARGIN_LABEL,
        description=ZuvLabels.PREF_MARGIN_DESC,
        min=0.0,
        default=0.005,
        precision=3
    )

    margin_px: IntProperty(
        name=ZuvLabels.PREF_MARGIN_PX_LABEL,
        description=ZuvLabels.PREF_MARGIN_PX_DESC,
        min=0,
        default=5,
        update=update_margin_px
    )

    margin_show_in_px: BoolProperty(
        name=ZuvLabels.PREF_MARGIN_SHOW_PX_LABEL,
        description=ZuvLabels.PREF_MARGIN_SHOW_PX_DESC,
        default=True,
        update=update_margin_show_in_px
    )

    # ProcessingMode: BoolProperty(
    #     name=ZuvLabels.PREF_WORK_ON_SELECTED_LABEL,
    #     description=ZuvLabels.PREF_WORK_ON_SELECTED_DESC,
    #     default=False)

    UnwrapMethod: EnumProperty(
        items=[
            ("ANGLE_BASED",
                ZuvLabels.PREF_UNWRAP_METHOD_ANGLE_LABEL,
                ZuvLabels.PREF_UNWRAP_METHOD_ANGLE_DESC),
            ("CONFORMAL",
                ZuvLabels.PREF_UNWRAP_METHOD_CONFORMAL_LABEL,
                ZuvLabels.PREF_UNWRAP_METHOD_CONFORMAL_DESC)],
        default="CONFORMAL")

    PinColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.PIN_UV_ISLAND_ISLAND_COLOR_NAME,
        description=ZuvLabels.PIN_UV_ISLAND_ISLAND_COLOR_DESC,
        subtype='COLOR',
        default=[0.25, 0.4, 0.4, 1],
        size=4,
        min=0,
        max=1)

    FinishedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TAG_FINISHED_COLOR_NAME,
        description=ZuvLabels.TAG_FINISHED_COLOR_DESC,
        subtype='COLOR',
        default=[0, 0.5, 0, 0.4],
        size=4,
        min=0,
        max=1)

    ExcludedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TAG_FINISHED_COLOR_NAME,
        description=ZuvLabels.TAG_FINISHED_COLOR_DESC,
        subtype='COLOR',
        default=[0.97, 0.026, 0.5, 0.4],
        size=4,
        min=0,
        max=1)

    UnFinishedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TAG_UNFINISHED_COLOR_NAME,
        description=ZuvLabels.TAG_UNFINISHED_COLOR_DESC,
        subtype='COLOR',
        default=[0.937, 0.448, 0.735, 0.2],
        size=4,
        min=0,
        max=1)

    RandomizePinColor: bpy.props.BoolProperty(
        name=ZuvLabels.PIN_UV_ISLAND_RAND_COLOR_NAME,
        description=ZuvLabels.PIN_UV_ISLAND_RAND_COLOR_DESC,
        default=True)

    TexelDensity: FloatProperty(
        name=ZuvLabels.PREF_TEXEL_DENSITY_LABEL,
        description=ZuvLabels.PREF_TEXEL_DENSITY_DESC,
        min=0.001,
        default=1024.0,
        precision=2
    )

    td_checker: FloatProperty(
        name=ZuvLabels.PREF_TD_CHECKER_LABEL,
        description=ZuvLabels.PREF_TD_CHECKER_DESC,
        min=0.001,
        default=47.59,
        precision=2
    )

    td_set_mode: EnumProperty(
        name=ZuvLabels.PREF_TD_SET_MODE_LABEL,
        description=ZuvLabels.PREF_TD_SET_MODE_DESC,
        items=[
            (
                'island',
                ZuvLabels.PREF_SET_PER_ISLAND_LABEL,
                ZuvLabels.PREF_SET_PER_ISLAND_DESC
            ),
            (
                'overall',
                ZuvLabels.PREF_SET_OVERALL_LABEL,
                ZuvLabels.PREF_SET_OVERALL_DESC
            ),
        ],
        default="overall"
    )

    UVCoverage: FloatProperty(
        name=ZuvLabels.PREF_UV_COVERAGE_LABEL,
        description=ZuvLabels.PREF_UV_DENSITY_DESC,
        min=0.001,
        default=1.0,
        precision=3
    )

    # td_unit: EnumProperty(
    #     name=ZuvLabels.PREF_UNITS_LABEL,
    #     description=ZuvLabels.PREF_UNITS_DESC,
    #     items=[
    #         ('100000', 'km', 'KILOMETERS'),
    #         ('100', 'm', 'METERS'),
    #         ('1', 'cm', 'CENTIMETERS'),
    #         ('0.1', 'mm', 'MILLIMETERS'),
    #         ('0.0001', 'um', 'MICROMETERS'),
    #         ('160934', 'mil', 'MILES'),
    #         ('30.48', 'ft', 'FEET'),
    #         ('2.54', 'in', 'INCHES'),
    #         ('0.00254', 'th', 'THOU')
    #     ],
    #     default="100"
    # )

    td_unit: EnumProperty(
        name=ZuvLabels.PREF_UNITS_LABEL,
        description=ZuvLabels.PREF_UNITS_DESC,
        items=[
            ('km', 'km', 'KILOMETERS'),
            ('m', 'm', 'METERS'),
            ('cm', 'cm', 'CENTIMETERS'),
            ('mm', 'mm', 'MILLIMETERS'),
            ('um', 'um', 'MICROMETERS'),
            ('mil', 'mil', 'MILES'),
            ('ft', 'ft', 'FEET'),
            ('in', 'in', 'INCHES'),
            ('th', 'th', 'THOU')
        ],
        default="m"
    )

    TD_TextureSizeX: IntProperty(
        name=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL,
        description=ZuvLabels.PREF_TD_TEXTURE_SIZE_DESC,
        min=1,
        default=1024)

    TD_TextureSizeY: IntProperty(
        name=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL,
        description=ZuvLabels.PREF_TD_TEXTURE_SIZE_DESC,
        min=1,
        default=1024)

    td_im_size_presets: EnumProperty(
        name=ZuvLabels.PREF_IMAGE_SIZE_PRESETS_LABEL,
        description=ZuvLabels.PREF_IMAGE_SIZE_PRESETS_DESC,
        items=[
            ('16', '16', ''),
            ('32', '32', ''),
            ('64', '64', ''),
            ('128', '128', ''),
            ('256', '256', ''),
            ('512', '512', ''),
            ('1024', '1024', ''),
            ('2048', '2048', ''),
            ('4096', '4096', ''),
            ('8192', '8192', ''),
            ('Custom', 'Custom', '')
        ],
        default='1024',
        update=image_size_update_function)

    td_color_equal: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TD_COLOR_EQUAL_LABEL,
        description=ZuvLabels.TD_COLOR_EQUAL_DESC,
        subtype='COLOR',
        default=[0.0, 1.0, 0.0],
        size=3,
        min=0,
        max=1
    )

    td_color_less: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TD_COLOR_LESS_LABEL,
        description=ZuvLabels.TD_COLOR_LESS_DESC,
        subtype='COLOR',
        default=[0.0, 0.0, 1.0],
        size=3,
        min=0,
        max=1
    )

    td_color_over: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TD_COLOR_OVER_LABEL,
        description=ZuvLabels.TD_COLOR_OVER_DESC,
        subtype='COLOR',
        default=[1.0, 0.0, 0.0],
        size=3,
        min=0,
        max=1
    )

    # autoActivateUVSync: bpy.props.BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_ACTIVATE_UV_SYNC_LABEL,
    #     description=ZuvLabels.PREF_AUTO_ACTIVATE_UV_SYNC_DESC,
    #     default=True)

# Zen UV Checker Preferences
    def get_files_dict(self, context):
        try:
            if self.files_dict == "":
                self.files_dict = dumps(update_files_info(self.assetspath))
            files_dict = loads(self.files_dict)
            return files_dict
        except Exception:
            print("Warning!", sys.exc_info()[0], "occurred.")
            self.files_dict = dumps(update_files_info(self.assetspath))
            return None

    def get_x_res_list(self, context):
        """ Get resolutions list for files from files_dict """
        files_dict = self.get_files_dict(context)
        if files_dict:
            # Update info in resolutions_x list
            values_x.clear()
            for image in files_dict:
                value = files_dict[image]["res_x"]
                if value not in values_x:
                    values_x.append(value)
            values_x.sort()
            identifier = 0
            resolutions_x.clear()
            for value in values_x:
                resolutions_x.append((str(value), str(value), "", identifier))
                identifier += 1
            return resolutions_x
        return [('None', 'None', '', 0), ]

    def get_y_res_list(self, context):
        """ Fills resolutions_y depend on current value of SizeX """
        files_dict = self.get_files_dict(context)
        if files_dict:
            res_x = self.SizesX
            if res_x and res_x.isdigit():
                res_x = int(res_x)
                # If axes locked - return same value as Resolution X
                if self.lock_axes:
                    return [(str(res_x), str(res_x), "", 0)]
                identifier = 0
                values_y.clear()
                resolutions_y.clear()
                for image in files_dict:
                    value = files_dict[image]["res_y"]
                    if files_dict[image]["res_x"] == res_x and value not in values_y:
                        values_y.append(value)
                        resolutions_y.append((str(value), str(value), "", identifier))
                        identifier += 1
            if resolutions_y:
                return resolutions_y
        return [('None', 'None', '', 0), ]

    def zchecker_image_items(self, context):
        files_dict = self.get_files_dict(context)
        if files_dict:
            files = []
            identifier = 0
            # If filter disabled - return all images from dict
            if not self.chk_rez_filter:
                for image in files_dict:
                    files.append((image, image, "", identifier))
                    identifier += 1
                return files

            res_x = self.SizesX
            res_y = self.SizesY
            if res_x and res_y and res_x.isdigit() and res_y.isdigit():
                res_x = int(res_x)
                res_y = int(res_y)
                values = []
                for image in files_dict:
                    if files_dict[image]["res_x"] == res_x \
                            and files_dict[image]["res_y"] == res_y \
                            and image not in values:
                        values.append(image)
                        if self.chk_orient_filter:
                            if "orient" in image:
                                files.append((image, image, "", identifier))
                                identifier += 1
                        else:
                            files.append((image, image, "", identifier))
                            identifier += 1
            if files:
                return files
        return [('None', 'None', '', 0), ]

    def dynamic_update_function(self, context):
        if self.dynamic_update and get_materials_with_overrider(bpy.data.materials):
            self.checker_presets_update_function(context)

    def update_x_res(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def update_orient_switch(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        if self.chk_orient_filter:
            addon_prefs["SizesX"] = 1
            addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def update_y_res(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def dynamic_update_function_overall(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        if self.dynamic_update:
            materials_with_overrider = get_materials_with_overrider(bpy.data.materials)
            # print("Mats with overrider in bpy.data: ", materials_with_overrider)
            if materials_with_overrider:
                self.checker_presets_update_function(context)

    # def show_checker_in_uv_layout(self, context):
    #     materials_with_overrider = get_materials_with_overrider(get_materials_from_objects(context, context.selected_objects))
    #     if materials_with_overrider:
    #         image = bpy.data.images.get(self.ZenCheckerPresets)
    #         # update_image_in_uv_layout(context, image)

    def checker_presets_update_function(self, context):
        image = bpy.data.images.get(self.ZenCheckerImages)
        if image:
            zen_checker_image_update(context, image)
        else:
            # print("Image not Loaded. Load image ", self.ZenCheckerPresets)
            image = load_checker_image(context, self.ZenCheckerImages)
            if image:
                zen_checker_image_update(context, image)
        # self.show_checker_in_uv_layout(context)

    def update_assetspath(self, context):
        self.files_dict = dumps(update_files_info(self.assetspath))

    assetspath: StringProperty(
        name=label.PROP_ASSET_PATH,
        subtype='DIR_PATH',
        default=os.path.join(get_path(), "images"),
        update=update_assetspath
    )

    files_dict: StringProperty(
        name="Zen Checker Files Dict",
        default=""
    )

    dynamic_update: BoolProperty(
        name=label.PROP_DYNAMIC_UPDATE_LABEL,
        description=label.PROP_DYNAMIC_UPDATE_DESC,
        default=True
    )

    ZenCheckerPresets: EnumProperty(
        name=label.CHECKER_PRESETS_LABEL,
        description=label.CHECKER_PRESETS_DESC,
        items=[
            ('Zen-UV-512-colour.png', 'Zen Color 512x512', '', 1),
            ('Zen-UV-1K-colour.png', 'Zen Color 1024x1024', '', 2),
            ('Zen-UV-2K-colour.png', 'Zen Color 2048x2048', '', 3),
            ('Zen-UV-4K-colour.png', 'Zen Color 4096x4096', '', 4),
            ('Zen-UV-512-mono.png', 'Zen Mono 512x512', '', 5),
            ('Zen-UV-1K-mono.png', 'Zen Mono 1024x1024', '', 6),
            ('Zen-UV-2K-mono.png', 'Zen Mono 2048x2048', '', 7),
            ('Zen-UV-4K-mono.png', 'Zen Mono 4096x4096', '', 8)],
        default="Zen-UV-1K-colour.png",
        update=checker_presets_update_function
    )

    # ShowCheckerInUVLayout: bpy.props.BoolProperty(
    #     name=label.CHECKER_SHOW_IN_UV_LABEL,
    #     description=label.CHECKER_SHOW_IN_UV_DESC,
    #     default=True,
    #     update=show_checker_in_uv_layout
    # )

    lock_axes: BoolProperty(
        name=label.PROP_LOCK_AXES_LABEL,
        description=label.PROP_LOCK_AXES_DESC,
        default=True,
        update=update_x_res
    )

    chk_rez_filter: BoolProperty(
        name=label.PROP_RES_FILTER_LABEL,
        description=label.PROP_RES_FILTER_DESC,
        default=False,
        update=update_x_res
    )

    chk_orient_filter: BoolProperty(
        name=label.PROP_ORIENT_FILTER_LABEL,
        description=label.PROP_ORIENT_FILTER_DESC,
        default=False,
        update=update_orient_switch
    )

    SizesX: EnumProperty(
        name=label.PROP_TEXTURE_X_LABEL,
        description=label.PROP_TEXTURE_X_DESC,
        items=get_x_res_list,
        update=update_x_res
    )

    SizesY: EnumProperty(
        name=label.PROP_TEXTURE_Y_LABEL,
        description=label.PROP_TEXTURE_Y_DESC,
        items=get_y_res_list,
        update=update_y_res
    )

    ZenCheckerImages: EnumProperty(
        name=label.PROP_CHK_IMAGES_LABEL,
        items=zchecker_image_items,
        update=checker_presets_update_function
    )

    use_zensets: BoolProperty(
        name="Use Zen Sets to Highlight Errors",
        description="Use Zen Sets to create Zen Sets Groups with Mesh Errors",
        default=False)

    # Sticky UV Editor Properties
    uv_editor_side: EnumProperty(
        name="UV Editor Side",
        description="3D Viewport area side where to open UV Editor",
        items={('LEFT', "Left",
                "Open UV Editor on the left side of 3D Viewport area", 0),
               ('RIGHT', "Right",
                "Open UV Editor on the right side of 3D Viewport area", 1)},
        default='LEFT')
    show_ui_button: BoolProperty(
        name="Show Overlay Button",
        description="Show overlay button on corresponding side of 3D Viewport",
        default=True)
    remember_uv_editor_settings: BoolProperty(
        name="Remember UV Editor Settings",
        description="Remember changes made in UV Editor area",
        default=True)

    StkUvEdProps: PointerProperty(type=UVEditorSettings)

    view_mode: EnumProperty(
        name="View Mode",
        description="Adjust UV Editor view when open",
        items={('DISABLE', "Disable",
                "Do not modify the view", 0),
               ('FRAME_ALL', "Frame All UVs",
                "View all UVs", 1),
               ('FRAME_SELECTED', "Frame Selected",
                "View all selected UVs", 2),
               ('FRAME_ALL_FIT', "Frame All UDIMs",
                "View all UDIMs", 3)},
        default='DISABLE')
    use_uv_select_sync: BoolProperty(
        name="UV Sync Selection",
        description="Keep UV an edit mode mesh selection in sync",
        default=False)

    stk_ed_button_v_position: FloatProperty(
        name="Button Vertical Position %",
        description="The vertical position of the button in percentages.",
        min=2.0,
        max=90.0,
        default=50,
        precision=1
    )

    stk_ed_button_h_position: FloatProperty(
        name="Button Horizontal Position %",
        description="The horizontal position of the button in percentages.",
        min=0.0,
        max=40.0,
        default=0.0,
        precision=1
    )

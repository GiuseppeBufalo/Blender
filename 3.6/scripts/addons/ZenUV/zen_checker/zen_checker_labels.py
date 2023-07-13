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

"""
    Zen Checker Text Blocks
"""


class ZCheckerLabels:
    """ Zen Checker Labels """
    ADDON_NAME = "ZenUVChecker"
    PANEL_CHECKER_LABEL = "Checker Map"
    ZEN_CHECKER_ICO = "checker_32"

    OT_CHECKER_TOGGLE_LABEL = "Checker Texture (Toggle)"
    OT_CHECKER_TOGGLE_DESC = "Add Checker Texture to the mesh (Toggle)"
    OT_CHECKER_RESET_LABEL = "Reset Checker"
    OT_CHECKER_RESET_DESC = "Reset Zen UV Checker to Default state "
    OT_CHECKER_REMOVE_LABEL = "Remove Checker Nodes"
    OT_CHECKER_REMOVE_DESC = "Remove Zen UV Checker Nodes from the scene materials"

    OT_CHECKER_OPEN_EDITOR_LABEL = "Open Shader Editor"
    OT_CHECKER_OPEN_EDITOR_DESC = "Open Shader Editor with Zen UV Checker Node"

    OT_RESET_PATH_LABEL = "Reset Path"
    OT_RESET_PATH_DESC = "Reset Checker Library path to Default State"

    CHECKER_PANEL_LABEL = "Checker Library folder:"
    CHECKER_PRESETS_LABEL = "Zen UV Checker Presets"
    CHECKER_PRESETS_DESC = "Presets of Zen UV Default Checker"

    CHECKER_SHOW_IN_UV_LABEL = "Show Image In UV Editor"
    CHECKER_SHOW_IN_UV_DESC = "Show Image In UV Editor Toggle"

    ZEN_CHECKER_POPUP_LABEL_PART_1 = "Checker Texture is missing in nodes."
    ZEN_CHECKER_POPUP_LABEL_PART_2 = "Best way - Reset Checker to Default state."
    ZEN_CHECKER_POPUP_LABEL_PART_3 = "If you know what Nodes are you can Open Shader Editor and do it manually."

    OT_COLLECT_IMAGES_LABEL = "Refresh Texture Library"
    OT_COLLECT_IMAGES_DESC = "Refresh Textures from Checker Library Folder"

    OT_APPEND_CHECKER_LABEL = "Load Your Texture"
    OT_APPEND_CHECKER_DESC = """Open File Browser and add
 the selected texture to the Checker Library"""

    PANEL_HELP_LABEL = "Help"
    PANEL_HELP_DOC_LABEL = "Documentation"
    PANEL_HELP_DOC_LINK = "https://zen-masters.github.io/Zen-UV/checker/"

    MESS_RESET_PATH = "Path to the Checker Library will be changed to Default state"

    PROP_ASSET_PATH = "Checker Library"
    PROP_TEXTURE_X_LABEL = "X Res"
    PROP_TEXTURE_X_DESC = "X resolution"
    PROP_TEXTURE_Y_LABEL = "Y Res"
    PROP_TEXTURE_Y_DESC = "Y resolution"

    PROP_CHK_IMAGES_LABEL = ""
    PROP_CHK_IMAGES_DESC = ""

    PROP_LOCK_AXES_LABEL = "Lock"
    PROP_LOCK_AXES_DESC = ""
    PROP_RES_FILTER_LABEL = "Resolution Filter"
    PROP_RES_FILTER_DESC = ""
    PROP_ORIENT_FILTER_LABEL = "Orient Filter"
    PROP_ORIENT_FILTER_DESC = "Orient Checker Filter"

    PROP_DYNAMIC_UPDATE_LABEL = "Auto Sync Checker"
    PROP_DYNAMIC_UPDATE_DESC = """Automatically sync selected Checker Texture
with Viewport"""

    OT_SHOW_FOLDER_LABEL = "Open Checker Folder"
    OT_SHOW_FOLDER_DESC = "Open Checker Folder"

    OT_KEYMAPS_LABEL = "Checker Keymaps"
    OT_KEYMAPS_DESC = "Set Shortcuts for Zen UV Checker"

    # Stretch Map
    OT_STRETCH_SELECT_LABEL = "Select Stretched"
    OT_STRETCH_SELECT_DESC = "Select Stretched Islands"

    PROP_STRETCHED_FILTER_LABEL = "Filter"
    PROP_STRETCHED_FILTER_DESC = "Select stretched if factor more than Filter"

    PROP_INTERPOLATION_LABEL = "Interpolation"
    PROP_INTERPOLATION_DESC = "Texture Checker Interpolation"


if __name__ == '__main__':
    pass

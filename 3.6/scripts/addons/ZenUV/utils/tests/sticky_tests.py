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


from .addon_test_utils import AddonTestManual


def Test_wm_sticky_uv_editor(context):
    '''  '''
    # bpy.ops.wm.sticky_uv_editor(ui_button=False, desc=" Show/Hide UV Editor on the side of the 3D Viewport.\nHold * (Zen Modifier Key) to open UV Editor in a separate window.\nHold Ctrl + Shift to open Sticky UV Editor Preferences")
    raise AddonTestManual


def Test_wm_sticky_uv_editor_split(context):
    ''' Open UV Editor in a separate window '''
    # bpy.ops.wm.sticky_uv_editor_split()
    raise AddonTestManual


tests_sticky_uv_sys = (
    Test_wm_sticky_uv_editor,
    Test_wm_sticky_uv_editor_split,
)


if __name__ == "__main__":
    pass

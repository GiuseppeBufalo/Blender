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

import os
import bpy
import bpy.utils.previews
from enum import IntEnum

_zenuv_preview_icons = None
ZENUV_ICONS = bpy.utils.previews.new()

# Register Icons
icons = [
    "unmark-seams_32.png",
    "mark-seams_32.png",
    "zen-uv_32.png",
    "zen-unwrap_32.png",
    "Discord-Logo-White_32.png",
    "quadrify_32.png",
    "checker_32.png",
    "tr_control_cen.png",
    "transform-orient.png",
    "transform-flip.png",
    "transform-scale.png",
    "transform-rotate.png",
    "transform-fit.png",
    "transform-cursor.png",
    "transform-move.png",
    "transform-distribute.png",
    "tr_control_bl.png",
    "tr_control_br.png",
    "tr_control_tl.png",
    "tr_control_tr.png",
    "tr_control_bc.png",
    "tr_control_lc.png",
    "tr_control_rc.png",
    "tr_control_tc.png",
    "tr_rotate_bc.png",
    "tr_rotate_br.png",
    "tr_rotate_cen.png",
    "tr_rotate_bl.png",
    "tr_rotate_lc.png",
    "tr_rotate_rc.png",
    "tr_rotate_tc.png",
    "tr_rotate_tl.png",
    "tr_rotate_tr.png",
    "tr_control_off.png",
    "stack_32.png",
    "pack.png",
    "select.png",
    "zen-bbq.png",
    "zen-sets.png",
    "relax-1_32.png"
]


def icon_register(fileName):
    name = fileName.split('.')[0]   # Don't include file extension
    icons_dir = os.path.dirname(__file__)
    ZENUV_ICONS.load(name, os.path.join(icons_dir, fileName), 'IMAGE')
    # print(name, os.path.join(icons_dir, fileName))


def icon_get(name):
    return ZENUV_ICONS[name].icon_id


class ZIconsType(IntEnum):
    Vert = 0,
    VertP = 1,
    Edge = 2,
    EdgeP = 3,
    Face = 4,
    FaceP = 5,

    Sets = 6,
    Parts = 7,

    AddonLogoPng = 8,
    AddonLogoSvg = 9,
    AddonLogoPng2x = 10,

    DiscordLogo = 11,

    AddonZenUVLogo = 12,
    AddonZenChecker = 13,

    SmartSelect = 14,

    AddonZenBBQ = 15,

def zuv_icon_get(id):
    global _zenuv_preview_icons
    if _zenuv_preview_icons:
        return _zenuv_preview_icons[icons[id][0]].icon_id
    return None


def register():
    global ZENUV_ICONS
    # print(f"icons REGISTERED {ZENUV_ICONS}")
    for icon in icons:
        icon_register(icon)


def unregister():
    global ZENUV_ICONS
    ZENUV_ICONS.clear()


if __name__ == "__main__":
    pass

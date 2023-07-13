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


from mathutils import Vector
from ZenUV.ui.labels import ZuvLabels

ADDON_NAME = "ZenUV"

zenuv_update_filename = "ZenUV_*.zip"
zenuv_update_filter = "*ZenUV*.zip"

u_axis = Vector((1.0, 0.0))
v_axis = Vector((0.0, 1.0))

FACE_UV_AREA_MULT = 100000

ADV_UV_MAP_NAME_PATTERN = "UVChannel_"

ZUV_COPIED = "ZUV_Copied_UV"
ZUV_STORED = "ZUV_Stored_UV"

TEST_OBJ_NAME_CUBE = 'ZenUvTestCube'
TEST_OBJ_NAME_CYLINDER = 'ZenUvTestCylinder'

PACK_EXCLUDED_FACEMAP_NAME = "ZenUV_PackExcluded"
PACK_EXCLUDED_V_MAP_NAME = "zen_uv_pack_excluded"


class Planes:

    x3 = Vector((1, 0, 0))
    y3 = Vector((0, 1, 0))
    z3 = Vector((0, 0, 1))

    x3_negative = Vector((-1.0, 0.0, 0.0))
    y3_negative = Vector((0.0, -1.0, 0.0))
    z3_negative = Vector((0.0, 0.0, -1.0))

    axis_x = Vector((1, 0))
    axis_y = Vector((0, 1))

    pool_3d_dict = {
        "x": x3,
        "y": y3,
        "z": z3,
        "-x": x3_negative,
        "-y": y3_negative,
        "-z": z3_negative
    }

    pool_3d_orient_dict = {
        "x": x3,
        "y": y3,
        # "z": z3,
        "-x": x3_negative,
        "-y": y3_negative,
        # "-z": z3_negative
    }

    pool_3d = (
        x3,
        y3,
        z3,
        x3_negative,
        y3_negative,
        z3_negative
    )
    pool_2d = (axis_x, axis_y)


class UiConstants:

    unified_mark_enum = [
            ("SEAM_BY_UV_BORDER", ZuvLabels.MARK_BY_BORDER_LABEL, ZuvLabels.MARK_BY_BORDER_DESC),
            ("SHARP_BY_UV_BORDER", ZuvLabels.MARK_SHARP_BY_BORDER_LABEL, ZuvLabels.MARK_SHARP_BY_BORDER_DESC),
            ("SEAM_BY_SHARP", ZuvLabels.SEAM_BY_SHARP_LABEL, ZuvLabels.SEAM_BY_SHARP_DESC),
            ("SHARP_BY_SEAM", ZuvLabels.SHARP_BY_SEAM_LABEL, ZuvLabels.SHARP_BY_SEAM_DESC),
            ("SEAM_BY_OPEN_EDGES", ZuvLabels.SEAM_BY_OPEN_EDGES_LABEL, ZuvLabels.SEAM_BY_OPEN_EDGES_DESC),
        ]

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


class ReshapeProperties:
    def __init__(
        self,
        sources,
        along,
        spacing,
        # length_axis,
        sorting,
        rev_dir,
        starts_pos,
        ends_pos,
        offset,
        border_offset,
        border_proportion,
        detect_corners
    ) -> None:
        self.sources = sources  # {"SELECTED","UAXIS","VAXIS","BORDERS"}
        # Blender uv layer (UV Map)
        self.uv_layer = None
        # Base position of the stripe
        # Overrided value not work as expected
        self.base_position = None
        # End position of the stripe
        # Overrided value not work as expected
        self.end_position = None
        self.orient_along = along  # {"INPLACE","U","V","AUTO","ORIGINAL"}
        self.spacing = spacing  # {"UV","GEOMETRY","EVENLY"}
        # self.length_axis = length_axis
        self.sorting = sorting  # {"TOP_LEFT","BOTTOM_RIGHT"}
        self.reverse_dir = rev_dir  # Reverse direction of the stripe
        self.starts_pos = starts_pos  # {"ASIS","MAX","MID","MIN"}
        self.ends_pos = ends_pos  # {"ASIS","MAX","MID","MIN"}
        self.offset = offset
        self.border_offset = border_offset
        self.border_proportion = border_proportion
        self.detect_corners = detect_corners  # {'CORNER','PINS','CORNER_AND_PINS'}

        self.iter_counter = -1

        self.prev_tail = None
        self.prev_head = None
        self.border_head = None
        self.sequence_head = None

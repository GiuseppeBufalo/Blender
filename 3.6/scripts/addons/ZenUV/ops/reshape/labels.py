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


class ReshapeLabels:

    RESHAPE_OP_LABEL = "Reshape Island"
    RESHAPE_OP_DESC = "Changes the form of the island in accordance with the input parameters"

    PROP_DISTRIBUTE_LABEL = "Distribute"
    PROP_DISTRIBUTE_DESC = "Distribute vertices along the line"
    PROP_STRAIGHTEN_LABEL = "Straighten"
    PROP_STRAIGHTEN_DESC = "Straighten selected edge loop and relax connected vertices"
    PROP_ALIGN_TO_LABEL = "Along"
    PROP_ALIGN_TO_DESC = "Alignment options"
    PROP_LENGTH_FROM_LABEL = "Length"
    PROP_LENGTH_FROM_DESC = "Total length of edge loop from bounding box of initial selection"
    PROP_DISTRIBUTION_FROM_LABEL = "Spacing"
    PROP_DISTRIBUTION_FROM_DESC = "How to create spaces between points"
    PROP_REV_START_LABEL = "Detect start from:"
    PROP_REV_START_DESC = "Define the initial Direction of the loop"
    PROP_REV_DIR_LABEL = "Reverse Direction"
    PROP_REV_DIR_DESC = "Change the direction of the aligned line"
    PROP_REL_LINK_LABEL = "Relax Linked"
    PROP_REL_LINK_DESC = "Relax Linked"
    PROP_REL_MODE_LABEL = "Relax Method"
    PROP_REL_MODE_DESC = "Method of Relaxation"

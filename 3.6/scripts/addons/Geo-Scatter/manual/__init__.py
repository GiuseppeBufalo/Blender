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

# (c) 2022 Jakub Uhlik

from . import debug

from . import config
from . import keys
from . import navigator
# from . import tools
from . import ops
from . import gizmos
from . import brushes

import bpy

classes = config.classes + keys.classes + navigator.classes + ops.classes + gizmos.classes + brushes.classes


# TODO: tools -->> to be moved and merged -->> curve.draw_bezier_area, related: ./curve/draw_bezier_area -->> update to multi surface?


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    keys.register_keyconfig()
    
    # TODO: maybe i could do it withou it? if so, i would have none of this register/unregister init/deinit stuff, which would be nice
    gizmos.init()
    
    # # NOTE: until module is merged, this need to be here
    # tools.init()


def unregister():
    # TODO: maybe i could do it withou it? if so, i would have none of this register/unregister init/deinit stuff, which would be nice
    gizmos.deinit()
    
    # # NOTE: until module is merged, this need to be here
    # tools.deinit()
    
    keys.unregister_keyconfig()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# NOTE $ pycodestyle --ignore=W293,E501,E741,E402 .

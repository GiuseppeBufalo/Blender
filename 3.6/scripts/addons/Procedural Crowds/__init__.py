# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
        "name": 'Procedural Crowds',
        "author": "Difffuse Studio, @pavan_bhadaja",
        "version": (1, 0, 5),
        "blender": (3, 40, 0),
        "category": "Asset",
        "doc_url": "https://blendermarket.com/products/procedural-crowds/docs",
        "location" : "View3D > Sidebar"
}

import bpy
from . import preferences
from . import properties, ui, operators

def register():
    preferences.register()
    properties.register()
    operators.register()
    ui.register()
    
def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()
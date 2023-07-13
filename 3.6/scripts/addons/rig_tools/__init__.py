# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


bl_info = {
    "name": "Auto-Rig Pro Tools",
    "author": "Artell",
    "version": ( 3,68,20 ),
    "blender": (2, 80, 0),
    "location": "3D View > Properties> Rig Main Properties",
    "description": "Enables the Auto-Rig Pro tools (operators, snap IK-FK...) Do not install it if the Auto-Rig Pro addon is already installed. ",
    "tracker_url": "http://lucky3d.fr/auto-rig-pro/doc/bug_report.html",    
    "category": "Animation"} 


if "bpy" in locals():
    import importlib
    if "rig_prefs" in locals():
        importlib.reload(rig_prefs)
    if "rig_functions" in locals():
        importlib.reload(rig_functions)
    


import bpy
from bpy.app.handlers import persistent
#import script files
from . import rig_prefs
from . import rig_functions



def register():  
    rig_prefs.register()
    rig_functions.register()    
    

def unregister():   
    rig_prefs.unregister()
    rig_functions.unregister()
    

if __name__ == "__main__":
    register()
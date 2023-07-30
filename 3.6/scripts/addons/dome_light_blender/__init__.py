# ///////////////////////////////////////////////////////////////
#
# Blender Dome Light
# by: WANDERSON M. PIMENTA
# version: 2.0.0
#
# This Addon is inspired by EasyHDRI after it has been without
# updates for a long time I created new versions derived from
# it and within the GPL terms.
# Credits from the EasyHDRI creator:
# http://codeofart.com/easy-hdri-2-8/
#
# ///////////////////////////////////////////////////////////////

import bpy
from . dome_light import *

# Add-on info
bl_info = {
    "name": "Dome Light",
    "author": "Wanderson M Pimenta",
    "version": (2, 0, 1),
    "blender": (2, 90, 0),
    "location": "View3D > Properties > Dome Light",
    "description": "Create a Dome Light", 
    "wiki_url": "",
    "tracker_url": "",      
    "category": "3D View"
}

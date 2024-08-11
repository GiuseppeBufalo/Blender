#pylint: disable=import-error, relative-beyond-top-level

'''
Copyright (C) 2020 Oliver J Post
olepost1@gmail.com

Created by Oliver J Post

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


bl_info = {
    "name" : "SMUDGR Pro",
    "author" : "OliverJPost",
    "description" : "Smudgr Pro allows you to effortlessly add realism to your materials",
    "blender" : (2, 81, 0),
    "version" : (2, 0, 0),
    "location" : "Properties > Material, on the bottom of the panel",
    "warning" : "",
    "category" : "Material"
}


import bpy
import sys
from bpy.app.handlers import persistent
from bpy.utils import previews


if __name__ != "SMR_PRO":
    sys.modules['SMR_PRO'] = sys.modules[__name__]

# load and reload submodules
##################################

from . SMR_SETTINGS import SMR_SETTINGS
from . SMR_PREFERENCES import SMR_PREFERENCES, SMR_UPDATE_PATH
from . SMR_PANEL import SMR_PANEL
from . SMR_INFO import SMR_OT_INFO
from . SMR_CALLBACK import SMR_ACTIVATE
from . SMR_BAKE import SMR_OT_BAKE, SMR_OT_FULLBAKE
from . SMR_AUTOMATIC import SMR_OT_AUTOMATIC
from . panel_operators import SMR_FORCECHOISE, SMR_MANUALCHOISE, SMR_NOCHOISE, SMR_PICK_SLOT,  SMR_UL_SLOTS_UI, SMR_GETBACK
from . SMR_ADDMAIN import SMR_OT_ADD
from . SMR_ADDPART import SMR_OT_ADDPART
from . smr_pcoll import SMR_OT_NEXT, SMR_OT_PREVIOUS
from . SMR_AT import SMR_OT_AT, SMR_OT_ATREMOVE
from . influence_operators import SMR_OT_INFLUENCE, SMR_OT_INFPRESET, SMR_OT_NOPACK, SMR_OT_PACK, SMR_OT_PREVIEW, SMR_OT_REMOVEINFLUENCE, SMR_OT_STOPPREVIEW, SMR_OT_TEXPAINT
from . smr_common import SMR_OT_RESET
from . SMR_DELETE import SMR_ADELETE, SMR_CDELETE
from . SMR_DECALMACHINE import SMR_APPLYDECAL

# startup procedure
##################################
@persistent
def SMR_start(dummy):
    """
    runs the activating class when a file is loaded
    """    

    bpy.ops.SMR.activate()


# register
##################################

from . pcoll import preview_collections


classes = (
    SMR_SETTINGS,
    SMR_PANEL,
    SMR_ACTIVATE,
    SMR_OT_NEXT,
    SMR_OT_PREVIOUS,
    SMR_OT_RESET,
    SMR_OT_INFO,
    SMR_OT_ADD,
    SMR_OT_ADDPART,
    SMR_OT_AT,
    SMR_OT_ATREMOVE,
    SMR_OT_PREVIEW,
    SMR_OT_STOPPREVIEW,
    SMR_OT_INFLUENCE,
    SMR_OT_REMOVEINFLUENCE,
    SMR_OT_INFPRESET,
    SMR_OT_TEXPAINT,
    SMR_OT_PACK,
    SMR_OT_AUTOMATIC,
    SMR_UL_SLOTS_UI,
    SMR_PICK_SLOT,
    SMR_OT_BAKE,
    SMR_OT_NOPACK,
    SMR_UPDATE_PATH,
    SMR_PREFERENCES,
    SMR_NOCHOISE,
    SMR_FORCECHOISE,
    SMR_MANUALCHOISE,
    SMR_ADELETE,
    SMR_CDELETE,
    SMR_OT_FULLBAKE,
    SMR_GETBACK,
    SMR_APPLYDECAL
    )


def register():
    for cls in classes:    
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.SMR = bpy.props.PointerProperty(type=SMR_SETTINGS)
    
    pcoll_dust = previews.new()
    pcoll_smudge = previews.new()  
    pcoll_scratch = previews.new()
    pcoll_droplets = previews.new()
        
    preview_collections["prev_dust"] = pcoll_dust
    preview_collections["prev_smudge"] = pcoll_smudge
    preview_collections["prev_scratch"] = pcoll_scratch
    preview_collections["prev_droplets"] = pcoll_droplets
    if not SMR_start in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(SMR_start)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    if SMR_start in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(SMR_start)
    
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

if __name__ == "__main__":
    register()

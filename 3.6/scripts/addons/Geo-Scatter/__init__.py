
# 88     88  dP""b8 888888 88b 88 .dP"Y8 888888
# 88     88 dP   `" 88__   88Yb88 `Ybo." 88__
# 88  .o 88 Yb      88""   88 Y88 o.`Y8b 88""
# 88ood8 88  YboodP 888888 88  Y8 8bodP' 888888


# Geo-Scatter is a multi program product, please consult our legal page www.geoscatter.com/legal


# 8888b.     db    888888    db        8b    d8    db    88b 88    db     dP""b8 888888 8b    d8 888888 88b 88 888888
#  8I  Yb   dPYb     88     dPYb       88b  d88   dPYb   88Yb88   dPYb   dP   `" 88__   88b  d88 88__   88Yb88   88
#  8I  dY  dP__Yb    88    dP__Yb      88YbdP88  dP__Yb  88 Y88  dP__Yb  Yb  "88 88""   88YbdP88 88""   88 Y88   88
# 8888Y"  dP""""Yb   88   dP""""Yb     88 YY 88 dP""""Yb 88  Y8 dP""""Yb  YboodP 888888 88 YY 88 888888 88  Y8   88    https://asciiflow.com/

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> User Interaction <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#
# ┌──────────────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────────┐
# │tweaking a setting│-►│update factory│-►│update function│-►│changing geonode nodetree│-► blender do it's thing, change instance
# └──────────────────┘  └──────────────┘  └───────────────┘  └─────────────────────────┘
#
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> How Presets Are handled <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                                    ┌────────┐
#                                    │  Json  │ 
#                                    └───▲────┘   
#                                        │ 
#                                    ┌───▼────┐ settings<>dict<>json done in presetting.py -> /!\ Data Loss from settings to dict
#                                    │  Dict  │
#                                    └───▲────┘
#                                        ├──────────────────────────┐
#  ------------------------              │  update_factory.py       │
#  |    copy/paste buffer |    ┌─────────▼───────────────┐          │
#  |  synchronize settings|◄--►│ scatter5.particlesystems│          │
#  |updatefactory features|    │  particle_settings.py   │          │
#  ------------------------    └─────────┬───────────────┘          │
#                                        │                          │ texture_datablock.py
#                                ┌───────▼──────────┐       ┌───────▼───────────┐
#                                │ Geonode NodeTree ◄───────┤   TEXTURE_NODE    │ #special nodegroup dedicated to procedural textures
#                                └───────┬──────────┘       └───────────────────┘
#                                        ▼                  
#                                  BlenderInstancing                           
#                                
#   ┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ 
#   │ >>>> Implementating a new feature into the procedural workflow Work-Steps:                                        │                                                                                
#   │ ───────────────────────────────────────────────────────────────────────────────────────────────────────────────── │                                                                                        
#   │  > Prototype the feature in Geonode then implement in "resouces/blends/data.blend" color-coded and correcly named │                                                                                                                          
#   │  > Tweaking support:                                                                                              │                             
#   │      > Set up properties in "particle_settings.py" with correct values & same name as in nodetree                 │                                                                                                          
#   │      > Dress up settings in GUI "ui_tweaking.py"                                                                  │                                                          
#   │      > Bridge settings to nodetree from update factory in "update_factory.py"                                     │                                                                                                                                
#   │  > Header menu features & buffers/synch:                                                                          │                                 
#   │      > Lock/unlock -> implement _locked boolean in "particle_settings.py"                                         │                                             
#   │      > Synchronize settings: update properties and gui in "synchronize.py"                                        │     
#   │  > Preset support:                                                                                                │                           
#   │      > Update "presetting.py" data management                                                                     │      
#   │      > Update SCATTER5_PT_per_settings_category_header category preset paste support from ui_menu.py              |
#   └───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Inheritence Structure <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#
#    ┌─────────────────────┐
#    │Emitter Target Object│ scat_scene = bpy.context.scene.scatter5
#    └──────────┬──┬───────┘ emitter = scat_scene.emitter
#               │  │   ┌────────────────┐
#               │  └───►Masks Collection│ emitter.scatter5.mask_systems
#               │      └────────────────┘ (== per object property)
#    ┌──────────▼──────────┐
#    │  System Collection  │ psys = emitter.scatter5.particle_systems
#    └─┬──┬──┬──┬──┬──┬──┬─┘ (== per object property)
#     .. .. .│ .. .. .. ..
#            │
#    ┌───────▼───────┐
#    │Scatter System │ psy = psys["Foo"]
#    └─────┬────┬────┘                                      
#          │    │ ┌────────┐ 
#          │    └─►Settings│-> update factory -> update function -> NodegroupChange
#          │      └────────┘   
#    ┌─────▼─────────────────────────────┐
#    │ScatterObj/Modifier/UniqueNodegroup│
#    └───────────────────────────────────┘  
#      scatter_obj = psy.scatter_obj
#      used either for: 
#          -take data from emitter with object info node
#          -use the scatter_object data vertices for manual point distribution
#       Note that scatter_obj can switch mesh-data to store multiple manual point distribution method.
#


bl_info = {
    "name"            : "Geo-Scatter",
    "author"          : "bd3d, Carbon2",
    "description"     : "Geo-Scatter 5.3.2 for Blender 3.3+",
    "blender"         : (3, 3, 0),
    "version"         : (5, 3, 2),
    "engine_version"  : "Scatter5 Geonode Engine MKIII", #& .TEXTURE *DEFAULT* MKIII
    "wiki_url"        : "https://sites.google.com/view/scatter5docs/manual",
    "tracker_url"     : "https://discord.gg/vMwNUJxB",
    "category"        : "",
}


import bpy

#from . import cpp #cpp functions only for baking for now 
from . import resources
from . import widgets
from . import manual
from . import properties
from . import scattering
from . import curve
from . import procedural_vg
from . import utils
from . import terrain
from . import handlers
#from . import baking #not used for now prolly for 5.1
from . import ui
from . import external

main_modules = [ 
    #cpp,
    resources,
    widgets,
    manual,
    properties,
    scattering,
    curve,
    procedural_vg, 
    utils,
    terrain,
    handlers,
    #baking,
    ui, 
    external,
    ]


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .ooooo.   .oooo.   ooo. .oo.    .oooo.o  .ooooo.
# 888           888  d88' `88b `P  )88b  `888P"Y88b  d88(  "8 d88' `88b
# 888           888  888ooo888  .oP"888   888   888  `"Y88b.  888ooo888
# `88b    ooo   888  888    .o d8(  888   888   888  o.  )88b 888    .o
#  `Y8bood8P'  o888o `Y8bod8P' `Y888""8o o888o o888o 8""888P' `Y8bod8P'


def cleanse_modules():
    """remove all plugin modules from sys.modules, will load them again, creating an effective hit-reload soluton
    Not sure why blender is no doing this already whe disabling a plugin..."""
    #https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040

    import sys
    all_modules = sys.modules 
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
    
    for k,v in all_modules.items():
        if k.startswith(__name__):
            del sys.modules[k]

    return None 


# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
#                        d"     YD
#                        "Y88888P'


def register():

    for m in main_modules:
        m.register()
    
    return None

def unregister():

    for m in reversed(main_modules):
        m.unregister()

    #final step, remove modules from sys.modules 
    cleanse_modules()

    return None


#if __name__ == "__main__":
#    register()

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

# oooooooooo.  oooo       o8o               .o88o.           
# `888'   `Y8b `888       `"'               888 `"           
#  888     888  888      oooo  ooo. .oo.   o888oo   .ooooo.  
#  888oooo888'  888      `888  `888P"Y88b   888    d88' `88b 
#  888    `88b  888       888   888   888   888    888   888 
#  888    .88P  888       888   888   888   888    888   888 
# o888bood8P'  o888o     o888o o888o o888o o888o   `Y8bod8P' 


bl_info = {
    "name"           : "Geo-Scatter",
    "description"    : "Geo-Scatter 5.4.0 for Blender 3.3+ (Individual License)",
    "author"         : "bd3d, Carbon2",
    "blender"        : (3, 3, 0),
    "version"        : (5, 4, 0),
    "engine_nbr"     : "MKIV",
    "engine_version" : "Geo-Scatter Engine MKIV", #& .TEXTURE *DEFAULT* MKIV
    "doc_url"        : "https://www.geoscatter.com/documentation",
    "tracker_url"    : "https://discord.gg/vMwNUJxB",
    "category"       : "",
    }

# ooo        ooooo            o8o                   ooo        ooooo                 .o8              oooo                     
# `88.       .888'            `"'                   `88.       .888'                "888              `888                     
#  888b     d'888   .oooo.   oooo  ooo. .oo.         888b     d'888   .ooooo.   .oooo888  oooo  oooo   888   .ooooo.   .oooo.o 
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        8 Y88. .P  888  d88' `88b d88' `888  `888  `888   888  d88' `88b d88(  "8 
#  8  `888'   888   .oP"888   888   888   888        8  `888'   888  888   888 888   888   888   888   888  888ooo888 `"Y88b.  
#  8    Y     888  d8(  888   888   888   888        8    Y     888  888   888 888   888   888   888   888  888    .o o.  )88b 
# o8o        o888o `Y888""8o o888o o888o o888o      o8o        o888o `Y8bod8P' `Y8bod88P"  `V88V"V8P' o888o `Y8bod8P' 8""888P' 


MODULE_NAMES = (
    "resources",
    "widgets",
    "manual",        
    "properties",
    "scattering",
    "curve",
    "procedural_vg", 
    "utils",
    "terrain",       
    "handlers",
    "ui",
    )

# Import the modules dynamically
import importlib
MAIN_MODULES = []
for module_name in MODULE_NAMES:
    module = importlib.import_module("." + module_name, __package__)
    MAIN_MODULES.append(module)
    continue 


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

    try:
        for m in MAIN_MODULES:
            m.register()
            
    # very common user report, previously failed register, then user try to register again, and stumble into the first already registered class
    # we don't want them to report this specific error, it' useless and don't indicate the original error, most of the time we gently ask them to restart their session
    # Note that we could skip a class register if the class is already registered, however the initial activation process shouldn't be faulty at the first place
    
    except Exception as e:        
        if ("register_class(...): already registered as a subclass 'SCATTER5_OT_print_icon_id'" in str(e)):
            raise Exception("\n\nDear User,\nAre you using the correct version of blender with our plugin?\nAn error occured during this activation, it seems that a previous activation failed\nPlease restart blender\n\n")
        raise e
    
    return None

def unregister():

    for m in reversed(MAIN_MODULES):
        m.unregister()

    # final step, remove modules from sys.modules 
    cleanse_modules()

    return None


#if __name__ == "__main__":
#    register()
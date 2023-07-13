

import bpy, os, sys 

#   ooooooooo.                                   o8o
#   `888   `Y88.                                 `"'
#    888   .d88' oooo d8b  .ooooo.  oooo    ooo oooo   .ooooo.  oooo oooo    ooo  .oooo.o
#    888ooo88P'  `888""8P d88' `88b  `88.  .8'  `888  d88' `88b  `88. `88.  .8'  d88(  "8
#    888          888     888ooo888   `88..8'    888  888ooo888   `88..]88..8'   `"Y88b.
#    888          888     888    .o    `888'     888  888    .o    `888'`888'    o.  )88b
#   o888o        d888b    `Y8bod8P'     `8'     o888o `Y8bod8P'     `8'  `8'     8""888P'


#General Previews code utility, used to create custom icons but also previews from manager and preset
#Note to self, Dorian, you could centralize everything icon/preview gallery register related perhaps in one and only module? 



import bpy.utils.previews

def get_previews_from_directory( directory, format=".png", previews=None,):
    """install previews with bpy.utils.preview, will try to search for all image file inside given directory"""

    if (previews is None):
        previews = bpy.utils.previews.new()

    for f in os.listdir(directory) :
        
        if (f[-len(format):] == format ):
            previews.load( f[:-len(format)], os.path.join(directory, f), "IMAGE")

        continue 

    return previews 

def get_previews_from_paths( paths, use_basename=True,  previews=None,):
    """install previews with bpy.utils.preview, will loop over list of image path"""

    if (previews is None):
        previews = bpy.utils.previews.new()

    for p in paths :
        
        if (use_basename):
              icon_name = os.path.basename(p).split('.')[0]
        else: icon_name = p  
        
        if (icon_name not in previews):
            previews.load( icon_name, p, "IMAGE")

        continue 

    return previews 

def remove_previews( previews, ):
    """remove previews wuth bpy.utils.preview"""

    bpy.utils.previews.remove(previews)
    previews.clear()

    return None 

def install_dat_icons_in_cache(directory):
    """Install Dat icons to `space_toolsystem_common.py` `_icon_cache` dictionary, 
    This is used by the native toolsystem and needed for our toolbar hijacking"""

    scr = bpy.utils.system_resource('SCRIPTS')
    pth = os.path.join(scr,'startup','bl_ui')

    if (pth not in sys.path):
        sys.path.append(pth)

    from bl_ui.space_toolsystem_common import _icon_cache

    for f in os.listdir(directory) :

        if (f.startswith("SCATTER5") and f.endswith(".dat") ):

            icon_value = bpy.app.icons.new_triangles_from_file( os.path.join(directory,f) )
            _icon_cache[f.replace(".dat","")]=icon_value

        continue 

    return None 


# ooooooooo.                             .oooooo.                            .         o8o
# `888   `Y88.                          d8P'  `Y8b                         .o8         `"'
#  888   .d88'  .ooooo.   .oooooooo    888          oooo  oooo   .oooo.o .o888oo      oooo   .ooooo.   .ooooo.  ooo. .oo.    .oooo.o
#  888ooo88P'  d88' `88b 888' `88b     888          `888  `888  d88(  "8   888        `888  d88' `"Y8 d88' `88b `888P"Y88b  d88(  "8
#  888`88b.    888ooo888 888   888     888           888   888  `"Y88b.    888         888  888       888   888  888   888  `"Y88b.
#  888  `88b.  888    .o `88bod8P'     `88b    ooo   888   888  o.  )88b   888 .       888  888   .o8 888   888  888   888  o.  )88b
# o888o  o888o `Y8bod8P' `8oooooo.      `Y8bood8P'   `V88V"V8P' 8""888P'   "888"      o888o `Y8bod8P' `Y8bod8P' o888o o888o 8""888P'
#                        d"     YD
#                        "Y88888P'


#Our custom "W_" Icons are stored here
Icons = {}

def cust_icon(str_value):

    #"W_" Icons
    if (str_value.startswith("W_")):
        global Icons
        if (str_value in Icons):
            return Icons[str_value].icon_id 

    #"SCATTER5_" Icons = .dat format
    elif str_value.startswith("SCATTER5_"):
        from bl_ui.space_toolsystem_common import _icon_cache
        if (str_value in _icon_cache):
            return _icon_cache[str_value] 

    return 0 


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



class SCATTER5_OT_print_icon_id(bpy.types.Operator):

    bl_idname      = "scatter5.print_icon_id"
    bl_label       = ""
    bl_description = "for debug purpose"

    icon : bpy.props.StringProperty(default="")

    def execute(self, context):

        print(cust_icon(self.icon))

        return {'FINISHED'}


classes = (

    SCATTER5_OT_print_icon_id,

    )


# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.   .oooooooo
#  888ooo88P'  d88' `88b 888' `88b
#  888`88b.    888ooo888 888   888
#  888  `88b.  888    .o `88bod8P'
# o888o  o888o `Y8bod8P' `8oooooo.
#                        d"     YD
#                        "Y88888P'


from . import directories

def register():

    global Icons
    Icons = get_previews_from_directory(directories.addon_icons)
    Icons = get_previews_from_directory(os.path.join(directories.addon_icons,"placeholder"), previews=Icons)

    install_dat_icons_in_cache(directories.addon_dat_icons)

    return None 

def unregister():

    global Icons
    remove_previews(Icons)
    
    return None 
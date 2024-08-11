
#####################################################################################################
#
#  ooooo     ooo ooooo
#  `888'     `8' `888'
#   888       8   888
#   888       8   888
#   888       8   888
#   `88.    .8'   888
#     `YbodP'    o888o
#
#####################################################################################################


import bpy

from . import ui_templates 
from . import ui_menus
from . import ui_system_list
from . import ui_creation
from . import ui_notification
from . import ui_tweaking
from . import ui_extra
from . import ui_emitter_select
from . import ui_addon
from . import ui_manual
from . import ui_biome_library
from . import open_manager


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'

classes  =  []
classes +=  ui_menus.classes
classes +=  ui_system_list.classes
classes +=  ui_creation.classes
classes +=  ui_notification.classes
classes +=  ui_tweaking.classes
classes +=  ui_extra.classes
classes +=  ui_emitter_select.classes
classes +=  ui_addon.classes
classes +=  ui_manual.classes
classes +=  ui_biome_library.classes
classes +=  open_manager.classes

#classes possessing "USER_DEFINED bl_category", will be dynamically reloaded
user_tab_classes = [cls for cls in classes if hasattr(cls,"bl_category") and (cls.bl_category=="USER_DEFINED") ]


def register():

    #patch class with user defined category
    for cls in user_tab_classes: 
        cls.bl_category = bpy.context.preferences.addons["Geo-Scatter"].preferences.tab_name

    for cls in classes:
        bpy.utils.register_class(cls)

    #register biome library previews, build strucure, online fetch..
    ui_biome_library.register()

    #register shortcuts
    ui_system_list.register_quicklister_shortcuts()

    return 


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    #register biome library previews, build strucure, online fetch..
    ui_biome_library.unregister()

    #unregister shortcuts
    ui_system_list.unregister_quicklister_shortcuts()

    return



#if __name__ == "__main__":
#    register()
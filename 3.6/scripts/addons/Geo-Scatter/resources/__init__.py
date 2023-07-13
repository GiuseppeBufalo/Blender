
################################################################################################
# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.   .oooo.o  .ooooo.  oooo  oooo  oooo d8b  .ooooo.   .ooooo.   .oooo.o
#  888ooo88P'  d88' `88b d88(  "8 d88' `88b `888  `888  `888""8P d88' `"Y8 d88' `88b d88(  "8
#  888`88b.    888ooo888 `"Y88b.  888   888  888   888   888     888       888ooo888 `"Y88b.
#  888  `88b.  888    .o o.  )88b 888   888  888   888   888     888   .o8 888    .o o.  )88b
# o888o  o888o `Y8bod8P' 8""888P' `Y8bod8P'  `V88V"V8P' d888b    `Y8bod8P' `Y8bod8P' 8""888P'
#
################################################################################################


import bpy

from . import translate
from . import directories
from . import icons
from . import packaging
from . thumbnail import thumb_generation  


# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.   .oooooooo
#  888ooo88P'  d88' `88b 888' `88b
#  888`88b.    888ooo888 888   888
#  888  `88b.  888    .o `88bod8P'
# o888o  o888o `Y8bod8P' `8oooooo.
#                        d"     YD
#                        "Y88888P'


classes  = []
classes += icons.classes
classes += packaging.classes
classes += thumb_generation.classes


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    #load all icons
    icons.register()

    #set upd default library folders 
    directories.library_startup()

    return  



def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    icons.unregister()

    return 

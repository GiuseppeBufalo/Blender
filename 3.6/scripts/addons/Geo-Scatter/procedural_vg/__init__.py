
#####################################################################################################
#
# ooooooooo.                                                .o8                                 oooo       oooooo     oooo
# `888   `Y88.                                             "888                                 `888        `888.     .8'
#  888   .d88' oooo d8b  .ooooo.   .ooooo.   .ooooo.   .oooo888  oooo  oooo  oooo d8b  .oooo.    888         `888.   .8'    .oooooooo
#  888ooo88P'  `888""8P d88' `88b d88' `"Y8 d88' `88b d88' `888  `888  `888  `888""8P `P  )88b   888          `888. .8'    888' `88b
#  888          888     888   888 888       888ooo888 888   888   888   888   888      .oP"888   888           `888.8'     888   888
#  888          888     888   888 888   .o8 888    .o 888   888   888   888   888     d8(  888   888            `888'      `88bod8P'
# o888o        d888b    `Y8bod8P' `Y8bod8P' `Y8bod8P' `Y8bod88P"  `V88V"V8P' d888b    `Y888""8o o888o            `8'       `8oooooo.
#                                                                                                                          d"     YD
#                                                                                                                          "Y88888P'
#####################################################################################################


import bpy

from . import mask_type
from . import add_mask
from . import remove
from . import refresh_all


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


classes = ()
classes += add_mask.classes
classes += refresh_all.classes
classes += mask_type.classes
classes += remove.classes


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    return 


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    return 



#if __name__ == "__main__":
#    register()
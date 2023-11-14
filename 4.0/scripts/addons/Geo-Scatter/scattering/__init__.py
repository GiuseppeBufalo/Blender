
#####################################################################################################
#
#  .oooooo..o                         .       .                       o8o
# d8P'    `Y8                       .o8     .o8                       `"'
# Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b oooo  ooo. .oo.    .oooooooo
#  `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P `888  `888P"Y88b  888' `88b
#      `"Y88b 888        .oP"888    888     888   888ooo888  888      888   888   888  888   888
# oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888      888   888   888  `88bod8P'
# 8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b    o888o o888o o888o `8oooooo.
#                                                                                      d"     YD
#                                                                                      "Y88888P'
#####################################################################################################


import bpy

from . import emitter
from . import add_psy
from . import add_biome
from . import remove
from . import rename
from . import selection
from . import instances
from . import update_factory
from . import presetting
from . import copy_paste
from . import ops
from . import synchronize
from . import texture_datablock 
from . import bitmap_library
from . import export_particles


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


classes  = []
classes += emitter.classes
classes += add_psy.classes
classes += add_biome.classes
classes += remove.classes
classes += selection.classes
classes += instances.classes
classes += presetting.classes
classes += update_factory.classes
classes += copy_paste.classes
classes += ops.classes
classes += synchronize.classes
classes += bitmap_library.classes
classes += export_particles.classes


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    #register preset gallery previews
    presetting.gallery_register()

    #register bitmap gallery previews
    bitmap_library.bitmaps_register()

    #register all texture_data sub-classes
    texture_datablock.register()

    #register shotcuts
    add_psy.register_quickscatter_shortcuts()

    return 


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    #unregister preset gallery previews
    presetting.gallery_unregister()

    #unregister bitmap gallery previews
    bitmap_library.bitmaps_unregister()

    #register all texture_data sub-classes
    texture_datablock.unregister()

    #unregister shotcuts
    add_psy.unregister_quickscatter_shortcuts()

    return


#if __name__ == "__main__":
#    register()
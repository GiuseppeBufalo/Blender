
#####################################################################################################
#
# ooooo     ooo     .    o8o  oooo
# `888'     `8'   .o8    `"'  `888
#  888       8  .o888oo oooo   888   .oooo.o
#  888       8    888   `888   888  d88(  "8
#  888       8    888    888   888  `"Y88b.
#  `88.    .8'    888 .  888   888  o.  )88b
#    `YbodP'      "888" o888o o888o 8""888P'   Handy Tools and Functions
#
#####################################################################################################


import bpy

from . import coll_utils
from . import override_utils
from . import create_utils
from . import mod_utils
from . import np_utils 
from . import vg_utils
from . import import_utils
from . import event_utils
from . import str_utils
from . import path_utils
from . import node_utils
from . import extra_utils 
from . import draw_utils



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
classes += coll_utils.classes
classes += event_utils.classes
classes += extra_utils.classes
classes += draw_utils.classes
classes += path_utils.classes
classes += vg_utils.classes
classes += import_utils.classes


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    node_utils.register()

    return 

def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    node_utils.unregister()
    
    return 



#if __name__ == "__main__":
#    register()
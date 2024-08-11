
# ooooooooooooo                                         oooo                .
# 8'   888   `8                                         `888              .o8
#      888      oooo d8b  .oooo.   ooo. .oo.    .oooo.o  888   .oooo.   .o888oo  .ooooo.
#      888      `888""8P `P  )88b  `888P"Y88b  d88(  "8  888  `P  )88b    888   d88' `88b
#      888       888      .oP"888   888   888  `"Y88b.   888   .oP"888    888   888ooo888
#      888       888     d8(  888   888   888  o.  )88b  888  d8(  888    888 . 888    .o
#     o888o     d888b    `Y888""8o o888o o888o 8""888P' o888o `Y888""8o   "888" `Y8bod8P'


import bpy 


def translate(key, context=None):
    """translate this string"""

    blender_language = bpy.context.preferences.view.language

    if blender_language == "en_US":
        return key

    # elif blender_language == "fr_FR'":
    #     return "Français"
    #     #return fr_FR[key]

    # elif blender_language == "es":
    #     return "Spanish"
    #     #return es[key]

    # elif blender_language == "ja_JP'":
    #     return "Japanese"
    #     #return es[key]

    # elif blender_language == "zh_CN":
    #     return "Chinese Simplified"
    #     #return es[key]
    
    else:
        #nut supported = english 
        return key


def generate_translate_csv():
    """introspect all translate() function, and create traduction dict files, key is always english""" 
    return 




# oooooooooo.   o8o      .                     oooo                            ooooo         o8o   .o8
# `888'   `Y8b  `"'    .o8                     `888                            `888'         `"'  "888
#  888     888 oooo  .o888oo ooo. .oo.  .oo.    888   .oooo.   oo.ooooo.        888         oooo   888oooo.
#  888oooo888' `888    888   `888P"Y88bP"Y88b   888  `P  )88b   888' `88b       888         `888   d88' `88b
#  888    `88b  888    888    888   888   888   888   .oP"888   888   888       888          888   888   888
#  888    .88P  888    888 .  888   888   888   888  d8(  888   888   888       888       o  888   888   888
# o888bood8P'  o888o   "888" o888o o888o o888o o888o `Y888""8o  888bod8P'      o888ooooood8 o888o  `Y8bod8P'
#                                                               888
#                                                              o888o

import bpy
import os 
import random

from .. resources import directories
from .. resources.translate import translate
from .. utils.extra_utils import dprint


# oooooooooo.                                          oooooooooooo
# `888'   `Y8b                                         `888'     `8
#  888      888 oooo    ooo ooo. .oo.    .oooo.         888         ooo. .oo.   oooo  oooo  ooo. .oo.  .oo.
#  888      888  `88.  .8'  `888P"Y88b  `P  )88b        888oooo8    `888P"Y88b  `888  `888  `888P"Y88bP"Y88b
#  888      888   `88..8'    888   888   .oP"888        888    "     888   888   888   888   888   888   888
#  888     d88'    `888'     888   888  d8(  888        888       o  888   888   888   888   888   888   888
# o888bood8P'       .8'     o888o o888o `Y888""8o      o888ooooood8 o888o o888o  `V88V"V8P' o888o o888o o888o
#               .o..P'
#               `Y8P'

from .. resources.icons import get_previews_from_directory, remove_previews

#need to store bpy.utils.previews in global 
BitmapPreviews = {}

def bitmaps_register():
    """Dynamically create EnumProperty from custom loaded previews"""

    global BitmapPreviews 
    BitmapPreviews = get_previews_from_directory(directories.lib_bitmaps, format=".jpg")
    listbitmaps = [ file.replace(".jpg","") for file in os.listdir(directories.lib_bitmaps) if file.endswith(".jpg") ]
    items = [(translate("Nothing Found"), translate("Nothing Found"), "", "BLANK1", 0, ),]

    if (len(listbitmaps)!=0): 
        items = [ #items generator
                    (   e, #enum value
                        e.title().replace("_"," "), #enum name
                        "", #enum description
                        BitmapPreviews[e].icon_id if e in BitmapPreviews else "BLANL1", #enum icon
                        i, #enumeration 
                    )  
                    for i,e in enumerate(listbitmaps)
                ]

    bpy.types.WindowManager.scatter5_bitmap_library = bpy.props.EnumProperty(items=items, update=update_scatter5_bitmap_library,)

    return None 

def bitmaps_unregister():

    del bpy.types.WindowManager.scatter5_bitmap_library

    global BitmapPreviews 
    remove_previews(BitmapPreviews)

    return None 

def reload_bitmaps():

    bitmaps_unregister()
    bitmaps_register()

    return None 

class SCATTER5_OT_reload_bitmap_library(bpy.types.Operator):

    bl_idname      = "scatter5.reload_bitmap_library"
    bl_label       = ""
    bl_description = ""

    def execute(self, context):

        reload_bitmaps()

        return {'FINISHED'} 


# oooooooooooo                                                ooooo     ooo                  .o8                .
# `888'     `8                                                `888'     `8'                 "888              .o8
#  888         ooo. .oo.   oooo  oooo  ooo. .oo.  .oo.         888       8  oo.ooooo.   .oooo888   .oooo.   .o888oo  .ooooo.
#  888oooo8    `888P"Y88b  `888  `888  `888P"Y88bP"Y88b        888       8   888' `88b d88' `888  `P  )88b    888   d88' `88b
#  888    "     888   888   888   888   888   888   888        888       8   888   888 888   888   .oP"888    888   888ooo888
#  888       o  888   888   888   888   888   888   888        `88.    .8'   888   888 888   888  d8(  888    888 . 888    .o
# o888ooooood8 o888o o888o  `V88V"V8P' o888o o888o o888o         `YbodP'     888bod8P' `Y8bod88P" `Y888""8o   "888" `Y8bod8P'
#                                                                            888
#                                                                           o888o

#need to pass an arg to a enum update fct here
NgName = "" 

def update_scatter5_bitmap_library(self, context):
            
    global NgName
    ng = bpy.data.node_groups.get(NgName)
    if (ng is None):
        return None

    choice = self.scatter5_bitmap_library 
    img_path = os.path.join(directories.lib_bitmaps , choice+".jpg" )
    if not os.path.exists(img_path):
        return None

    dprint("PROP_FCT: updating WindowManager.scatter5_bitmap_library")    
        
    from .. utils.import_utils import import_image
    ng.scatter5.texture.image_ptr = import_image(img_path, hide=True, use_fake_user=False)

    NgName = ""

    return None


# ooooo                                   oooo                       ooo        ooooo
# `888'                                   `888                       `88.       .888'
#  888  ooo. .oo.   oooo    ooo  .ooooo.   888  oooo   .ooooo.        888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  888  `888P"Y88b   `88.  .8'  d88' `88b  888 .8P'   d88' `88b       8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#  888   888   888    `88..8'   888   888  888888.    888ooo888       8  `888'   888  888ooo888  888   888   888   888
#  888   888   888     `888'    888   888  888 `88b.  888    .o       8    Y     888  888    .o  888   888   888   888
# o888o o888o o888o     `8'     `Y8bod8P' o888o o888o `Y8bod8P'      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'


class SCATTER5_OT_bitmap_draw_menu(bpy.types.Operator):

    bl_idname      = "scatter5.bitmap_draw_menu"
    bl_label = ""
    bl_description = translate("Choose custom images from your bitmap library")

    ng_name : bpy.props.StringProperty()

    def execute(self, context):

        ng = bpy.data.node_groups.get(self.ng_name)
        if (ng is None): 
            return {'FINISHED'}
        global NgName
        NgName = ng.name 

        def draw(self, context):
            layout = self.layout

            #Draw Previews Templates
            layout.template_icon_view(bpy.context.window_manager, "scatter5_bitmap_library", scale=5, show_labels=False, scale_popup=3.5)
            layout.separator()
            layout.operator("scatter5.open_directory", text=translate("Open Library"), icon="FOLDER_REDIRECT").folder = directories.lib_bitmaps
            layout.separator()
            layout.operator("scatter5.reload_bitmap_library", text=translate("Refresh Library"), icon="FILE_REFRESH")

        bpy.context.window_manager.popup_menu(draw, title=translate("Choose your Image Below"), icon="ASSET_MANAGER")

        return {'FINISHED'}


#  .oooooo..o oooo         o8o                    .oooooo.
# d8P'    `Y8 `888         `"'                   d8P'  `Y8b
# Y88bo.       888  oooo  oooo  oo.ooooo.       888      888 oo.ooooo.   .ooooo.
#  `"Y8888o.   888 .8P'   `888   888' `88b      888      888  888' `88b d88' `88b
#      `"Y88b  888888.     888   888   888      888      888  888   888 888ooo888
# oo     .d8P  888 `88b.   888   888   888      `88b    d88'  888   888 888    .o
# 8""88888P'  o888o o888o o888o  888bod8P'       `Y8bood8P'   888bod8P' `Y8bod8P'
#                                888                          888
#                               o888o                        o888o


class SCATTER5_OT_bitmap_skip(bpy.types.Operator):

    bl_idname      = "scatter5.bitmap_skip"
    bl_label       = ""
    bl_description = ""

    option : bpy.props.StringProperty() #in "left"/"right"/"random"
    ng_name : bpy.props.StringProperty()

    def execute(self, context):
        
        ng = bpy.data.node_groups.get(self.ng_name)
        if (ng is None): 
            return {'FINISHED'}
        global NgName
        NgName = ng.name 

        #get items from library enum property
        enum_items = [ tup[0] for tup in bpy.types.WindowManager.scatter5_bitmap_library.keywords['items'] ]
        active_enum = bpy.context.window_manager.scatter5_bitmap_library
        i = enum_items.index(active_enum)
        
        #or access folder directly? 
        #listbitmaps = [ file.replace(".jpg","") for file in os.listdir(directories.lib_bitmaps) if file.endswith(".jpg") ]

        if (self.option=="left"):
            if (i==0):
                i=len(enum_items) #go to end if below 0
            bpy.context.window_manager.scatter5_bitmap_library = enum_items[i-1]

        if (self.option=="right"):
            if (i==len(enum_items)-1):
                  i=0 #go to begining if last 
            else: i+=1
            bpy.context.window_manager.scatter5_bitmap_library = enum_items[i]

        if (self.option=="random"):
            bpy.context.window_manager.scatter5_bitmap_library = random.choice(enum_items)
            return {'FINISHED'}

        return {'FINISHED'}

#                                o8o               .
#                                `"'             .o8
# oooo d8b  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
# `888""8P d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
#  888     888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
#  888     888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# d888b    `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
#                    d"     YD
#                    "Y88888P'


classes = (
    
    SCATTER5_OT_reload_bitmap_library, 
    SCATTER5_OT_bitmap_draw_menu,
    SCATTER5_OT_bitmap_skip,

    )


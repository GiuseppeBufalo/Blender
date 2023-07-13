

#####################################################################################################
#
#       .o.             .o8        .o8                        ooooooooo.                       .o88o.
#      .888.           "888       "888                        `888   `Y88.                     888 `"
#     .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.    888   .d88' oooo d8b  .ooooo.  o888oo
#    .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b   888ooo88P'  `888""8P d88' `88b  888
#   .88ooo8888.   888   888  888   888  888   888  888   888   888          888     888ooo888  888
#  .8'     `888.  888   888  888   888  888   888  888   888   888          888     888    .o  888
# o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o o888o        d888b    `Y8bod8P' o888o
#
#####################################################################################################


import bpy 
import os

from .. ui import ui_addon #need to draw addon prefs from here..

from .. resources.translate import translate
from .. resources import directories

from .. utils import path_utils 


def upd_tab_name(self,context):
    """dynamically change category & reload some panel upon update""" 

    from .. ui import user_tab_classes

    for cls in reversed(user_tab_classes):
        if (cls.is_registered):
            bpy.utils.unregister_class(cls)

    for cls in user_tab_classes:
        if (not cls.is_registered):
            cls.bl_category = self.tab_name
            bpy.utils.register_class(cls)

    return None 

def upd_blend_folder(self,context):

    self.high_nest = False    

    if (not os.path.exists(self.blend_folder)):
        print("ERROR: the selected folder do not exists")
        print(self.blend_folder)
        return None

    folds = path_utils.get_direct_folder_paths(self.blend_folder)

    if (folds is None): 
        print("ERROR: upd_blend_folder() did not find any get_direct_folder_paths()")
        return None

    for f in folds:
        if len(path_utils.get_direct_folder_paths(f)):
            self.high_nest = True

    return None

class SCATTER5_PR_blend_environment_paths(bpy.types.PropertyGroup):
    """addon_prefs.blend_environment_paths[x]"""

    name : bpy.props.StringProperty()

    blend_folder : bpy.props.StringProperty(
        subtype="DIR_PATH",
        description=translate("When creating a biome, our plugin will search for blends in your _asset_library_ or in the given path"),
        update=upd_blend_folder
        )
    
    high_nest : bpy.props.IntProperty()


class SCATTER5_AddonPref(bpy.types.AddonPreferences):
    """addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences"""
    
    from .. __init__ import bl_info
    bl_idname = bl_info["name"]

    # 88b 88      88""Yb    db    88b 88 888888 88        88b 88    db    8b    d8 888888
    # 88Yb88 ___  88__dP   dPYb   88Yb88 88__   88        88Yb88   dPYb   88b  d88 88__
    # 88 Y88 """  88"""   dP__Yb  88 Y88 88""   88  .o    88 Y88  dP__Yb  88YbdP88 88""
    # 88  Y8      88     dP""""Yb 88  Y8 888888 88ood8    88  Y8 dP""""Yb 88 YY 88 888888

    tab_name : bpy.props.StringProperty(
        default=bl_info["name"],
        update=upd_tab_name,
        )

    # 8b    d8    db    88""Yb 88  dP 888888 888888 
    # 88b  d88   dPYb   88__dP 88odP  88__     88   
    # 88YbdP88  dP__Yb  88"Yb  88"Yb  88""     88   
    # 88 YY 88 dP""""Yb 88  Yb 88  Yb 888888   88   

    fetch_automatic_allow : bpy.props.BoolProperty(
        default=True,
        )
    fetch_automatic_daycount : bpy.props.IntProperty(
        default=6,
        min=1, max=31,
        )

    # 88     88 88""Yb 88""Yb    db    88""Yb Yb  dP
    # 88     88 88__dP 88__dP   dPYb   88__dP  YbdP
    # 88  .o 88 88""Yb 88"Yb   dP__Yb  88"Yb    8P
    # 88ood8 88 88oodP 88  Yb dP""""Yb 88  Yb  dP

    library_path : bpy.props.StringProperty(
        default= directories.lib_default,
        subtype="DIR_PATH",
        )
    blend_environment_path_asset_browser_allow : bpy.props.BoolProperty(
        default=True,
        )
    blend_environment_path_allow : bpy.props.BoolProperty(
        default=False,
        )
    blend_environment_paths : bpy.props.CollectionProperty(type=SCATTER5_PR_blend_environment_paths)
    blend_environment_paths_idx : bpy.props.IntProperty()

    # 888888 8b    d8 88 888888     8b    d8 888888 888888 88  88  dP"Yb  8888b.
    # 88__   88b  d88 88   88       88b  d88 88__     88   88  88 dP   Yb  8I  Yb
    # 88""   88YbdP88 88   88       88YbdP88 88""     88   888888 Yb   dP  8I  dY
    # 888888 88 YY 88 88   88       88 YY 88 888888   88   88  88  YbodP  8888Y"

    emitter_method : bpy.props.EnumProperty(
        default= "pointer",
        items=[ 
                ("pointer",translate("Pointer") ,translate("Display the emitter pointer"),"NONE",1 ),
                ("menu",translate("Menu") ,translate("Use a dropdown menu with many emitter options"),"NONE",2 ),
                ("pin",translate("Pin") ,translate("The active object will be designated as emitter, except if pinned"),"NONE",3 ),
                ("remove",translate("Panel") ,translate("Go back to the emitter panel"),"NONE",4 ),
                
              ],
        ) 
    emitter_use_set_active : bpy.props.BoolProperty(
        default=False,
        description=translate("Show 'Set active as Emitter-Target' Operator."),
        )

    # 88 88b 88 888888 888888 88""Yb 888888    db     dP""b8 888888
    # 88 88Yb88   88   88__   88__dP 88__     dPYb   dP   `" 88__
    # 88 88 Y88   88   88""   88"Yb  88""    dP__Yb  Yb      88""
    # 88 88  Y8   88   888888 88  Yb 88     dP""""Yb  YboodP 888888

    ui_library_item_size : bpy.props.FloatProperty(
        default=7.0,
        min=5,
        max=15,
        name=translate("Item Size")
        )
    ui_library_typo_limit : bpy.props.IntProperty(
        default=40,
        min=4,
        max=100,
        name=translate("Typo Limit"),
        )
    ui_library_adaptive_columns : bpy.props.BoolProperty(
        name=translate("Adaptive Columns"),
        default=True,
        )
    ui_library_columns : bpy.props.IntProperty(
        default=4,
        min=1,
        max=40,
        soft_max=10,
        name=translate("Number of Columns"),
        )
    ui_lister_scale_y : bpy.props.FloatProperty(
        default=1.2,
        min=0.1,
        max=5,
        name=translate("Row Height")
        )
    ui_use_dark_box : bpy.props.BoolProperty(
        default=False,
        )
    ui_show_boxpanel_icon : bpy.props.BoolProperty(
        default=False,
        )
    ui_selection_y : bpy.props.FloatProperty(
        default=0.86,
        soft_min=0.7,
        max=1.25,
        )
    ui_boxpanel_separator : bpy.props.FloatProperty(
        default=1.0,
        max=10,
        )
    ui_boxpanel_height : bpy.props.FloatProperty(
        default=1.2,
        min=0.03, max=4,
        )
    ui_bool_use_standard : bpy.props.BoolProperty(
        default=True,
        )
    ui_bool_use_openclose : bpy.props.BoolProperty(
        default=True,
        )
    ui_bool_use_iconcross : bpy.props.BoolProperty(
        default=False,
        )
    ui_bool_indentation : bpy.props.FloatProperty(
        default=0.07,
        min=-0.2, max=0.2,
        )
    ui_word_wrap_max_char_factor : bpy.props.FloatProperty(
        default=1.0,
        min=0.3,
        max=3,
        )
    ui_word_wrap_y : bpy.props.FloatProperty(
        default=0.8,
        min=0.1,
        max=3,
        )
    ui_apply_scale_warn : bpy.props.BoolProperty(
        default=True,
        )
    
    # 8b    d8    db    88b 88 88   88    db    88         888888 88  88 888888 8b    d8 888888 
    # 88b  d88   dPYb   88Yb88 88   88   dPYb   88           88   88  88 88__   88b  d88 88__   
    # 88YbdP88  dP__Yb  88 Y88 Y8   8P  dP__Yb  88  .o       88   888888 88""   88YbdP88 88""   
    # 88 YY 88 dP""""Yb 88  Y8 `YbodP' dP""""Yb 88ood8       88   88  88 888888 88 YY 88 888888 
    
    from .. manual import config
    manual_theme : bpy.props.PointerProperty(type=config.SCATTER5_PR_preferences_theme, )
    manual_use_overlay : bpy.props.BoolProperty(name="Use Overlay", default=True, )
    
    # 8888b.  888888 88""Yb 88   88  dP""b8
    #  8I  Yb 88__   88__dP 88   88 dP   `"
    #  8I  dY 88""   88""Yb Y8   8P Yb  "88
    # 8888Y"  888888 88oodP `YbodP'  YboodP

    debug_interface : bpy.props.BoolProperty(default=False)
    debug : bpy.props.BoolProperty(default=False)
    debug_depsgraph : bpy.props.BoolProperty(default=False)

    # 8888b.  88""Yb    db    Yb        dP 
    #  8I  Yb 88__dP   dPYb    Yb  db  dP  
    #  8I  dY 88"Yb   dP__Yb    YbdPYbdP   
    # 8888Y"  88  Yb dP""""Yb    YP  YP     
    #drawing part in ui module
    
    def draw(self,context):
        layout = self.layout
        ui_addon.draw_addon(self,layout) #need to draw addon prefs from here..

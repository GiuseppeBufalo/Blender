

#####################################################################################################
#
#   .oooooo.                 o8o
#  d8P'  `Y8b                `"'
# 888           oooo  oooo  oooo       oo.ooooo.  oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
# 888           `888  `888  `888        888' `88b `888""8P d88' `88b  888' `88b d88(  "8
# 888     ooooo  888   888   888        888   888  888     888   888  888   888 `"Y88b.
# `88.    .88'   888   888   888        888   888  888     888   888  888   888 o.  )88b
#  `Y8bood8P'    `V88V"V8P' o888o       888bod8P' d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                       888                           888
#                                      o888o                         o888o
#####################################################################################################

# ABOUT THIS MODULE
#
# procedurally register the boolean props used for interface, all ui props need to be in bpy.context.window_manager to ingore history
# we search for keywords commented in our whole projects and register our props with their default values
#
# https://blender.stackexchange.com/questions/269837/how-to-pass-text-argument-to-a-popover-panel
# this is our alternative solution ( than manually registering dedicated properties 30+ times for our header settings/docs popovers
# we procedurally add these properties to scat_ui.popovers_args at regtime, we just search for string arg in tagged comment lines

import bpy 
import os
import re 
import pathlib

from time import process_time

from .. resources.directories import addon_scatter
from .. resources.translate import translate
from .. utils.path_utils import get_subpaths

# oooooooooooo                                       .    o8o
# `888'     `8                                     .o8    `"'
#  888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.    .oooo.o
#  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b  d88(  "8
#  888    "     888   888   888   888  888         888    888  888   888  888   888  `"Y88b.
#  888          888   888   888   888  888   .o8   888 .  888  888   888  888   888  o.  )88b
# o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o 8""888P'


def codegen_reg_context_pointer_args(scope_ref={},):
    """codegen for registering popovers args"""

    d,keywords = {},[]

    #search everywhere in the main tweaking modules 
    files = [os.path.join(addon_scatter,"ui",module+".py") for module in ("ui_creation","ui_tweaking","ui_extra","ui_addon",)] 
    for py in files:
        with open(py,'r') as f:
            txt = f.read()
            #gather name of the property
            keywords += re.findall(r'REGTIME_INSTRUCTION:POPOVER_PROP:"(.*?)"', txt,)
        continue

    for prop_name in keywords:
        if prop_name not in d.keys():
            d[prop_name] = bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class,)
        continue

    #define objects in dict
    scope_ref.update(d)
    return d 

def codegen_reg_ui_booleans(scope_ref={},):
    """codegen for registering all ui open/close properties"""

    d,keywords,defaults = {},[],[]

    #search everywhere except here
    files = get_subpaths(addon_scatter, file_type=".py", excluded_files=["gui_settings.py",])
    for py in files:
        with open(py,'r') as f:
            txt = f.read()
            #gather name of the property
            keywords += re.findall(r'REGTIME_INSTRUCTION:UI_BOOL_KEY:"(.*?)"', txt,) #name of the property
            #gather default values 
            defaults += re.findall(r'UI_BOOL_VAL:"(.*?)"', txt,) 
            #example: 
            #REGTIME_INSTRUCTION:UI_BOOL_KEY:"my_ui_property";UI_BOOL_VAL:"0"
        continue

    for (prop_name,default) in zip(keywords,defaults):
        if prop_name not in d.keys():
            d[prop_name] = bpy.props.BoolProperty(default=int(default), description=translate("Open/Close this interface layout"),)
        continue

    #define objects in dict
    scope_ref.update(d)
    return d 


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_PR_popovers_dummy_class(bpy.types.PropertyGroup):
    """dummy class used just to create pointers"""

    dummy : bpy.props.BoolProperty() #dummy needed just to make the class valid

class SCATTER5_PR_popovers_arg(bpy.types.PropertyGroup):
    """bpy.context.window_manager.scatter5.ui.popovers_args"""

    dummy : bpy.props.BoolProperty() #dummy needed just to make the class valid

    #registered pointers used to pass arg via context on the fly 
    codegen_reg_context_pointer_args(scope_ref=__annotations__)

class SCATTER5_PR_ui(bpy.types.PropertyGroup): 
    """scat_ui = bpy.context.window_manager.scatter5.ui, props used for opening/closing gui"""

    #Panel popover arguments, registered on the fly 
    popovers_args : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_arg)

    #BoxPanel opening/closing props, registered on the fly 
    codegen_reg_ui_booleans(scope_ref=__annotations__)
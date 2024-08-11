
###############################################################################################################################################################
#
# oooooooooo.   o8o                                             ooooo         o8o   .o8
# `888'   `Y8b  `"'                                             `888'         `"'  "888
#  888     888 oooo   .ooooo.  ooo. .oo.  .oo.    .ooooo.        888         oooo   888oooo.  oooo d8b  .oooo.   oooo d8b oooo    ooo
#  888oooo888' `888  d88' `88b `888P"Y88bP"Y88b  d88' `88b       888         `888   d88' `88b `888""8P `P  )88b  `888""8P  `88.  .8'
#  888    `88b  888  888   888  888   888   888  888ooo888       888          888   888   888  888      .oP"888   888       `88..8'
#  888    .88P  888  888   888  888   888   888  888    .o       888       o  888   888   888  888     d8(  888   888        `888'
# o888bood8P'  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'      o888ooooood8 o888o  `Y8bod8P' d888b    `Y888""8o d888b        .8'
#                                                                                                                         .o..P'
#                                                                                                                         `Y8P'
###############################################################################################################################################################

import bpy
import os
import json
import pathlib
from datetime import datetime, date

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. import utils
from .. utils.event_utils import get_event
from .. utils.str_utils import word_wrap


# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
#                                 o888o

def set_is_open(self,value):
    """write in library a little text file with boolean statement"""

    file = os.path.join(self.name,"_folder_opening_") #note that _closed_default_ _active_default_ are not used anymore. junk..
    with open(file, 'w') as f:
        f.seek(0)
        f.write(f"{value}")
        f.truncate()

    return None


def get_is_open(self):
    """get statement from text file, if none found, then consider that is open"""

    file = os.path.join(self.name,"_folder_opening_")

    if (not os.path.exists(file)):
        return True

    with open(file, 'r') as f:
        statement = f.read()

    return eval(statement)


class SCATTER5_PR_library(bpy.types.PropertyGroup):
    """bpy.context.window_manager.scatter5.library"""

    #name == path 
    name : bpy.props.StringProperty()

    #generic information
    type : bpy.props.StringProperty() #type of element: Folder|Biome|Online
    user_name : bpy.props.StringProperty()  
    keywords : bpy.props.StringProperty()
    author : bpy.props.StringProperty()
    website : bpy.props.StringProperty()
    description : bpy.props.StringProperty()

    ##'Online' element: info
    estimated_density : bpy.props.FloatProperty(default=-1)
    layercount : bpy.props.IntProperty()

    #'Online' element: filled if .jpg of biome found 
    icon : bpy.props.StringProperty() #iconpath

    #Special for 'Online' element
    messages : bpy.props.StringProperty() #for "Online" : message list used when clicking on online biome type 
    is_info : bpy.props.BoolProperty(default=False) #for "Online" : used to display other icon if info
    user_has : bpy.props.BoolProperty(default=False)
    greyed_out : bpy.props.BoolProperty() #useful to announce something to come soon

    #special for 'Folder' element
    level : bpy.props.IntProperty()
    is_open : bpy.props.BoolProperty(get=get_is_open,set=set_is_open)


class SCATTER5_PR_folder_navigation(bpy.types.PropertyGroup):
    """bpy.context.window_manager.scatter5.folder_navigation
    propgroup derrived from list above, constatly rebuilt for interface purpose"""

    name : bpy.props.StringProperty()
    level : bpy.props.IntProperty()
    is_open : bpy.props.BoolProperty()
    is_dead_end : bpy.props.BoolProperty()
    elements_count : bpy.props.IntProperty()
    icon : bpy.props.StringProperty()


# oooooooooo.               o8o  oooo        .o8       oooooooooooo oooo                                                        .
# `888'   `Y8b              `"'  `888       "888       `888'     `8 `888                                                      .o8
#  888     888 oooo  oooo  oooo   888   .oooo888        888          888   .ooooo.  ooo. .oo.  .oo.    .ooooo.  ooo. .oo.   .o888oo  .oooo.o
#  888oooo888' `888  `888  `888   888  d88' `888        888oooo8     888  d88' `88b `888P"Y88bP"Y88b  d88' `88b `888P"Y88b    888   d88(  "8
#  888    `88b  888   888   888   888  888   888        888    "     888  888ooo888  888   888   888  888ooo888  888   888    888   `"Y88b.
#  888    .88P  888   888   888   888  888   888        888       o  888  888    .o  888   888   888  888    .o  888   888    888 . o.  )88b
# o888bood8P'   `V88V"V8P' o888o o888o `Y8bod88P"      o888ooooood8 o888o `Y8bod8P' o888o o888o o888o `Y8bod8P' o888o o888o   "888" 8""888P'

#Build whole props-collection of libraries


def biome_in_subpaths(path):
    """check if there's some biomes down this path"""
    for p in utils.path_utils.get_subpaths(path):
        if p.endswith(".biome"):
            return True
    return False


def recur_biomes_mapping(mapping=[], path="", level=0):
    """will map a path folder biome structure with basic information"""

    #ignore if no biomes elements found
    if (not biome_in_subpaths(path)):
        return None

    mapping.append({"path":path,"level":level,"type":"Folder",})

    for p in os.listdir(path): #order of list generated by listdir is important..
        p = os.path.join(path,p)

        if os.path.isfile(p):
            if p.endswith(".biome"): 
                mapping.append({ "path":p, "level":level, "type":"???",})
                #type will be assigned can either be a Biome or Online element 

        elif os.path.isdir(p):
            recur_biomes_mapping(mapping=mapping, path=p, level=level+1)

        continue

    return None 


def rebuild_library():
    """fill  scatter5.library collection property with information about the library: biomes, folder or market elements
    the library will then be read directly in the grid_flow() layout """

    wm = bpy.context.window_manager

    #remove all existing items from lib
    for _ in range(len(wm.scatter5.library)):
        wm.scatter5.library.remove(0)

    #Recur all folder and files within library for navigation
    ElementsMapping = []
    recur_biomes_mapping(mapping=ElementsMapping, path=directories.lib_biomes,) #gather everything in ../_biomes_
    recur_biomes_mapping(mapping=ElementsMapping, path=directories.lib_market,) #also gather previews from ../_market_

    #library navigation = list every folder & files
    for element in ElementsMapping:
        e = wm.scatter5.library.add()

        #add basic information needed for navigation
        e.name  = element["path"] #/!\ we are storing path, using os.basename to show name in GUI
        e.level = element["level"] #used in folder navigation for spacing gui 
        e.type  = element["type"] #assign if type is folder, if not re-assign later 
        
        #folder element do not need all info below
        if (e.type=="Folder"):
            continue

        #find an icon if it exists right next to .biome file? 
        icon_path = e.name.replace(".biome",".jpg")
        if (os.path.exists(icon_path)):
            e.icon = icon_path #show icon preview in layout.grid_flow()

        #read information detained in .biome json file and transfer them in our element 
        with open(e.name) as f:
            try:
                d = json.load(f)
                d_inf = d["info"]
            except Exception as Error:
                print("")
                print("/!\\ GEO-SCATTER BIOME MANAGER WARNING /!\\")
                print("    There was a .biome file with bad .json encoding!")
                print("    Path: "+e.name)
                print("    Error message:")
                print(Error)
                print("")
                continue

        if ("type" in d_inf):
            e.type = d_inf.get("type")

        if ("name" in d_inf):
            e.user_name = d_inf.get("name")
        else:
            e.user_name = ".".join(os.path.basename(e.name).replace("_"," ").title().split(".")[:-1])

            #we might use '#' to manage order for ex online element, please ignore everything left of '#' (being indexes)
            if ("#" in e.user_name):
                e.user_name = e.user_name.split("#")[-1]

        if ("author" in d_inf):
            e.author = d_inf.get("author") 

        if ("website" in d_inf):
            e.website  = d_inf.get("website")

        if ("estimated_density" in d_inf):
            e.estimated_density = d_inf.get("estimated_density")

        if ("layercount" in d_inf):
            e.layercount = d_inf.get("layercount")

        if ("description" in d_inf):
            e.description = d_inf.get("description")

        if ("messages" in d_inf):
            e.messages = d_inf.get("messages")
            if (type(e.messages) is list):
                e.messages = "_#_".join(e.messages)

        if ("keywords" in d_inf):
            
            if (type(d_inf.get("keywords")) is list):
                  e.keywords = ",".join(d_inf.get("keywords"))
            else: e.keywords = d_inf.get("keywords") 
                
            #add a few automatic keywords 

            if (e.type not in e.keywords):
                e.keywords+= f",{e.type}"
            
            if (e.layercount==1) and ("Layer" not in e.keywords):
                e.keywords+= f",Single,Layer"
            elif (e.layercount>1):
                e.keywords+= f",Multi,Aio"

            if (e.author not in e.keywords):
                e.keywords+= f",{e.author}"

            if (e.user_name not in e.keywords):
                e.keywords+= f",{e.user_name}"

        if (e.type=="Online"):
            try:
                user_has_file = os.path.basename(e.name).replace(".biome",".userhave").split('#')[1]
                e.user_has = os.path.exists(os.path.join(directories.lib_userhas,user_has_file))
            except:
                e.user_has = False

            if ("is_info" in d_inf):
                e.is_info  = d_inf.get("is_info")

            if ("greyed_out" in d_inf):
                e.greyed_out = d_inf.get("greyed_out")

        continue 

    return 


# oooooooooo.               o8o  oooo        .o8       ooooooooo.                                   o8o
# `888'   `Y8b              `"'  `888       "888       `888   `Y88.                                 `"'
#  888     888 oooo  oooo  oooo   888   .oooo888        888   .d88' oooo d8b  .ooooo.  oooo    ooo oooo   .ooooo.  oooo oooo    ooo  .oooo.o
#  888oooo888' `888  `888  `888   888  d88' `888        888ooo88P'  `888""8P d88' `88b  `88.  .8'  `888  d88' `88b  `88. `88.  .8'  d88(  "8
#  888    `88b  888   888   888   888  888   888        888          888     888ooo888   `88..8'    888  888ooo888   `88..]88..8'   `"Y88b.
#  888    .88P  888   888   888   888  888   888        888          888     888    .o    `888'     888  888    .o    `888'`888'    o.  )88b
# o888bood8P'   `V88V"V8P' o888o o888o `Y8bod88P"      o888o        d888b    `Y8bod8P'     `8'     o888o `Y8bod8P'     `8'  `8'     8""888P'

#create previews from scat_win.library that we create above 


#need to store bpy.utils.previews here
LibPreviews = {}


def register_library_previews():
    """Register every previews for each elements of scatter5 manager library"""

    scat_win = bpy.context.window_manager.scatter5

    global LibPreviews 
    from .. resources.icons import get_previews_from_paths
    all_icons = [ e.icon for e in scat_win.library if (e.type!="Folder") and (e.icon!="") ]
    LibPreviews = get_previews_from_paths(all_icons, use_basename=False,)
    
    return


def unregister_library_previews():
    """unregister all icons of library"""

    global LibPreviews 
    from .. resources.icons import remove_previews
    remove_previews(LibPreviews)

    return 


def preview_icon(icon_path):
    """get icon id of given element.icon"""
            
    global LibPreviews 
    if (icon_path in LibPreviews):
        return LibPreviews[icon_path].icon_id

    return None


# oooooooooo.               o8o  oooo        .o8       oooooooooooo           oooo        .o8
# `888'   `Y8b              `"'  `888       "888       `888'     `8           `888       "888
#  888     888 oooo  oooo  oooo   888   .oooo888        888          .ooooo.   888   .oooo888   .ooooo.  oooo d8b
#  888oooo888' `888  `888  `888   888  d88' `888        888oooo8    d88' `88b  888  d88' `888  d88' `88b `888""8P
#  888    `88b  888   888   888   888  888   888        888    "    888   888  888  888   888  888ooo888  888
#  888    .88P  888   888   888   888  888   888        888         888   888  888  888   888  888    .o  888
# o888bood8P'   `V88V"V8P' o888o o888o `Y8bod88P"      o888o        `Y8bod8P' o888o `Y8bod88P" `Y8bod8P' d888b


def is_dead_end(path):
    """check if there's some other nested folder with some biomes in this path (for folder navigation ICON gui)"""
    
    for p in os.listdir(path):
        p = os.path.join(path,p)
        
        if (os.path.isdir(p) and biome_in_subpaths(p)):
            return False
        
    return True


def is_path_in_closed_folders(path):
    """check if the given path is located in a folder being closed in the gui"""
    
    wm = bpy.context.window_manager
    closed_elements = [ c.name for c in wm.scatter5.library if (c.type=="Folder") and (not c.is_open) ]
    
    for c in closed_elements:
        if ( (path!=c) and path.startswith(os.path.join(c,"")) ):
            return True
        
    return False


def rebuild_folder_navigation():
    """build folder navigation from biome library items
    this is constatly regenerate folder_navigation uilist based on the biome library elements"""

    wm = bpy.context.window_manager

    #clean all previous data
    wm.scatter5.folder_navigation.clear()

    for li in wm.scatter5.library:

        #we want to gather all folder
        if (li.type!="Folder"):
            continue
        #we also want to ignore the market folder, that's not for the biome library navigation 
        if ("_market_" in li.name):
            continue 
        #filter out folder in closed folder
        if is_path_in_closed_folders(li.name):
            continue 

        fo = wm.scatter5.folder_navigation.add()
        fo.name = li.name
        fo.level = li.level
        fo.is_open = li.is_open
        fo.is_dead_end = is_dead_end(fo.name)
        fo.elements_count = len([f for f in utils.path_utils.get_subpaths(fo.name) if f.endswith(".biome")])
        fo.icon = "W_FOLDER" if fo.is_dead_end else "W_FOLDER_CLOSED" if fo.is_open else "W_FOLDER_OPEN"
        
    return None


class SCATTER5_UL_folder_navigation(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):

        if (not item):
            return None

        row = layout.row(align=True)    
        row.separator(factor=item.level*1.15)

        #operator that will open/close in library then rebuild the list
        row.operator("scatter5.open_close_folder_navigation", icon_value=cust_icon(item.icon), emboss=False, depress=True, text="").path = item.name

        basename = os.path.basename(item.name)
        if (basename=="_biomes_"):
            basename=translate("All")
        row.label(text=basename)

        return None


class SCATTER5_OT_open_close_folder_navigation(bpy.types.Operator):

    bl_idname      = "scatter5.open_close_folder_navigation"
    bl_label       = translate("Open/Close this Folder")
    bl_description = translate("Hold [ALT] to open this folder in your File Explorer")
    bl_options     = {'REGISTER', 'INTERNAL'}

    path : bpy.props.StringProperty()

    def execute(self, context):

        event = get_event()

        if (event.ctrl):
            bpy.ops.scatter5.open_directory(folder=self.path)
            return {'FINISHED'}

        wm = bpy.context.window_manager
        e = wm.scatter5.library[self.path]
        e.is_open = not e.is_open #will write directly in disk

        #from library navigation, create a dynamic list that will update itself when closing/opening folder
        rebuild_folder_navigation()

        #need to move active index, otherwise index might be out of length
        for i,e in enumerate(wm.scatter5.folder_navigation):
            if (e.name==self.path):
                wm.scatter5.folder_navigation_idx = i
                break 

        bpy.context.area.tag_redraw()

        return {'FINISHED'}


# oooooooooo.                                        o8o
# `888'   `Y8b                                       `"'
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo oooo  ooo. .oo.    .oooooooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'  `888  `888P"Y88b  888' `88b
#  888      888  888      .oP"888    `88..]88..8'    888   888   888  888   888
#  888     d88'  888     d8(  888     `888'`888'     888   888   888  `88bod8P'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'     o888o o888o o888o `8oooooo.
#                                                                     d"     YD
#                                                                     "Y88888P'


def limit_string(word, limit):

    if len(word)>limit-3:
        return word[:limit-3] + "..."

    return word


def match_word(search_string, keyword_string, ):

    search_string, keyword_string = search_string.lower(), keyword_string.lower()
    terms = search_string.split(" ")

    r = []
    for w in terms:
        r.append(w in keyword_string)

    if r:
        return all(r)
    return False 


#  dP""b8 88""Yb 88 8888b.    888888 88     888888 8b    d8 888888 88b 88 888888
# dP   `" 88__dP 88  8I  Yb   88__   88     88__   88b  d88 88__   88Yb88   88
# Yb  "88 88"Yb  88  8I  dY   88""   88  .o 88""   88YbdP88 88""   88 Y88   88
#  YboodP 88  Yb 88 8888Y"    888888 88ood8 888888 88 YY 88 888888 88  Y8   88


def draw_biome_element(e, layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_op     = scat_scene.operators.load_biome

    optext = limit_string(e.user_name, addon_prefs.ui_library_typo_limit)
    opicon = "ADD"

    #add a bit of separation on top
    col = layout.column(align=True)
    col.separator(factor=0.7)

    #LargeIcon
    ixon = cust_icon("W_DEFAULT_PREVIEW") if (e.icon=="") else preview_icon(e.icon)
    itembox = col.column(align=True).box()
    itembox.template_icon( icon_value=ixon , scale=addon_prefs.ui_library_item_size )

    #Draw Biome Item Operator

    action_row = col.row(align=True)
    action_row.scale_y = 0.95

    if (scat_op.progress_context==e.name):
    
        progress = action_row.row(align=True)
        progress.ui_units_x = 4
        progress.prop(scat_op,"progress_bar",text=scat_op.progress_label,)

        return None 

    ope = action_row.row(align=True)
    ope.ui_units_x = 4
    ope.operator_context = "INVOKE_DEFAULT"
    
    #if scatter button is not enabled will need to inform user about it
    if (scat_scene.emitter is None):
        optext = translate("No Emitter") 
        opicon = "ERROR"
        ope.enabled = False
    elif (bpy.context.mode!="OBJECT"):
        optext = translate("Not Object-Mode") 
        opicon = "ERROR"
        ope.enabled = False

    load = ope.row(align=True)
    op = load.operator("scatter5.load_biome", text=optext, emboss=True, depress=False, icon=opicon)
    op.emitter_name = "" #Auto
    op.json_path = e.name
    op.single_layer = -1

    down = ope.row(align=True)
    down.scale_x = 0.95
    down.context_pointer_set("pass_ui_arg_lib_obj", e)
    down.menu("SCATTER5_MT_per_biome_main_menu", text="", icon="DOWNARROW_HLT",)

    return None


def draw_online_element(e, layout,):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    scat_scene = bpy.context.scene.scatter5

    optext = limit_string( e.user_name, addon_prefs.ui_library_typo_limit )

    #add a bit of separation on top
    col = layout.column(align=True)
    col.separator(factor=0.7)

    #LargeIcon
    ixon = cust_icon("W_DEFAULT_PREVIEW") if (e.icon=="") else preview_icon(e.icon) 
    itembox = col.column(align=True).box()
    itembox.active = not e.greyed_out
    itembox.template_icon( icon_value=ixon , scale=addon_prefs.ui_library_item_size )

    #Operations Under Icon

    #Display correct icon!
    kwargs = {"text":optext, "emboss":True}

    #Is this an info?
    if (e.is_info):
        kwargs["icon"] = "INFO"

    #do the user possess this pack? no?
    elif (not e.user_has):
        kwargs["icon_value"] = cust_icon("W_SUPERMARKET")

    #if yes then use checkmark icon
    else:
        kwargs["icon_value"] = cust_icon("W_CHECKMARK") #kwargs["icon"] = "CHECKBOX_HLT"

    #Open Url Operator
    action_row = col.row(align=True)
    action_row.scale_y = 0.95

    ope = action_row.row(align=True)
    ope.ui_units_x = 4
    load = ope.row(align=True)
    op = load.operator("wm.url_open", **kwargs)
    op.url = e.website

    return None 


# 88     88 88""Yb 88""Yb    db    88""Yb Yb  dP      dP""b8 88""Yb 88 8888b.
# 88     88 88__dP 88__dP   dPYb   88__dP  YbdP      dP   `" 88__dP 88  8I  Yb
# 88  .o 88 88""Yb 88"Yb   dP__Yb  88"Yb    8P       Yb  "88 88"Yb  88  8I  dY
# 88ood8 88 88oodP 88  Yb dP""""Yb 88  Yb  dP         YboodP 88  Yb 88 8888Y"


def draw_library_grid(self, layout): 
    """Draw user Biome Library"""

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_win    = bpy.context.window_manager.scatter5

    grid = layout.grid_flow(
        row_major=True,
        columns=0 if (addon_prefs.ui_library_adaptive_columns) else addon_prefs.ui_library_columns, 
        even_columns=False,
        even_rows=False,
        align=False,
        )

    count = 0
    for i,e in enumerate(scat_win.library):
            
        #We don't want to see any folder element here
        if (e.type=="Folder"): 
            continue

        #If element coming from _market_ just ignore
        if ("_market_" in e.name):
            continue 

        #Filter by active navigation tab 
        if not e.name.startswith(os.path.join(scat_win.folder_navigation[scat_win.folder_navigation_idx].name,"")):
            continue 

        #filter search bar? 
        if (scat_scene.library_search != ""):
            if not match_word( scat_scene.library_search, e.keywords,):
                continue 

        count += 1

        #Draw Biome Element 
        if (e.type=="Biome"):
            draw_biome_element(e, grid)
            continue

        #Draw Online Element
        elif (e.type=="Online"):
            draw_online_element(e, grid)
            continue

        continue

    #Add a few more just to space out
    if (count!=0):

        for i in range(20):

            block = grid.column()
            preview = block.column(align=True)
            block.separator(factor=0.2)
            preview.template_icon( icon_value=cust_icon("W_BLANK1") , scale=addon_prefs.ui_library_item_size )
            operator = preview.row()
            operator.label(text="")
            operator.scale_y = 0.9

        scroll = layout.row()
        scroll.operator("scatter5.scroll_to_top", text=translate("Lost? Scroll to Top"),emboss=False)

    #If nothing Found??
    if (count==0):

        if (len(scat_win.folder_navigation)==0):

            if (not biome_in_subpaths(directories.lib_biomes)):

                l = layout.column(align=True)
                l.active = False
                l.label(text=translate("Your Biome Library is Empty! The plugin is not shipped with Biomes by default."))
                
                layout.operator("scatter5.exec_line", text=translate("Get a Package"),icon_value=cust_icon("W_SUPERMARKET")).api = "scat_win.category_manager='market' ; bpy.ops.scatter5.tag_redraw()"
                layout.operator("scatter5.install_package", text=translate("Install a Package"),icon="NEWFOLDER")
                
                layout.separator()
                
                l = layout.column(align=True)
                l.active = False
                l.label(text=translate("First time using our plugin? Watcht the tutorial."))
                                
                layout.operator("wm.url_open", text=translate("Installation Tutorial"), icon="URL").url = "https://youtu.be/wDB9WDOWxlY"

            else:
                ope = layout.row()
                ope.active = False
                ope.label(text=translate("You may need to reload your library by pressing the button below"))
    
                layout.operator("scatter5.reload_biome_library", text=translate("Reload Your Biome-Library"), icon="FILE_REFRESH")

        elif (scat_scene.library_search!=""):
            badsearch = layout.row()
            badsearch.active = False
            badsearch.label(icon="VIEWZOOM", text=f'{translate("Nothing found with Keyword")}  "{scat_scene.library_search}"  {translate("In Active Folder")}')

        else:
            # Not probable at all 
            nothing = layout.column()
            nothing.active = False
            nothing.label(text="This Folder Seems to be empty!")
            nothing.label(text='"'+scat_win.folder_navigation[scat_win.folder_navigation_idx].name+'"')

    return 


#  dP"Yb  88b 88 88     88 88b 88 888888      dP""b8 88""Yb 88 8888b.
# dP   Yb 88Yb88 88     88 88Yb88 88__       dP   `" 88__dP 88  8I  Yb
# Yb   dP 88 Y88 88  .o 88 88 Y88 88""       Yb  "88 88"Yb  88  8I  dY
#  YbodP  88  Y8 88ood8 88 88  Y8 888888      YboodP 88  Yb 88 8888Y" 


def draw_online_grid(self, layout): 
    """Draw Online Store"""

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    scat_scene  = bpy.context.scene.scatter5
    scat_win    = bpy.context.window_manager.scatter5

    grid = layout.grid_flow(
        row_major=True,
        columns=0 if (addon_prefs.ui_library_adaptive_columns) else addon_prefs.ui_library_columns,
        even_columns=False,
        even_rows=False,
        align=False,
        )

    count = 0
    for i,e in enumerate(scat_win.library):
            
        #Only Show Online Items
        if (e.type!="Online"): 
            continue

        #Only Show item in market and onlin
        if ("_market_" not in e.name): 
            continue

        #Draw Element 
        draw_online_element(e, grid)

        count += 1
        continue

    # Add a few more just to space out

    if count!=0:

        for i in range(20):

            block = grid.column()
            preview = block.column(align=True)
            block.separator(factor=0.2)
            preview.template_icon( icon_value=cust_icon("W_BLANK1") , scale=addon_prefs.ui_library_item_size )
            operator = preview.row()
            operator.label(text="")
            operator.scale_y = 0.9

        scroll = layout.row()
        scroll.operator("scatter5.scroll_to_top", text=translate("Lost? Scroll to Top"),emboss=False)

    # If nothing Found : 

    if (count==0):

        youmay = layout.row()
        youmay.active = False
        youmay.label(text=translate("It seems that there's nothing in the store? Please Refresh"))

        reloading= layout.row()
        reloading.separator(factor=5)
        reloading.operator("scatter5.manual_fetch_from_git", text=translate("Refresh"), icon="FILE_REFRESH")
        reloading.separator(factor=5)

    return 


#   .oooooo.               oooo   o8o                             oooooooooooo               .             oooo
#  d8P'  `Y8b              `888   `"'                             `888'     `8             .o8             `888
# 888      888 ooo. .oo.    888  oooo  ooo. .oo.    .ooooo.        888          .ooooo.  .o888oo  .ooooo.   888 .oo.
# 888      888 `888P"Y88b   888  `888  `888P"Y88b  d88' `88b       888oooo8    d88' `88b   888   d88' `"Y8  888P"Y88b
# 888      888  888   888   888   888   888   888  888ooo888       888    "    888ooo888   888   888        888   888
# `88b    d88'  888   888   888   888   888   888  888    .o       888         888    .o   888 . 888   .o8  888   888
#  `Y8bood8P'  o888o o888o o888o o888o o888o o888o `Y8bod8P'      o888o        `Y8bod8P'   "888" `Y8bod8P' o888o o888o

#Gather Previews from github server to "_market_" Folder


def fetching_from_git():

    try: 
        print("")
        print("SCATTER5 Will Try to update the `_market_` Folder :")

        from .. resources.directories import lib_market
        last_fetch_path = os.path.join(lib_market,"last_fetch.json")


        print(f"         -Removing all files from _market_ folder...")
        for file in os.listdir(lib_market):
            os.remove(os.path.join(lib_market, file))

        url = "https://raw.githubusercontent.com/DB3D/scatter-fetch/main/_market_.zip"
        print(f"         -Downloading .zip (containting only json and image files) from github sever...")
        print(f"          {url}")
        import requests
        adress = requests.get(url)
        fetched_scatpack = os.path.join(lib_market, "_market_.zip")
        with open(fetched_scatpack, 'wb') as f:
            f.write(adress.content)

        #unzip in location
        print(f"         -Unzipping in _market_ folder location...")
        from .. resources.packaging import unzip_in_location
        unzip_in_location(fetched_scatpack,lib_market)
        
        #Update Last Fetch Infomration on disk as json file
        print(f"         -Updating `last_fetch.json` last refresh information...")
        now = datetime.now()
        dump_dict = {"year":now.year,"month":now.month,"day":now.day}
        with open(last_fetch_path, 'w') as f:
            json.dump(dump_dict, f, indent=4)

        print(f"         -Online fetch successful! Your _market_ folder is now up to date.")
        print(f"          We will now proceed to reload your library")

    except Exception as e:
        print(f"         -Couldn't connect to the internet.",e)

    return None 


def automatic_fetch():
    """Write all Previews on disk every X Days or if last_fetch_path path not found"""

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    
    def fetch_condition():

        #don't fetch if user don't allows it
        if (not addon_prefs.fetch_automatic_allow):
            return False
        
        from .. resources.directories import lib_market
        last_fetch_path = os.path.join(lib_market,"last_fetch.json")

        #Fetch if no last_fetch.json file
        if (not os.path.exists(last_fetch_path)):
            return True

        #try to get last fetch date
        try:
            now = datetime.now()
            with open(last_fetch_path) as f:
                date_dict = json.load(f)
                last_date = date(date_dict["year"], date_dict["month"], date_dict["day"])
            current_date = date(now.year, now.month, now.day)
            delta = current_date - last_date
            
        #if failed due to json corrupted, recreate file
        except Exception as e:
            print("We couldn't update your scatpack previews!\nWhile trying to get the last date, an error occured:")
            print(e)
            return False

        #if older fetch fit time criteria, fetch again
        if (delta.days>=addon_prefs.fetch_automatic_daycount):
            print(f"SCATTER5 `_market_` Folder Last Fetch: {delta.days} days ago")
            return True
        
        return False

    if fetch_condition():
        fetching_from_git()

    return None 


class SCATTER5_OT_manual_fetch_from_git(bpy.types.Operator):

    bl_idname      = "scatter5.manual_fetch_from_git"
    bl_label       = "manual_fetch_from_git"
    bl_description = ""
    bl_options     = {'INTERNAL'}

    def execute(self, context):
                
        fetching_from_git()
        bpy.ops.scatter5.reload_biome_library()
        
        return {'FINISHED'}



# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.   .oooooooo
#  888ooo88P'  d88' `88b 888' `88b
#  888`88b.    888ooo888 888   888
#  888  `88b.  888    .o `88bod8P'
# o888o  o888o `Y8bod8P' `8oooooo.
#                        d"     YD
#                        "Y88888P'


class SCATTER5_OT_reload_biome_library(bpy.types.Operator):

    bl_idname  = "scatter5.reload_biome_library"
    bl_label   = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        unregister()
        register()
        return {'FINISHED'}


def register():

    #fetch from github in "_market_" folder, this won't happend that often
    automatic_fetch()

    #build library item list from directories
    rebuild_library()

    #from scatter5.library, load all previews
    register_library_previews()

    #from scatter5.library, create a dynamic list that will update itself when closing/opening folder
    rebuild_folder_navigation()

    return 


def unregister():

    unregister_library_previews()

    return 


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_UL_folder_navigation,

    SCATTER5_OT_reload_biome_library,
    SCATTER5_OT_open_close_folder_navigation,

    SCATTER5_OT_manual_fetch_from_git,

    )
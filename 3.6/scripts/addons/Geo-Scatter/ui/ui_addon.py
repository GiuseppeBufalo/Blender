

#####################################################################################################
#
# ooooo     ooo ooooo            .o.             .o8        .o8
# `888'     `8' `888'           .888.           "888       "888
#  888       8   888           .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.
#  888       8   888          .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b
#  888       8   888         .88ooo8888.   888   888  888   888  888   888  888   888
#  `88.    .8'   888        .8'     `888.  888   888  888   888  888   888  888   888
#    `YbodP'    o888o      o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o
#
#####################################################################################################


import bpy, os, platform 

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. utils.str_utils import word_wrap, square_area_repr, count_repr

from . import ui_templates


# ooo        ooooo            o8o                         .o.             .o8        .o8
# `88.       .888'            `"'                        .888.           "888       "888
#  888b     d'888   .oooo.   oooo  ooo. .oo.            .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b          .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b
#  8  `888'   888   .oP"888   888   888   888         .88ooo8888.   888   888  888   888  888   888  888   888
#  8    Y     888  d8(  888   888   888   888        .8'     `888.  888   888  888   888  888   888  888   888
# o8o        o888o `Y888""8o o888o o888o o888o      o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o


def draw_addon(self,layout):
    """drawing dunction of AddonPrefs class, stored in properties"""

    row = layout.row()
    r1 = row.separator()
    col = row.column()
    r3 = row.separator()
        
    #Enter Manager 

    col.label(text=translate("Enter Geo-Scatter Manager."),)

    enter = col.row()
    enter.scale_y = 1.5
    enter.operator("scatter5.impost_addonprefs",text=translate("Enter Manager"),icon_value=cust_icon('W_SCATTER')).state = True

    col.separator(factor=1.5)

    #Write license block 

    license_path = directories.addon_license_type

    col.label(text=translate("Geo-Scatter Product: License Agreement."),)
    
    box = col.box()
    word_wrap(layout=box, max_char=81, alert=False, active=False, string="Geo-Scatter is comprised of two programs working together: a python script released under the GNU GPL and a geometry-node algorithm called the “GEO-SCATTER ENGINE” with a license similar to Royalty free licensing. By using Geo-Scatter, users agree to the terms and conditions of both licenses. Only licenses downloaded from the official source listed on “www.geoscatter.com/download” are legitimate. Compared to the Royalty Free license, the “GEO-SCATTER ENGINE” end user license agreement provides an additional advantage by allowing users to share Blender scenes using the algorithm, while also placing restrictions on how users may interact with the algorithm through the usage of scripts or plugins.",)
    box.operator("wm.url_open", text="Both licenses can be found on “www.geoscatter.com/legal”", emboss=True, )

    is_individual = os.path.exists(os.path.join(license_path,"1.txt"))
    if (is_individual):
        col.separator(factor=1.5)
        col.label(text=translate("Geo-Scatter Engine: Individual License."),)
        box = col.box()
        word_wrap(layout=box, max_char=81, alert=False, active=False, string="The “Individual” license for “GEO-SCATTER ENGINE” is a non-transferable license that grants a single user the right to use the “GEO-SCATTER ENGINE” on any computer they own for either personal or professional use. This license requires a one-time fee and is subject to the terms and conditions outlined in the agreement found on “www.geoscatter.com/legal”. This license grants the licensee the permission to interact with our engine through the use of the “Geo-Scatter” plugin.",)
        box.operator("wm.url_open", text="This agreement is available on “www.geoscatter.com/legal”", emboss=True, )
    
    is_team = os.path.exists(os.path.join(license_path,"2.txt"))
    if (is_team):
        col.separator(factor=1.5)
        col.label(text=translate("Geo-Scatter Engine: Team License."),)
        box = col.box()
        word_wrap(layout=box, max_char=81, alert=False, active=False, string="The “Team” license for “GEO-SCATTER ENGINE” permits up to six users who belong to the same team or organization to use the “GEO-SCATTER ENGINE” on up to six computers. This license is transferable within the same organization but not to other organizations or individuals. A one-time fee is required for this license, and it is subject to the terms and conditions outlined in the agreement found on “www.geoscatter.com/legal”. This license grants licensee(s) the permission to interact with our engine through the use of the “Geo-Scatter” plugin.",)
        box.operator("wm.url_open", text="This agreement is available on “www.geoscatter.com/legal”", emboss=True, )
    
    is_studio = os.path.exists(os.path.join(license_path,"3.txt"))
    if (is_studio):
        col.separator(factor=1.5)
        col.label(text=translate("Geo-Scatter Engine: Studio License."),)
        box = col.box()
        word_wrap(layout=box, max_char=81, alert=False, active=False, string="The “Studio” license for “GEO-SCATTER ENGINE” allows every employee of a business to use the “GEO-SCATTER ENGINE” on an unlimited number of computers. Like the “Team” license, this license is transferable within the same organization but not to other organizations or individuals. A one-time fee is required for this license, and it is subject to the terms and conditions outlined in the agreement found on “www.geoscatter.com/legal”. This license grants licensee(s) permission to interact with our engine using official or custom scripts/plugins.",)
        box.operator("wm.url_open", text="This agreement is available on “www.geoscatter.com/legal”", emboss=True, )
    
    col.separator(factor=1.5)
    col.label(text=translate("Contact Information:"),)
    box = col.box()
    word_wrap(layout=box, max_char=81, alert=False, active=False, string="If you have any inquiries or any questions, you may contact us via “contact@geoscatter.com” or through our diverse social medial lised on “www.geoscatter.com” or within this very plugin.",)
    box.operator("wm.url_open", text="Visit “www.geoscatter.com", emboss=True, )

    disclaimer = col.column()
    disclaimer.separator(factor=0.7)
    disclaimer.active = True
    disclaimer.label(text="*Extend this interface if the texts are not readable.",)

    col.separator(factor=2)

    return None


# ooooo   ooooo  o8o   o8o                     oooo         o8o
# `888'   `888'  `"'   `"'                     `888         `"'
#  888     888  oooo  oooo  .oooo.    .ooooo.   888  oooo  oooo  ooo. .oo.    .oooooooo
#  888ooooo888  `888  `888 `P  )88b  d88' `"Y8  888 .8P'   `888  `888P"Y88b  888' `88b
#  888     888   888   888  .oP"888  888        888888.     888   888   888  888   888
#  888     888   888   888 d8(  888  888   .o8  888 `88b.   888   888   888  `88bod8P'
# o888o   o888o o888o  888 `Y888""8o `Y8bod8P' o888o o888o o888o o888o o888o `8oooooo.
#                      888                                                   d"     YD
#                  .o. 88P                                                   "Y88888P'
#                  `Y888P


def addonpanel_overridedraw(self,context):
    """Impostor Main"""

    layout = self.layout

    scat_win = bpy.context.window_manager.scatter5

    #Prefs
    if (scat_win.category_manager=="prefs"):
        draw_add_prefs(self, layout)

    elif (scat_win.category_manager=="library"):
        from . biome_library import draw_library_grid
        draw_library_grid(self, layout)

    elif (scat_win.category_manager=="market"):
        from . biome_library import draw_online_grid
        draw_online_grid(self, layout)

    elif (scat_win.category_manager=="stats"):
        draw_stats(self, layout)

    return None

            
def addonheader_overridedraw(self, context):
    """Impostor Header"""

    layout = self.layout

    scat_win = bpy.context.window_manager.scatter5

    row = layout.row()
    row.template_header()

    scat = row.row(align=True)
    scat.scale_x = 1.1
    scat.menu("SCATTER5_MT_manager_header_menu_scatter", text="Geo-Scatter",icon_value=cust_icon('W_SCATTER'))

    if (scat_win.category_manager=="library"):
        row.menu("SCATTER5_MT_manager_header_menu_open", text=translate("File"),)
        row.menu("SCATTER5_MT_manager_header_menu_biome_interface", text=translate("Interface"),)
        popover = row.row(align=True)
        popover.emboss = "NONE"
        popover.popover(panel="SCATTER5_PT_creation_operator_load_biome",text="Settings" ,)

    elif (scat_win.category_manager=="market"):
        row.menu("SCATTER5_MT_manager_header_menu_open", text=translate("File"),)
        row.menu("SCATTER5_MT_manager_header_menu_biome_interface", text=translate("Interface"),)

    elif (scat_win.category_manager=="prefs"):
        row.menu("USERPREF_MT_save_load", text=translate("Preferences"),)

    elif (scat_win.category_manager=="stats"):
        row.menu("SCATTER5_MT_manager_header_menu_operations", text=translate("Operations"),)

    layout.separator_spacer()

    if (scat_win.category_manager=="stats"):
        layout.popover(panel="SCATTER5_PT_manager_header_menu_stats_filter",text=translate("Filter"),icon='FILTER',)

    exit = layout.column()
    exit.alert = True
    exit.operator("scatter5.impost_addonprefs",text=translate("Exit"),icon='PANEL_CLOSE').state = False

    return None


def addonnavbar_overridedraw(self, context):
    """importor T panel"""

    layout = self.layout

    scat_scene = bpy.context.scene.scatter5
    scat_win = bpy.context.window_manager.scatter5

    #Close if user is dummy 

    if (not context.space_data.show_region_header):
        exit = layout.column()
        exit.alert = True
        exit.operator("scatter5.impost_addonprefs",text=translate("Exit"),icon='PANEL_CLOSE').state = False
        exit.scale_y = 1.8
        return None

    #Draw main categories 

    enum = layout.column()
    enum.scale_y = 1.3
    enum.prop(scat_win,"category_manager",expand=True)

    layout.separator(factor=5)

    #Per category T panel

    if (scat_win.category_manager=="library"):

        #layout.label(text=translate("Search")+" :")

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.prop(scat_scene,"library_search",icon="VIEWZOOM",text="") 

        layout.separator(factor=0.33)

        #layout.label(text=translate("Navigate")+" :")

        wm = bpy.context.window_manager
        navigate = layout.column()
        navigate.scale_y = 1
        navigate.template_list("SCATTER5_UL_folder_navigation", "", wm.scatter5, "folder_navigation", wm.scatter5, "folder_navigation_idx",rows=20,)

        lbl = navigate.column()
        lbl.scale_y = 0.8
        lbl.active = False
        lbl.separator()

        elements_count = 0 
        if (len(scat_win.folder_navigation)!=0):
            elements_count = scat_win.folder_navigation[scat_win.folder_navigation_idx].elements_count

        lbl.label(text=f'{elements_count} {translate("Elements in Folder")}')
        
        #lbl.separator(factor=2)
        #lbl.label(text=translate("Need more?"))
        #lbl.operator("scatter5.exec_line",text=translate("Check out what's available"),emboss=False).api = 'scat_win.category_manager = "market" ; bpy.context.area.tag_redraw()'

    elif (scat_win.category_manager=="market"):
        pass

    elif (scat_win.category_manager=="stats"):
        pass

    elif (scat_win.category_manager=="prefs"):
        pass

    return None


# 88  88 88  88888    db     dP""b8 88  dP      dP"Yb  88""Yb 888888 88""Yb    db    888888  dP"Yb  88""Yb
# 88  88 88     88   dPYb   dP   `" 88odP      dP   Yb 88__dP 88__   88__dP   dPYb     88   dP   Yb 88__dP
# 888888 88 o.  88  dP__Yb  Yb      88"Yb      Yb   dP 88"""  88""   88"Yb   dP__Yb    88   Yb   dP 88"Yb
# 88  88 88 "bodP' dP""""Yb  YboodP 88  Yb      YbodP  88     888888 88  Yb dP""""Yb   88    YbodP  88  Yb


class SCATTER5_OT_impost_addonprefs(bpy.types.Operator):
    """Monkey patch drawing code of addon preferences to our own code, temporarily"""

    bl_idname      = "scatter5.impost_addonprefs"
    bl_label       = ""
    bl_description = translate("replace/restore native blender preference ui by custom scatter manager ui")

    state : bpy.props.BoolProperty()

    Status = False
    AddonPanel_OriginalDraw = None
    AddonNavBar_OriginalDraw = None
    AddonHeader_OriginalDraw = None

    def panel_hijack(self):
        """register impostors"""

        cls = type(self)
        if (cls.Status==True):
            return None

        #show header just in case user hided it (show/hide header on 'PREFERENCE' areas)

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if (area.type == 'PREFERENCES'):
                    for space in area.spaces:
                        if (space.type == 'PREFERENCES'):
                            space.show_region_header = True

        #Save Original Class Drawing Function in global , and replace their function with one of my own 

        cls.AddonPanel_OriginalDraw = bpy.types.USERPREF_PT_addons.draw
        bpy.types.USERPREF_PT_addons.draw = addonpanel_overridedraw
            
        cls.AddonNavBar_OriginalDraw = bpy.types.USERPREF_PT_navigation_bar.draw
        bpy.types.USERPREF_PT_navigation_bar.draw = addonnavbar_overridedraw
        
        cls.AddonHeader_OriginalDraw = bpy.types.USERPREF_HT_header.draw
        bpy.types.USERPREF_HT_header.draw = addonheader_overridedraw
        
        cls.Status=True

        return None

    def panel_restore(self):
        """restore and find original drawing classes"""

        cls = type(self)
        if (cls.Status==False):
            return None

        #restore original drawing code 
        
        bpy.types.USERPREF_PT_addons.draw = cls.AddonPanel_OriginalDraw
        cls.AddonPanel_OriginalDraw = None 

        bpy.types.USERPREF_PT_navigation_bar.draw = cls.AddonNavBar_OriginalDraw
        cls.AddonNavBar_OriginalDraw = None 

        bpy.types.USERPREF_HT_header.draw = cls.AddonHeader_OriginalDraw
        cls.AddonHeader_OriginalDraw = None 

        #Trigger Redraw, otherwise some area will be stuck until user put cursor 

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if (area.type == 'PREFERENCES'):
                    area.tag_redraw()
                    
        cls.Status=False

        return None

    def execute(self, context):

        if (self.state==True):
              self.panel_hijack()
        else: self.panel_restore()

        return{'FINISHED'}


# oooooooooo.                                        ooooo     ooo                              ooooooooo.                       .o88o.
# `888'   `Y8b                                       `888'     `8'                              `888   `Y88.                     888 `"
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo   888       8   .oooo.o  .ooooo.  oooo d8b   888   .d88' oooo d8b  .ooooo.  o888oo   .oooo.o
#  888      888 `888""8P `P  )88b   `88. `88.  .8'    888       8  d88(  "8 d88' `88b `888""8P   888ooo88P'  `888""8P d88' `88b  888    d88(  "8
#  888      888  888      .oP"888    `88..]88..8'     888       8  `"Y88b.  888ooo888  888       888          888     888ooo888  888    `"Y88b.
#  888     d88'  888     d8(  888     `888'`888'      `88.    .8'  o.  )88b 888    .o  888       888          888     888    .o  888    o.  )88b
# o888bood8P'   d888b    `Y888""8o     `8'  `8'         `YbodP'    8""888P' `Y8bod8P' d888b     o888o        d888b    `Y8bod8P' o888o   8""888P'



def draw_add_prefs(self, layout):
    
    #limit panel width

    row = layout.row()
    row.alignment="LEFT"
    main = row.column()
    main.alignment = "LEFT"

    draw_add_packs(self,main)
    ui_templates.separator_box_out(main)

    draw_add_environment(self,main)
    ui_templates.separator_box_out(main)

    draw_add_paths(self,main)
    ui_templates.separator_box_out(main)

    draw_add_fetch(self,main)
    ui_templates.separator_box_out(main)

    draw_add_browser(self,main)
    ui_templates.separator_box_out(main)

    #draw_add_lang(self,main)
    #ui_templates.separator_box_out(main)
    
    draw_add_npanl(self,main)
    ui_templates.separator_box_out(main)

    draw_add_workflow(self,main)
    ui_templates.separator_box_out(main)

    draw_add_customui(self,main)
    ui_templates.separator_box_out(main)

    draw_add_shortcut(self,main)
    ui_templates.separator_box_out(main)

    draw_add_dev(self,main)
    ui_templates.separator_box_out(main)
            
    for i in range(10):
        layout.separator_spacer()

    return None 


def draw_add_packs(self,layout):

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_packs", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_packs";UI_BOOL_VAL:"1"
        icon = "NEWFOLDER", 
        name = translate("Install a Package"),
        doc_panel = "SCATTER5_PT_docs", 
        popover_argument = "ui_add_packs", #REGTIME_INSTRUCTION:POPOVER_PROP:"ui_add_packs"
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            rwoo = col.row()
            rwoo.operator("scatter5.install_package", text=translate("Install a Package"), icon="NEWFOLDER")
            scatpack = rwoo.row()
            scatpack.operator("scatter5.exec_line", text=translate("Find Biomes Online"),icon_value=cust_icon("W_SUPERMARKET")).api = "scat_win.category_manager='market' ; bpy.ops.scatter5.tag_redraw()"

            ui_templates.separator_box_in(box)

    return None


def draw_add_fetch(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_fetch", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_fetch";UI_BOOL_VAL:"1"
        icon = "URL", 
        name = translate("Scatpack Previews Fetch"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            ui_templates.bool_toggle(col, 
                prop_api=addon_prefs,
                prop_str="fetch_automatic_allow", 
                label=translate("Automatically Fetch Biome Previews from Web."), 
                icon="FILE_REFRESH", 
                left_space=False,
                )
            
            col.separator()
            row = col.row()
            #
            subr = row.row()
            subr.active = addon_prefs.fetch_automatic_allow
            subr.prop(addon_prefs, "fetch_automatic_daycount", text=translate("Fetch every n Day"),)
            #
            subr = row.row()
            subr.operator("scatter5.manual_fetch_from_git", text=translate("Refresh Online Previews"), icon="FILE_REFRESH")

            ui_templates.separator_box_in(box)
    
    return None

    
def draw_add_browser(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_browser", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_browser";UI_BOOL_VAL:"1"
        icon = "ASSET_MANAGER", 
        name = translate("Asset Browser Convert"),
        doc_panel = "SCATTER5_PT_docs", 
        popover_argument = "ui_add_browser", #REGTIME_INSTRUCTION:POPOVER_PROP:"ui_add_browser"
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
            
            col.operator("scatter5.make_asset_library", text=translate("Convert blend(s) in folder"), icon="FILE_BLEND",)
                
            col.separator(factor=0.5)
            word_wrap(layout=col, max_char=70, alert=False, active=True, string=translate("Warning, this operator will quit this session to sequentially open all blends and marks their asset(s). Please do not interact with the interface until the task is finished.."),)

            ui_templates.separator_box_in(box)
    
    return None


def draw_add_lang(self,layout):

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_lang", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_lang";UI_BOOL_VAL:"1"
        icon = "WORLD_DATA", 
        name = translate("Languages"),
        )
    if is_open: 

            box.label(text="TODO create .excel sheet, separate it per column into single column file, create enum from single column, make enum then made translate() fct work on restart")

            txt = box.column()
            txt.scale_y = 0.8
            txt.label(text="Supported Languages:")
            txt.label(text="        -English")
            txt.label(text="        -Spanish")
            txt.label(text="        -French")
            txt.label(text="        -Japanese")
            txt.label(text="        -Chinese (Simplified)")

            ui_templates.separator_box_in(box)

    return None 


def draw_add_npanl(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_npanl", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_npanl";UI_BOOL_VAL:"1"
        icon = "MENU_PANEL", 
        name = translate("N Panel Name"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            ope = col.row()
            ope.alert = (addon_prefs.tab_name in [""," ","  "])
            ope.prop(addon_prefs,"tab_name",text="")
            
            ui_templates.separator_box_in(box)

    return None


def draw_add_paths(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_paths", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_paths";UI_BOOL_VAL:"1"
        icon = "FILEBROWSER", 
        name = translate("Scatter-Library Location"),
        doc_panel = "SCATTER5_PT_docs", 
        popover_argument = "ui_add_paths", #REGTIME_INSTRUCTION:POPOVER_PROP:"ui_add_paths"
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
                
            is_library = os.path.exists(addon_prefs.library_path)
            is_biomes  = os.path.exists(os.path.join(addon_prefs.library_path,"_biomes_"))
            is_presets = os.path.exists(os.path.join(addon_prefs.library_path,"_presets_"))
            is_bitmaps = os.path.exists(os.path.join(addon_prefs.library_path,"_bitmaps_"))

            colc = col.column(align=True)

            pa = colc.row(align=True)
            pa.alert = not is_library
            pa.prop(addon_prefs,"library_path",text="")

            if ( False in (is_library, is_biomes, is_presets,) ):

                colc.separator(factor=0.7)

                warn = colc.column(align=True)
                warn.scale_y = 0.9
                warn.alert = True
                warn.label(text=translate("There's problem(s) with the location you have chosen"),icon="ERROR")
                
                if (not is_library):
                    warn.label(text=" "*10 + translate("-The chosen path does not exists"))
                if (not is_biomes):
                    warn.label(text=" "*10 + translate("-'_biomes_' Directory not Found"))
                if (not is_presets):
                    warn.label(text=" "*10 + translate("-'_presets_' Directory not Found"))
                if (not is_bitmaps):
                    warn.label(text=" "*10 + translate("-'_bitmaps_' Directory not Found"))

                warn.label(text=translate("Geo-Scatter will use the default library location instead"),icon="BLANK1")

            if all([ is_library, is_biomes, is_presets, is_bitmaps]) and (directories.lib_library!=addon_prefs.library_path):
                colc.separator(factor=0.7)

                warn = colc.column(align=True)
                warn.scale_y = 0.85
                warn.label(text=translate("Chosen Library is Valid, Please save your addonprefs and restart blender."),icon="CHECKMARK")

            col.separator()

            row = col.row()
            col1 = row.column()
            col1.operator("scatter5.reload_biome_library", text=translate("Reload Library"), icon="FILE_REFRESH")
            col1.operator("scatter5.reload_preset_gallery", text=translate("Reload Presets"), icon="FILE_REFRESH")
            col1.operator("scatter5.dummy", text=translate("Reload Images"), icon="FILE_REFRESH")

            col2 = row.column()
            col2.operator("scatter5.open_directory", text=translate("Open Library"),icon="FOLDER_REDIRECT").folder = directories.lib_library
            col2.operator("scatter5.open_directory", text=translate("Open Default Library"),icon="FOLDER_REDIRECT").folder = directories.lib_default
            col2.operator("scatter5.open_directory", text=translate("Open Blender Addons"),icon="FOLDER_REDIRECT").folder = directories.blender_addons                    
            
            ui_templates.separator_box_in(box)

    return None 


def draw_add_environment(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_environment", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_environment";UI_BOOL_VAL:"1"
        icon = "LONGDISPLAY", 
        name = translate("Biomes Environment Paths"),
        doc_panel = "SCATTER5_PT_docs", 
        popover_argument = "ui_add_environment", #REGTIME_INSTRUCTION:POPOVER_PROP:"ui_add_environment"
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            ui_templates.bool_toggle(col,
                prop_api=addon_prefs,
                prop_str="blend_environment_path_asset_browser_allow", 
                label=translate("Search for .blend in asset-library paths"),
                icon="ASSET_MANAGER",
                left_space=False,
                )

            if (addon_prefs.blend_environment_path_asset_browser_allow):

                col.separator(factor=0.5)
                alcol = col.box().column()

                if (len(bpy.context.preferences.filepaths.asset_libraries)!=0):

                    for l in bpy.context.preferences.filepaths.asset_libraries:

                        row = alcol.row()
                        row.enabled = False
                        row.prop(l,"path", text="")

                        continue
                else:
                    row = alcol.row(align=True)
                    row.active = False
                    row.label(text=translate("No Path(s) Found"))

                col.separator(factor=0.5)

            ui_templates.bool_toggle(col,
                prop_api=addon_prefs,
                prop_str="blend_environment_path_allow",
                label=translate("Search for .blend in given paths"),
                icon="FILE_BLEND",
                left_space=False,
                )

            if (addon_prefs.blend_environment_path_allow):

                col.separator(factor=0.5)

                alcocol = col.column(align=True)
                alcol = alcocol.box().column()

                #property interface

                if (len(addon_prefs.blend_environment_paths)!=0):

                    for l in addon_prefs.blend_environment_paths:

                        row = alcol.row(align=True)

                        path = row.row(align=True)
                        path.alert = not os.path.exists(l.blend_folder)
                        path.prop(l, "blend_folder", text="", )

                        #find index for remove operator
                        for i,p in enumerate(addon_prefs.blend_environment_paths):
                            if (p.name==l.name):
                                break
                        
                        op = row.operator("scatter5.exec_line", text="", icon="TRASH",)
                        op.api = f"addon_prefs.blend_environment_paths.remove({i})"

                        continue

                else:
                    row = alcol.row(align=True)
                    row.active = False
                    row.label(text=translate("No Path(s) Found"))

                    
                #add button 

                addnew = alcocol.row(align=True)
                addnew.scale_y = 0.85
                op = addnew.operator("scatter5.exec_line", text=translate("New Path"), icon="ADD", depress=False)
                op.api = "n = addon_prefs.blend_environment_paths.add() ; n.name=str(len(addon_prefs.blend_environment_paths)-1)"
                
                #too much nest warnings

                for p in addon_prefs.blend_environment_paths:
                    if (p.high_nest):

                        col.separator(factor=1.0)
                        alcol = col.column(align=True)
                        alcol.scale_y = 0.9
                        alcol.alert = True

                        word_wrap(layout=alcol, max_char=65, alert=True, active=True, icon="INFO", string=translate("Warning, some path(s) seems to contain a lot of folders? Our plugin will only search for files in the first two level of folders"),)
                        break 

                col.separator(factor=0.5)

            ui_templates.separator_box_in(box)

    return None


def draw_add_workflow(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_workflow", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_workflow";UI_BOOL_VAL:"1"
        icon = "W_SCATTER", 
        name = translate("Workflow"),
        doc_panel = "SCATTER5_PT_docs", 
        popover_argument = "ui_add_workflow", #REGTIME_INSTRUCTION:POPOVER_PROP:"ui_add_workflow"
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            emitmethod = col.column(align=True)
            emitmethod.label(text=translate("Emitter Swapping:"))
            emit_prop = emitmethod.column() 
            emit_prop.scale_y = 1.0
            emit_prop.prop(addon_prefs,"emitter_method",expand=False, text="",)

            ui_templates.separator_box_in(box)

    return None
    

def draw_add_shortcut(self,layout):

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_shortcut", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_shortcut";UI_BOOL_VAL:"1"
        icon = "EVENT_TAB", 
        name = translate("Shortcuts"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            def get_hotkey_entry_item(km, kmi_name):
                """collect keymap item"""

                for i, km_item in enumerate(km.keymap_items):
                    if (km.keymap_items.keys()[i]==kmi_name):
                        return km_item
                return None 
            
            wm = bpy.context.window_manager
            kc = wm.keyconfigs.user
            km = kc.keymaps['Window']

            col.label(text=translate("Quick-Scatter Shortcut")+":",)

            kmi = get_hotkey_entry_item(km,"scatter5.define_add_psy")
            if kmi:
                row = col.row()
                row.context_pointer_set("keymap", km)
                row.prop(kmi, "type", text="", full_event=True)

            col.label(text=translate("Quick-Lister Shortcut")+":",)
            
            kmi = get_hotkey_entry_item(km,"scatter5.quick_lister")
            if kmi:
                row = col.row()
                row.context_pointer_set("keymap", km)
                row.prop(kmi, "type", text="", full_event=True)
            
            # WATCH: is user manually removes items from keymap, they will draw. that is ok, but not sure if something else can be missing. whole keymap? is that possible? or anything else?
            
            gesture_map = {
                'PRIMARY': ('Primary', 0),
                'SECONDARY': ('Secondary', 1),
                'TERTIARY': ('Tertiary', 2),
                'QUATERNARY': ('Quaternary', 3),
            }
            
            usermap = getattr(bpy.context.window_manager.keyconfigs.get("Blender user"), "keymaps", None, )
            if(usermap is not None):
                from ..manual import keys
                
                col.separator()
                col.label(text=translate("Manual Mode Shortcuts") + ":", )
                
                km_name, km_args, km_content = keys.op_key_defs
                km = usermap.find(km_name, **km_args)
                r = col.row()
                r.context_pointer_set("keymap", km)
                for kmi in km.keymap_items:
                    if(kmi.idname == "scatter5.manual_enter"):
                        break
                r.label(text=kmi.name, )
                r.prop(kmi, "type", text="", full_event=True, )
                
                col.separator()
                col.label(text=translate("Tools") + ":", )
                
                km_name, km_args, km_content = keys.op_key_defs
                km = usermap.find(km_name, **km_args)
                for item in km_content['items']:
                    item_id = km.keymap_items.find(item[0])
                    if(item_id != -1):
                        kmi = km.keymap_items[item_id]
                        k = kmi.idname.split('.')[-1]
                        if(not k.startswith('manual_brush_tool_')):
                            # NOTE: skip ops that are not brush tools
                            continue
                        
                        r = col.row()
                        r.context_pointer_set("keymap", km)
                        r.label(text=kmi.name, )
                        r.prop(kmi, "type", text="", full_event=True, )
                
                # sort gestures
                ls = [None, None, None, None]
                km_name, km_args, km_content = keys.mod_key_defs
                km = usermap.find(km_name, **km_args)
                for kmi in km.keymap_items:
                    if(kmi.idname == 'scatter5.manual_tool_gesture'):
                        n = gesture_map[getattr(kmi.properties, 'gesture', )][0]
                        i = gesture_map[getattr(kmi.properties, 'gesture', )][1]
                        ls[i] = (n, kmi, )
                
                col.separator()
                col.label(text=translate("Tool Gestures") + ":", )
                
                for i in range(len(ls)):
                    if(ls[i] is not None):
                        n, kmi = ls[i]
                        r = col.row()
                        r.context_pointer_set("keymap", km)
                        r.label(text=n, )
                        r.prop(kmi, "type", text="", full_event=True, )
            
            ui_templates.separator_box_in(box)

    return None
    

def draw_add_customui(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_customui", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_customui";UI_BOOL_VAL:"1"
        icon = "COLOR", 
        name = translate("Interface"),
        )
    if is_open:

            # row = box.row()
            # row.separator(factor=0.3)
            # row.prop(addon_prefs,"ui_selection_y", text=translate("Selection Area: Items Height"))
            # row.separator(factor=0.3)

            ui_templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_use_dark_box", 
                label=translate("Box-Panel: Use Dark Header"), 
                icon="ALIGN_MIDDLE", 
                left_space=True,
                )

            ui_templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_show_boxpanel_icon", 
                label=translate("Box-Panel: Use Icons"), 
                icon="MONKEY", 
                left_space=True,
                )

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_boxpanel_separator", text=translate("Box-Panel: Spacing Between Panels"))
            row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_boxpanel_height", text=translate("Box-Panel: Title Height"))
            row.separator(factor=0.3)

            ui_templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_bool_use_standard", 
                label=translate("Toggle: Use Icons"), 
                icon="CHECKBOX_HLT", 
                invert_checkbox=True,
                left_space=True,
                )

            ui_templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_bool_use_openclose", 
                label=translate("Toggle: Use Open/Close"), 
                icon="DOWNARROW_HLT", 
                invert_checkbox=False,
                left_space=True,
                )

            ui_templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="ui_bool_use_iconcross", 
                label=translate("Toggle: Use Crosses Toggled Off"), 
                icon="CANCEL", 
                left_space=True,
                enabled=not addon_prefs.ui_bool_use_standard
                )

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_bool_indentation", text=translate("Toggle: Indentation"))
            row.separator(factor=0.3)

            # # NOTE: no longer active, multiplier moved to theme. will be part of manual mode theme ui.
            # row = box.row()
            # row.separator(factor=0.3)
            # row.prop(addon_prefs,"ui_scale_viewport", text=translate("Viewport: Scatter5 Infobox Scale"))
            # row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_word_wrap_max_char_factor", text=translate("Info-Text: Max Character per Lines"))
            row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs,"ui_word_wrap_y", text=translate("Info-Text: Paragraph Height"))
            row.separator(factor=0.3)
            
            # ------------------------------------------------------------------ manual mode options >>>
            
            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs, "manual_use_overlay", text=translate("Manual Mode: Use Overlay"))
            row.separator(factor=0.3)
            
            # ------------------------------------------------------------------ manual mode options <<<
            # ------------------------------------------------------------------ manual mode theme >>>
            theme = addon_prefs.manual_theme
            
            ui_templates.bool_toggle(box,
                prop_api=theme,
                prop_str="show_ui", 
                label=translate("Show Manual Mode Theme"), 
                icon="W_DISTMANUAL",
                invert_checkbox=False,
                left_space=True,
                )
            if (theme.show_ui):

                row = box.row()
                row.separator(factor=0.3)
                
                c = row.box().column()
                c.row().prop(theme, 'circle_steps')
                c.row().prop(theme, 'fixed_radius_default')
                c.row().prop(theme, 'fixed_center_dot_radius_default')
                c.row().prop(theme, 'no_entry_sign_size_default')
                c.row().prop(theme, 'no_entry_sign_color')
                c.row().prop(theme, 'no_entry_sign_thickness_default')
                c.row().prop(theme, 'default_outline_color')
                c.row().prop(theme, 'default_outline_color_press')
                c.row().prop(theme, 'outline_color_eraser')
                c.row().prop(theme, 'outline_color_hint')
                c.row().prop(theme, 'outline_color_disabled_alpha')
                c.row().prop(theme, 'outline_color_helper_alpha')
                c.row().prop(theme, 'outline_color_gesture_helper_alpha')
                c.row().prop(theme, 'outline_color_falloff_helper_alpha')
                c.row().prop(theme, 'outline_thickness_default')
                c.row().prop(theme, 'outline_thickness_helper_default')
                c.row().prop(theme, 'outline_dashed_steps_multiplier')
                c.row().prop(theme, 'default_fill_color')
                c.row().prop(theme, 'default_fill_color_press')
                c.row().prop(theme, 'fill_color_press_eraser')
                c.row().prop(theme, 'fill_color_helper_hint')
                c.row().prop(theme, 'fill_color_disabled_alpha')
                c.row().prop(theme, 'fill_color_helper_alpha')
                c.row().prop(theme, 'fill_color_gesture_helper_alpha')
                c.row().prop(theme, 'text_size_default')
                c.row().prop(theme, 'text_color')
                c.row().prop(theme, 'text_tooltip_outline_color')
                c.row().prop(theme, 'text_tooltip_background_color')
                c.row().prop(theme, 'text_tooltip_outline_thickness')
                c.row().prop(theme, 'point_size_default')
                c.row().prop(theme, 'grid_overlay_size')
                c.row().prop(theme, 'grid_overlay_color_a')
                c.row().prop(theme, 'grid_overlay_color_b')
                c.row().prop(theme, 'info_box_scale')
                c.row().prop(theme, 'info_box_shadow_color')
                c.row().prop(theme, 'info_box_fill_color')
                c.row().prop(theme, 'info_box_outline_color')
                c.row().prop(theme, 'info_box_outline_thickness_default')
                c.row().prop(theme, 'info_box_logo_color')
                c.row().prop(theme, 'info_box_text_header_color')
                c.row().prop(theme, 'info_box_text_body_color')
                
                row.separator(factor=0.3)
            # ------------------------------------------------------------------ manual mode theme <<<
            
            ui_templates.separator_box_in(box)

    return None
    

def draw_add_dev(self,layout):

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

    box, is_open = ui_templates.box_panel(self, layout, 
        prop_str = "ui_add_dev", #REGTIME_INSTRUCTION:UI_BOOL_KEY:"ui_add_dev";UI_BOOL_VAL:"1"
        icon = "CONSOLE", 
        name = translate("Debugging"),
        )
    if is_open:

            ui_templates.bool_toggle(box, 
                prop_api=addon_prefs,
                prop_str="debug", 
                label=translate("Debug Mode."), 
                icon="CONSOLE", 
                left_space=True,
                )

            d = box.row()
            d.active = addon_prefs.debug
            ui_templates.bool_toggle(d, 
                prop_api=addon_prefs,
                prop_str="debug_depsgraph", 
                label=translate("Depsgraph console prints."), 
                icon="CONSOLE", 
                left_space=True,
                )

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            op = col.operator("scatter5.update_nodetrees", text=translate("Force-Update All Nodetrees"),)
            op.force_update = True

            ui_templates.separator_box_in(box)

    return None


# oooooooooo.                                            ooooo         o8o               .
# `888'   `Y8b                                           `888'         `"'             .o8
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo       888         oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888      888 `888""8P `P  )88b   `88. `88.  .8'        888         `888  d88(  "8   888   d88' `88b `888""8P
#  888      888  888      .oP"888    `88..]88..8'         888          888  `"Y88b.    888   888ooo888  888
#  888     d88'  888     d8(  888     `888'`888'          888       o  888  o.  )88b   888 . 888    .o  888
# o888bood8P'   d888b    `Y888""8o     `8'  `8'          o888ooooood8 o888o 8""888P'   "888" `Y8bod8P' d888b



class SCATTER5_UL_list_scatter_large(bpy.types.UIList):
    """selection area"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        
        if not item:
            return 

        p = item
        scat_scene = bpy.context.scene.scatter5
        row = layout.row(align=True)            

        #Color 
        if (scat_scene.lister_show_color):

            color = row.row()
            color.scale_x = 0.2
            color.prop(p,"s_color",text="")

        #Name 
        name = row.row(align=True)
        name.prop(p,"name", text="", emboss=False, )

        #Stats
        if (scat_scene.lister_show_stats_surface):

            #spacer
            row.separator()

            info = row.row()
            info.active = False            
            info.label(text= square_area_repr( p.get_surfaces_square_area(evaluate="gather") ), icon="SURFACE_NSURFACE",)

        #Stats
        if (scat_scene.lister_show_stats_count):

            #spacer
            row.separator()

            info = row.row()
            info.active = False
            info.label(text=count_repr(p.scatter_count_viewport_consider_hidden, unit="Pts"), icon="RESTRICT_VIEW_ON" if p.hide_viewport else "RESTRICT_VIEW_OFF")
            info.label(text=count_repr(p.scatter_count_render, unit="Pts"), icon="RESTRICT_RENDER_ON" if p.hide_render else "RESTRICT_RENDER_OFF")

        #Render/Lock 

        if (scat_scene.lister_show_selection or scat_scene.lister_show_render_state or scat_scene.lister_show_lock):

            row.separator()

            sub = row.box().row(align=True)
            sub.scale_x = 0.9
            sub.scale_y = 0.55

            #Selection
            if (scat_scene.lister_show_selection):

                sel = sub.row(align=True)
                sel.scale_x = 0.95
                sel.prop(p,"sel", text="", icon="RESTRICT_SELECT_OFF"if p.sel else "RESTRICT_SELECT_ON", emboss=False,)

            #Render Status
            if (scat_scene.lister_show_render_state):
        
                sub.prop(p, "hide_viewport", text="", icon="RESTRICT_VIEW_ON" if p.hide_viewport else "RESTRICT_VIEW_OFF", invert_checkbox=True, emboss=False,)
                sub.prop(p, "hide_render", text="", icon="RESTRICT_RENDER_ON" if p.hide_render else "RESTRICT_RENDER_OFF", invert_checkbox=True, emboss=False,)

            #Lock 
            if (scat_scene.lister_show_lock):

                loc = sub.row(align=True)
                loc.scale_x = 1.02
                loc.prop(p,"lock",text="",icon="LOCKED" if p.is_all_locked() else "UNLOCKED", emboss=False, invert_checkbox=p.is_all_locked())

            row.separator()

        #Visibility Row
        if (scat_scene.lister_show_visibility):

            sub = row.box().row(align=True)
            sub.scale_x = 0.95
            sub.scale_y = 0.55

            #Visibility Preview 
            vis = sub.row(align=True)
            vis.scale_x = 1.07
            vis.active = p.s_visibility_facepreview_allow
            vis.prop(p,"s_visibility_facepreview_allow", text="", emboss=False, icon="SELECT_INTERSECT" if p.s_visibility_facepreview_allow else "SELECT_EXTEND",)

            #Visibility %
            vis = sub.row(align=True)
            vis.scale_x = 1.07
            vis.prop(p,"s_visibility_view_allow", text="", emboss=False, icon_value=cust_icon(f"W_PERCENTAGE_{str(p.s_visibility_view_allow).upper()}"),)

            #Visibility Cam 
            vis = sub.row(align=True)
            vis.active = p.s_visibility_cam_allow
            vis.prop(p,"s_visibility_cam_allow", text="", emboss=False, icon= "OUTLINER_OB_CAMERA" if p.s_visibility_cam_allow else "CAMERA_DATA",)

            #Visibility Maxload
            sub.prop(p,"s_visibility_maxload_allow", text="", emboss=False, icon_value= cust_icon("W_FIRE") if p.s_visibility_maxload_allow else cust_icon("W_FIRE_FALSE"),)

            row.separator()

        #Display Features
        if (scat_scene.lister_show_display):

            sub = row.box().row(align=True)
            sub.scale_x = 0.95
            sub.scale_y = 0.55

            #Allow Display
            dis = sub.row(align=True)
            dis.scale_x = 1.1
            dis.active = p.s_display_allow
            dis.prop(p,"s_display_allow", text="", emboss=False, icon_value=cust_icon(f"W_DISPLAY_{str(p.s_display_allow).upper()}"),)

            #Display method 
            method = sub.row(align=True)
            method.active = p.s_display_allow
            method.prop(p,"s_display_method", text="", emboss=False, icon_only=True,)
        
        return None


def draw_stats(self, layout):

    col = layout.column()

    scat_scene = bpy.context.scene.scatter5
    emitter = scat_scene.emitter
    emitters = scat_scene.get_all_emitters()

    #gather some data while in the loop  
    
    global_scatter_system_len = 0
    global_count_viewport_consider_hidden = -1
    global_count_render = -1

    for e in emitters:

        psy_active = e.scatter5.get_psy_active()
        local_scatter_system_len =  len(e.scatter5.particle_systems)

        # Emitter name and set new emitter operator 

        erow = col.row()
        erow.scale_y = 1.5

        sub = erow.row(align=True)
        sub.alignment="LEFT"
        op = sub.operator("scatter5.set_new_emitter",text=e.name, emboss=False, icon_value=cust_icon("W_EMITTER" if (e==emitter) else "W_EMITTER_EMPTY"),)
        op.obj_name = e.name
        op.select = True

        sub = erow.row(align=True)
        sub.alignment="LEFT"
        sub.label(text=f'{local_scatter_system_len} {translate("System(s)")}', icon="PARTICLE_DATA")

        # Emitter Information

        if (scat_scene.lister_show_stats_count):

            erow.separator(factor=4)
            erow.separator_spacer()

            inforow = erow.row(align=True)
            inforow.alignment="RIGHT"
            inforow.active = False

            #Instance Count Information

            if (scat_scene.lister_show_stats_count):

                all_count = [p.scatter_count_viewport_consider_hidden for p in e.scatter5.particle_systems]
                total = sum([c for c in all_count if c>=0])
                skip = all([c<0 for c in all_count])
                inforow.label(text="..." if (total<0 or skip) else f'{total:,} {"Pts"}', icon="RESTRICT_VIEW_OFF")

                if (total>=0) and not skip:
                    if (global_count_viewport_consider_hidden==-1): #default ==-1, trigger to 0 when valid
                        global_count_viewport_consider_hidden=0
                    global_count_viewport_consider_hidden += total


                all_count = [p.scatter_count_render for p in e.scatter5.particle_systems]
                total = sum([c for c in all_count if c>=0])
                skip = all([c<0 for c in all_count])
                inforow.label(text="..." if (total<0 or skip) else f'{total:,} {"Pts"}', icon="RESTRICT_RENDER_OFF")

                if (total>=0) and not skip:
                    if (global_count_render==-1): #default ==-1, trigger to 0 when valid
                        global_count_render=0
                    global_count_render += total

        erow.separator(factor=4)

        col.separator(factor=1) 

        #Per emitter Scatter List Templates 

        template = col.row()

        ui_list = template.column(align=True)
        ui_list.scale_y = 1.1
        ui_list.template_list("SCATTER5_UL_list_scatter_large", "", e.scatter5, "particle_systems", e.scatter5, "particle_systems_idx", type="DEFAULT", rows=local_scatter_system_len,)


        #Operators side menu
        
        ope = template.column(align=True)

        #add
        
        add = ope.column(align=True)
        op = add.operator("scatter5.add_psy_simple",text="",icon="ADD",)
        op.emitter_name = e.name
        op.surfaces_names = "_!#!_".join( [o.name for o in bpy.context.selected_objects if (o.type=="MESH")] )
        op.instances_names = "_!#!_".join( [o.name for o in bpy.context.selected_objects] )
        op.psy_color_random = True 

        #remove
        
        rem = ope.column(align=True)
        rem.enabled = psy_active is not None
        op = rem.operator("scatter5.remove_system",text="",icon="REMOVE",)
        op.emitter_name = e.name
        op.method = "alt"
        op.undo_push = True

        ope.separator()

        #selection menu

        menu = ope.row()
        menu.context_pointer_set("s5_ctxt_ptr_emitter", e)
        menu.menu("SCATTER5_MT_selection_menu", icon='DOWNARROW_HLT', text="",)

        #move up & down

        if (local_scatter_system_len>1):

            ope.separator()        

            updo = ope.column(align=True)
            updo.enabled = local_scatter_system_len!=0
            op = updo.operator("scatter5.list_move",text="",icon="TRIA_UP")
            op.target_idx = e.scatter5.particle_systems_idx 
            op.direction = "UP"    
            op.api_propgroup = f"bpy.data.objects['{e.name}'].scatter5.particle_systems"
            op.api_propgroup_idx = f"bpy.data.objects['{e.name}'].scatter5.particle_systems_idx"
            op = updo.operator("scatter5.list_move",text="",icon="TRIA_DOWN")
            op.target_idx = e.scatter5.particle_systems_idx       
            op.direction = "DOWN"   
            op.api_propgroup = f"bpy.data.objects['{e.name}'].scatter5.particle_systems"
            op.api_propgroup_idx = f"bpy.data.objects['{e.name}'].scatter5.particle_systems_idx"

        #right spacers
        
        template.separator(factor=0.1)

        #Update global len 

        global_scatter_system_len+= local_scatter_system_len

        col.separator(factor=1)

        continue

    #global len not found anything? 

    if (global_scatter_system_len==0):

        text = layout.column()
        text.active = False
        text.alignment="CENTER"
        text.label(text=translate("No Scatter-System(s) Added Yet?"))

    #Grand Tota Recap 

    col = layout.column()
    col.scale_y = 0.85

    erow = col.row()
    erow.scale_y = 1.5
    erow.active = False

    sub = erow.row(align=True)
    sub.alignment="LEFT"
    sub.label(text=f'{len(emitters)} {translate("Emitter(s)")}', icon_value=cust_icon("W_EMITTER"),)

    sub = erow.row(align=True)
    sub.alignment="LEFT"
    sub.label(text=f'{global_scatter_system_len} {translate("System(s)")}', icon="PARTICLE_DATA")

    erow.separator(factor=4)
    erow.separator_spacer()

    inforow = erow.row(align=True)
    inforow.alignment="RIGHT"

    #Total Stats

    if (scat_scene.lister_show_stats_count):

        inforow.label(text=count_repr(global_count_viewport_consider_hidden, unit="Pts"), icon="RESTRICT_VIEW_OFF")
        inforow.label(text=count_repr(global_count_render, unit="Pts"), icon="RESTRICT_RENDER_OFF")

    erow.separator(factor=4)

    return 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    SCATTER5_OT_impost_addonprefs,
    SCATTER5_UL_list_scatter_large,

    )


#if __name__ == "__main__":
#    register()
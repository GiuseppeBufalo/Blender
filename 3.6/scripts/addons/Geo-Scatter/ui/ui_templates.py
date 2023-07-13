
#####################################################################################################
#       .                                          oooo                .
#     .o8                                          `888              .o8
#   .o888oo  .ooooo.  ooo. .oo.  .oo.   oo.ooooo.   888   .oooo.   .o888oo  .ooooo.
#     888   d88' `88b `888P"Y88bP"Y88b   888' `88b  888  `P  )88b    888   d88' `88b
#     888   888ooo888  888   888   888   888   888  888   .oP"888    888   888ooo888
#     888 . 888    .o  888   888   888   888   888  888  d8(  888    888 . 888    .o
#     "888" `Y8bod8P' o888o o888o o888o  888bod8P' o888o `Y888""8o   "888" `Y8bod8P'
#                                        888
#                                       o888o
#####################################################################################################


import bpy 

from .. resources.icons import cust_icon
from .. resources.translate import translate

from . ui_menus import SCATTER5_PT_docs


#  .oooooo..o                                                       .
# d8P'    `Y8                                                     .o8
# Y88bo.       .ooooo.  oo.ooooo.   .oooo.   oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o
#  `"Y8888o.  d88' `88b  888' `88b `P  )88b  `888""8P `P  )88b    888   d88' `88b `888""8P d88(  "8
#      `"Y88b 888ooo888  888   888  .oP"888   888      .oP"888    888   888   888  888     `"Y88b.
# oo     .d8P 888    .o  888   888 d8(  888   888     d8(  888    888 . 888   888  888     o.  )88b
# 8""88888P'  `Y8bod8P'  888bod8P' `Y888""8o d888b    `Y888""8o   "888" `Y8bod8P' d888b    8""888P'
#                        888
#                       o888o


def separator_box_out(layout):
    """spacing between box panels"""

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    height = addon_prefs.ui_boxpanel_separator
    return layout.separator(factor=height)


def separator_box_in(layout):
    """spacing at the end of a box panel"""

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    if addon_prefs.ui_use_dark_box:
          return layout.separator(factor=0.3)
    else: return layout.separator(factor=0.3)


# oooooooooo.                             ooooooooo.                                   oooo
# `888'   `Y8b                            `888   `Y88.                                 `888
#  888     888  .ooooo.  oooo    ooo       888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  888oooo888' d88' `88b  `88b..8P'        888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  888    `88b 888   888    Y888'          888          .oP"888   888   888  888ooo888  888
#  888    .88P 888   888  .o8"'88b         888         d8(  888   888   888  888    .o  888
# o888bood8P'  `Y8bod8P' o88'   888o      o888o        `Y888""8o o888o o888o `Y8bod8P' o888o


def box_panel( self,
               layout,
               prop_str="", #scatter5.ui panel close prop
               icon="", #header icon
               master_category_toggle="",
               name="", #header title
               warning_panel=False,
               doc_panel="", #optional doc panel on the right
               pref_panel="", #optional pref panel on the right 
               popover_argument="", #scat_ui.prop argument
               tweaking_panel=False, #special actions if tweaking panel
               force_open=False,
               ):
    """draw sub panel opening template, use fct to add own settings""" 

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    scat_ui     = bpy.context.window_manager.scatter5.ui
    scat_scene  = bpy.context.scene.scatter5
    emitter     = scat_scene.emitter
    psy_active  = emitter.scatter5.get_psy_active() if emitter else None
    is_open     = getattr(scat_ui,prop_str) if (not force_open) else True

    #determine layout style

    if (addon_prefs.ui_use_dark_box):
        
        box = layout.box()
        header = box.box().row(align=True)
    
    else:
        
        col = layout.column(align=True)
        header = col.box().row(align=True)
        header.scale_y = 1.1
        
        if (is_open):
              box = col.box()
              box.separator(factor=-1)
        else: box = None 

    #ui custom panel height
    header.scale_y = addon_prefs.ui_boxpanel_height

    #use open/close arrow icons style instead
    if (not addon_prefs.ui_show_boxpanel_icon):
        icon = "W_PANEL_OPEN" if is_open else "W_PANEL_CLOSED"

        #special active option for tweaking panels 
        if tweaking_panel and psy_active:

                #assuming popover panel is str
                s_category = popover_argument
                if psy_active.is_category_used(s_category):
                    icon+="_ACTIVE"

    #generic title open/close + icon on the left

    args={"text":name, "emboss":False,}
    
    if (icon):
        if (type(icon) is int):
              args["icon_value"]=icon
        elif (icon.startswith("W_")):
              args["icon_value"]=cust_icon(icon)
        else: args["icon"]=icon

    title = header.row(align=True)
    title.alignment = "LEFT"
    title.prop(scat_ui, prop_str, **args)

    #because everything is aligned on the left, if title is too tiny you can miss the hitbox
    hiddenprop = header.row(align=True)
    hiddenprop.prop(scat_ui, prop_str, text=" ", icon="BLANK1", emboss=False,)

    toolbar = header.row(align=True)
    toolbar.alignment = "RIGHT"

    #category toggle for tweaking active psy 

    if (master_category_toggle):
        
        if (psy_active):
            
            m = toolbar.row(align=True)
            m.scale_y = 0.9
            m.emboss = "NONE"
            m.active = True
            m.prop(psy_active, master_category_toggle, text="", icon_value=cust_icon(f"W_CHECKBOX_{str(getattr(psy_active,master_category_toggle)).upper()}"),)

        else: 
            m = toolbar.row(align=True)
            m.scale_y = 0.9
            m.active = True
            m.label(text="", icon="BLANK1",)

    #panel popovers ? 

    if (pref_panel):

        m = toolbar.row(align=True)
        m.scale_x = 0.95
        m.active = False
        m.emboss = "NONE"
        icon_value = cust_icon("W_PREFERENCES")

        #transfer arg, for the panel
        if (psy_active):

            #just pass string ? 
            if (type(popover_argument) is str):

                m.context_pointer_set("s5_ctxt_ptr_popover",getattr(scat_ui.popovers_args,popover_argument))

                if tweaking_panel:
                    #icon of the panel is used to transfer information to the user!
                    s_category = popover_argument
                    #if settings category is locked, display lock icon
                    is_locked = getattr(psy_active, f"{s_category}_locked")
                    if is_locked: 
                        icon_value = cust_icon("W_LOCKED_GREY")
                    else:
                        #is synch, display synch icon 
                        is_synch = psy_active.is_synchronized(s_category)
                        if is_synch: 
                            icon_value = cust_icon("W_ARROW_SYNC_GREY")
                        #later on, will need to also consider frozen state
            else: 

                m.context_pointer_set("s5_ctxt_ptr_popover",popover_argument)


        m.popover(panel=pref_panel, text="", icon_value=icon_value,)

    #documentation ?

    if (doc_panel):

        m = toolbar.row(align=True)
        m.scale_x = 0.95
        m.active = True
        m.emboss = "NONE"

        #transfer arg, for the panel
        if (popover_argument):

            #all docs str popovers args need to match docs dict in ui.ui_menu
            m.context_pointer_set("s5_ctxt_ptr_popover",getattr(scat_ui.popovers_args,popover_argument))

        m.popover(panel=doc_panel, text="", icon_value=cust_icon("W_INFO"),)

    #big warning icon? could potentially develop this part to show warning message to user like we did in S4, maybe replacing doc ? 

    if (warning_panel):

        m = toolbar.row(align=True)
        m.scale_x = 0.95
        m.alert = True
        m.active = False
        m.label(text="", icon="INFO")

    return box, is_open  


# ooooooooooooo                                 oooo
# 8'   888   `8                                 `888
#      888       .ooooo.   .oooooooo  .oooooooo  888   .ooooo.
#      888      d88' `88b 888' `88b  888' `88b   888  d88' `88b
#      888      888   888 888   888  888   888   888  888ooo888
#      888      888   888 `88bod8P'  `88bod8P'   888  888    .o
#     o888o     `Y8bod8P' `8oooooo.  `8oooooo.  o888o `Y8bod8P'
#                         d"     YD  d"     YD
#                         "Y88888P'  "Y88888P'

def bool_toggle( layout,
                 prop_api=None,
                 prop_str="",
                 label="",
                 icon="",
                 left_space=True, #special for some toggle that are too close to the left border
                 enabled=True,
                 active=True,
                 invert_checkbox=False,
                 open_close_api="",
                 return_layout=False,
                 return_title_layout=False,
                 feature_availability=True,
                 ): 
        
    #feature not available ? 
    if (not feature_availability):
        if (return_layout):
            if (return_title_layout):
                return None,None,None
            return None,None
        return None 

    addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
    scat_ui     = bpy.context.window_manager.scatter5.ui
    scat_scene  = bpy.context.scene.scatter5
    emitter     = scat_scene.emitter
    psy_active  = emitter.scatter5.get_psy_active() if emitter else None

    is_toggled  = getattr(prop_api,prop_str)==True
    is_open     = None
    openlbl     = None

    #main layout

    MainCol = layout.column(align=True)
    MainCol.enabled = enabled
    MainCol.active = active

    #main toggle row

    Boolrow = MainCol.row(align=True)

    #draw arrow open/close button? 
    if (open_close_api and addon_prefs.ui_bool_use_openclose):

        if (open_close_api=="use_spacer"):
            
            Boolrow.separator(factor=3.25)

        else:
            if "." in open_close_api:
                is_open = eval(open_close_api)
            else:
                is_open = getattr(scat_ui,open_close_api)
            
            #TODO need to replace the label of the feature by the open/close instead, but layout will never be close enough...

            # openlbl = label
            # label = ""

            arrow = Boolrow.row(align=True)
            arrow.scale_x = 0.9
            arrow.prop(scat_ui, open_close_api, text="", emboss=False, icon_value=cust_icon("W_PANEL_OPEN" if is_open else "W_PANEL_CLOSED"),)

            Boolrow.separator(factor=0.5)

    #draw small space on the left ? 
    elif (left_space):
        Boolrow.separator(factor=1.5)

    #draw toggle, two possible style
    if (addon_prefs.ui_bool_use_standard or icon==""):

        #classic checkbox style
        prop=Boolrow.row(align=True)
        prop.scale_y = 1.05
        prop.prop(prop_api,prop_str, text=label, invert_checkbox=invert_checkbox,)

    else:

        #or icon style
        if (addon_prefs.ui_bool_use_iconcross and not is_toggled):
            args = {"text":"", "icon":"PANEL_CLOSE"}
        else:
            if not icon.startswith("W_"): 
                  args = {"text":"", "icon":icon}
            else: args = {"text":"", "icon_value":cust_icon(icon)}
        if invert_checkbox==True: 
            args["invert_checkbox"] = True  

        prop=Boolrow.row(align=True)
        prop.scale_y = 1.0
        prop.prop(prop_api,prop_str, **args )

        prop.separator()

        if label:
            prop.label(text=label)

    #just return toggle value?
    
    if (not return_layout):
        return None, is_toggled       

    #return layout for indentation style interface

    if (is_open is not None):
        active_feature = is_toggled
        is_toggled = is_open

    #main features row

    FeaturesRow = MainCol.row()

    if (is_toggled):
        if (left_space):
            _1tocol = FeaturesRow.column() ; _1tocol.scale_x = 0.01
        spacer = FeaturesRow.row()
        spacer.label(text="")
        spacer.scale_x = addon_prefs.ui_bool_indentation

    feature_col = FeaturesRow.column()

    if (is_open is not None):
        feature_col.active = active_feature

    #leave a little beathing gap
    if (is_toggled):
        feature_col.separator(factor=0.25)

    #special return values for drawing on the left space of the row? 
    if (return_title_layout):
        return feature_col, Boolrow, is_toggled    

    return feature_col, is_toggled
        

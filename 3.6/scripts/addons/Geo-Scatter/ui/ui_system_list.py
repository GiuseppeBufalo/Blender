
#####################################################################################################
#
# ooooo     ooo ooooo       .oooooo..o                          .                                    ooooo         o8o               .
# `888'     `8' `888'      d8P'    `Y8                        .o8                                    `888'         `"'             .o8
#  888       8   888       Y88bo.      oooo    ooo  .oooo.o .o888oo  .ooooo.  ooo. .oo.  .oo.         888         oooo   .oooo.o .o888oo
#  888       8   888        `"Y8888o.   `88.  .8'  d88(  "8   888   d88' `88b `888P"Y88bP"Y88b        888         `888  d88(  "8   888
#  888       8   888            `"Y88b   `88..8'   `"Y88b.    888   888ooo888  888   888   888        888          888  `"Y88b.    888
#  `88.    .8'   888       oo     .d8P    `888'    o.  )88b   888 . 888    .o  888   888   888        888       o  888  o.  )88b   888 .
#    `YbodP'    o888o      8""88888P'      .8'     8""888P'   "888" `Y8bod8P' o888o o888o o888o      o888ooooood8 o888o 8""888P'   "888"
#                                      .o..P'
#                                      `Y8P'
#####################################################################################################

import bpy 

from .. resources.icons import cust_icon
from .. resources.translate import translate

from .. utils.extra_utils import is_rendered_view
from .. utils.str_utils import word_wrap, square_area_repr, count_repr

from .. scattering.emitter import is_ready_for_scattering


# ooooooooo.
# `888   `Y88.
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88(  "8
#  888          888     888   888  888   888 `"Y88b.
#  888          888     888   888  888   888 o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                  888
#                                 o888o


class SCATTER5_PR_particle_interface_items(bpy.types.PropertyGroup): 
    """bpy.context.object.scatter5.particle_interface_items, will be stored on emitter"""

    #these object.scatter5.particle_interface_items will be constantly rebuild on major user interaction

    interface_item_type : bpy.props.StringProperty()  #GROUP/SCATTER

    interface_group_name : bpy.props.StringProperty()

    interface_item_psy_uuid : bpy.props.IntProperty()

    interface_ident_icon : bpy.props.StringProperty()

    interface_add_separator : bpy.props.BoolProperty()

    def get_interface_item_source(self):

        if (self.interface_item_type=="SCATTER"):
            for p in self.id_data.scatter5.particle_systems:
                if (p.uuid==self.interface_item_psy_uuid):
                    return p

        elif (self.interface_item_type=="GROUP"):
            for g in self.id_data.scatter5.particle_groups:
                if (g.name==self.interface_group_name):
                    return g            

        return None 

    def get_item_index(self):

        for i,itm in enumerate(self.id_data.scatter5.particle_interface_items):
            if (itm==self):
                return i

        return None


# ooooo     .                                    oooooooooo.
# `888'   .o8                                    `888'   `Y8b
#  888  .o888oo  .ooooo.  ooo. .oo.  .oo.         888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888    888   d88' `88b `888P"Y88bP"Y88b        888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888    888   888ooo888  888   888   888        888      888  888      .oP"888    `88..]88..8'
#  888    888 . 888    .o  888   888   888        888     d88'  888     d8(  888     `888'`888'
# o888o   "888" `Y8bod8P' o888o o888o o888o      o888bood8P'   d888b    `Y888""8o     `8'  `8'


def UL_scatter_list_factory(lister_large=False, lister_stats=False,):
    """drawing item function for large/small item lists are highly similar"""

    def fct(self, context, layout, data, item, icon, active_data, active_propname):

        if (not item):
            layout.label(text="ERROR: Item is None")
            return None
        
        #draw scatter item 
        source_itm = item.get_interface_item_source()
        if (not source_itm):
            layout.label(text="ERROR: Item source is None")
            return None    

        emitter = item.id_data
        addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences

        #define main layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = addon_prefs.ui_selection_y   
         
        if (lister_large or lister_stats):
            row.scale_y *= addon_prefs.ui_lister_scale_y
            row.separator(factor=0.8)

        if (item.interface_item_type=="SCATTER"):
            p = source_itm

            #Indentation

            if (item.interface_ident_icon!=""): 
                indent = row.row(align=True)
                indent.scale_x = 0.85
                indent.label(text="", icon_value=cust_icon(item.interface_ident_icon),)

            #Color & name

            colname = row.row(align=True)
            colname.alignment = "LEFT"

            color = colname.row()
            color.scale_x = 0.25
            color.prop(p,"s_color",text="")

            name = colname.row()
            name.prop(p,"name", text="", emboss=False, )

            #Adjustments

            if ((lister_stats) and (item.interface_ident_icon=="")):

                #need to adjust indentation in statistic inferface
                space = row.row(align=True)
                space.scale_x = 0.85
                space.label(text="", icon="BLANK1",)
            
            #rightside

            if (lister_stats):

                rightactions = row.row(align=True)
                rightactions.alignment = "RIGHT"

                infoactions = rightactions.split()
                infoactions.active = False
                infoactions.scale_x = 0.75
                infoactions.label(text= square_area_repr( p.get_surfaces_square_area(evaluate="gather") ), icon="SURFACE_NSURFACE",)
                infoactions.label(text=count_repr(p.scatter_count_viewport_consider_hidden, unit="Pts"), icon="RESTRICT_VIEW_OFF",)
                infoactions.label(text=count_repr(p.scatter_count_render, unit="Pts"), icon="RESTRICT_RENDER_OFF",)
                
            if (not lister_stats):

                rightactions = row.row(align=True)
                rightactions.alignment = "RIGHT"
                rightactions.scale_x = 0.95

                #select
                ractions = rightactions.row(align=True)
                ractions.scale_x = 0.85
                ractions.prop(p,"sel", text="", icon="RESTRICT_SELECT_OFF" if p.sel else "RESTRICT_SELECT_ON", emboss=False,)
                
                #hide viewport
                ractions = rightactions.row(align=True)
                ractions.scale_x = 1.0
                ractions.prop(p, "hide_viewport", text="", icon="RESTRICT_VIEW_ON" if p.hide_viewport else "RESTRICT_VIEW_OFF", invert_checkbox=True, emboss=False,)
                
                #hide render
                ractions = rightactions.row(align=True)
                ractions.scale_x = 1.0
                ractions.prop(p, "hide_render", text="", icon_value=cust_icon("W_SHOW_RENDER_OFF") if p.hide_render else cust_icon("W_SHOW_RENDER_ON"), invert_checkbox=True, emboss=False,)

            #props only for large lister
            if (lister_large):

                #lock
                ractions = rightactions.row(align=True)
                ractions.scale_x = 0.90
                ractions.prop(p,"lock",text="",icon="LOCKED" if p.is_all_locked() else "UNLOCKED", emboss=False, invert_checkbox=p.is_all_locked(),)

                #separator
                rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)
                
                #dice
                ractions = rightactions.row(align=True)
                op = ractions.operator("scatter5.batch_randomize", text="", icon_value=cust_icon("W_SHOW_DICE"), emboss=False,)
                op.emitter_name = emitter.name
                op.psy_name = p.name

                #separator
                rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                #percentage
                ractions = rightactions.row(align=True)
                ractions.scale_x = 1.0
                ractions.prop(p, "s_visibility_view_allow", text="", icon_value=cust_icon("W_SHOW_VIS_PERC_ON") if p.s_visibility_view_allow else cust_icon("W_SHOW_VIS_PERC_OFF"), emboss=False,)

                #preview area
                ractions = rightactions.row(align=True)
                ractions.scale_x = 1.0
                ractions.prop(p, "s_visibility_maxload_allow", text="", icon_value=cust_icon("W_SHOW_VIS_MAXLOAD_ON") if p.s_visibility_maxload_allow else cust_icon("W_SHOW_VIS_MAXLOAD_OFF"), emboss=False,)

                #preview area
                ractions = rightactions.row(align=True)
                ractions.scale_x = 1.0
                ractions.prop(p, "s_visibility_facepreview_allow", text="", icon_value=cust_icon("W_SHOW_VIS_VIEW_ON") if p.s_visibility_facepreview_allow else cust_icon("W_SHOW_VIS_VIEW_OFF"), emboss=False,)

                #cam opti
                ractions = rightactions.row(align=True)
                ractions.scale_x = 1.0
                ractions.prop(p, "s_visibility_cam_allow", text="", icon_value=cust_icon("W_SHOW_VIS_CLIP_ON") if p.s_visibility_cam_allow else cust_icon("W_SHOW_VIS_CLIP_OFF"), emboss=False,)

                #separator
                rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                #display as
                ractions = rightactions.row(align=True)
                ractions.scale_x = 1.0
                ractions.prop(p, "s_display_allow", text="", icon_value=cust_icon("W_SHOW_DISPLAY_ON") if p.s_display_allow else cust_icon("W_SHOW_DISPLAY_OFF"), emboss=False,)

                rightactions.separator(factor=0.991111)

        elif (item.interface_item_type=="GROUP"):
            
            g = source_itm
            gpsys = [p for p in emitter.scatter5.particle_systems if (p.group!="") and (p.group==g.name) ]

            #Arrow

            arrow = row.row(align=True)
            arrow.scale_x = 0.8
            op = arrow.operator("scatter5.exec_line", text="", icon="TRIA_DOWN" if g.open else "TRIA_RIGHT", emboss=False,)
            op.api = f"bpy.data.objects['{emitter.name}'].scatter5.particle_groups['{g.name}'].open ^= True"
                        
            #Name 

            name = row.row(align=True)
            name.prop(g,"name", text="", emboss=False,)

            #set of icons

            rightactions = row.row(align=True)
            rightactions.alignment = "RIGHT"
            rightactions.scale_x = 0.95

            if (not lister_stats):

                #select
                ractions = rightactions.row(align=True)
                ractions.scale_x = 0.90
                toggle_status = [p.sel for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_SEL_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "sel"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(not any(toggle_status))

                #hide viewport
                ractions = rightactions.row(align=True)
                toggle_status = [not p.hide_viewport for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_VIEW_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "hide_viewport"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(any(toggle_status))

                #hide render
                ractions = rightactions.row(align=True)
                toggle_status = [not p.hide_render for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_RENDER_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "hide_render"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(any(toggle_status))

            #props only for large lister
            if (lister_large):

                #lock
                ractions = rightactions.row(align=True)
                ractions.scale_x = 0.90
                toggle_status = [p.is_all_locked() for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_LOCK_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "lock"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = "lock_special"

                #separator
                rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                #dice
                ractions = rightactions.row(align=True)
                op = ractions.operator("scatter5.batch_randomize", text="", icon_value=cust_icon("W_GROUP_TOGGLE_DICE"), emboss=False,)
                op.emitter_name = emitter.name
                op.group_name = g.name

                #separator
                rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                #percentage
                ractions = rightactions.row(align=True)
                toggle_status = [p.s_visibility_view_allow for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_PERC_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_view_allow"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(not any(toggle_status))

                #maxload
                ractions = rightactions.row(align=True)
                toggle_status = [p.s_visibility_maxload_allow for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_MAXLOAD_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_maxload_allow"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(not any(toggle_status))

                #preview area
                ractions = rightactions.row(align=True)
                toggle_status = [p.s_visibility_facepreview_allow for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_PREV_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_facepreview_allow"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(not any(toggle_status))

                #cam opti
                ractions = rightactions.row(align=True)
                toggle_status = [p.s_visibility_cam_allow for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_CLIP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_cam_allow"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(not any(toggle_status))

                #separator
                rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                #display as
                ractions = rightactions.row(align=True)
                toggle_status = [p.s_display_allow for p in gpsys]
                icon = cust_icon("W_GROUP_TOGGLE_DISP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_NONE")
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_display_allow"
                op.emitter_name = emitter.name
                op.group_name = g.name
                op.setvalue = str(not any(toggle_status))
                
                rightactions.separator(factor=0.991111)

        #draw separator
        if (item.interface_add_separator):

            #larger if large version
            if (lister_large or lister_stats):
                  col.separator(factor=1.6)
            else: col.separator(factor=2.0)

        return None

    return fct


class SCATTER5_UL_list_scatter_small(bpy.types.UIList):
    """system-list compact size, for N panel & quick list shortcut"""

    draw_item = UL_scatter_list_factory()

class SCATTER5_UL_list_scatter_large(bpy.types.UIList):
    """system-list full options, for manager interface"""
    
    draw_item = UL_scatter_list_factory(lister_large=True)

class SCATTER5_UL_list_scatter_stats(bpy.types.UIList):
    """system-list full options, for manager interface"""
    
    draw_item = UL_scatter_list_factory(lister_stats=True)



# oooooooooo.                                            oooo   o8o               .
# `888'   `Y8b                                           `888   `"'             .o8
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo       888  oooo   .oooo.o .o888oo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'        888  `888  d88(  "8   888
#  888      888  888      .oP"888    `88..]88..8'         888   888  `"Y88b.    888
#  888     d88'  888     d8(  888     `888'`888'          888   888  o.  )88b   888 .
# o888bood8P'   d888b    `Y888""8o     `8'  `8'          o888o o888o 8""888P'   "888"


def draw_fix_button(layout, operator_id):
    """layout template to draw a quickfix button operator_id in 'scatter5.fix_nodetrees' or 'scatter5.fix_scatter_obj' depending on context"""
    
    layout.separator(factor=0.5)
    fixbutton = layout.row()
    fixbutton.scale_y = 0.9
    fixbutton.label(text="")
    fixbutton.operator(operator_id, text=translate("Quickfix"))
    fixbutton.label(text="")
    
    return None

def draw_particle_selection_inner(layout, addon_prefs=None, scat_scene=None, emitter=None, psy_active=None, group_active=None,): 
    """used in tweaking panel but also in quick lister interface"""

    row = layout.row()

    #left spacers
    row.separator(factor=0.5)

    #list template
    
    template = row.column()

    ui_list = template.column()
    ui_list.scale_y = addon_prefs.ui_selection_y
    ui_list.template_list("SCATTER5_UL_list_scatter_small", "", emitter.scatter5, "particle_interface_items", emitter.scatter5, "particle_interface_idx", type="DEFAULT", rows=10,)

    #debug info

    if (addon_prefs.debug_interface):

        template.separator(factor=0.5)

        template_debug = template.column().box()
        template_debug.label(text="Debug Interface, Dev Only", icon="GHOST_DISABLED",)
        debug = template_debug.column().box()

        debug.alignment = "LEFT"
        debug.scale_y = 0.8
        debug.label(text=f"    emitter.get_psy_active() = {psy_active.name if psy_active else '/'}")
        debug.label(text=f"    emitter.get_group_active() = {group_active.name if group_active else '/'}")
        debug.prop(emitter.scatter5,"particle_interface_idx", text="emitter.particle_interface_idx", emboss=False,)
        debug.operator("scatter5.exec_line", text="emitter.particle_interface_refresh()").api = f"emitter.scatter5.particle_interface_refresh()"

        debug = template_debug.column().box()
        debug.label(text="emitter.particle_systems:")

        for i,p in enumerate(emitter.scatter5.particle_systems):
            
            debugr = debug.row(align=True)
            debugr.scale_y = 0.7
            debugrr = debugr.row(align=True)
            debugrr.scale_x = 0.3
            debugrr.label(text=str(i),)
            debugrr = debugr.row(align=True)
            debugrr.scale_x = 0.3
            debugrr.prop(p,"s_color",text="",)
            debugr.prop(p,"name",text="",)
            debugr.prop(p,"group",text="",icon="TRIA_RIGHT")
            debugr.prop(p,"active",text="",)
            debugr.prop(p,"sel",text="",)

        debug = template_debug.column().box()
        debug.label(text="emitter.particle_groups:")

        for i,g in enumerate(emitter.scatter5.particle_groups):
            debug.prop(g,"name", text="", icon="GROUP",)
    
        debug = template_debug.column().box()
        debug.label(text="psy_active info:")

        if (psy_active is not None): 
            
            debug.prop(psy_active, "name_bis")
            debug.prop(psy_active, "scatter_obj")
            
            if (psy_active.scatter_obj):
                scatter_mod = psy_active.get_scatter_mod()
                if (scatter_mod):
                    debug.prop(scatter_mod, "node_group")
                    
            debug.prop(psy_active, "blender_version")
            debug.prop(psy_active, "addon_version")
            debug.prop(psy_active, "addon_type")
            debugr = debug.row()
            debugr.enabled = False
            debugr.prop(psy_active, "uuid", emboss=True,)

    #important info about active psy

    if (psy_active is not None): 

        #scatter_obj is None ? User Messed with things

        if (psy_active.scatter_obj is None):
            
            template.separator(factor=0.5)
            warn = layout.column()
            word_wrap( string=translate("Warning, we couldn't find the scatter-object associated to this scatter-system."), active=True,  layout=warn, alignment="CENTER", max_char=35, icon="INFO")

            draw_fix_button(warn,"scatter5.fix_scatter_obj")
            
        #scatter_mod is None ?

        elif (psy_active.get_scatter_mod(strict=True, raise_exception=False) is None):

            template.separator(factor=0.5)
            warn = layout.column()
            if (psy_active.get_scatter_mod(strict=False, raise_exception=False) is None):
                  word_wrap( string=translate("Warning, we couldn't find any scatter-engine modifier associated with scatter-system."), active=True,  layout=warn, alignment="CENTER", max_char=35, icon="INFO")
            else: word_wrap( string=translate("Warning, the current scatter-engine associated with this scatter-system is outdated."), active=True,  layout=warn, alignment="CENTER", max_char=35, icon="INFO")

            draw_fix_button(warn,"scatter5.fix_nodetrees")

        #user has accidentaly remove the scatter obj? 

        elif (psy_active.scatter_obj.name not in bpy.context.scene.objects):

            template.separator(factor=0.5)
            warn = layout.column()
            word_wrap( string=translate("Warning, the scatter-object used by this scatter-system has been removed from this scene."), active=True,  layout=warn, alignment="CENTER", max_char=35, icon="INFO")

            draw_fix_button(warn,"scatter5.fix_scatter_obj")

        #user has hidden the scatter_obj ? 

        elif (not psy_active.scatter_obj.visible_get() and not psy_active.hide_viewport):
            if (bpy.context.area.type=="VIEW_3D") and (bpy.context.space_data.local_view is None):
                
                template.separator(factor=0.5)
                warn = layout.column()
                word_wrap( string=translate("This scatter-system collection is hidden. Check your outliner."), active=True,  layout=warn, alignment="CENTER", max_char=35, icon="INFO")

    #Operators side menu
    
    ope = row.column(align=True)

    #add
    
    add = ope.column(align=True)
    add.enabled = is_ready_for_scattering()
    op = add.operator("scatter5.add_psy_simple",text="",icon="ADD",)
    op.emitter_name = emitter.name
    op.surfaces_names = "_!#!_".join( [o.name for o in bpy.context.selected_objects if (o.type=="MESH")] )
    op.instances_names = "_!#!_".join( [o.name for o in bpy.context.selected_objects] )
    op.psy_color_random = True 

    #remove
    
    rem = ope.column(align=True)
    rem.enabled = not ((psy_active is None) and (group_active is None))
    op = rem.operator("scatter5.remove_system",text="",icon="REMOVE",)
    op.emitter_name = emitter.name
    op.method = "dynamic_uilist"
    op.undo_push = True

    ope.separator()
    
    #selection menu

    menu = ope.row()
    menu.context_pointer_set("pass_ui_arg_emitter", emitter)
    menu.menu("SCATTER5_MT_selection_menu", icon='DOWNARROW_HLT', text="",)
    
    #biome reader group/ungroup

    ope.separator()        

    #move up & down

    updo = ope.column(align=True)
    updo.enabled = (len(emitter.scatter5.particle_systems)!=0)

    op = updo.operator("scatter5.move_interface_items",text="",icon="TRIA_UP",)
    op.direction = "UP"    

    op = updo.operator("scatter5.move_interface_items",text="",icon="TRIA_DOWN",)
    op.direction = "DOWN"   

    #bring all system(s) to local view
    if (bpy.context.space_data.type=="VIEW_3D") and (bpy.context.space_data.local_view is not None):

        ope.separator()
        op = ope.operator("scatter5.exec_line", text="", icon="ZOOM_SELECTED",)
        op.api = f"[p.scatter_obj.local_view_set(bpy.context.space_data,p.sel) for p in psys]"
        op.description = translate("Isolate the selected system(s) within local view")

    #right spacers
    row.separator(factor=0.1)

    return None


#   .oooooo.                                                         .o.                     .    o8o
#  d8P'  `Y8b                                                       .888.                  .o8    `"'
# 888           oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.           .8"888.      .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
# 888           `888""8P d88' `88b `888  `888   888' `88b         .8' `888.    d88' `"Y8   888   `888  d88' `88b `888P"Y88b
# 888     ooooo  888     888   888  888   888   888   888        .88ooo8888.   888         888    888  888   888  888   888
# `88.    .88'   888     888   888  888   888   888   888       .8'     `888.  888   .o8   888 .  888  888   888  888   888
#  `Y8bood8P'   d888b    `Y8bod8P'  `V88V"V8P'  888bod8P'      o88o     o8888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
#                                               888
#                                              o888o


class SCATTER5_OT_group_psys(bpy.types.Operator):

    bl_idname      = "scatter5.group_psys"
    bl_label       = translate("Group/UnGroup Scatter-System(s)")
    bl_description = translate("Group/UnGroup Scatter-System(s)\nGrouping scatter-system(s) together is a great way to manage your scatter layers, it offers a way to organize your scatter's more easily in your interface. You'll be able to easily hide scatter layers by their groups, and tweak their group settings, such as defining a group mask, a group scale or a group pattern. Group settings applies to all scatter layers members of a defined group.")
    bl_options     = {'INTERNAL','UNDO'}

    action : bpy.props.StringProperty(default="GROUP") #GROUP/UNGROUP/NEWGROUP
    name : bpy.props.StringProperty(default="MyGroup")
    emitter_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    group_target : bpy.props.StringProperty(default="", options={'SKIP_SAVE',})

    reset_index : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE',})

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("No Emitter found")

        psys_sel = emitter.scatter5.get_psys_selected()

        #pause for optimization purposes, this might trigger a lot of updates
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):
                
            #if action is new group, need to find a proper name

            if (self.action=="NEWGROUP"):

                groups_used = [ p.group for p in emitter.scatter5.particle_systems if (p.group!="") ]

                idx = 0
                original_name = self.name
                while (self.name in groups_used):
                    idx += 1
                    self.name = f"{original_name}.{idx:03}"

            #add to group (note that psy.group update function will automatically create the group)

            if ((self.action=="GROUP") or (self.action=="NEWGROUP")):

                #if operator usedin the context of an active group
                if (self.group_target!=""):
                    self.name = self.group_target

                if (self.name==""):
                    bpy.ops.scatter5.popup_dialog(
                        'INVOKE_DEFAULT',
                        msg=translate("Please choose another name"),
                        header_title=translate("Invalid Name"),
                        header_icon="LIBRARY_DATA_BROKEN",
                        )
                    return {'FINISHED'}

                for p in psys_sel:
                    if (p.group!=self.name):
                        p.group = self.name

            #or ungroup 

            elif (self.action=="UNGROUP"):

                #if operator usedin the context of an active group
                if (self.group_target!=""):
                    for p in emitter.scatter5.particle_systems:
                        if (p.group==self.group_target):
                            p.group = ""

                else:
                    for p in psys_sel:
                        p.group = ""

            #rebuild system-list interface
            emitter.scatter5.particle_interface_refresh()

            #restore psy sel, rebuilding interface will trigger index change
            for p in emitter.scatter5.particle_systems:
                p.sel = p in psys_sel

        return {'FINISHED'}


# oooooooooo.                .             oooo
# `888'   `Y8b             .o8             `888
#  888     888  .oooo.   .o888oo  .ooooo.   888 .oo.
#  888oooo888' `P  )88b    888   d88' `"Y8  888P"Y88b
#  888    `88b  .oP"888    888   888        888   888
#  888    .88P d8(  888    888 . 888   .o8  888   888
# o888bood8P'  `Y888""8o   "888" `Y8bod8P' o888o o888o


class SCATTER5_OT_batch_toggle(bpy.types.Operator):

    bl_idname      = "scatter5.batch_toggle"
    bl_label       = translate("Batch toggle Scatter-System(s)")
    bl_description = translate("Batch toggle Scatter-System(s)")
    bl_options     = {'INTERNAL','UNDO'}

    propname : bpy.props.StringProperty(default="") #hide_viewport/hide_render
    emitter_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    group_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    scene_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    setvalue : bpy.props.StringProperty(default="auto", options={'SKIP_SAVE',},)

    @classmethod
    def description(cls, context, properties,):
        if (properties.propname=="sel"):
            return translate("Batch Select/Deselet system(s)")
        elif (properties.propname=="hide_viewport"):
            return translate("Batch Hide/Unhide system(s) from viewport")
        elif (properties.propname=="hide_render"):
            return translate("Batch Hide/Unhide system(s) from render")
        return ""

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter

        #if input is scene, batch toggle all psys of scene
        if (self.scene_name!=""):
            assert (self.scene_name in bpy.data.scenes)
            psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys()

        #if input is group, batch toggle all element of group
        elif (self.group_name!=""):
            assert (emitter is not None)
            g = emitter.scatter5.particle_groups[self.group_name]
            psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

        #else we batch on all emitter psys
        elif (self.emitter_name!=""):
            assert (emitter is not None)
            psys = emitter.scatter5.particle_systems[:]

        else: 
            raise Exception("Please choose either scene_name, emitter_name, or group_name + emitter_name as args")

        with context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            #special case for lock property... lock property is a fake, used as an operator
            if (self.setvalue=="lock_special"):
                setvalue = not any(p.is_all_locked() for p in psys) #p.lock
                [setattr(p,"lock",True) for p in psys if (p.is_all_locked()!=setvalue)]
                return {'FINISHED'}

            setvalue = eval(self.setvalue)
            [setattr(p,self.propname,setvalue) for p in psys if (getattr(p,self.propname)!=setvalue)]

        #refresh areas
        [a.tag_redraw() for a in context.screen.areas]

        return {'FINISHED'}


class SCATTER5_OT_batch_randomize(bpy.types.Operator):

    bl_idname      = "scatter5.batch_randomize"
    bl_label       = translate("Batch Randomize Scatter-System(s)")
    bl_description = translate("Batch Randomize Scatter-System(s)")
    bl_options     = {'INTERNAL','UNDO'}

    context_selection : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE',},)
    emitter_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    psy_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    group_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    scene_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)

    def invoke(self, context, event):
        self.alt = event.alt
        return self.execute(context)

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter

        #input is currently selected psys on context emitter?
        if (self.context_selection==True):
            psys = emitter.scatter5.get_psys_selected()
        
        #if input is scene, batch toggle all psys of scene
        elif (self.scene_name!=""):
            assert (self.scene_name in bpy.data.scenes)
            psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys()

        #if input is group, batch toggle all element of group
        elif (self.group_name!=""):
            assert (emitter is not None)
            g = emitter.scatter5.particle_groups[self.group_name]
            psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

        #if inputis group, just toggle psyname
        elif (self.psy_name!=""):
            assert (emitter is not None)
            psys = [ emitter.scatter5.particle_systems[self.psy_name] ]
            if (self.alt):
                psys = emitter.scatter5.get_psys_selected(all_emitters=scat_scene.factory_alt_selection_method=="all_emitters")

        #else we batch on all emitter psys
        elif (self.emitter_name!=""):
            assert (emitter is not None)
            psys = emitter.scatter5.particle_systems[:]

        else: 
            raise Exception("Please choose either scene_name, emitter_name, or group_name + emitter_name as args")

        with context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            for p in psys:

                #randomize distribution seed
                if (p.s_distribution_method=="random"):
                    p.s_distribution_is_random_seed = True

                elif (p.s_distribution_method=="clumping"):
                    p.s_distribution_clump_is_random_seed = True
                    p.s_distribution_clump_children_density = True

                elif (p.s_distribution_method=="volume"):
                    p.s_distribution_volume_is_random_seed = True

                elif (p.s_distribution_method=="random_stable"):
                    p.s_distribution_stable_is_random_seed = True

                #randomize patterns
                for i in (1,2,3):
                    if getattr(p,f"s_pattern{i}_allow"):
                        texture_name = getattr(p,f"s_pattern{i}_texture_ptr")
                        if (texture_name is not None):
                            ng = p.get_scatter_mod().node_group.nodes[f's_pattern{i}'].node_tree.nodes['texture'].node_tree
                            if ng.name.startswith(".TEXTURE *DEFAULT*"):
                                continue
                            t = ng.scatter5.texture
                            t.mapping_random_is_random_seed = True

                #randomize fallnoisy
                for k in p.bl_rna.properties.keys():
                    if (k.endswith("fallnoisy_is_random_seed")):
                        if getattr(p,k.replace("fallnoisy_is_random_seed","fallremap_allow")):
                            setattr(p,k,True)

                #missing something?
                continue

        return {'FINISHED'}


# ooo        ooooo                                      ooooo         o8o               .
# `88.       .888'                                      `888'         `"'             .o8
#  888b     d'888   .ooooo.  oooo    ooo  .ooooo.        888         oooo   .oooo.o .o888oo
#  8 Y88. .P  888  d88' `88b  `88.  .8'  d88' `88b       888         `888  d88(  "8   888
#  8  `888'   888  888   888   `88..8'   888ooo888       888          888  `"Y88b.    888
#  8    Y     888  888   888    `888'    888    .o       888       o  888  o.  )88b   888 .
# o8o        o888o `Y8bod8P'     `8'     `Y8bod8P'      o888ooooood8 o888o 8""888P'   "888"


class SCATTER5_OT_move_interface_items(bpy.types.Operator):
    """special move-set behavior for our group system item"""

    bl_idname      = "scatter5.move_interface_items"
    bl_label       = translate("Move the active system Up/Down")
    bl_description = translate("Organize your interface by moving your scatter-system or scatter-group up or down the interface lister")
    bl_options     = {'INTERNAL','UNDO'}

    direction : bpy.props.StringProperty(default="UP") #UP/DOWN
    target_idx : bpy.props.IntProperty(default=0)
    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("No Emitter found")
            return {'FINISHED'}

        psy_active = emitter.scatter5.get_psy_active()
        group_active = emitter.scatter5.get_group_active()

        propgroup     = emitter.scatter5.particle_interface_items
        target_idx    = emitter.scatter5.particle_interface_idx
        len_propgroup = len(propgroup)


        #don't even bother to move anything if we are located at the list extrmities
        if ((self.direction=="DOWN") and (target_idx==len_propgroup-1)) or \
           ((self.direction=="UP") and (target_idx==0)):
          return {'FINISHED'}

        #save selection, this operation might f up sel
        save_sel = emitter.scatter5.get_psys_selected()[:]

        #do we move a psy itm?
        if (psy_active is not None):

            #if we move a psy item in group, simply move them within their group
            if (psy_active.group!=""):

                #find all idx part of same group as psy_active
                possible_idxs = [ i for i,itm in enumerate(propgroup) if 
                                        (itm.interface_item_type=="SCATTER") 
                                    and (itm.get_interface_item_source() is not None)
                                    and (itm.get_interface_item_source().group==psy_active.group) 
                                ]

                if (self.direction=="DOWN"):

                    #find first available index above target
                    possible_idxs = [i for i in possible_idxs if i>target_idx]
                    if (len(possible_idxs)):
                        new_idx = possible_idxs[0]
                        propgroup.move(target_idx,new_idx)

                elif (self.direction=="UP"):

                    #find last available index below target 
                    possible_idxs = [i for i in possible_idxs if i<target_idx]
                    if (len(possible_idxs)):
                        new_idx = possible_idxs[-1]
                        propgroup.move(target_idx,new_idx)

            #if we move a psy item in group, we need to ignore 
            else:
                
                #find all idx not part of any groups, or group idx
                possible_idxs = [ i for i,itm in enumerate(propgroup) if 
                                   (    (itm.interface_item_type=="SCATTER") 
                                    and (itm.get_interface_item_source() is not None)
                                    and (itm.get_interface_item_source().group=="") ) \
                                    or  (itm.interface_item_type=="GROUP")
                                ]

                if (self.direction=="DOWN"):

                    #find first available index above target
                    possible_idxs = [i for i in possible_idxs if i>target_idx]
                    if (len(possible_idxs)):
                        new_idx = possible_idxs[0]
                        propgroup.move(target_idx,new_idx)

                elif (self.direction=="UP"):

                    #find last available index below target 
                    possible_idxs = [i for i in possible_idxs if i<target_idx]
                    if (len(possible_idxs)):
                        new_idx = possible_idxs[-1]
                        propgroup.move(target_idx,new_idx)

            #update interface & make sure active item is still active
            emitter.scatter5.set_interface_active_item(item=psy_active)

        #or we move a group itm? 
        elif (group_active is not None):
            
            #find all idx not part of any groups, or group idx
            possible_idxs = [ i for i,itm in enumerate(propgroup) if 
                               (    (itm.interface_item_type=="SCATTER") 
                                and (itm.get_interface_item_source() is not None)
                                and (itm.get_interface_item_source().group=="") ) \
                                or  (itm.interface_item_type=="GROUP")
                            ]

            if (self.direction=="DOWN"):

                #find first available index above target
                possible_idxs = [i for i in possible_idxs if i>target_idx]
                if (len(possible_idxs)):
                    new_idx = possible_idxs[0]
                    propgroup.move(target_idx,new_idx)

            elif (self.direction=="UP"):

                #find last available index below target 
                possible_idxs = [i for i in possible_idxs if i<target_idx]
                if (len(possible_idxs)):
                    new_idx = possible_idxs[-1]
                    propgroup.move(target_idx,new_idx)

            #update interface & make sure active item is still active
            emitter.scatter5.set_interface_active_item(item=group_active)

        #restore selection
        [setattr(p,"sel",p in save_sel) for p in emitter.scatter5.particle_systems]

        return {'FINISHED'}


class SCATTER5_OT_generic_list_move(bpy.types.Operator):

    bl_idname      = "scatter5.generic_list_move"
    bl_label       = translate("Move Item")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    direction : bpy.props.StringProperty(default="UP") #UP/DOWN
    target_idx : bpy.props.IntProperty(default=0)

    api_propgroup  : bpy.props.StringProperty(default="emitter.scatter5.mask_systems")
    api_propgroup_idx : bpy.props.StringProperty(default="emitter.scatter5.mask_systems_idx")

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter

        target_idx    = self.target_idx
        current_idx   = eval(f"{self.api_propgroup_idx}")
        len_propgroup = eval(f"len({self.api_propgroup})")

        if ((self.direction=="UP") and (current_idx!=0)):
            exec(f"{self.api_propgroup}.move({target_idx},{target_idx}-1)")
            exec(f"{self.api_propgroup_idx} -=1")
            return {'FINISHED'}

        if ((self.direction=="DOWN") and (current_idx!=len_propgroup-1)):
            exec(f"{self.api_propgroup}.move({target_idx},{target_idx}+1)")
            exec(f"{self.api_propgroup_idx} +=1")
            return {'FINISHED'}

        return {'FINISHED'}



#   .oooooo.      ooooo         o8o               .
#  d8P'  `Y8b     `888'         `"'             .o8
# 888      888     888         oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
# 888      888     888         `888  d88(  "8   888   d88' `88b `888""8P
# 888      888     888          888  `"Y88b.    888   888ooo888  888
# `88b    d88b     888       o  888  o.  )88b   888 . 888    .o  888
#  `Y8bood8P'Ybd' o888ooooood8 o888o 8""888P'   "888" `Y8bod8P' d888b


class SCATTER5_OT_quick_lister(bpy.types.Operator):
    #modal dialog box -> https://blender.stackexchange.com/questions/274785/how-to-create-a-modal-dialog-box-operator

    bl_idname = "scatter5.quick_lister"
    bl_label = translate("Quick Lister")
    bl_description = translate("Quick Lister")
    bl_options = {'INTERNAL'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    #find if dialog is currently active?

    def get_cls(self):
        cls = SCATTER5_OT_quick_lister
        return cls

    dialog_state = False

    def get_dialog_state(self)->bool:
        return self.get_cls().dialog_state
        
    def set_dialog_state(self, value:bool,)->None:
        self.get_cls().dialog_state = value
        return None

    instance_type : bpy.props.StringProperty(default="UNDEFINED", options={'SKIP_SAVE',},)

    def invoke(self,context,event,):
        """decide if we'll invoke modal or dialog"""

        #define emitter
        self.emitter = bpy.data.objects.get(self.emitter_name)
        if (self.emitter is None):
            self.emitter = bpy.context.scene.scatter5.emitter

        #launch both modal & dialog instance of this operator simultaneously
        if (self.instance_type=="UNDEFINED"):
            bpy.ops.scatter5.quick_lister('INVOKE_DEFAULT',instance_type="DIALOG",)
            bpy.ops.scatter5.quick_lister('INVOKE_DEFAULT',instance_type="MODAL",)
            return {'FINISHED'}

        #launch a dialog instance?
        if (self.instance_type=="DIALOG"):
            self.set_dialog_state(True)
            return context.window_manager.invoke_popup(self)

        #launch a modal instance?
        if (self.instance_type=="MODAL"):
            self.modal_start(context)
            context.window_manager.modal_handler_add(self)  
            return {'RUNNING_MODAL'}

        return {'FINISHED'}

    def __del__(self):
        """called when the operator has finished"""

        #some of our instances might be gone from memory, 
        #therefore 'instance_type' is not available for some instance at this stage
        #not the dialog box instance tho & we need to update class status

        try:
            if (self.instance_type=="DIALOG"):
                self.set_dialog_state(False)
        except:
            pass
            
        return None

    layer_equivalence = {"ONE":1,"NUMPAD_1":1,"TWO":2,"NUMPAD_2":2,"THREE":3,"NUMPAD_3":3,"FOUR":4,"NUMPAD_4":4,"FIVE":5,"NUMPAD_5":5,"SIX":6,"NUMPAD_6":6,"SEVEN":7,"NUMPAD_7":7,"EIGHT":8,"NUMPAD_8":8,"NINE":9,"NUMPAD_9":9,"ZERO":10,"NUMPAD_0":10,}

    def modal(self,context,event,):
        """for modal instance"""

        #[a.tag_redraw() for a in context.screen.areas] #Not working :-(

        #modal state only active while dialog instance is! 
        if (self.get_dialog_state()==False):
            self.modal_quit(context)
            return {'FINISHED'}

        #no shortcut if no emitter!
        if (self.emitter is None):
            return {'PASS_THROUGH'}

        #USE NUM KEY to switch active interface item
        if (event.type in self.layer_equivalence.keys()):
            if (event.value=="RELEASE"):
                save_selection = [p.sel for p in self.emitter.scatter5.particle_systems]
                self.emitter.scatter5.particle_interface_idx = self.layer_equivalence[event.type]
                for v,p in zip(save_selection,self.emitter.scatter5.particle_systems): 
                    p.sel = v
            return {'PASS_THROUGH'}

        #CTRL+C
        elif (event.ctrl and event.type=="C"):
            if (event.value=="RELEASE"):
                bpy.ops.scatter5.copy_paste_systems(emitter_name=self.emitter.name,copy=True,)
            return {'PASS_THROUGH'}

        #CTRL V
        elif (event.ctrl and event.type=="V"):
            if (event.value=="RELEASE"):
                bpy.ops.scatter5.copy_paste_systems(emitter_name=self.emitter.name,paste=True,)
            return {'PASS_THROUGH'}

        #A/ALT+A
        elif (event.type=="A"):
            if (event.value=="RELEASE"):
                if (event.alt):
                    for p in self.emitter.scatter5.particle_systems:
                        p.sel = False
                    return {'PASS_THROUGH'}
                for p in self.emitter.scatter5.particle_systems:
                    p.sel = True
            return {'PASS_THROUGH'}

        #DELETE
        elif (event.type=="DEL"):
            if (event.value=="RELEASE"):
                bpy.ops.scatter5.remove_system(method="selection", emitter_name=self.emitter.name,) 
            return {'PASS_THROUGH'}

        #CTRL+G/ALT+G
        elif (event.type=="G"):
            if (event.value=="RELEASE"):

                #group
                if (event.ctrl):

                    group_active = self.emitter.scatter5.get_group_active()
                    #add to active group?
                    if (group_active is not None):
                        bpy.ops.scatter5.group_psys(emitter_name=self.emitter.name, action="GROUP",group_target=group_active.name,reset_index=True,)
                        return {'PASS_THROUGH'}
                    #or simply add new?
                    bpy.ops.scatter5.group_psys(emitter_name=self.emitter.name, action="NEWGROUP",reset_index=True,)
                    return {'PASS_THROUGH'}

                #ungroup
                if (event.alt):
                    save_hide_viewport = [p.hide_viewport for p in self.emitter.scatter5.particle_systems]
                    bpy.ops.scatter5.group_psys(emitter_name=self.emitter.name, action="UNGROUP",reset_index=True,)
                    for v,p in zip(save_hide_viewport,self.emitter.scatter5.particle_systems): 
                        p.hide_viewport = v
                    return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}

    def modal_start(self,context,):
        return None

    def modal_quit(self,context,):
        return None

    def draw(self, context):

        layout = self.layout

        layout.separator(factor=1.5)

        addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
        scat_scene  = bpy.context.scene.scatter5
        emitter = self.emitter

        if (emitter is not None):
            psy_active  = emitter.scatter5.get_psy_active()
            group_active = emitter.scatter5.get_group_active()

        row = layout.row()
            
        rwoo = row.row()
        rwoo.separator(factor=0.45)
        rwoo.alignment = "LEFT"
        rwoo.scale_x = 1.5
        rwoo.menu("SCATTER5_MT_emitter_dropdown_menu", text=f" {emitter.name}  " if (emitter is not None) else translate("Emitter"), icon="DOWNARROW_HLT",)
        
        rwoo = row.row()
        rwoo.alignment = "RIGHT"
        rwoo.scale_x = 1.2
        rwoo.prop(scat_scene, "emitter", text="")
        rwoo.separator(factor=0.3)

        if (emitter is not None):
            from .. ui.ui_system_list import draw_particle_selection_inner
            draw_particle_selection_inner(layout, addon_prefs, scat_scene, emitter, psy_active, group_active)
            
        else: 
            col = layout.column()
            col.active = False
            col.separator()
            row = col.row()
            row.separator(factor=1.2)
            row.label(text=translate("Please Select an Emitter"), icon_value=cust_icon("W_EMITTER"),)
            col.separator()

        layout.separator(factor=1.5)

        return None 


    def execute(self, context,):
        """mandatory function called when user press on 'ok' """

        return {'FINISHED'}



quicklister_keymaps = []

def register_quicklister_shortcuts():
    if(bpy.app.background):
        # NOTE: if blender is run headless, i.e. with -b, --background option, there is no window, so adding keymap will fail with error:
        #     km  = kc.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
        # AttributeError: 'NoneType' object has no attribute 'keymaps'
        # so, lets skip that completely.. and unregistering step as well
        return
    
    #add hotkey
    wm  = bpy.context.window_manager
    kc  = wm.keyconfigs.addon
    km  = kc.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
    kmi = km.keymap_items.new("scatter5.quick_lister", 'Q', 'PRESS', shift=True,ctrl=True,alt=False,)

    quicklister_keymaps.append(kmi)

    return None

def unregister_quicklister_shortcuts():
    if(bpy.app.background):
        # see `register_quicklister_shortcuts()` above
        return

    #remove hotkey
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps["Window"]
    for kmi in quicklister_keymaps:
        km.keymap_items.remove(kmi)
    quicklister_keymaps.clear()

    return None


# oooooooooo.                                          .o8   o8o                              oooooooooo.
# `888'   `Y8b                                        "888   `"'                              `888'   `Y8b
#  888     888  .ooooo.  oooo  oooo  ooo. .oo.    .oooo888  oooo  ooo. .oo.    .oooooooo       888     888  .ooooo.  oooo    ooo
#  888oooo888' d88' `88b `888  `888  `888P"Y88b  d88' `888  `888  `888P"Y88b  888' `88b        888oooo888' d88' `88b  `88b..8P'
#  888    `88b 888   888  888   888   888   888  888   888   888   888   888  888   888        888    `88b 888   888    Y888'
#  888    .88P 888   888  888   888   888   888  888   888   888   888   888  `88bod8P'        888    .88P 888   888  .o8"'88b
# o888bood8P'  `Y8bod8P'  `V88V"V8P' o888o o888o `Y8bod88P" o888o o888o o888o `8oooooo.       o888bood8P'  `Y8bod8P' o88'   888o
#                                                                             d"     YD
#                                                                             "Y88888P'

class SCATTER5_OT_batch_bounding_box(bpy.types.Operator):

    bl_idname      = "scatter5.batch_bounding_box"
    bl_label       = translate("Batch-Set Objects Bounding-Box")
    bl_description = translate("Toggle between 'Bounding-Box' or 'Textured' display for all original object(s) used as instances by of the scatter-system(s).\nPlease note that this might impact other scatter-system(s) as well.")
    bl_options     = {'INTERNAL', 'UNDO'}

    #interface
    pop_dialog : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    pop_influence_options : bpy.props.EnumProperty(
        name=translate("Influence"),
        default="all",
        items=[("sel",translate("Selected System(s)"),"",),
               ("all",translate("All System(s)"),"",),
               ],) 
    pop_influence_value : bpy.props.EnumProperty(
        name=translate("Value"),
        default="BOUNDS",
        items=[("BOUNDS",translate("Enable"),"",),
               ("TEXTURED",translate("Disable"),"",),
               ],) 

    #internal settings
    use_sel_all : bpy.props.BoolProperty(options={"SKIP_SAVE",},)
    psy_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    group_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    emitter_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    scene_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    set_value : bpy.props.StringProperty(default="auto", options={"SKIP_SAVE",},)

    def draw(self, context):
        layout = self.layout
        
        layout.prop(self,"pop_influence_options",)
        layout.prop(self,"pop_influence_value",)
        layout.separator(factor=0.5)

        psys = bpy.data.objects[0].scatter5.get_psys_selected(all_emitters=True) if (self.pop_influence_options=="sel") else bpy.context.scene.scatter5.get_all_psys()
        objs = [o for p in psys for o in p.get_instance_objs() ]

        layout.label(text=translate("Apply to")+f" {len(psys)} "+translate("Scatter-System(s)")+" → "+f" {len(objs)} "+translate("Objects"),)

        return None

    def invoke(self, context, event):

        if (self.pop_dialog):
            return bpy.context.window_manager.invoke_props_dialog(self) 

        return self.execute(context)

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #automatically define settings if user has been using a dialog box
        if (self.pop_dialog):
            if (self.pop_influence_options=="all"):
                  self.use_sel_all = True
            else: self.scene_name = bpy.context.scene
            self.set_value = self.pop_influence_value

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter

        if (self.use_sel_all):
            psys = emitter.scatter5.get_psys_selected(all_emitters=True)

        #if input is scene, batch toggle all psys of scene
        elif (self.scene_name!=""):
            assert (self.scene_name in bpy.data.scenes)
            psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys()

        #if input is group, batch toggle all element of group
        elif (self.group_name!=""):
            assert (emitter is not None)
            g = emitter.scatter5.particle_groups[self.group_name]
            psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

        #if inputis group, just toggle psyname
        elif (self.psy_name!=""):
            assert (emitter is not None)
            psys = [ emitter.scatter5.particle_systems[self.psy_name] ]

        #else we batch on all emitter psys
        elif (self.emitter_name!=""):
            assert (emitter is not None)
            psys = emitter.scatter5.particle_systems[:]

        for p in psys:

            objs = p.get_instance_objs()
            
            if (not len(objs)):
                return {'FINISHED'}

            if (self.set_value=="auto"):
                  set_value = any(o.display_type=="TEXTURED" for o in objs)
                  set_value = "BOUNDS" if set_value else "TEXTURED"
            else: set_value = self.set_value

            for o in objs: 
                if (o.display_type!=set_value):
                    o.display_type = set_value

            continue

        return {'FINISHED'}


# class SCATTER5_OT_batch_optimization(bpy.types.Operator):

#     bl_idname      = "scatter5.batch_optimization"
#     bl_label       = translate("Batch-Set Objects Bounding-Box")
#     bl_description = translate("Toggle between 'Bounding-Box' or 'Textured' display for all original object(s) used as instances by of the scatter-system(s).\nPlease note that this might impact other scatter-system(s) as well.")
#     bl_options     = {'INTERNAL', 'UNDO'}

#     #interface
#     pop_dialog : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
#     pop_influence_options : bpy.props.EnumProperty(
#         name=translate("Influence"),
#         default="all",
#         items=[("sel",translate("Selected System(s)"),"",),
#                ("all",translate("All System(s)"),"",),
#                ],) 


#     #replicate optimization features
#     #TODO, but would be nasty...


#     #internal settings
#     use_sel_all : bpy.props.BoolProperty(options={"SKIP_SAVE",},)
#     psy_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     group_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     emitter_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     scene_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     set_value : bpy.props.StringProperty(default="auto", options={"SKIP_SAVE",},)

#     def draw(self, context):
#         layout = self.layout
        
#         layout.prop(self,"pop_influence_options",)
#         layout.prop(self,"pop_influence_value",)
#         layout.separator(factor=0.5)

#         psys = bpy.data.objects[0].scatter5.get_psys_selected(all_emitters=True) if (self.pop_influence_options=="sel") else bpy.context.scene.scatter5.get_all_psys()
#         objs = [o for p in psys for o in p.get_instance_objs() ]

#         layout.label(text=translate("Apply to")+f" {len(psys)} "+translate("Scatter-System(s)")+" → "+f" {len(objs)} "+translate("Objects"),)

#         return None

#     def invoke(self, context, event):

#         if (self.pop_dialog):
#             return bpy.context.window_manager.invoke_props_dialog(self) 

#         return self.execute(context)

#     def execute(self, context):

#         scat_scene = context.scene.scatter5

#         #automatically define settings if user has been using a dialog box
#         if (self.pop_dialog):
#             if (self.pop_influence_options=="all"):
#                   self.use_sel_all = True
#             else: self.scene_name = bpy.context.scene
#             self.set_value = self.pop_influence_value

#         #Get Emitter (will find context emitter if nothing passed)
#         emitter = bpy.data.objects.get(self.emitter_name)
#         if (emitter is None):
#             emitter = scat_scene.emitter

#         if (self.use_sel_all):
#             psys = emitter.scatter5.get_psys_selected(all_emitters=True)

#         #if input is scene, batch toggle all psys of scene
#         elif (self.scene_name!=""):
#             assert (self.scene_name in bpy.data.scenes)
#             psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys()

#         #if input is group, batch toggle all element of group
#         elif (self.group_name!=""):
#             assert (emitter is not None)
#             g = emitter.scatter5.particle_groups[self.group_name]
#             psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

#         #if inputis group, just toggle psyname
#         elif (self.psy_name!=""):
#             assert (emitter is not None)
#             psys = [ emitter.scatter5.particle_systems[self.psy_name] ]

#         #else we batch on all emitter psys
#         elif (self.emitter_name!=""):
#             assert (emitter is not None)
#             psys = emitter.scatter5.particle_systems[:]

#         for p in psys:

#             objs = p.get_instance_objs()
            
#             if (not len(objs)):
#                 return {'FINISHED'}

#             if (self.set_value=="auto"):
#                   set_value = any(o.display_type=="TEXTURED" for o in objs)
#                   set_value = "BOUNDS" if set_value else "TEXTURED"
#             else: set_value = self.set_value

#             for o in objs: 
#                 if (o.display_type!=set_value):
#                     o.display_type = set_value

#             continue

#         return {'FINISHED'}



#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_UL_list_scatter_small,
    SCATTER5_UL_list_scatter_large,
    SCATTER5_UL_list_scatter_stats,

    SCATTER5_OT_group_psys,
    SCATTER5_OT_batch_toggle,
    SCATTER5_OT_batch_randomize,

    SCATTER5_OT_move_interface_items,
    SCATTER5_OT_generic_list_move,

    SCATTER5_OT_quick_lister,
    
    SCATTER5_OT_batch_bounding_box,

    )
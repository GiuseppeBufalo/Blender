
#####################################################################################################
#
# ooooo     ooo ooooo      ooo        ooooo
# `888'     `8' `888'      `88.       .888'
#  888       8   888        888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo   .oooo.o
#  888       8   888        8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888  d88(  "8
#  888       8   888        8  `888'   888  888ooo888  888   888   888   888  `"Y88b.
#  `88.    .8'   888        8    Y     888  888    .o  888   888   888   888  o.  )88b
#    `YbodP'    o888o      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P' 8""888P'
#
#####################################################################################################

#Note that i'm not consistent, and some menus are not here select


import bpy
import os
import json

from .. resources.icons import cust_icon
from .. resources.translate import translate
from .. resources import directories

from .. utils.extra_utils import is_rendered_view
from .. utils.str_utils import word_wrap

from .. scattering.copy_paste import is_BufferCategory_filled

from . import ui_creation
from . import ui_templates


#  .oooooo..o           oooo                          .    o8o                             ooo        ooooo
# d8P'    `Y8           `888                        .o8    `"'                             `88.       .888'
# Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.         888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b        8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#      `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888        8  `888'   888  888ooo888  888   888   888   888
# oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888        8    Y     888  888    .o  888   888   888   888
# 8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'



class SCATTER5_MT_selection_menu(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_selection_menu"
    bl_label       = ""
    bl_description = ""

    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        scat_scene   = bpy.context.scene.scatter5
        emitter      = context.pass_ui_arg_emitter 
        psys         = emitter.scatter5.particle_systems
        group_active = emitter.scatter5.get_group_active()
        psy_active   = emitter.scatter5.get_psy_active()
        psys_sel     = emitter.scatter5.get_psys_selected()

        #Select All 

        is_some_sel = any(p.sel for p in emitter.scatter5.particle_systems)
        is_addonprefs = (context.space_data.type=="PREFERENCES")

         
        #selection operators
        
        if (not is_addonprefs):

            if (len(psys_sel)==len(psys)):
                seltxt = translate("De-Select All System(s)")+f" [{len(psys)}]"
                selicon = cust_icon("W_GROUP_TOGGLE_SEL_NONE")
            else:
                seltxt = translate("Select All System(s)")+f" [{len(psys)}]"
                selicon = cust_icon("W_GROUP_TOGGLE_SEL_ALL")

            sel = layout.row()
            sel.enabled = bool(len(psys))
            op = sel.operator("scatter5.toggle_selection", text=seltxt, icon_value=selicon,)
            op.emitter_name = emitter.name

            layout.separator()

        
        #group

        _ = translate("Group") + translate("Ungroup") #For biome reader version, they'll need this translation
        
        sub = layout.row(align=True)
        sub.enabled = is_some_sel
        sub.menu("SCATTER5_MT_selection_menu_sub_groups",text=translate("Group Selected")+f" [{len(psys_sel)}]", icon="OUTLINER_COLLECTION")

        sub = layout.row(align=True)
        ungroup_enabled = is_some_sel
        if ( is_some_sel and all( (p.group=="") for p in psys_sel) ):
            ungroup_enabled = False
        sub.enabled = ungroup_enabled
        op = sub.operator("scatter5.group_psys",text=translate("Ungroup Selected")+f" [{len(psys_sel)}]", icon="GROUP")
        op.emitter_name = emitter.name
        op.action = "UNGROUP"

        layout.separator()
        

        #lock

        if (not is_addonprefs):
            
            sub = layout.row(align=True)
            sub.enabled = bool(len(psys_sel))
            op = sub.operator("scatter5.exec_line", icon="LOCKED", text=translate("Lock Selected")+f" [{len(psys_sel)}]")
            op.api = f"[p.lock_all() for p in psys_sel]"
            op.description = translate("Lock/unlock the scatter-system(s). Once locked, it will be impossible to interact with the settings. No signal will be sent to the scatter engine when you tweak a property, and their interface will be disabled.")

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys_sel))
            op = sub.operator("scatter5.exec_line", icon="UNLOCKED", text=translate("Unlock Selected")+f" [{len(psys_sel)}]")
            op.api = f"[p.unlock_all() for p in psys_sel]"
            op.description = translate("Lock/unlock the scatter-system(s). Once locked, it will be impossible to interact with the settings. No signal will be sent to the scatter engine when you tweak a property, and their interface will be disabled.")

            layout.separator()
            
        #randomize

        if (not is_addonprefs):

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys_sel))
            op = sub.operator("scatter5.batch_randomize", icon_value=cust_icon("W_DICE"), text=translate("Randomize Selected")+f" [{len(psys_sel)}]")
            op.context_selection=True
            
            layout.separator()
            
        #show color 

        if (not is_addonprefs):

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys))
            op = sub.operator("scatter5.set_solid_and_object_color",text=translate("Set Viewport Display Colors"), icon="RESTRICT_COLOR_ON",)
            op.mode = "restore" if ((context.space_data.shading.type=="SOLID") and (context.space_data.shading.color_type=="OBJECT")) else "set"

            layout.separator()
            
        #direct nodetree access

        row = layout.row()
        row.enabled = (psy_active is not None)
        op = row.operator("scatter5.open_editor", text=translate("Reveal Active-System Engine"), icon="NODETREE",)
        op.editor_type = "GeometryNodeTree"
        op.instructions = f"area.spaces[0].pin = True ; area.spaces[0].node_tree = bpy.data.objects['{emitter.name}'].scatter5.get_psy_active().get_scatter_mod().node_group"
        op.description = translate("Each scatter layers are based on a complex geometry-node nodetree. If you're an advanced user, you are able to precisely change the scatter-engine core nodetree at will, in order to, for example, add new features, or change precise algorithmic behaviors. This operator will reveal the active system nodetree in a blender node editor.")

        layout.separator()

        #Copy 

        row = layout.row()
        row.enabled = is_some_sel
        op = row.operator("scatter5.copy_paste_systems",text=translate("Copy Selected System(s)")+f" [{len(psys_sel)}]",icon="DUPLICATE")
        op.emitter_name = emitter.name
        op.copy = True

        #Paste 

        from .. scattering.copy_paste import is_BufferSystems_filled

        row = layout.row() 
        row.enabled = is_BufferSystems_filled()
        op = row.operator("scatter5.copy_paste_systems",text=translate("Paste System(s)"),icon="DUPLICATE")
        op.emitter_name = emitter.name
        op.paste = True

        row = layout.row()
        row.enabled = is_BufferSystems_filled()
        op = row.operator("scatter5.copy_paste_systems",text=translate("Paste System(s) & Synchronize"),icon="DUPLICATE")
        op.emitter_name = emitter.name
        op.paste = True
        op.synchronize = True

        #3D view special, this menu is also available from addon prefs
        
        layout.separator()

        row = layout.row()
        row.enabled = is_some_sel
        row.menu("SCATTER5_MT_preset_menu_uilist",text=translate("Apply Preset to Selected")+f" [{len(psys_sel)}]",icon="PRESET",)

        
        #Remove all System 
        
        if (not is_addonprefs):

            layout.separator()

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys))
            op = sub.operator("scatter5.remove_system",text=translate("Clear All System(s)")+f" [{len(psys)}]", icon="TRASH")
            op.emitter_name = emitter.name
            op.method  = "clear"
            op.undo_push = True
            
        return None


class SCATTER5_MT_selection_menu_sub_groups(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_selection_menu_sub_groups"
    bl_label       = ""
    bl_description = ""

    def __init__(self):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter

        emitter.scatter5.cleanse_unused_particle_groups()

        return None
        
    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        layout     = self.layout
        scat_scene = bpy.context.scene.scatter5
        emitter    = context.pass_ui_arg_emitter 
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected()

        layout.enabled = bool(len(psys_sel))

        for g in emitter.scatter5.particle_groups: 

            sub = layout.row(align=True)
            op = sub.operator("scatter5.group_psys",text=g.name, icon="GROUP")
            op.emitter_name = emitter.name
            op.action = "GROUP"
            op.name = g.name

        layout.separator()

        sub = layout.row(align=True)
        op = sub.operator("scatter5.group_psys",text=translate("New Group"), icon="ADD")
        op.emitter_name = emitter.name
        op.action = "NEWGROUP"
        op.name = "MyGroup"

        return None 


# ooooo   ooooo                           .o8                          ooo        ooooo
# `888'   `888'                          "888                          `88.       .888'
#  888     888   .ooooo.   .oooo.    .oooo888   .ooooo.  oooo d8b       888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo   .oooo.o
#  888ooooo888  d88' `88b `P  )88b  d88' `888  d88' `88b `888""8P       8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888  d88(  "8
#  888     888  888ooo888  .oP"888  888   888  888ooo888  888           8  `888'   888  888ooo888  888   888   888   888  `"Y88b.
#  888     888  888    .o d8(  888  888   888  888    .o  888           8    Y     888  888    .o  888   888   888   888  o.  )88b
# o888o   o888o `Y8bod8P' `Y888""8o `Y8bod88P" `Y8bod8P' d888b         o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P' 8""888P'


class SCATTER5_PT_scatter_preset_header(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scatter_preset_header"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout

        addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
        scat_scene = bpy.context.scene.scatter5
        scat_op = scat_scene.operators.add_psy_preset
        
        preset_exists = os.path.exists(scat_op.preset_path)

        #Preset Name

        #layout.label(text=translate("Not Preset Chosen Yet") if not preset_exists else os.path.basename(scat_op.preset_path),)

        #Emitter

        # layout.separator(factor=0.33)

        # col = layout.column(align=True)
        # txt = col.row()
        # txt.label(text=translate("Emitter")+" :")

        # op = col.operator("scatter5.exec_line",text=translate("Refresh m² Estimation"),icon="SURFACE_NSURFACE",)
        # op.api = "bpy.context.scene.scatter5.emitter.scatter5.estimate_square_area()"
        # op.description = translate("Recalculate Emitter Surface m² Estimation")
        
        #Preset Path 

        layout.separator(factor=0.15)

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Active Preset")+" :")
        
        path = col.row(align=True)
        path.alert = not preset_exists
        path.prop(scat_op,"preset_path",text="")
        path.operator("scatter5.open_directory",text="",icon="FILE_TEXT").folder = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".preset")
            
        #Options 

        col.separator(factor=0.6)

        col = layout.column(align=True)
        col.label(text=translate("Utility")+" :",)

        ui_templates.bool_toggle(col, 
              prop_api=scat_op,
              prop_str="preset_find_color", 
              label=translate("Use Material Display Color"), 
              left_space=False,
              )
        
        col.separator(factor=0.5)

        ui_templates.bool_toggle(col, 
              prop_api=scat_op,
              prop_str="preset_find_name", 
              label=translate("Use Instance Name"), 
              left_space=False,
              )

        #Library 

        col.separator(factor=0.6)

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Preset Library")+" :")

        col.operator("scatter5.reload_preset_gallery",text=translate("Reload Preset Library"), )#icon="FILE_REFRESH")

        col.separator()
        col.operator("scatter5.open_directory",text=translate("Open Preset Library"), ).folder = directories.lib_presets #icon="FOLDER_REDIRECT")

        #Create 

        col.separator(factor=0.6)

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Create Preset")+" :")

        col.operator("scatter5.save_operator_preset", text=translate("New Preset(s) from Selected"),)#icon="FILE_NEW")

        col.separator()
        op = col.operator("scatter5.generate_thumbnail",text=translate("Render Active Thumbnail"),)#icon="RESTRICT_RENDER_OFF")
        op.json_path = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".preset")
        op.render_output = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".jpg")

        return None


class SCATTER5_PT_per_settings_category_header(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_per_settings_category_header"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):

        layout     = self.layout
        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected()

        #Msg if no system 
        if (psy_active is None):
            layout.label(text=translate("No System(s) Active"), icon="INFO",)
            return 

        #get UILayout arg
        s_category = context.pass_ui_arg_popover.path_from_id().split(".")[-1]
        is_locked  = psy_active.is_locked(s_category)

        #### Category Operators

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Operators")+" :")
        operators = col.row(align=True)
        operators.scale_x = 5

        #COPY
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5
        op = rwoo.operator("scatter5.copy_paste_category",text="", icon_value=cust_icon("W_BOARD_COPY"),)
        op.copy = True
        op.single_category = s_category
            
        #PASTE
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5
        rwoo.enabled = is_BufferCategory_filled(s_category)
        op = rwoo.operator("scatter5.copy_paste_category",text="", icon_value=cust_icon("W_BOARD_PASTE"),)
        op.paste = True
        op.single_category = s_category

        #RESET
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5 
        op = rwoo.operator("scatter5.reset_settings",text="", icon="LOOP_BACK")
        op.single_category = s_category

        #APPLY
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5
        op = rwoo.operator("scatter5.apply_category",text="", icon_value=cust_icon("W_BOARD_APPLY"),)
        op.single_category = s_category
        op.pop_dialog = True
            
        #### Lock Unlock

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Operators")+" :")
        locking = col.row(align=True)
        locking.scale_x = 2.5

        op = locking.operator("scatter5.exec_line", text="", icon="UNLOCKED", depress=not is_locked)
        op.api = f"psy_active.{s_category}_locked = False"
        op.description = translate("Lock/unlock this scatter-system settings category. Once the category is locked, it will be impossible to interact with its settings. No signal will be sent to the scatter engine when you tweak a property, and their interface will be disabled.")

        op = locking.operator("scatter5.exec_line", text="", icon="LOCKED", depress=is_locked )
        op.api = f"psy_active.{s_category}_locked = True"
        op.description = translate("Lock/unlock this scatter-system settings category. Once the category is locked, it will be impossible to interact with its settings. No signal will be sent to the scatter engine when you tweak a property, and their interface will be disabled.")

        #### Category Reset/Preset 

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Presets")+" :")
        row = col.row(align=True)
        row.menu("SCATTER5_MT_preset_menu_header", text=translate("Apply a Preset"),)

        #### Category Synchronization

        #INFO note that mask is currently not supported by synchronization feature currently in 5.1 release
        if (scat_scene.factory_synchronization_allow and psy_active.is_synchronized(s_category)):
            
            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Settings Synchronized")+" :")

            sync_channels = scat_scene.sync_channels
            lbl = layout.row()
            lbl.alert = True
            ch = [ch for ch in sync_channels if ch.psy_settings_in_channel(psy_active.name, s_category,)][0]
            lbl.prop(ch,s_category,text=translate("Disable Synchronization"),icon_value=cust_icon("W_ARROW_SYNC"), invert_checkbox=True,)

        #### Sepcial Operators

        if ((s_category=="s_distribution") and (psy_active.s_distribution_method!="manual_all")):

            #Export to manual 

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Manual Edition")+" :")

            ope = col.row()
            ope.operator_context = "INVOKE_DEFAULT"
            ope.operator("scatter5.manual_convert_from_procedural", text=translate("Convert to Manual Distribution"), icon="BRUSHES_ALL")

        if (s_category=="s_display"):

            #Visualize

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Display Color")+" :")

            ope = col.row()
            condition = (bpy.context.space_data.shading.type == 'SOLID') and (bpy.context.space_data.shading.color_type == 'OBJECT')
            op = ope.operator("scatter5.set_solid_and_object_color",text=translate("Set Viewport Display Colors"), icon="COLOR", depress=condition)
            op.mode = "restore" if condition else "set"

        if (s_category in ("s_display","s_instances",)):

            #Bounding Box

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Object(s) Bounding-Box")+" :")

            ope = col.row()
            condition = (bpy.context.space_data.shading.type == 'SOLID') and (bpy.context.space_data.shading.color_type == 'OBJECT')
            op = ope.operator("scatter5.batch_bounding_box",text=translate("Toggle Bounding-Box"), icon="CUBE",)
            op.emitter_name = emitter.name
            op.psy_name = psy_active.name

        layout.separator(factor=0.3)

        return None


class SCATTER5_PT_mask_header(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_mask_header"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}


    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter

        col = layout.column()
        txt = col.row()
        txt.label(text=translate("Mask-Data :"))
        prp = col.row()
        prp.operator("scatter5.refresh_every_masks",text=translate("Recalculate All Masks"),icon="FILE_REFRESH")
        
        return None


class SCATTER5_PT_graph_subpanel(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_graph_subpanel"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        dialog = context.pass_ui_arg_popover

        #Copy/Paste

        layout.label(text=translate("Graph Copy/Paste")+" :")

        row = layout.row(align=True)

        ope = row.row(align=True)
        ope.scale_x = 5
        op = ope.operator("scatter5.graph_copy_preset", text="", icon_value=cust_icon("W_BOARD_COPY"),)
        op.source_api=dialog.source_api
        op.mapping_api=dialog.mapping_api
        op.copy=True
        
        ope = row.row(align=True)
        ope.scale_x = 5
        from .. curve.fallremap import BufferGraphPreset
        ope.enabled = (BufferGraphPreset is not None)
        op = ope.operator("scatter5.graph_copy_preset", text="", icon_value=cust_icon("W_BOARD_PASTE"),)
        op.source_api=dialog.source_api
        op.mapping_api=dialog.mapping_api
        op.paste=True

        #Apply Selected, only for scatter-systems

        if (".nodes[" in dialog.source_api):
            
            ope = row.row(align=True)
            ope.scale_x = 5
            op = ope.operator("scatter5.graph_copy_preset", text="", icon_value=cust_icon("W_BOARD_APPLY"),)
            op.source_api=dialog.source_api
            op.mapping_api=dialog.mapping_api
            op.apply_selected=True

        #other options

        layout.label(text=translate("Widgets Defaults")+" :")

        col = layout.column(align=True)
        col.prop(dialog,"op_move")
        col.prop(dialog,"op_size")

        return None

#   .oooooo.                             .                             .        oooooooooo.
#  d8P'  `Y8b                          .o8                           .o8        `888'   `Y8b
# 888           .ooooo.  ooo. .oo.   .o888oo  .ooooo.  oooo    ooo .o888oo       888      888  .ooooo.   .ooooo.   .oooo.o
# 888          d88' `88b `888P"Y88b    888   d88' `88b  `88b..8P'    888         888      888 d88' `88b d88' `"Y8 d88(  "8
# 888          888   888  888   888    888   888ooo888    Y888'      888         888      888 888   888 888       `"Y88b.
# `88b    ooo  888   888  888   888    888 . 888    .o  .o8"'88b     888 .       888     d88' 888   888 888   .o8 o.  )88b
#  `Y8bood8P'  `Y8bod8P' o888o o888o   "888" `Y8bod8P' o88'   888o   "888"      o888bood8P'   `Y8bod8P' `Y8bod8P' 8""888P'



class SCATTER5_PT_docs(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_docs"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    txt_block_op_behavior = translate("Optionally, you are able to change the behavior of the operator by going in the popover menu, right next to the operator button. Change these settings to directly set-up masks, set-up optimization features, or preciesely define the future surface(s) that your scatter will populate for example.")
    txt_block_feature_hover = translate("Please, hover your cursor on the feature toggles of your choice to read each feature description.")
    txt_block_disinfo = translate("This distribution method has an impact on the workflow, please pay attention to the following information.")
    txt_block_grinfo = translate("This is a group features. These group settings will apply on all scatters while they are part of this group.")

    panel_docs = {
        #Creation Panel
        "ui_create_densit" : { 
            "text": translate("Scatter the selected objects located in your viewport or in your asset browser with the chosen density per square area in chosen unit scale.\nNote that the density will be converted to /m² automatically.")+"\n\n"+txt_block_op_behavior,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_density_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_preset" : { 
            "text": translate("Scatter the selected objects located in your viewport or in your asset browser with the selected preset. Preset files are storing the plugin settings information & their saved values, you are able to create and render your own preset in the header menu if needed.")+"\n\n"+txt_block_op_behavior,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_preset_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_manual" : { 
            "text": translate("Scatter the selected objects located in your viewport or in your asset browser and directly enter the manual workflow. Manual-mode is an entirely new scattering experience, you are able to precisely place / move / rescale / rotate instances with a subset of various brushes.")+"\n\n"+translate("Note that you are able to change the behavior of this operator in the popover menu right next to the operator button."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_manual_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_quick" : { 
            "text": translate("The 'Quick Scatter' operator is a shortcut based workflow designed to be quick and effective. Scatter the selected objects in the viewport or asset browser depending on where you called the shortcut. You can change the shortcut in the popover settings.")+"\n\n"+txt_block_op_behavior,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_quick_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_biomes" : { 
            "text": translate("Open your biome library from where you will be able to load new biomes into your designated surfaces, our biome-system will first load the assets and scatter the encoded preset layers one by one. You are able to create your own biomes in the biome interface header or in the export panel.")+"\n\n"+txt_block_op_behavior+translate("Note that this menu is also available in the biome interface header."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_biome_scatter",
            "url_title":translate("Online Manual"),
            },
        #Tweaking Panel
        "ui_tweak_select" : { 
            "text": translate("Select or set active your scatter-system in the interface below. Selecting multiple system(s) at the same time is key in order to batch change properties, this the most powerful functionality of our plugin; by pressing 'ALT' while changing the value of any settings, toggles or pointers you will apply the property value to all selected system(s).\n\nIf you are working with a lot of scatter-system(s) in your scene, we advise you to close this panel and use the Lister interface in our plugin manager or use the quick-lister shortcut (by default 'SHIFT+CTRL+Q').\n\n Pro-Tip: pressing the 'ALT' or 'SHIFT' key in the system-list will isolate or add the selection."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_list_interfaces",
            "url_title":translate("Online Manual"),
            },
        "s_surface" : { 
            "text": translate("By default, any new scatter will use the chosen emitter mesh as the distribution surface. With 5.3 you are able to pick surface(s) of your choice independently from the emitter.\n\nNote that if you choose to scatter a system on many surfaces, make sure that the UV(s), vertex-color(s) or vertex-group(s) attributes are share across all surfaces, otherwise the pointers will highlight in red."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_surfaces",
            "url_title":translate("Online Manual"),
            },
        "s_distribution" : { 
            "text": translate("In order to scatter anything we need to distribute points on your designated surface(s) first! Below you will be able to choose between a variety of distribution algorithm.\n\nPlease, hover on the distribution method of your choice to read their full description."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution",
            "url_title":translate("Online Manual"),
            },
        "s_mask" : { 
            "text": translate("In the culling-mask category you are able to remove the scattered points non-destructively with the help of various masking features.")+"\n\n"+translate("Note that masks based on the topology of your surface(s) will be faster to compute.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureCullingmask",
            "url_title":translate("Online Manual"),
            },
        "s_scale" : { 
            "text": translate("Have complete control over the scale of your instances.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScale",
            "url_title":translate("Online Manual"),
            },
        "s_rot" : { 
            "text": translate("Have complete control over your instances orientations.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureRotation",
            "url_title":translate("Online Manual"),
            },
        "s_pattern" : { 
            "text": translate("Influence your instances density and scale from a chosen texture-data. Scatter texture-data are re-usable datablocks similar to the now obsolete blender texture data."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeaturePattern",
            "url_title":translate("Online Manual"),
            },
        "s_abiotic" : { 
            "text": translate("The abiotic factors are all factors related to your surface(s) topology that can have an influence your distribution density or scale.")+"\n\n"+txt_block_feature_hover, 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureAbiotic",
            "url_title":translate("Online Manual"),
            },
        "s_proximity" : { 
            "text": translate("Influence your distribution density, orientation or scale by proximity of given elements.")+"\n\n"+txt_block_feature_hover, 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureProximity",
            "url_title":translate("Online Manual"),
            },
        "s_ecosystem" : { 
            "text": translate("Ecosystem(s) gives you the ability of defining relationship rules in-between your scatter-system(s)."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureEcosystem",
            "url_title":translate("Online Manual"),
            },
        "s_push" : { 
            "text": translate("Offset your instances locations.")+"\n\n"+txt_block_feature_hover, 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOffset",
            "url_title":translate("Online Manual"),
            },
        "s_wind" : { 
            "text": translate("Create the illusion of a wind-simulation by tilting your instances.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureWind",
            "url_title":translate("Online Manual"),
            },
        "s_visibility" : {
            "text": translate("Control how many instances are visible during the various rendering states, for optimizing your work-time performance.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOptimization",
            "url_title":translate("Online Manual"),
            },
        "s_instances" : { 
            "text": translate("Control how your instances are assigned to the scattered points. Here you are able to add or remove objects to the instance list.")+"\n\n"+translate("You are able to directly select object(s) from this list, press the ALT key while doing so to re-center the view."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstancing",
            "url_title":translate("Online Manual"),
            },
        "s_display" : { 
            "text": translate("Change how your instances are displayed in the viewport, for optimizing your work-time performance."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOptimization&section_display_as",
            "url_title":translate("Online Manual"),
            },
        #Extra Panel
        "ui_extra_displace" : { 
            "text": translate("Quickly add displacement effects to the active object"), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOptimization&section_display_as",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_vgs" : { 
            "text": translate("Generate useful vertex-data masks, either to influence your scatter, your shaders, or else.."), 
            "url" : "https://www.geoscatter.com/documentation",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_masterseed" : { 
            "text": translate("The master seed influence every other Geo-Scatter seeds in this .blend, increment this seed to iterate between various scattering possibilities non-destructively."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureExtra&article_master_seed",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_synch" : { 
            "text": translate("Synchronize scattering settings of the chosen scatter-system(s) together.")+"\n\n"+translate("How to use: create a synchronization channel, add system(s) to the channel, define which settings categories are affected.")+"\n\n"+translate("Changing the values of one system will also apply the value to all system(s) in the channel."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureExtra&article_synchronization",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_update" : { 
            "text": translate("Few controls update behavior controls."+"\n\n"+txt_block_feature_hover), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOptimization&section_slider_reactivity",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_export" : { 
            "text": translate("Export/convert the selected-system(s) to various object types or scatter format."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureExtra&article_export_to_json",
            "url_title":translate("Online Manual"),
            },
        #Addon prefs popover
        "ui_add_packs" : { 
            "text": translate("ScatPacks are premade libraries containing biomes, presets or assets ready to be used within our plugin. A scatpack format should end with the extension '.scatpack'. Please note that some asset-makers might store their assets outside of our plugin scatter-library, if it is the case, please add the path to the context asset library folder in the environment path panel.\n\nAnyone is free to create his own biome pack! You can make your own '.scatpack' by renaming a compressed .zip extension. The content of the zip should respect the '_presets_'/'_biomes_' folder hierarchy. Be careful to only zip what is yours & respect assets licenses!"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation",
            "url_title":translate("Online Manual"),
            },
        "ui_add_environment" : { 
            "text": translate("Some biomes packs makers might store their assets outside of our plugin, their scatpacks will not contain any .blend files! If it is the case, you will need to make sure that the .blend files related to the biomes can be found in the list(s) below"), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation&article_define_environment_paths",
            "url_title":translate("Online Manual"),
            },
        "ui_add_paths" : { 
            "text": translate("Change the location of your scatter-library. The scatter-library contains all your biomes, presets & more."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation&section_manage_your_scatter_library",
            "url_title":translate("Online Manual"),
            },
        "ui_add_browser" : { 
            "text": translate("Our scattering plugin works flawlessly with the blender asset browser, as you can directly Scatter the selected Assets. It might be worth it to also install your assets as an asset-browser library. This is done in the blender preferences editor ‘File Paths’.\n\nIf your pack does not support blender asset browser, you are able to automatically convert many blends of a given folder to asset-ready ready blends Hereby. This process will save the blends to the current version you are running, be aware of this please!\n\nNested folders are not supported. Please do not run this operator from a blend file located in the folder you want to process. Please use this operator carefully, the result cannot be undone. Do not use this operator from an unsaved blend file.`\n\nOpen the console window to see progress."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation&section_don_t_have_the_time_to_read_",
            "url_title":translate("Online Manual"),
            },
        "ui_add_workflow" : { 
            "text": translate("By default you will need to change your emitter by quitting the active panel and going back to the emitter panel. However there are alternative workflow available"), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&article_switching_emitter_s",
            "url_title":translate("Online Manual"),
            },
        #Get flowmap painter info
        "get_flowmap" : { 
            "text": translate("A flowmap is a baked directional information. The 2D directional vectors, ranging from -1 to 1, is remapped to 0-1, then baked into the Red and Green channel of an image texture or color-attribute. The blue channel is un-used and can be utilized as an additional strenght information.\n\nFlowmaps cannot be created natively in blender. You'll need to download the Flowmap-painter addon by Clemens Beute on Gumroad.\nThen use his addon in Vertex-paint while using the UV Space color option."),
            "url" : "https://www.blendernation.com/2021/03/03/free-flow-map-painter-addon/",
            "url_title":translate("Flowmap Painter"),
            },
        #Features based on camera 
        "nocamera_info" : { 
            "text": translate("This functionality relies on the active camera, but an active camera can't be found in this scene.\n\nPlease add a camera, or disable this feature"), 
            "url" : "",
            "url_title":"",
            },
        #distribution availability
        "distinfos_clumping" : {
            "text": txt_block_disinfo+"\n\n"+translate("Exclusive feature(s) Available:\n• Clump Scale Influence\n• Clump Normal Influence"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_clump_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_faces" : {
            "text": txt_block_disinfo+"\n\n"+translate("Exclusive feature(s) Available:\n• Face Scale Influence"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_mesh_element_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_edges" : {
            "text": txt_block_disinfo+"\n\n"+translate("Exclusive feature(s) Available:\n• Edge Scale Influence"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_mesh_element_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_volume" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some feature(s) are not Available:\n• Mask>Vertex Group\n• Mask>Color-Attribute\n• Mask>Image\n• Mask>Material\n• Abiotic>Slope\n• Abiotic>Orientation\n• Abiotic>Curvature\n• Abiotic>Border\n•Visibility>Area-Preview\n\nAdditional Information:\n•Features relying on UV space or vertex-colors will be inconsistent"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_volume_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_manual" : {
            "text": txt_block_disinfo+"\n\n"+translate("Please be aware that all the features from the procedural workflow still applies on the points generated by manual-mode. The procedural features can impact your manual-distribution on their rotation/scale and can actually mask some areas of your distribution as well."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_manual_distribution",
            "url_title":translate("About Distribution"),
            },
        #Beginner interface explanations
        "s_beginners_remove" : {
            "text": translate("The Geo-Scatter Engine has a lot of features! And some are much more advanced than others! The Biome-Reader interface is designed for beginners, access to these advanced features can be achieved with our Geo-Scatter plugin. In the meanwhile you are able to disable these Features in this panel."),
            "url" : "",
            "url_title":"",
            },
        #group category features Explanations
        "s_gr_distribution" : {
            "text": txt_block_grinfo+"\n\n"+translate("This category of features is dedicated to influencing the distribution of the scatter-system(s) member of this group."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        "s_gr_mask" : {
            "text": txt_block_grinfo+"\n\n"+translate("This category of features is dedicated to masking the density of all scatter-system(s) member of this group."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        "s_gr_scale" : {
            "text": txt_block_grinfo+"\n\n"+translate("This category of features is dedicated to influencing the scale attribute of the scatter-system(s) member of this group."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        "s_gr_pattern" : {
            "text": txt_block_grinfo+"\n\n"+translate("This category of features is dedicated to masking the density via a scatter-texture data-block of all scatter-system(s) member of this group."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        }

    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        doc_key = context.pass_ui_arg_popover.path_from_id().split(".")[-1]
        doc = self.panel_docs[doc_key]

        word_wrap(layout=layout, active=True, max_char=36, scale_y=0.875, string=doc["text"], alignment="LEFT")

        if (doc["url"]!=""):
            layout.separator()
            link_title = translate("Flowmap Painter") if (doc_key=="get_flowmap") else translate("Online Manual")
            layout.operator("wm.url_open",text=doc["url_title"],icon="URL").url = doc["url"]

        return None


#   .oooooo.             oooo  oooo       ooooo     ooo     .    o8o  oooo   o8o      .
#  d8P'  `Y8b            `888  `888       `888'     `8'   .o8    `"'  `888   `"'    .o8
# 888           .ooooo.   888   888        888       8  .o888oo oooo   888  oooo  .o888oo oooo    ooo
# 888          d88' `88b  888   888        888       8    888   `888   888  `888    888    `88.  .8'
# 888          888   888  888   888        888       8    888    888   888   888    888     `88..8'
# `88b    ooo  888   888  888   888        `88.    .8'    888 .  888   888   888    888 .    `888'
#  `Y8bood8P'  `Y8bod8P' o888o o888o         `YbodP'      "888" o888o o888o o888o   "888"     .8'
#                                                                                         .o..P'
#                                                                                         `Y8P'


class SCATTER5_UL_list_collection_utility(bpy.types.UIList):
    """selection area"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
            
        coll = bpy.context.pass_ui_arg_collection

        row  = layout.row(align=True)
        
        row.prop(item,"name", text="", emboss=False, icon="OUTLINER_OB_EMPTY" if (item.type =="EMPTY") else "OUTLINER_OB_CURVE" if (item.type =="CURVE") else "OUTLINER_OB_MESH")

        #select operator 

        selct = row.row()

        if (bpy.context.mode=="OBJECT"):

            selct.active = (item==bpy.context.object)
            op = selct.operator("scatter5.select_object", emboss=False, text="",icon="RESTRICT_SELECT_OFF" if item in bpy.context.selected_objects else "RESTRICT_SELECT_ON")
            op.obj_name = item.name
            op.coll_name = coll.name
        
        else:
            selct.separator(factor=1.2)

        #remove operator 
        
        ope = row.row(align=False)
        ope.scale_x = 0.9
        op = ope.operator("scatter5.remove_from_coll", emboss=False, text="", icon="TRASH", )
        op.obj_name = item.name
        op.coll_name = coll.name

        return None


class SCATTER5_PT_collection_popover(bpy.types.Panel):
    """popover only used by draw_coll_ptr_prop() """

    bl_idname      = "SCATTER5_PT_collection_popover"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def __init__(self):

        self.coll = bpy.context.pass_ui_arg_collection

        #get breadcrumbs information 

        def get_collection_path(collection=None, path=[]):
            
            for c in bpy.context.scene.collection.children_recursive:
                if (collection.name in c.children):
                    path.insert(0, c.name)
                    get_collection_path(collection=c, path=path)
                    break 

            return path 

        self.breadcrumbs = get_collection_path(collection=self.coll, path=[])
        self.breadcrumbs.insert(0, bpy.context.scene.collection.name)
        self.breadcrumbs.append(self.coll.name)

        return None 

    def draw_breadcrumbs(self, layout):

        col = layout.box().column(align=True)
        col.scale_y = 0.9
        
        for i,name in enumerate(self.breadcrumbs):
            
            is_first = (i==0)
            is_last = (i==len(self.breadcrumbs)-1)
            
            row = col.row(align=True)
            row.alignment = "LEFT"
                
            #intendation
            if (not is_first):
               row.separator(factor=i*0.7)
            
            row.label(text="", icon="DISCLOSURE_TRI_DOWN" if (i!=len(self.breadcrumbs)-1) else "DISCLOSURE_TRI_RIGHT")
            row.label(text=name, icon="OUTLINER_COLLECTION")

        return None 

    def draw(self, context):
        layout = self.layout

        self.draw_breadcrumbs(layout)

        layout.template_list("SCATTER5_UL_list_collection_utility", "", self.coll, "objects", bpy.context.scene.scatter5, "dummy_idx", type="DEFAULT", rows=4,)

        ope = layout.row()
        op = ope.operator("scatter5.add_to_coll", text=translate("Add Viewport Selection"), icon="ADD")
        op.coll_name = self.coll.name

        return None


#   .oooooo.                                    .    o8o                              .oooooo..o               .       .    o8o
#  d8P'  `Y8b                                 .o8    `"'                             d8P'    `Y8             .o8     .o8    `"'
# 888          oooo d8b  .ooooo.   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.        Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
# 888          `888""8P d88' `88b `P  )88b    888   `888  d88' `88b `888P"Y88b        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
# 888           888     888ooo888  .oP"888    888    888  888   888  888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
# `88b    ooo   888     888    .o d8(  888    888 .  888  888   888  888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
#  `Y8bood8P'  d888b    `Y8bod8P' `Y888""8o   "888" o888o `Y8bod8P' o888o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                                                                                                            d"     YD
#                                                                                                                                            "Y88888P'

def creation_operators_draw_visibility(layout, hide_viewport=True, facepreview_allow=True, view_allow=True, cam=True, maxload=True,):

    scat_scene = bpy.context.scene.scatter5
    scat_op    = scat_scene.operators.create_operators
    emitter    = scat_scene.emitter

    #Hide on Creation 
    
    if (hide_viewport):

        ui_templates.bool_toggle(layout, 
            prop_api=scat_op,
            prop_str="f_visibility_hide_viewport", 
            label=translate("Set “Hide Viewport”"), 
            left_space=True,
            )

    #Viewport % Reduction 

    if (view_allow):

        tocol, is_toggled = ui_templates.bool_toggle(layout, 
            prop_api=scat_op,
            prop_str="f_visibility_view_allow", 
            label=translate("Set “Reduce Density”"), 
            left_space=True,
            return_layout=True,
            )
        if is_toggled:

            prop = tocol.column(align=True)
            prop.scale_y = 0.9
            prop.prop(scat_op,"f_visibility_view_percentage",)

            tocol.separator(factor=0.2)

    #Maximal Load

    if (maxload): 

        tocol, is_toggled = ui_templates.bool_toggle(layout, 
            prop_api=scat_op,
            prop_str="f_visibility_maxload_allow", 
            label=translate("Set “Max Amount”"),
            return_layout=True,
            )
        if is_toggled:

            subcol = tocol.column(align=True)
            subcol.scale_y = 0.95
            enum = subcol.row(align=True) 
            enum.prop(scat_op, "f_visibility_maxload_cull_method", expand=True)
            subcol.prop( scat_op, "f_visibility_maxload_treshold")

    #Face preview 
    
    if (facepreview_allow): 

        tocol, is_toggled = ui_templates.bool_toggle(layout, 
            prop_api=scat_op,
            prop_str="f_visibility_facepreview_allow", 
            label=translate("Set “Preview Area”"), 
            left_space=True,
            return_layout=True,
            )
        if is_toggled:

            row = tocol.row(align=True)
            row.scale_y = 0.9
            rowop = row.row(align=True)
            op = rowop.operator("scatter5.facesel_to_vcol", text=translate("Define Area"), icon="RESTRICT_SELECT_OFF", )
            op.surfaces_names = "_!#!_".join( s.name for s in scat_op.get_f_surfaces() )

            tocol.separator(factor=0.2)

    #Camera Optimization 

    if (cam):
        
        tocol, is_toggled = ui_templates.bool_toggle(layout, 
            prop_api=scat_op,
            prop_str="f_visibility_cam_allow", 
            label=translate("Set “Camera Optimization”"), 
            enabled=(bpy.context.scene.camera is not None),
            return_layout=True,
            )
        if is_toggled:

            #Camera Frustum 

            tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, 
                prop_api=scat_op,
                prop_str="f_visibility_camclip_allow", 
                label=translate("Set “Frustum Culling”"), 
                enabled=(bpy.context.scene.camera is not None),
                left_space=False,
                return_layout=True,
                )
            if is_toggled2:
                
                prop = tocol2.column(align=True)
                prop.prop(scat_op, "f_visibility_camclip_cam_boost_xy")

            #Camera Distance Culling 

            tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, 
                prop_api=scat_op,
                prop_str="f_visibility_camdist_allow", 
                label=translate("Set “Distance Culling”"), 
                enabled=(bpy.context.scene.camera is not None),
                left_space=False,
                return_layout=True,
                )
            if is_toggled2:

                prop = tocol2.column(align=True)
                prop.scale_y = 0.9
                prop.prop(scat_op, "f_visibility_camdist_min")
                prop.prop(scat_op, "f_visibility_camdist_max")

    return None 
    
def creation_operators_draw_display(layout,ctxt_operator,):

    scat_scene = bpy.context.scene.scatter5
    scat_op    = scat_scene.operators.create_operators

    ui_templates.bool_toggle(layout, 
        prop_api=scat_op,
        prop_str="f_display_bounding_box", 
        label=translate("Set object(s) “Bounds”"),
        left_space=True,
        )

    if (ctxt_operator=="load_biome"): #special case for biomes: will use placeholder saved within the .biome file

        ui_templates.bool_toggle(layout, 
            prop_api=scat_scene.operators.load_biome,
            prop_str="f_display_biome_allow", 
            label=translate("Set biome(s) “Display As”"),
            left_space=True,
            )

    else: #else, display allow, method option should be available 

        tocol, is_toggled = ui_templates.bool_toggle(layout, 
            prop_api=scat_op,
            prop_str="f_display_allow", 
            label=translate("Set scatte(s) “Display As”"),
            left_space=True,
            return_layout=True,
            )
        if is_toggled:

            tocol.prop(scat_op, "f_display_method", text="")

            if (scat_op.f_display_method=="placeholder_custom"):

                col = tocol.column()
                col.separator(factor=0.5)
                col.prop( scat_op, "f_display_custom_placeholder_ptr",text="")

    return None

def creation_operators_draw_surfaces(layout, ctxt_operator,):

    scat_scene   = bpy.context.scene.scatter5
    emitter      = bpy.context.scene.scatter5.emitter
    scat_op      = getattr(scat_scene.operators,ctxt_operator)
    scat_op_crea = scat_scene.operators.create_operators

    row = layout.row()
    row1 = row.row()
    row1.scale_x = 0.1
    row2 = row.column()
    row2.scale_y = 1.0

    col = row2
    if ( "is_toggled" in locals() ):
        col.enabled = not is_toggled 

    col.prop(scat_op_crea,"f_surface_method", text="")
    col.separator(factor=0.3)

    if (scat_op_crea.f_surface_method=="emitter"):
        pass

        #this interface is already too crowded
        #prop = col.row()
        #prop.enabled = False
        #prop.prop(scat_scene,"emitter", text="", icon_value=cust_icon("W_EMITTER"),)
        
    elif (scat_op_crea.f_surface_method=="object"):
        col.prop(scat_op_crea,"f_surface_object", text="")

    elif (scat_op_crea.f_surface_method=="collection"):
        
        surfcol = col.column(align=True)

        lis = surfcol.box().column(align=True)
        lis.scale_y = 0.85
        
        for i,o in enumerate(scat_op_crea.f_surfaces): 
            if (o.name!=""):
                lisr = lis.row()
                lisr.label(text=o.name)

                #remove given object
                op = lisr.operator("scatter5.exec_line", text="", icon="TRASH", emboss=False,)
                op.api = f"scat_ops.create_operators.f_surfaces[{i}].object = None ; scat_ops.create_operators.f_surfaces.remove({i})"
                op.undo = translate("Remove Predefined Surface(s)")
        
        if ("lisr" not in locals()):
            lisr = lis.row()
            lisr.label(text=translate("No Surface(s) Assigned"))

        #add selected objects & refresh their square area
        op = surfcol.operator("scatter5.exec_line", text=translate("Add Selection"), icon="ADD",)
        op.api = f"bpy.context.scene.scatter5.operators.create_operators.add_selection()"
        op.undo = translate("Add Predefined Surface(s)")

    return None

def creation_operators_draw_security(layout, sec_count=True, sec_verts=True):

    scat_op = bpy.context.scene.scatter5.operators.create_operators

    if (sec_count):

        row = layout.row(align=True)
        col1 = row.column() ; col1.scale_x = 0.2
        col2 = row.column()
        col3 = row.column()
        col1.label(text=" ")
        col2.prop(scat_op,"f_sec_count_allow",text="")
        col3.enabled = scat_op.f_sec_count_allow
        col3.scale_y = 0.87
        col3.prop(scat_op,"f_sec_count",text=translate("Heavy Scatter's"),)

    if (sec_verts):

        row = layout.row(align=True)
        col1 = row.column() ; col1.scale_x = 0.2
        col2 = row.column()
        col3 = row.column()
        col1.label(text=" ")
        col2.prop(scat_op,"f_sec_verts_allow",text="")
        col3.enabled = scat_op.f_sec_verts_allow
        col3.scale_y = 0.87
        col3.prop(scat_op,"f_sec_verts",text=translate("Heavy Object's"),)

    return None 

def creation_operators_draw_mask(layout,ctxt_operator):

    scat_scene = bpy.context.scene.scatter5
    emitter    = bpy.context.scene.scatter5.emitter
    scat_op    = getattr(scat_scene.operators,ctxt_operator)

    row = layout.row()
    row1 = row.row()
    row1.scale_x = 0.1
    row2 = row.column()
    row2.scale_y = 1.0

    row2.prop( scat_op, "f_mask_action_method",text="",)
    f_mask_action_method = getattr(scat_op,"f_mask_action_method")
    
    row2.separator(factor=0.2)

    if (f_mask_action_method!="none"):

        row2.prop( scat_op, "f_mask_action_type",text="",)
        f_mask_action_type = getattr(scat_op,"f_mask_action_type")

        if (f_mask_action_method=="assign"):

            row2.separator(factor=0.2)

            if (f_mask_action_type=="vg"):
                slotcol = row2.row(align=True)
                slotcol.prop_search(scat_op, "f_mask_assign_vg", emitter, "vertex_groups", text="")
                
            elif (f_mask_action_type=="bitmap"):
                slotcol = row2.row(align=True)
                slotcol.prop_search(scat_op, "f_mask_assign_bitmap", bpy.data, "images", text="")

            elif (f_mask_action_type=="curve"):
                slotcol = row2.row(align=True)
                slotcol.prop( scat_op, "f_mask_assign_curve_area", text="", icon="CURVE_BEZCIRCLE",)

            slotcol.prop( scat_op, "f_mask_assign_reverse", text="", icon="ARROW_LEFTRIGHT")

    return None 


#   .oooooo.                                    .    o8o                               .oooooo.                   ooooooooo.
#  d8P'  `Y8b                                 .o8    `"'                              d8P'  `Y8b                  `888   `Y88.
# 888          oooo d8b  .ooooo.   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.        888      888 oo.ooooo.        888   .d88'  .ooooo.  oo.ooooo.   .ooooo.  oooo    ooo  .ooooo.  oooo d8b  .oooo.o
# 888          `888""8P d88' `88b `P  )88b    888   `888  d88' `88b `888P"Y88b       888      888  888' `88b       888ooo88P'  d88' `88b  888' `88b d88' `88b  `88.  .8'  d88' `88b `888""8P d88(  "8
# 888           888     888ooo888  .oP"888    888    888  888   888  888   888       888      888  888   888       888         888   888  888   888 888   888   `88..8'   888ooo888  888     `"Y88b.
# `88b    ooo   888     888    .o d8(  888    888 .  888  888   888  888   888       `88b    d88'  888   888       888         888   888  888   888 888   888    `888'    888    .o  888     o.  )88b
#  `Y8bood8P'  d888b    `Y8bod8P' `Y888""8o   "888" o888o `Y8bod8P' o888o o888o       `Y8bood8P'   888bod8P'      o888o        `Y8bod8P'  888bod8P' `Y8bod8P'     `8'     `Y8bod8P' d888b    8""888P'
#                                                                                                  888                                    888
#                                                                                                 o888o                                  o888o


class SCATTER5_PT_creation_operator_add_psy_density(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_density"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_density")

        col.separator(factor=0.85)
        
        col.label(text=translate("Security Threshold")+":",)
        creation_operators_draw_security(col)

        col.separator(factor=0.85)

        col.label(text=translate("Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_scene, "objects_import_method", text="")

        col.separator(factor=0.85)
        
        col.label(text=translate("Future Scatter's Mask")+":",)
        creation_operators_draw_mask(col,"add_psy_density")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_density")

        return None

class SCATTER5_PT_creation_operator_add_psy_preset(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_preset"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_preset")

        col.separator(factor=0.85)

        col.label(text=translate("Security Threshold")+":",)
        creation_operators_draw_security(col)

        col.separator(factor=0.85)

        col.label(text=translate("Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_scene, "objects_import_method", text="")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Mask")+":",)
        creation_operators_draw_mask(col,"add_psy_preset")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_preset")

        return None

class SCATTER5_PT_creation_operator_add_psy_manual(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_manual"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_manual")

        col.separator(factor=0.85)

        col.label(text=translate("Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_scene, "objects_import_method", text="")
        
        col.separator(factor=0.85)

        col.label(text=translate("Transforms Settings")+":",)

        ui_templates.bool_toggle(col, 
            prop_api=scat_scene.operators.add_psy_manual,
            prop_str="f_rot_random_allow",
            label=translate("Use Random Rotation"),
            left_space=True,
            )

        ui_templates.bool_toggle(col, 
            prop_api=scat_scene.operators.add_psy_manual,
            prop_str="f_scale_random_allow",
            label=translate("Use Random Scale"),
            left_space=True,
            )

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_manual")

        return None

class SCATTER5_PT_creation_operator_add_psy_modal(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_modal"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Shortcut")+":",)

        def get_hotkey_entry_item(km, kmi_name):
            for i, km_item in enumerate(km.keymap_items):
                if (km.keymap_items.keys()[i]==kmi_name):
                    return km_item
            return None 

        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.8

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps['Window']
        kmi = get_hotkey_entry_item(km,"scatter5.define_add_psy")
        if (kmi):
            button = row2.row(align=True)
            button.scale_y = 1.2
            button.context_pointer_set("keymap", km)
            button.prop(kmi, "type", text="", full_event=True)

        col.separator(factor=0.85)

        col.label(text=translate("Default Density")+":",)

        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.8
        row2.scale_y = 1.05
        row2.prop(scat_scene.operators.add_psy_modal, "f_distribution_density")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col, hide_viewport=False, view_allow=False,)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_modal")

        col.separator(factor=0.85)

        col.label(text=translate("Import Behavior")+":",)

        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_scene, "objects_import_method", text="")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_modal")

        return None


class SCATTER5_PT_creation_operator_load_biome(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_load_biome"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"load_biome")

        col.separator(factor=0.85)

        col.label(text=translate("Security Threshold")+":",)
        creation_operators_draw_security(col)

        col.separator(factor=0.85)

        col.label(text=translate("Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_scene, "objects_import_method", text="")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Mask")+":",)
        creation_operators_draw_mask(col,"load_biome")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"load_biome")

        return None


# ooo        ooooo
# `88.       .888'
#  888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#  8  `888'   888  888ooo888  888   888   888   888
#  8    Y     888  888    .o  888   888   888   888
# o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'


class SCATTER5_MT_manager_header_menu_scatter(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_scatter"
    bl_label  = ""

    def draw(self, context):

        layout = self.layout

        from ..__init__ import bl_info
        layout.label(text=f"Plugin Version: {bl_info['version']}")
        layout.label(text=f"Blender Version: {bl_info['blender']}")

        layout.separator()

        layout.operator("wm.url_open",text=translate("Official Website"),icon="URL").url = "https://geoscatter.com"
        layout.operator("wm.url_open",text=translate("Documentation"),icon="URL").url = "https://geoscatter.com/documentation"
        layout.operator("wm.url_open",text=translate("Discord Community"),icon="URL").url = "https://discord.com/invite/F7ZyjP6VKB"
        layout.operator("wm.url_open",text=translate("Personal Assistance"),icon="URL").url = "https://www.blendermarket.com/products/scatter"
        layout.operator("wm.url_open",text=translate("Leave a Nice Review?"),icon="SOLO_ON").url = "https://www.blendermarket.com/products/scatter/ratings"
        

        return None


class SCATTER5_MT_manager_header_menu_interface(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_interface"
    bl_label  = ""

    def draw(self, context):

        layout = self.layout

        addon_prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
        scat_win = context.window_manager.scatter5

        if (scat_win.category_manager in ("library","market",)):

            layout.prop(addon_prefs,"ui_library_adaptive_columns") 
            layout.prop(addon_prefs,"ui_library_item_size",icon="ARROW_LEFTRIGHT") 
            #layout.prop(addon_prefs,"ui_library_typo_limit",icon="OUTLINER_DATA_FONT")  #seem that this is no longer required
            
            if (not addon_prefs.ui_library_adaptive_columns):
                layout.prop(addon_prefs,"ui_library_columns") 

        elif (scat_win.category_manager in ("lister_large","lister_stats",)):

            layout.prop(addon_prefs,"ui_lister_scale_y") 

        return None 


class SCATTER5_MT_manager_header_menu_open(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_open"
    bl_label  = ""

    def draw(self, context):

        layout = self.layout

        scat_win = context.window_manager.scatter5

        if (scat_win.category_manager=="library"):

            row = layout.row()
            row.operator_context = "INVOKE_DEFAULT"
            row.operator("scatter5.save_biome_to_disk_dialog", text=translate("Create New Biome"),icon="FILE_NEW")
            layout.separator()

            layout.operator("scatter5.reload_biome_library", text=translate("Reload Library"), icon="FILE_REFRESH")
            layout.operator("scatter5.open_directory", text=translate("Open Library"), icon="FOLDER_REDIRECT").folder = directories.lib_biomes
            layout.operator("scatter5.install_package", text=translate("Install a Package"), icon="NEWFOLDER")
                        
        elif (scat_win.category_manager=="market"):

            layout.operator("wm.url_open",text=translate("Add your Packs here? Contact Us"),icon="URL").url="https://discord.com/invite/F7ZyjP6VKB"

            layout.separator()

            layout.operator("scatter5.manual_fetch_from_git",text=translate("Refresh Online Previews"), icon="FILE_REFRESH")
            layout.operator("scatter5.open_directory",text=translate("Open Library"), icon="FOLDER_REDIRECT").folder = directories.lib_biomes
            layout.operator("scatter5.install_package", text=translate("Install a Package"), icon="NEWFOLDER")

        return None 


class SCATTER5_MT_per_biome_main_menu(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_main_menu"
    bl_label  = ""

    def __init__(self):

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name

        return None 

    def draw(self, context):
        layout = self.layout

        lib_element = bpy.context.window_manager.scatter5.library[self.path_arg]

        #Scatter Single Layer Menu

        layout.menu("SCATTER5_MT_per_biome_sub_menu_single_layer",text=translate("Scatter single layer"),icon="DOCUMENTS")

        #Rename 

        ope = layout.column()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.rename_biome", text=translate("Rename this .biome"), icon="FONT_DATA")
        op.old_name = lib_element.user_name
        op.path = lib_element.name #element.name == path

        #Thumbnail Operator 

        ope = layout.row()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.generate_thumbnail",text=translate("Thumbnail generator"),icon="RESTRICT_RENDER_OFF")
        op.json_path = lib_element.name
        op.render_output = lib_element.name.replace(".biome",".jpg")

        #Overwrite Biome Menu

        layout.menu("SCATTER5_MT_per_biome_sub_menu_overwrite",text=translate("Overwrite this .biome"),icon="FILE_NEW")  

        #Open Files Menu 

        layout.menu("SCATTER5_MT_per_biome_sub_menu_open_files",text=translate("Open files"),icon="FILE_FOLDER")  
        
        return None 


class SCATTER5_MT_per_biome_sub_menu_single_layer(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_sub_menu_single_layer"
    bl_label  = ""

    def __init__(self):

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name

        #get json dict 
        with open(self.path_arg) as f:
            d = json.load(f)

        self.layers = []
        for k,v in d.items():
            #only care about layers!
            if (not k.isdigit()):
                continue
            self.layers.append(v["name"])

        return None 

    def draw(self, context):
        layout = self.layout

        for i,l in enumerate(self.layers):
            op = layout.operator("scatter5.load_biome", text=l, icon="FILE_BLANK" )
            op.emitter_name = "" #Auto
            op.json_path = self.path_arg
            op.single_layer = i+1

        return None 


class SCATTER5_MT_per_biome_sub_menu_overwrite(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_sub_menu_overwrite"
    bl_label  = ""

    def __init__(self):

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name
        lib_element = bpy.context.window_manager.scatter5.library[self.path_arg]

        #get json dict 
        with open(self.path_arg) as f:
            d = json.load(f)

        basepath, basename = os.path.split(lib_element.name)
        basename = basename.replace(".biome","")

        #get layer 
        self.layers = []
        for k,v in d.items():
            #save biome name!
            if (k=="info"):
                self.biome_name = v["name"]
                continue
            #only care about layers!
            if (not k.isdigit()):
                continue
            #can only overwrite unique preset style!
            if ("BASENAME" not in v["preset"]):
                continue
            p = os.path.join(basepath,v["preset"].replace("BASENAME",basename))
            if (not os.path.exists(p)):
                continue
            self.layers.append((v["name"],p))
            continue

        return None 

    def draw(self, context):
        layout = self.layout

        lib_element = bpy.context.window_manager.scatter5.library[self.path_arg]

        #overwrite whole biome 

        ope = layout.column()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.save_biome_to_disk_dialog", text=f'{translate("Overwrite")} "{self.biome_name}" .biome', icon="FILE_NEW")
        op.redefine_biocrea_settings = True
        op.biocrea_biome_name = lib_element.user_name
        op.biocrea_creation_directory = os.path.dirname(lib_element.name)
        op.biocrea_file_keywords = lib_element.keywords
        op.biocrea_file_author = lib_element.author
        op.biocrea_file_website = lib_element.website
        op.biocrea_file_description = lib_element.description

        #overwrite layers settings 

        if (len(self.layers)!=0):
            
            layout.separator()

            for i,(n,l) in enumerate(self.layers):
                op = layout.operator("scatter5.save_operator_preset", text=f'{translate("Overwrite")} "{n}" .preset', icon="FILE_NEW" )
                op.biome_overwrite_mode = True 
                op.biome_temp_directory = l

        return None 


class SCATTER5_MT_per_biome_sub_menu_open_files(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_sub_menu_open_files"
    bl_label  = ""

    def __init__(self):

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name

        #get layer 
        with open(self.path_arg) as f:
            d = json.load(f)
        self.layers = []
        i=0
        for k,v in d.items():
            if k.isdigit():
                self.layers.append( (v["name"],self.path_arg.replace(".biome",f".layer{i:02}.preset")) )
                i+=1

        return None 

    def draw(self, context):
        layout = self.layout

        op = layout.operator("scatter5.open_directory", text=f'{translate("Open")} "{os.path.basename(self.path_arg)}"', icon="FILE_TEXT")
        op.folder = self.path_arg

        if (len(self.layers)!=0):

            layout.separator()

            for n,p in self.layers:
                op = layout.operator("scatter5.open_directory", text=f'{translate("Open")} "{n}" .preset', icon="FILE_TEXT" )
                op.folder = p

        layout.separator()

        op = layout.operator("scatter5.open_directory", text=translate("Open Parent Directory"), icon="FOLDER_REDIRECT")
        op.folder = os.path.dirname(self.path_arg)
        
        return None 


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


import sys, inspect
classes = ( obj for name, obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(obj) and name.startswith("SCATTER5_") )


#if __name__ == "__main__":
#    register()
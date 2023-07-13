
#####################################################################################################
#
# ooooo     ooo ooooo      ooooo      ooo               .    o8o   .o88o.
# `888'     `8' `888'      `888b.     `8'             .o8    `"'   888 `"
#  888       8   888        8 `88b.    8   .ooooo.  .o888oo oooo  o888oo 
#  888       8   888        8   `88b.  8  d88' `88b   888   `888   888   
#  888       8   888        8     `88b.8  888   888   888    888   888   
#  `88.    .8'   888        8       `888  888   888   888 .  888   888   
#    `YbodP'    o888o      o8o        `8  `Y8bod8P'   "888" o888o o888o  
#
#####################################################################################################



import bpy

from .. resources.icons import cust_icon
from .. resources.translate import translate

from .. utils.str_utils import word_wrap
from .. utils.str_utils import version_to_float

from . import ui_templates


#   .oooooo.   oooo                            oooo
#  d8P'  `Y8b  `888                            `888
# 888           888 .oo.    .ooooo.   .ooooo.   888  oooo   .oooo.o
# 888           888P"Y88b  d88' `88b d88' `"Y8  888 .8P'   d88(  "8
# 888           888   888  888ooo888 888        888888.    `"Y88b.
# `88b    ooo   888   888  888    .o 888   .o8  888 `88b.  o.  )88b
#  `Y8bood8P'  o888o o888o `Y8bod8P' `Y8bod8P' o888o o888o 8""888P'


#globals, list of list, NOTIF_ARGS[1][0] == notif type
NOTIF_ARGS = [] 


def notifs_check_1(): 
    """check if there are warning messages to be displayed:
    - OLD_BL_VERSION
    - EXPERIMENTAL_BUILD
    - NODE_UNDEFINED
    - NODETREE_UPDATE_NEEDED
    - PLUGIN_OVERLOAD
    """

    #reset any notifs not in the following categories
    global NOTIF_ARGS
    NOTIF_ARGS = [ n for n in NOTIF_ARGS if n[0] not in ("OLD_BL_VERSION","EXPERIMENTAL_BUILD","NODE_UNDEFINED","NODETREE_UPDATE_NEEDED","PLUGIN_OVERLOAD",) ]

    #current version
    from .. __init__ import bl_info
    user_addon_bl_version = version_to_float(".".join(map(str,bl_info['blender'])), truncated=True,)
    user_blender_version = version_to_float(bpy.app.version_string, truncated=True,)

    #check if user is using a too old blender version?

    if (user_blender_version<user_addon_bl_version):

        print(f"\nWARNING : VERSIONS TOO OLD FOR PLUGIN")
        NOTIF_ARGS.append(["OLD_BL_VERSION",user_blender_version,user_addon_bl_version])

    #check for users living dangerously 

    if ( ("Beta" in bpy.app.version_string) or ("Alpha" in bpy.app.version_string) or ("Candidate" in bpy.app.version_string) ):

        print(f"\nWARNING : DON'T EXPECT PLUGIN TO WORK WITH EXPERIMENTAL BUILDS")
        NOTIF_ARGS.append(["EXPERIMENTAL_BUILD",])

    #check if user have both plugins installed?

    used_ext = {ext.module for ext in bpy.context.preferences.addons}
    if ( ("Geo-Scatter" in used_ext) and ("Biome-Reader" in used_ext) ):
        
        print(f"\nWARNING : GEO-SCATTER and BIOME-READER CANNOT BE INSTALLED SIMULTANEOUSLY")
        NOTIF_ARGS.append(["PLUGIN_OVERLOAD",])

    #if no psys in this .blend, nothing else to warn

    all_psys = bpy.context.scene.scatter5.get_all_psys()
    if (len(all_psys)==0): 
        return None

    #Useful versioning information

    all_psys_blender_version = [ version_to_float(p.blender_version, truncated=True,) for p in all_psys ]
    psy_min_blender_version = min(all_psys_blender_version) 
    psy_max_blender_version = max(all_psys_blender_version) 
    
    all_psys_addon_version = [ version_to_float(p.addon_version, truncated=True,) for p in all_psys ]
    psy_min_addon_version = min(all_psys_addon_version)
    psy_max_addon_version = max(all_psys_addon_version)

    #check for forward compatibility errors, if a psy version is above current version

    def recursive_seek_undefined(ng,gather):
        if (ng is not None):
            for n in ng.nodes:
                if (n.bl_idname=="NodeUndefined"):
                    gather.append([ng.name,n.name])
                elif (n.type=="GROUP"):
                    recursive_seek_undefined(n.node_tree,gather)
        return None

    undef = {}
    for p in all_psys:
        e = []
        recursive_seek_undefined(p.get_scatter_mod(strict=False).node_group,e,)
        if (len(e)!=0):
            undef[p.name] = e
        continue

    if (len(undef)!=0):

        print(f"\nWARNING : CORRUPTED NODES FOUND :")
        for k,v in undef.items():
            print(f"     SCATTER-SYSTEM: {k}")
            for e in v:
                print(f"       -undefined node: {e[0]}->{e[1]}")
        NOTIF_ARGS.append(["NODE_UNDEFINED",psy_max_blender_version,user_blender_version])

    #old systems in there? by default we get the scatter engine by their engine names, which are constantly up to date
    #if the scatter engine is not found with the struct mode activated, but found with the 

    old_psys = [ p for p in all_psys if ( p.get_scatter_mod(strict=False) is not None and p.get_scatter_mod() is None ) ]
    if (len(old_psys)!=0): 

        print(f"\nWARNING : OLD SYSTEMS FOUND :")
        for p in old_psys:
            print(f"     SCATTER-SYSTEM: {p.name} -> {p.get_scatter_mod(strict=False).name}")
        NOTIF_ARGS.append(["NODETREE_UPDATE_NEEDED"])

    return None 

def notifs_check_2(): 
    """check if there are warning messages to be displayed:
    - SUBDIVISION_LEVEL
    - ADAPTIVE_SUBDIVISION
    """

    #reset any notifs not in the following categories
    global NOTIF_ARGS
    NOTIF_ARGS = [ n for n in NOTIF_ARGS if n[0] not in ("SUBDIVISION_LEVEL","ADAPTIVE_SUBDIVISION",) ]

    all_psys = bpy.context.scene.scatter5.get_all_psys()
    if (len(all_psys)==0):
        return None

    all_surfaces = []
    for p in all_psys:
        for s in p.get_surfaces(): 
            if (s not in all_surfaces):
                all_surfaces.append(s)

    for s in all_surfaces:
        for m in s.modifiers:
            if (m.type=="SUBSURF"):

                if ((bpy.context.scene.cycles.feature_set=='EXPERIMENTAL') and (s.cycles.use_adaptive_subdivision==True)):
                    notif = ["ADAPTIVE_SUBDIVISION"]
                    if (notif not in NOTIF_ARGS):
                        NOTIF_ARGS.append(notif)

                elif (m.render_levels!=m.levels):
                    notif = ["SUBDIVISION_LEVEL"]
                    if (notif not in NOTIF_ARGS):
                        NOTIF_ARGS.append(notif)

    return None 

# oooooooooo.
# `888'   `Y8b
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888      888  888      .oP"888    `88..]88..8'
#  888     d88'  888     d8(  888     `888'`888'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'


def draw_notification_panel(self, layout,):

    main = layout.column()

    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)
    
    global NOTIF_ARGS
    for n in NOTIF_ARGS:
        notif_type = n[0]

        #undefined nodes, corrupted, do not save
        if (notif_type=="NODE_UNDEFINED"):

            box, is_open = ui_templates.box_panel(self, main, 
                prop_str = "ui_notification_1", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_1");BOOL_VALUE(1)
                icon = "ERROR", 
                name = translate("Node(s) Undefined"),
                warning_panel = True,
                )
            if is_open:

                col = box.column()

                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=32, icon="INFO", string=translate("Your blend file has corrupted nodes, surely because a forward compatibility manipulation."),)
                col.separator()

                rwoo = col.row()
                rwo1 = rwoo.row()
                exp = rwoo.row()
                rwo2 = rwoo.row()

                buttons = exp.column()
                buttons.scale_y = 1.2
                buttons.operator("wm.url_open", text=translate("About Forward Compatibility"), icon="URL",).url = "https://www.geoscatter.com/documentation.html#FeaturePrerequisite&article_compatibility_issues"
                buttons.separator()
                buttons.operator("scatter5.fix_nodetrees", text=translate("Attempt Reparation"), icon="RECOVER_LAST",).force_update = True

                col.separator()
                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=30, string=translate("Undefined nodegroup(s) are displayed in your console window."),)
                
                ui_templates.separator_box_in(box)

            ui_templates.separator_box_out(main)
            continue 

        #version of blender do not match with plugin
        elif (notif_type=="OLD_BL_VERSION"):

            box, is_open = ui_templates.box_panel(self, main, 
                prop_str = "ui_notification_2", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_2");BOOL_VALUE(1)
                icon = "ERROR", 
                name = translate("Incompatible Version"),
                warning_panel = True,
                )
            if is_open:

                col = box.column()

                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=31, icon="INFO", string=translate("Are you using the correct version of our plugin?\nWe don't think so. Please read the page below"),)
                col.separator()

                rwoo = col.row()
                rwo1 = rwoo.row()
                exp = rwoo.row()
                rwo2 = rwoo.row()

                exp.scale_y = 1.2
                exp.operator("wm.url_open", text=translate("About Compatibility"), icon="URL",).url = "https://www.geoscatter.com/documentation.html#Changelogs&article_compatibility_advices"

                ui_templates.separator_box_in(box)

            ui_templates.separator_box_out(main)
            continue

        #user is using beta or alpha build
        elif (notif_type=="EXPERIMENTAL_BUILD"):

            box, is_open = ui_templates.box_panel(self, main, 
                prop_str = "ui_notification_3", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_3");BOOL_VALUE(1)
                icon = "ERROR", 
                name = translate("Unofficial Build"),
                warning_panel = True,
                )
            if is_open:

                col = box.column()
                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=28, icon="INFO", string=translate("Please don't expect plugins to support experimental versions of blender."),)
                
                ui_templates.separator_box_in(box)

            ui_templates.separator_box_out(main)
            continue

        #both our plugins installed?
        elif (notif_type=="PLUGIN_OVERLOAD"):

            box, is_open = ui_templates.box_panel(self, main, 
                prop_str = "ui_notification_4", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_4");BOOL_VALUE(1)
                icon = "ERROR", 
                name = translate("Plugin Overload"),
                warning_panel = True,
                )
            if is_open:

                col = box.column()
                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=28, icon="INFO", string=translate("Please do not install our Geo-Scatter and Biome-Reader Plugins simultaneously, there's no reasons to do so and it might lead to errors."),)
                
                ui_templates.separator_box_in(box)

            ui_templates.separator_box_out(main)
            continue

        #old psy found, please update
        elif (notif_type=="NODETREE_UPDATE_NEEDED"):

            box, is_open = ui_templates.box_panel(self, main, 
                prop_str = "ui_notification_5", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_5");BOOL_VALUE(1)
                icon = "ERROR", 
                name = translate("Update Required"),
                warning_panel = True,
                )
            if is_open:

                col = box.column()

                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=29, icon="INFO", string=translate("Hello dear user, there are scatter-system(s) made with a lower version of our plugin in this .blend file, we need to update all nodetree(s)."),)
                col.separator()

                rwoo = col.row()
                rwo1 = rwoo.row()
                exp = rwoo.row()
                rwo2 = rwoo.row()

                exp.scale_y = 1.2
                exp.operator("scatter5.fix_nodetrees", text=translate("Update Nodetree(s)"), icon="FILE_REFRESH",)

                col.separator()
                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=31, string=translate("This update process might take a minute. Changing versions of your sofware(s)/plugin(s) mid-project is not advised, save copies of your project first!",),)
                
                ui_templates.separator_box_in(box)

            ui_templates.separator_box_out(main)
            continue

        #scatter surface subdivision discrepencies
        elif (notif_type=="SUBDIVISION_LEVEL"):

            box, is_open = ui_templates.box_panel(self, main, 
                prop_str = "ui_notification_6", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_6");BOOL_VALUE(1)
                icon = "ERROR", 
                name = translate("Subdivision Discrepancies"),
                warning_panel = True,
                )
            if is_open:

                col = box.column()
                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=33, icon="INFO", string=translate("One of your scatter-surface(s) has different subdiv levels in viewport/render.\nExpect discrepancies if your scatter-surface is unstable."),)
                
                ui_templates.separator_box_in(box)

            ui_templates.separator_box_out(main)
            continue

        #scatter surface adaptive subdivision
        elif (notif_type=="ADAPTIVE_SUBDIVISION"):

            box, is_open = ui_templates.box_panel(self, main, 
                prop_str = "ui_notification_7", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_7");BOOL_VALUE(1)
                icon = "ERROR", 
                name = translate("Adaptive Subdivision"),
                warning_panel = True,
                )
            if is_open:

                col = box.column()
                word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=33, icon="INFO", string=translate("One of your scatter-surface(s) has adaptive subdiv enabled. Adaptive subdivision is calculated only within shader-space, please avoid scattering on shader-only objects."),)
                
                ui_templates.separator_box_in(box)

            ui_templates.separator_box_out(main)
            continue

        continue 
    
    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)

    return None 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_PT_notification(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_notification"
    bl_label       = translate("Notification")
    bl_category    = "USER_DEFINED" #will be replaced right before ui.__ini__.register()
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "" #nothing == enabled everywhere
    bl_order       = 1

    @classmethod
    def poll(cls, context,):
        if context.mode not in ("OBJECT","PAINT_WEIGHT","PAINT_VERTEX","PAINT_TEXTURE","EDIT_MESH"):
            return False
        
        global NOTIF_ARGS
        if (len(NOTIF_ARGS)==0):
           return False

        return True
        
    def draw_header(self, context):
        self.layout.label(text="", icon_value=cust_icon("W_SCATTER"),)

    def draw_header_preset(self, context):
        row = self.layout.row()
        row.alignment = "RIGHT"
        row.alert = True
        row.label(text=translate("New Message"),)
        row.label(text="", icon="INFO")

    def draw(self, context):
        layout = self.layout
        draw_notification_panel(self,layout)


classes = (

    SCATTER5_PT_notification,

    )


#if __name__ == "__main__":
#    register()


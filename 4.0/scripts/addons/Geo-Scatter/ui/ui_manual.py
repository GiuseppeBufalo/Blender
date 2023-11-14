

#####################################################################################################
#
# ooooo     ooo ooooo      ooo        ooooo                                             oooo
# `888'     `8' `888'      `88.       .888'                                             `888
#  888       8   888        888b     d'888   .oooo.   ooo. .oo.   oooo  oooo   .oooo.    888
#  888       8   888        8 Y88. .P  888  `P  )88b  `888P"Y88b  `888  `888  `P  )88b   888
#  888       8   888        8  `888'   888   .oP"888   888   888   888   888   .oP"888   888
#  `88.    .8'   888        8    Y     888  d8(  888   888   888   888   888  d8(  888   888
#    `YbodP'    o888o      o8o        o888o `Y888""8o o888o o888o  `V88V"V8P' `Y888""8o o888o
#
#####################################################################################################



import bpy

from .. resources.icons import cust_icon
from .. resources.translate import translate

from . import ui_templates


#   .oooooo.    ooooo     ooo ooooo      ooooo   ooooo  o8o      o8o                     oooo         o8o
#  d8P'  `Y8b   `888'     `8' `888'      `888'   `888'  `"'      `"'                     `888         `"'
# 888            888       8   888        888     888  oooo     oooo  .oooo.    .ooooo.   888  oooo  oooo  ooo. .oo.    .oooooooo
# 888            888       8   888        888ooooo888  `888     `888 `P  )88b  d88' `"Y8  888 .8P'   `888  `888P"Y88b  888' `88b
# 888     ooooo  888       8   888        888     888   888      888  .oP"888  888        888888.     888   888   888  888   888
# `88.    .88'   `88.    .8'   888        888     888   888      888 d8(  888  888   .o8  888 `88b.   888   888   888  `88bod8P'
#  `Y8bood8P'      `YbodP'    o888o      o888o   o888o o888o     888 `Y888""8o `Y8bod8P' o888o o888o o888o o888o o888o `8oooooo.
#                                                                888                                                   d"     YD
#                                                            .o. 88P                                                   "Y88888P'
#                                                            `Y888P

# 88  88 88  88888    db     dP""b8 88  dP        db     dP""b8 888888 88 Yb    dP 888888     888888  dP"Yb   dP"Yb  88     .dP"Y8
# 88  88 88     88   dPYb   dP   `" 88odP        dPYb   dP   `"   88   88  Yb  dP  88__         88   dP   Yb dP   Yb 88     `Ybo."
# 888888 88 o.  88  dP__Yb  Yb      88"Yb       dP__Yb  Yb        88   88   YbdP   88""         88   Yb   dP Yb   dP 88  .o o.`Y8b
# 88  88 88 "bodP' dP""""Yb  YboodP 88  Yb     dP""""Yb  YboodP   88   88    YP    888888       88    YbodP   YbodP  88ood8 8bodP'


OLT_TOOLBAR = {}

#Proceeding to hijack the '_tools' dict of 'VIEW3D_PT_tools_active' class. 
#when i use the term "Hijacking" in this addon, i mean TEMPORARILY changing native python code with our own
#Currently hijacking is used here on the toolsystem and header for creating a "fake" custom mode
#Hijack also used on addonprefs for creating our custom manager interface  

#All tools Generated below are fake, It's for display purpose only!
#we have our own toolset of modal operators, and we dynamically switch them by checking which fake tool are active TODO ???? How to send singal?

def hijack_tools_dict():

    import os, sys
    scr = bpy.utils.system_resource('SCRIPTS')
    pth = os.path.join(scr,'startup','bl_ui')
    if pth not in sys.path:
        sys.path.append(pth)

    from bl_ui.space_toolsystem_common import ToolDef
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active

    '''
    def generate_tool(cls,):
        """Tools Generation -> code sampled "scripts/modules/bpy/utils.__init__.register_tool()"""    

        return ToolDef.from_dict({
            "idname": cls.brush_type,
            "label": cls.bl_label.replace(translate("Brush"),""),
            "description": cls.bl_description,
            "icon": cls.dat_icon,
            "cursor": None,
            "widget": None,
            "keymap": None,
            "data_block": None,
            "operator": None,
            "draw_settings": None,
            "draw_cursor": None,
            })
    '''
    
    from ..manual import brushes
    
    def generate_tool(cls,):
        return ToolDef.from_dict({
            "idname": cls.tool_id,
            "label": cls.bl_label.replace(translate("Brush"),""),
            # "description": cls.bl_description,
            "description": "Shortcut: [{}]".format(brushes.ToolKeyConfigurator.get_fancy_string_shortcut_for_tool(cls.tool_id)),
            "icon": cls.dat_icon,
            "cursor": None,
            "widget": None,
            "keymap": None,
            "data_block": None,
            "operator": None,
            "draw_settings": None,
            "draw_cursor": None,
            })

    global OLT_TOOLBAR
    OLT_TOOLBAR = VIEW3D_PT_tools_active._tools
    
    toolbar = [
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_dot),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_pose),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_path),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_chain),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_spatter),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_spray),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_spray_aligned),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_lasso_fill),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_clone),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_move),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_free_move),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_smooth),
        ToolDef.from_dict({
                "idname": brushes.SCATTER5_OT_manual_brush_tool_manipulator.tool_id,
                "label": translate("Manipulator"),
                "description": "Shortcut [{}]".format(brushes.ToolKeyConfigurator.get_fancy_string_shortcut_for_tool(brushes.SCATTER5_OT_manual_brush_tool_manipulator.tool_id)),
                "icon": brushes.SCATTER5_OT_manual_brush_tool_manipulator.dat_icon,
                "widget": brushes.SCATTER5_OT_manual_brush_tool_manipulator.tool_widget,
                "cursor": None, "keymap": None, "data_block": None, "operator": None, "draw_settings": None, "draw_cursor": None,
            }),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_drop_down),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_eraser),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_dilute),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_rotation_set),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_random_rotation),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_spin),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_comb),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_z_align),
        None,
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_scale_set),
        generate_tool(brushes.SCATTER5_OT_manual_brush_tool_grow_shrink),
        None,
    ]
    
    #Add instance index painting tool if instance method is by index
    psy_active = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active()
    if (psy_active.s_instances_method=="ins_collection" and psy_active.s_instances_pick_method=="pick_idx"):
        toolbar += [
            None,
            generate_tool(brushes.SCATTER5_OT_manual_brush_tool_object_set),
        ]
    
    #Currently private testing Physic tool
    if (bpy.context.preferences.addons["Geo-Scatter"].preferences.debug_interface):
        toolbar += [
            None,
            generate_tool(brushes.SCATTER5_OT_manual_brush_tool_heaper),
            # generate_tool(brushes.SCATTER5_OT_manual_brush_tool_debug_3d),
            # generate_tool(brushes.SCATTER5_OT_manual_brush_tool_debug_errors),
        ]

    #add the tools to the toolbar
    VIEW3D_PT_tools_active._tools = {
        None: [ ],
        'OBJECT': toolbar
        }
    
    return 



def restore_tools_dict():

    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
    global OLT_TOOLBAR
    VIEW3D_PT_tools_active._tools = OLT_TOOLBAR
    return 



#  dP""b8 88  88    db    88b 88  dP""b8 888888     .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8
# dP   `" 88  88   dPYb   88Yb88 dP   `" 88__       `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."
# Yb      888888  dP__Yb  88 Y88 Yb  "88 88""       o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b
#  YboodP 88  88 dP""""Yb 88  Y8  YboodP 888888     8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'


HijackedSettings = {
    "show_region_header" : None,
    "show_region_tool_header" : None,
    "show_region_toolbar":None,
    "show_region_ui" : None,
    "show_text" : None,
    "show_stats" : None,
    "active_tool": None,
    "show_gizmo": None,
}


def change_settings(context):

    global HijackedSettings

    #Show Header
    HijackedSettings["show_region_header"] = context.space_data.show_region_header 
    context.space_data.show_region_header = True

    #Show Toolbar
    HijackedSettings["show_region_toolbar"] = context.space_data.show_region_toolbar 
    context.space_data.show_region_toolbar = True

    #Show Tool Header 
    HijackedSettings["show_region_tool_header"] = context.space_data.show_region_tool_header
    context.space_data.show_region_tool_header = False

    #Hide PropertiesPanel ?
    HijackedSettings["show_region_ui"] = context.space_data.show_region_ui
    context.space_data.show_region_ui = False #Hide? Do not Hide? it's useless to have it but it might be confusing to have it popping out every time...
    #bpy.context.scene.scatter5.ui_enabled = False
    
    #Hide Statistics (we'll prolly draw our own?)
    HijackedSettings["show_text"] = context.space_data.overlay.show_text
    context.space_data.overlay.show_text = False
    HijackedSettings["show_stats"] = context.space_data.overlay.show_stats
    context.space_data.overlay.show_stats = False

    #Hide Gizmos, not used in this mode anyway 
    HijackedSettings["show_gizmo"] = context.space_data.show_gizmo 
    # context.space_data.show_gizmo = False
    # well, now they are used..
    context.space_data.show_gizmo = True

    #Save active tool
    HijackedSettings["active_tool"] = context.workspace.tools.from_space_view3d_mode(context.mode).idname

    return None

def restore_settings(context):

    global HijackedSettings
    
    #Restore Header
    context.space_data.show_region_header = HijackedSettings["show_region_header"]

    #Restore Tool Header 
    context.space_data.show_region_tool_header = HijackedSettings["show_region_tool_header"]

    #Restore Toolbar 
    context.space_data.show_region_toolbar = HijackedSettings["show_region_toolbar"]

    #Restore PropertiesPanel 
    context.space_data.show_region_ui = HijackedSettings["show_region_ui"] #Hide? Do not Hide? it's useless to have it but it might be confusing to have it popping out every time...
    #bpy.context.scene.scatter5.ui_enabled = True

    #Restore Statistics 
    context.space_data.overlay.show_text = HijackedSettings["show_text"]
    context.space_data.overlay.show_stats = HijackedSettings["show_stats"]

    #Restore Gizmos
    context.space_data.show_gizmo = HijackedSettings["show_gizmo"]

    #Restore old active tool 
    bpy.ops.wm.tool_set_by_id(name = HijackedSettings["active_tool"],)

    return None



#  dP""b8 888888 88b 88 888888 88""Yb    db    88         88  88 88  88888    db     dP""b8 88  dP
# dP   `" 88__   88Yb88 88__   88__dP   dPYb   88         88  88 88     88   dPYb   dP   `" 88odP
# Yb  "88 88""   88 Y88 88""   88"Yb   dP__Yb  88  .o     888888 88 o.  88  dP__Yb  Yb      88"Yb
#  YboodP 888888 88  Y8 888888 88  Yb dP""""Yb 88ood8     88  88 88 "bodP' dP""""Yb  YboodP 88  Yb



HijackingStatus = False 
View3DHeader_OriginalDraw = None


def modal_hijacking(context):
    """register impostors"""
    #print("HIJACKING")

    global HijackingStatus
    if HijackingStatus==True:
        return None

    #change a bunch of settings 
    change_settings(context)

    #override header drawing function by one of my own temporarily 
    global View3DHeader_OriginalDraw
    View3DHeader_OriginalDraw = bpy.types.VIEW3D_HT_header.draw
    bpy.types.VIEW3D_HT_header.draw = view3d_overridedraw

    #override _tools dict from class VIEW3D_PT_tools_active with my own temporarily
    hijack_tools_dict()

    HijackingStatus=True
    return None
    

def modal_hijack_restore(context):
    """restore and find original drawing classes"""
    #print("RESTORING")
    
    global HijackingStatus
    if HijackingStatus==False:
        return None

    #restore override
    global View3DHeader_OriginalDraw
    bpy.types.VIEW3D_HT_header.draw = View3DHeader_OriginalDraw
    View3DHeader_OriginalDraw = None 

    #restore override
    restore_tools_dict()

    #restore the settings we changed precedently
    restore_settings(context)

    HijackingStatus=False
    return None



# oooooooooo.                                oooo             ooooo   ooooo                           .o8
# `888'   `Y8b                               `888             `888'   `888'                          "888
#  888     888 oooo d8b oooo  oooo   .oooo.o  888 .oo.         888     888   .ooooo.   .oooo.    .oooo888   .ooooo.  oooo d8b
#  888oooo888' `888""8P `888  `888  d88(  "8  888P"Y88b        888ooooo888  d88' `88b `P  )88b  d88' `888  d88' `88b `888""8P
#  888    `88b  888      888   888  `"Y88b.   888   888        888     888  888ooo888  .oP"888  888   888  888ooo888  888
#  888    .88P  888      888   888  o.  )88b  888   888        888     888  888    .o d8(  888  888   888  888    .o  888
# o888bood8P'  d888b     `V88V"V8P' 8""888P' o888o o888o      o888o   o888o `Y8bod8P' `Y888""8o `Y8bod88P" `Y8bod8P' d888b



def view3d_overridedraw(self, context, ):
    l = self.layout
    try: 
        headoverr_main(l,context)
    except Exception as e:
        l.alert = True
        l.label(text=str(e))
        l.separator_spacer()
        headoverr_exitbutton(l)
    return 

def headoverr_exitbutton(l, ):
    exit = l.row()
    exit.alert = True
    # more prominent button..
    # exit.scale_x = 2.0
    exit.scale_x = 1.5
    exit.operator('scatter5.manual_exit', icon='PANEL_CLOSE', )

def procedural_override_msg(layout=None, scale=False, rotation=False, ):

    emitter      = bpy.context.scene.scatter5.emitter
    psy_active   = emitter.scatter5.get_psy_active()
    did_override = False 

    if scale:
        if (psy_active.s_scale_default_allow or psy_active.s_scale_random_allow or psy_active.s_scale_min_allow or psy_active.s_scale_mirror_allow or psy_active.s_scale_shrink_allow or psy_active.s_scale_grow_allow):
            did_override = True 
    if rotation:
        if (psy_active.s_rot_align_z_allow or psy_active.s_rot_align_y_allow or psy_active.s_rot_random_allow or psy_active.s_rot_add_allow):
            did_override = True 

    if did_override and (layout is not None):
        lbl = layout.column()
        lbl.scale_y = 0.8
        lbl.alert = True
        lbl.separator()
        lbl.label(text=translate("Procedural Settings Active"),icon="OBJECT_ORIGIN" if scale else "CON_ROTLIKE")
    return 

def headoverr_main(l, context, ):
    emitter = context.scene.scatter5.emitter
    psy_active = emitter.scatter5.get_psy_active()
    
    from ..manual.brushes import ToolBox
    tool = ToolBox.reference
    
    if(tool is None):
        l.alert = True
        l.label(text="ERROR: Active Brush is None! how did you do that?")
        l.separator_spacer()
        headoverr_exitbutton(l)
        return
    
    # brush_label = tool.bl_label
    # brush_icon  = tool.icon
    # # brush_type = tool.brush_type
    # brush_type = tool.tool_id
    
    # l.label(text="      ")
    l.separator(factor=8.0)
    
    props = tool._brush
    if(props._location and len(props._location)):
        l.popover("SCATTER5_PT_tool_location_menu", text=translate("Location"))
    if(props._rotation and len(props._rotation)):
        l.popover("SCATTER5_PT_tool_rotation_menu", text=translate("Rotation"))
    if(props._scale and len(props._scale)):
        l.popover("SCATTER5_PT_tool_scale_menu", text=translate("Scale"))
    if(props._settings and len(props._settings)):
        l.popover("SCATTER5_PT_tool_settings_menu", text=translate("Settings"))
    if(props._tool and len(props._tool)):
        l.popover("SCATTER5_PT_tool_tool_menu", text=translate("Tool"))
    
    
    '''
    # ico = l.row()
    # no more icons, was too much? blender officially dropped the icons too
    # if brush_icon.startswith("W_"):
    #       ico.label(text=brush_label+"   ", icon_value=cust_icon(brush_icon) )
    # else: ico.label(text=brush_label+"   ", icon=brush_icon )
    
    # # brush space, uncomment to make it accessible while drawing..
    # l.prop( psy_active, "s_distribution_space", expand=True, )

    #Brush
    if brush_type in ["comb_brush", "spin_brush", "random_rotation_brush", "z_align_brush", ]:
        l.popover("SCATTER5_PT_brush_settings_menu", text=translate("Brush")) #Note that We could write the settings directly within the header like blender is also doing
    
    # from ..manual import debug
    # if(debug.debug_mode()):
    #     if(brush_type in ('debug_brush_2d', )):
    #         l.popover("SCATTER5_PT_brush_settings_menu", text=translate("Brush"))
    
    #Instance 
    if brush_type in ["object_brush","dot_brush","spatter_brush","path_brush","chain_brush","spray_brush","spray_aligned_brush","pose_brush","physics_brush"]:
        if(psy_active.s_instances_method=="ins_collection" and psy_active.s_instances_pick_method=="pick_idx"):
            l.popover("SCATTER5_PT_brush_instance_menu", text=translate("Instances"))

    #Rotation
    if brush_type in ["dot_brush","path_brush","chain_brush","spatter_brush","spray_brush","spray_aligned_brush","rotation_brush","move_brush","pose_brush","physics_brush","lasso_fill"]:
        l.popover("SCATTER5_PT_brush_rotation_menu", text=translate("Rotation"))

    #Scale 
    if brush_type in ["dot_brush","path_brush","chain_brush","spatter_brush","spray_brush","spray_aligned_brush","scale_brush","scale_grow_shrink_brush","pose_brush","physics_brush","lasso_fill"]:
        l.popover("SCATTER5_PT_brush_scale_menu", text=translate("Scale"))

    #Stroke
    if brush_type not in ("dot_brush", "pose_brush", "manipulator", ):
        l.popover("SCATTER5_PT_brush_stroke_menu", text=translate("Stroke"))
    
    if(brush_type in ("manipulator", )):
        l.popover("SCATTER5_PT_brush_manipulator_menu", text=translate("Manipulator"))
    '''
    
    # l.menu("SCATTER5_MT_tool_sync_menu", text=translate("Sync"))
    
    # l.separator(factor=1.0)
    # l.prop(context.scene.scatter5.manual, 'use_sync', )
    
    l.menu("SCATTER5_MT_tool_options_menu", text=translate("Options"))
    
    #Points
    l.menu("SCATTER5_MT_brush_point_menu", text=translate("Points"))
    # systems menu
    l.menu("SCATTER5_MT_systems_menu", text=translate("Systems"))

    l.separator_spacer()

    #Below == Rendering Tab on the right
    #Code below = exact sample from native code

    tool_settings = context.tool_settings
    view = context.space_data
    shading = view.shading
    show_region_tool_header = view.show_region_tool_header
    overlay = view.overlay
    obj = context.active_object
    
    object_mode = 'OBJECT' if obj is None else obj.mode
    has_pose_mode = (
        (object_mode == 'POSE') or
        (object_mode == 'WEIGHT_PAINT' and context.pose_object is not None)
    )
    
    # # Viewport Settings
    # l.popover(
    #     panel="VIEW3D_PT_object_type_visibility",
    #     icon_value=view.icon_from_show_object_viewport,
    #     text="",
    # )

    # # Gizmo toggle & popover.
    # row = l.row(align=True)
    # # FIXME: place-holder icon.
    # row.prop(view, "show_gizmo", text="", toggle=True, icon='GIZMO')
    # sub = row.row(align=True)
    # sub.active = view.show_gizmo
    # sub.popover(
    #     panel="VIEW3D_PT_gizmo_display",
    #     text="",
    # )

    # Overlay toggle & popover.
    row = l.row(align=True)
    row.prop(overlay, "show_overlays", icon='OVERLAY', text="")
    sub = row.row(align=True)
    sub.active = overlay.show_overlays
    sub.popover(panel="VIEW3D_PT_overlay", text="")

    row = l.row()
    row.active = (object_mode == 'EDIT') or (shading.type in {'WIREFRAME', 'SOLID'})

    # While exposing 'shading.show_xray(_wireframe)' is correct.
    # this hides the key shortcut from users: T70433.
    if has_pose_mode:
        draw_depressed = overlay.show_xray_bone
    elif shading.type == 'WIREFRAME':
        draw_depressed = shading.show_xray_wireframe
    else:
        draw_depressed = shading.show_xray
    row.operator(
        "view3d.toggle_xray",
        text="",
        icon='XRAY',
        depress=draw_depressed,
    )

    row = l.row(align=True)
    row.prop(shading, "type", text="", expand=True)
    sub = row.row(align=True)
    # TODO, currently render shading type ignores mesh two-side, until it's supported
    # show the shading popover which shows double-sided option.

    # sub.enabled = shading.type != 'RENDERED'
    sub.popover(panel="VIEW3D_PT_shading", text="")

    #Exit Button

    headoverr_exitbutton(l)
    
    return None


class SCATTER5_PT_tool_generic_menu(bpy.types.Panel, ):
    bl_idname = "SCATTER5_PT_tool_generic_menu"
    bl_label = ""
    bl_category = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    # bl_ui_units_x = 12
    
    # NOTE: all tools should have at least this..
    props_list = '_tool'
    '''
    _domain_specific_props = {
        # 3D (default): 2D (alternative)
        'radius': 'radius_2d',
    }
    
    def _domain_aware(self, context, domain, n, ):
        if(n in self._domain_specific_props.keys()):
            if(domain == '2D'):
                return self._domain_specific_props[n]
        return n
    '''
    
    def _get_group(self, context, g, n, ):
        if(context.scene.scatter5.manual.use_sync):
            if(n in g._sync):
                return context.scene.scatter5.manual.tool_default
        return g
    
    def draw(self, context):
        from ..manual.brushes import ToolBox
        g = ToolBox.reference._brush
        ls = getattr(g, self.props_list)
        # domain = getattr(g, '_domain')
        l = self.layout
        
        # l.use_property_split = True
        # l.use_property_decorate = False
        
        for n in ls:
            if(type(n) == str):
                # NOTE: single property
                if(g.bl_rna.properties[n].type == 'FLOAT'):
                    # NOTE: is float of some sort
                    if(g.bl_rna.properties[n].is_array):
                        # NOTE: is vector, expand to column
                        c = l.column()
                        # # c.prop(g, n)
                        # # c.prop(g, self._domain_aware(domain, n, ), )
                        # _n = self._domain_aware(context, domain, n, )
                        # c.prop(self._get_group(context, g, _n), _n, )
                        c.prop(self._get_group(context, g, n), n, )
                    else:
                        # # l.prop(g, n)
                        # # l.prop(g, self._domain_aware(domain, n, ), )
                        # _n = self._domain_aware(context, domain, n, )
                        # l.prop(self._get_group(context, g, _n), _n, )
                        
                        # slider = False
                        # if(n in ('radius_2d')):
                        #     # NOTE: extra slider on top because of pixel subtype
                        #     slider = True
                        #
                        # l.prop(self._get_group(context, g, n), n, slider=slider, )
                        l.prop(self._get_group(context, g, n), n, )
                # elif(g.bl_rna.properties[n].type == 'ENUM' and n in ('radius_units', )):
                #     # r = l.row(align=True)
                #     # r.label(text=translate(g.bl_rna.properties[n].name))
                #     # r.prop(self._get_group(context, g, n), n, expand=True, )
                #     # f = 0.333
                #     f = 0.333
                #     r = l.row()
                #     s = r.split(factor=f)
                #     s.label(text=translate(g.bl_rna.properties[n].name))
                #     s = s.split(factor=1.0)
                #     r = s.row()
                #     r.prop(self._get_group(context, g, n), n, expand=True, )
                elif(g.bl_rna.properties[n].type == 'ENUM' and n not in ('rotation_align', 'rotation_up', 'effect_axis', )):
                    # NOTE: add to list above as needed..
                    # NOTE: is enum, make label first, then expanded enum in row
                    c = l.column(align=True, )
                    c.label(text=translate(g.bl_rna.properties[n].name))
                    r = c.row(align=True)
                    # # r.prop(g, n, expand=True, )
                    # # r.prop(g, self._domain_aware(domain, n, ), expand=True, )
                    # _n = self._domain_aware(context, domain, n, )
                    # r.prop(self._get_group(context, g, _n), _n, expand=True, )
                    r.prop(self._get_group(context, g, n), n, expand=True, )
                else:
                    # NOTE: everything else
                    # # l.prop(g, n)
                    # # l.prop(g, self._domain_aware(domain, n, ), )
                    # _n = self._domain_aware(context, domain, n, )
                    # l.prop(self._get_group(context, g, _n), _n, )
                    l.prop(self._get_group(context, g, n), n, )
            elif(type(n) == tuple):
                # NOTE: multiple properties
                r = l.row(align=True, )
                e = True
                for i in n:
                    if(i.startswith('use_')):
                        # # NOTE: inject label from `_use` property and overwrite row with new
                        # c = l.column(align=True, )
                        # c.label(text=translate(g.bl_rna.properties[i].name))
                        # r = c.row(align=True, )
                        # # r.prop(g, i, text='', )
                        # # r.prop(g, self._domain_aware(domain, i, ), text='', )
                        # _n = self._domain_aware(context, domain, i, )
                        # r.prop(self._get_group(context, g, _n), _n, text='', )
                        # # if(not getattr(g, i)):
                        # if(not getattr(self._get_group(context, g, _n), _n, )):
                        #     # NOTE: `use_` will control active or inactive layout
                        #     e = False
                        
                        # c = r.column(align=True, )
                        c = r.column()
                        r = c.row(align=True, )
                        # _n = self._domain_aware(context, domain, i, )
                        # r.prop(self._get_group(context, g, _n), _n, )
                        r.prop(self._get_group(context, g, i), i, )
                        r = c.row(align=True, )
                        if(not getattr(self._get_group(context, g, i), i, )):
                            # NOTE: `use_` will control active or inactive layout
                            e = False
                    elif(i.endswith('_pressure')):
                        # NOTE: `_pressure` will add icon button
                        # # r.prop(g, i, text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                        # # r.prop(g, self._domain_aware(domain, i, ), text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                        # _n = self._domain_aware(context, domain, i, )
                        # r.prop(self._get_group(context, g, _n), _n, text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                        r.prop(self._get_group(context, g, i), i, text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                    else:
                        if(not e):
                            # NOTE: active/inactive from `use_` property encapsulated in a row so `use_` property can be clicked
                            r = r.row(align=True)
                            r.active = False
                        # NOTE: others
                        # # r.prop(g, i)
                        # # r.prop(g, self._domain_aware(domain, i, ), )
                        # _n = self._domain_aware(context, domain, i, )
                        # r.prop(self._get_group(context, g, _n), _n, )
                        
                        # slider = False
                        # if(i in ('radius_2d')):
                        #     # NOTE: extra slider on top because of pixel subtype
                        #     slider = True
                        #
                        # r.prop(self._get_group(context, g, i), i, slider=True, )
                        r.prop(self._get_group(context, g, i), i, )
            elif(type(n) == dict):
                # NOTE: special/once-in-use/unique properties as dict
                for k, v in n.items():
                    if(k == 'BUTTON'):
                        # # l.prop(g, v, toggle=True, )
                        # # l.prop(g, self._domain_aware(domain, v, ), toggle=True, )
                        # _n = self._domain_aware(context, domain, v, )
                        # l.prop(self._get_group(context, g, _n), _n, toggle=True, )
                        l.prop(self._get_group(context, g, v), v, toggle=True, )
                    elif(k == 'SECTION'):
                        # first is "use"/"enabled" prop
                        r = l.row()
                        # e = getattr(g, v[0])
                        # # r.prop(g, v[0])
                        # # r.prop(g, self._domain_aware(domain, v[0], ), )
                        # _n = self._domain_aware(context, domain, v[0], )
                        # r.prop(self._get_group(context, g, _n), _n, )
                        r.prop(self._get_group(context, g, v[0]), v[0], )
                        
                        e = getattr(self._get_group(context, g, v[0]), v[0], )
                        
                        # others are within section
                        c = l.column()
                        for i in range(1, len(v), 1):
                            if(g.bl_rna.properties[v[i]].type == 'ENUM' and v[i] not in ('rotation_align', 'rotation_up', 'effect_axis', )):
                                # NOTE: again, add to list above as needed..
                                cc = c.column(align=True, )
                                cc.label(text=translate(g.bl_rna.properties[v[i]].name))
                                rr = cc.row(align=True)
                                # # rr.prop(g, v[i], expand=True, )
                                # # rr.prop(g, self._domain_aware(domain, v[i], ), expand=True, )
                                # _n = self._domain_aware(context, domain, v[i], )
                                # rr.prop(self._get_group(context, g, _n), _n, expand=True, )
                                rr.prop(self._get_group(context, g, v[i]), v[i], expand=True, )
                            else:
                                # # c.prop(g, v[i])
                                # # c.prop(g, self._domain_aware(domain, v[i], ), )
                                # _n = self._domain_aware(context, domain, v[i], )
                                # c.prop(self._get_group(context, g, _n), _n, )
                                c.prop(self._get_group(context, g, v[i]), v[i], )
                        c.active = e
                    elif(k == 'RADIUS'):
                        # (('radius', 'radius_px', ), 'radius_pressure', ),
                        r = l.row(align=True, )
                        
                        if(len(v[0]) == 1):
                            # no units switch
                            r.prop(self._get_group(context, g, v[0][0]), v[0][0], slider=True, )
                        elif(len(v[0]) == 2):
                            # regular scene/view switch
                            u = getattr(self._get_group(context, g, v[0][0]), 'radius_units', ) == 'VIEW'
                            if(u):
                                r.prop(self._get_group(context, g, v[0][1]), v[0][1], slider=True, )
                            else:
                                r.prop(self._get_group(context, g, v[0][0]), v[0][0], slider=True, )
                        elif(len(v[0]) == 3):
                            # eraser case
                            u = getattr(self._get_group(context, g, v[0][0]), 'radius_units', ) == 'VIEW'
                            d = getattr(g, '_domain') == '2D'
                            if(d):
                                r.prop(self._get_group(context, g, v[0][2]), v[0][2], slider=True, )
                            elif(u):
                                r.prop(self._get_group(context, g, v[0][1]), v[0][1], slider=True, )
                            else:
                                r.prop(self._get_group(context, g, v[0][0]), v[0][0], slider=True, )
                        
                        if(len(v) == 2):
                            if(v[1].endswith('_pressure')):
                                r.prop(self._get_group(context, g, v[1]), v[1], text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                            else:
                                l.label(text="unknown: {}".format(v[1]))
                        elif(len(v) == 3):
                            if(v[1] is not None):
                                if(v[1].endswith('_pressure')):
                                    r.prop(self._get_group(context, g, v[1]), v[1], text='', icon='STYLUS_PRESSURE', toggle=True, icon_only=True, )
                                else:
                                    r.label(text="unknown: {}".format(v[1]))
                            f = 0.333
                            r = l.row(align=True)
                            s = r.split(factor=f)
                            s.label(text=translate(g.bl_rna.properties[v[2]].name))
                            s = s.split(factor=1.0)
                            r = s.row()
                            r.prop(self._get_group(context, g, v[2]), v[2], expand=True, )
                    elif(k == 'CONDITION'):
                        n = v[0]
                        e = getattr(self._get_group(context, g, n), v[1], ) == v[2]
                        r = l.row()
                        if(g.bl_rna.properties[n].type == 'FLOAT'):
                            if(g.bl_rna.properties[n].is_array):
                                c = r.column()
                                c.prop(self._get_group(context, g, n), n, )
                            else:
                                r.prop(self._get_group(context, g, n), n, )
                        elif(g.bl_rna.properties[n].type == 'ENUM' and n not in ('rotation_align', 'rotation_up', 'effect_axis', )):
                            c = r.column(align=True, )
                            c.label(text=translate(g.bl_rna.properties[n].name))
                            r = c.row(align=True)
                            r.prop(self._get_group(context, g, n), n, expand=True, )
                        else:
                            r.prop(self._get_group(context, g, n), n, )
                        r.active = e
                    elif(k == 'OVERRIDE'):
                        # first property
                        n = v[0]
                        r = l.row()
                        r.prop(self._get_group(context, g, n), n, )
                        # overrided with second property, if second is true, then first is disabled..
                        n = v[1]
                        l.prop(self._get_group(context, g, n), n, )
                        if(getattr(self._get_group(context, g, n), n)):
                            r.enabled = False
                    else:
                        l.label(text="unknown: {}:{}".format(k, v))
            else:
                # NOTE: catch problems..
                l.label(text="unknown: {}".format(n))


class SCATTER5_PT_tool_location_menu(SCATTER5_PT_tool_generic_menu, ):
    bl_idname = "SCATTER5_PT_tool_location_menu"
    props_list = '_location'


class SCATTER5_PT_tool_rotation_menu(SCATTER5_PT_tool_generic_menu, ):
    bl_idname = "SCATTER5_PT_tool_rotation_menu"
    props_list = '_rotation'


class SCATTER5_PT_tool_scale_menu(SCATTER5_PT_tool_generic_menu, ):
    bl_idname = "SCATTER5_PT_tool_scale_menu"
    props_list = '_scale'


class SCATTER5_PT_tool_settings_menu(SCATTER5_PT_tool_generic_menu, ):
    bl_idname = "SCATTER5_PT_tool_settings_menu"
    props_list = '_settings'


class SCATTER5_PT_tool_tool_menu(SCATTER5_PT_tool_generic_menu, ):
    bl_idname = "SCATTER5_PT_tool_tool_menu"
    props_list = '_tool'


'''
class SCATTER5_MT_tool_sync_menu(bpy.types.Menu):
    bl_idname = "SCATTER5_MT_tool_sync_menu"
    bl_label  = ""
    bl_description = translate("Synchronize Tool Settings")
    
    def draw(self, context):
        l = self.layout
        l.prop(context.scene.scatter5.manual, 'use_sync', )
        l.separator()
        l.operator("scatter5.manual_sync_tool_properties", text="Sync Everything").everything = True
        l.separator()
        l.operator("scatter5.manual_sync_tool_properties", text="Sync Tool Properties").tool = True
        l.operator("scatter5.manual_sync_tool_properties", text="Sync Location Properties").location = True
        l.operator("scatter5.manual_sync_tool_properties", text="Sync Rotation Properties").rotation = True
        l.operator("scatter5.manual_sync_tool_properties", text="Sync Scale Properties").scale = True
        l.operator("scatter5.manual_sync_tool_properties", text="Sync Settings Properties").settings = True
'''


class SCATTER5_MT_tool_options_menu(bpy.types.Menu, ):
    bl_idname = "SCATTER5_MT_tool_options_menu"
    bl_label  = ""
    bl_description = translate("Options")
    
    def draw(self, context):
        l = self.layout
        l.prop(context.scene.scatter5.manual, 'use_sync', )
        l.prop(context.scene.scatter5.manual, 'use_radius_exp_scale', )


# ooooooooo.              o8o                  .        ooo        ooooo
# `888   `Y88.            `"'                .o8        `88.       .888'
#  888   .d88'  .ooooo.  oooo  ooo. .oo.   .o888oo       888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  888ooo88P'  d88' `88b `888  `888P"Y88b    888         8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#  888         888   888  888   888   888    888         8  `888'   888  888ooo888  888   888   888   888
#  888         888   888  888   888   888    888 .       8    Y     888  888    .o  888   888   888   888
# o888o        `Y8bod8P' o888o o888o o888o   "888"      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'



class SCATTER5_MT_brush_point_menu(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_brush_point_menu"
    bl_label  = ""
    bl_description = translate("Operations on Points")

    def draw(self, context):
        layout=self.layout

        layout.operator("scatter5.disable_main_settings")
        layout.operator("scatter5.manual_apply_brush")
        layout.operator("scatter5.manual_drop_to_ground",)
        layout.operator("scatter5.manual_reassign_surface",)
        # layout.operator("scatter5.manual_drop",)
        # layout.operator("scatter5.manual_edit",)
        layout.separator()
        layout.operator("scatter5.manual_clear_orphan_data")
        layout.operator("scatter5.manual_clear")
        
        # from .. manual import debug
        # if(debug.debug_mode()):
        #     layout.separator()
        #     layout.operator("scatter5.manual_debug_regen_from_attrs")
        
        return None 


#  .oooooo..o                          .                                    ooo        ooooo
# d8P'    `Y8                        .o8                                    `88.       .888'
# Y88bo.      oooo    ooo  .oooo.o .o888oo  .ooooo.  ooo. .oo.  .oo.         888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  `"Y8888o.   `88.  .8'  d88(  "8   888   d88' `88b `888P"Y88bP"Y88b        8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#      `"Y88b   `88..8'   `"Y88b.    888   888ooo888  888   888   888        8  `888'   888  888ooo888  888   888   888   888
# oo     .d8P    `888'    o.  )88b   888 . 888    .o  888   888   888        8    Y     888  888    .o  888   888   888   888
# 8""88888P'      .8'     8""888P'   "888" `Y8bod8P' o888o o888o o888o      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'
#             .o..P'
#             `Y8P'


class SCATTER5_MT_systems_menu(bpy.types.Menu):

    bl_label = translate("System(s) List")
    bl_idname = "SCATTER5_MT_systems_menu"
    bl_description = translate("Change Active Manual System")
    
    def draw(self, context, ):
        layout = self.layout

        #wait, what if system is hidden? no way to hide/unhide? Hmmm

        emitter = context.scene.scatter5.emitter
        for p in emitter.scatter5.particle_systems:
            if (p.s_distribution_method=='manual_all'): #what if user want to convert procedural to manual from here? maybe 
                layout.row().operator('scatter5.manual_switch', text=p.name, icon="DOT" if p.active else "BLANK1",).name = p.name
            continue

        layout.separator()

        layout.row().operator('scatter5.manual_scatter_add_new', icon="ADD",)

        return None


# # -- SWITCHER v2 --

#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    # SCATTER5_PT_brush_settings_menu,
    # SCATTER5_PT_brush_instance_menu,
    # SCATTER5_PT_brush_scale_menu,
    # SCATTER5_PT_brush_rotation_menu,
    # SCATTER5_PT_brush_stroke_menu,
    # SCATTER5_PT_brush_manipulator_menu,
    SCATTER5_PT_tool_location_menu,
    SCATTER5_PT_tool_rotation_menu,
    SCATTER5_PT_tool_scale_menu,
    SCATTER5_PT_tool_settings_menu,
    SCATTER5_PT_tool_tool_menu,
    # SCATTER5_MT_tool_sync_menu,
    SCATTER5_MT_tool_options_menu,
    SCATTER5_MT_brush_point_menu,
    SCATTER5_MT_systems_menu,
)

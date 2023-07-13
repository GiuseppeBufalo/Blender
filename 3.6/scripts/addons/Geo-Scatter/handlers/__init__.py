
#####################################################################################################
# 
#  ooooo   ooooo                             .o8  oooo
#  `888'   `888'                            "888  `888
#   888     888   .oooo.   ooo. .oo.    .oooo888   888   .ooooo.  oooo d8b
#   888ooooo888  `P  )88b  `888P"Y88b  d88' `888   888  d88' `88b `888""8P
#   888     888   .oP"888   888   888  888   888   888  888ooo888  888
#   888     888  d8(  888   888   888  888   888   888  888    .o  888
#  o888o   o888o `Y888""8o o888o o888o `Y8bod88P" o888o `Y8bod8P' d888b
# 
#####################################################################################################

#find hereby callbacks and other updates function running in the background

#CRASH WARNING!! be very carreful here!!! 
#https://docs.blender.org/api/current/bpy.app.handlers.html?highlight=render_cancel#note-on-altering-data

import bpy
import datetime

from bpy.app.handlers import persistent
from mathutils import Vector

from .. utils.extra_utils import dprint
from .. utils.extra_utils import is_rendered_view, all_3d_viewports

from .. scattering.emitter import handler_emitter_check_if_deleted, handler_emitter_pin_mode_sync, handler_scene_emitter_cleanup, handler_f_surfaces_cleanup
from .. scattering.update_factory import update_active_camera_nodegroup, update_is_rendered_view_nodegroup, update_frame_start_end_nodegroup, update_manual_uuid_surfaces


# oooooooooo.                                                                          oooo
# `888'   `Y8b                                                                         `888
#  888      888  .ooooo.  oo.ooooo.   .oooo.o  .oooooooo oooo d8b  .oooo.   oo.ooooo.   888 .oo.
#  888      888 d88' `88b  888' `88b d88(  "8 888' `88b  `888""8P `P  )88b   888' `88b  888P"Y88b
#  888      888 888ooo888  888   888 `"Y88b.  888   888   888      .oP"888   888   888  888   888
#  888     d88' 888    .o  888   888 o.  )88b `88bod8P'   888     d8(  888   888   888  888   888
# o888bood8P'   `Y8bod8P'  888bod8P' 8""888P' `8oooooo.  d888b    `Y888""8o  888bod8P' o888o o888o
#                          888                d"     YD                      888
#                         o888o               "Y88888P'                     o888o

#lauch function on each depsgraph interaction


@persistent
def scatter5_depsgraph(scene,desp):

    #debug print
    dprint("HANDLER: 'scatter5_depsgraph'", depsgraph=True)

    #check on emitter prop
    handler_emitter_check_if_deleted() #ideally should be after each deletion operation??

    #check if f_surface has been deleted 
    handler_f_surfaces_cleanup() #ideally should be after each deletion operation??

    #update emitter pointer if in pin mode
    handler_emitter_pin_mode_sync()

    #delete object properties if user altD/ShiftD an emitter object, or if emitter deleted
    handler_scene_emitter_cleanup()

    #check for manual mode uuid if multisurfaces
    update_manual_uuid_surfaces()

    #hide system(s) when emitter is also hidden
    #handler_scene_emitter_hidden()

    #update is_rendered_view nodegroup
    shading_type_callback()

    #update active camera nodegroup
    update_active_camera_nodegroup() #force_update strictly forbidden, could create a feedback loop

    return None


#NOTE: update render/frame pre+post are needed in order to avoid "laggy/delayed" effect

# ooooooooo.                               .o8                     
# `888   `Y88.                            "888                     
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b 
#  888ooo88P'  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P 
#  888`88b.    888ooo888  888   888  888   888  888ooo888  888     
#  888  `88b.  888    .o  888   888  888   888  888    .o  888     
# o888o  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b    

#lauch function on pre/post final render operation


def assert_visibility_states():
    """values of the visibility states might be buggy, need a refresh signal"""

    #for all psys, we ensure that some problematic properties are up to date.. 
    #ugly fix, we don't understand why, sometimes the values of the properties below are not synchronized with their nodetrees
    for p in bpy.context.scene.scatter5.get_all_psys():
        
        #of valid systems only, as we might encounter some psys that needs their full nodetree to be updated
        if p.addon_version_is_valid():
            
            p.property_nodetree_refresh("s_visibility_view_viewport_method",)
            p.property_nodetree_refresh("s_visibility_maxload_viewport_method",)
            p.property_nodetree_refresh("s_visibility_facepreview_viewport_method",)
            p.property_nodetree_refresh("s_visibility_cam_viewport_method",)
            p.property_nodetree_refresh("s_display_viewport_method",)
            
        continue

    return None


IS_FINAL_RENDER = False


@persistent
def scatter5_render_init(scene,desp):
    # print("DEBUG-render_init")
    
    global IS_FINAL_RENDER
    IS_FINAL_RENDER = True

    #debug print
    dprint("HANDLER: 'scatter5_render_init'", depsgraph=True)
    
    #headless mode?
    if (bpy.app.background or (bpy.context.window_manager is None)): 
        print("WARNING: we advise `scene.render.use_lock_interface` to be `True` while running blender headlessly, as it might create inaccurate result otherwise. We enabled the settings for you.")
        scene.render.use_lock_interface = True

    #make sure visibility states are ok
    assert_visibility_states()
    
    return None


@persistent
def scatter5_render_pre(scene,desp):
    # print("DEBUG-render_pre")
    
    global IS_FINAL_RENDER
    IS_FINAL_RENDER = True

    #debug print
    dprint("HANDLER: 'scatter5_render_pre'", depsgraph=True)
        
    return None


@persistent
def scatter5_render_post(scene,desp):
    # print("DEBUG-render_post")

    #debug print
    dprint("HANDLER: 'scatter5_render_post'", depsgraph=True)
    
    return None


@persistent
def scatter5_render_cancel(scene,desp): 
    # print("DEBUG-render_cancel")

    global IS_FINAL_RENDER
    IS_FINAL_RENDER = False

    #debug print
    dprint("HANDLER: 'scatter5_render_cancel'", depsgraph=True)
    
    return None


@persistent
def scatter5_render_complete(scene,desp):
    # print("DEBUG-render_complete")

    global IS_FINAL_RENDER
    IS_FINAL_RENDER = False

    #debug print
    dprint("HANDLER: 'scatter5_render_init'", depsgraph=True)

    return None


# oooooooooooo                                                  
# `888'     `8                                                  
#  888         oooo d8b  .oooo.   ooo. .oo.  .oo.    .ooooo.    
#  888oooo8    `888""8P `P  )88b  `888P"Y88bP"Y88b  d88' `88b   
#  888    "     888      .oP"888   888   888   888  888ooo888   
#  888          888     d8(  888   888   888   888  888    .o   
# o888o        d888b    `Y888""8o o888o o888o o888o `Y8bod8P'   

#lauch function on each frame interaction, when animation is playing or scrubbing

@persistent
def scatter5_frame_pre(scene,desp): #desp always none? why?
    # print("DEBUG-frame_pre")
    
    global IS_FINAL_RENDER

    #debug print
    dprint(f"HANDLER: 'scatter5_frame_pre' is_final_render:{IS_FINAL_RENDER}", depsgraph=True)
 
    #viewport optimization: slow camera move, even if all are hidden!
    if (not IS_FINAL_RENDER):
        if (all(not p.scatter_obj.visible_get() for p in bpy.context.scene.scatter5.get_all_psys())):
            dprint(f"HANDLER: 'scatter5_frame_post' optimization denials, all are hidden", depsgraph=True)
            return None
    
    #update active camera nodegroup, we need to evaluate depsgraph and also send scene evaluation
    update_active_camera_nodegroup(force_update=True, scene=scene, render=(IS_FINAL_RENDER and scene.render.use_lock_interface),)

    #partial manual keyframe support 
    keyframe_support()

    return None


@persistent
def scatter5_frame_post(scene,desp): 
    # print("DEBUG-frame_post")

    global IS_FINAL_RENDER

    #debug print
    dprint(f"HANDLER: 'scatter5_frame_post' is_final_render:{IS_FINAL_RENDER}", depsgraph=True)

    #viewport optimization: slow camera move, even if all are hidden!
    if (not IS_FINAL_RENDER):
        if (all(not p.scatter_obj.visible_get() for p in bpy.context.scene.scatter5.get_all_psys())):
            dprint(f"HANDLER: 'scatter5_frame_post' optimization denials, all are hidden", depsgraph=True)
            return None
    
    #update active camera nodegroup, we need to evaluate depsgraph and also send scene evaluation
    update_active_camera_nodegroup(force_update=True, scene=scene, render=(IS_FINAL_RENDER and scene.render.use_lock_interface),)

    #partial manual keyframe support 
    keyframe_support()
        
    return None


def get_scatter5_animated_props():
    """find scatter5 properties that found in emitter animation data"""

    global IS_FINAL_RENDER

    #make sure keyframe also works when rendering & lock option
    if (IS_FINAL_RENDER and bpy.context.scene.render.use_lock_interface):
          scene = bpy.context.evaluated_depsgraph_get().scene
    else: scene = bpy.context.scene

    frame = scene.frame_current

    #gather Scatter5 keyable items: types.scene.scatter5, types.object.scatter5 & nodegroups.scatter5.texture

    keyable_list = []
    keyable_list.append(scene)
    keyable_list += (scene.scatter5.get_all_emitters())
    keyable_list += ([ng for ng in bpy.data.node_groups if ng.name.startswith(".TEXTURE")])

    #gather properties to be updated 

    props = {} #(id_data,propname) : (keyword, value)

    def store_prop(keyable,data_path, value):

        nonlocal props

        #find propname

        propname = data_path.split(".")[-1]

        #find id_data and keyword information depending on data type

        if (type(keyable) is bpy.types.Scene):
            keyword = "Scene"
            id_data = keyable.scatter5
        
        elif (type(keyable) is bpy.types.GeometryNodeTree):
            keyword = "GeometryNodeTree"
            id_data = keyable.scatter5.texture
        
        elif (type(keyable) is bpy.types.Object):

            if ("particle_systems" not in data_path):
                return None 
            
            idx = int(data_path.split("]")[0].split("[")[-1])
            if (len(keyable.scatter5.particle_systems)<=idx):
                return None 
            
            keyword = "ScatterSystem"
            id_data = keyable.scatter5.particle_systems[idx]

        #assert value, blender is separating vector values back to floats, we need to reassemble the vector values in order to update our props..

        if (id_data,propname) in props.keys():
            current_value = props[(id_data,propname)][1]
            
            if (type(current_value) in (float,int)):
                  value = Vector((current_value,value,0))
            else: value = Vector((current_value[0],current_value[1],value))

        #zip values
        props[(id_data,propname)] = (keyword, value)
                    
        return None

    for keyable in keyable_list:

        if ( (not keyable) or (not keyable.animation_data) ):
            continue

        for fc in keyable.animation_data.drivers:
            if (fc.data_path.startswith("scatter5")):
                store_prop(keyable, fc.data_path, keyable.path_resolve(fc.data_path),)
                if (IS_FINAL_RENDER and bpy.context.scene.render.use_lock_interface):
                    print("SCATTER5 WARNING : Driver animation of our settings is not supported with the lock interface option of blender.")

        action = keyable.animation_data.action
        if (action):
            for fc in action.fcurves:
                if (fc.data_path.startswith("scatter5")):
                    store_prop(keyable, fc.data_path, fc.evaluate(frame),)

    return props


def keyframe_support():
    """refresh the animated props"""

    for k,v in get_scatter5_animated_props().items():
        id_data, prop = k
        keyword, value = v

        if (keyword=="ScatterSystem"):
              id_data.property_run_update(prop, value,)
        else: setattr(id_data, prop, value,)
        
        dprint(f"HANDLER: 'keyframe_support' pr={prop} kw={keyword}, val={value}",)

    return None 


#   .oooooo.             oooo  oooo   .o8                           oooo
#  d8P'  `Y8b            `888  `888  "888                           `888
# 888           .oooo.    888   888   888oooo.   .oooo.    .ooooo.   888  oooo
# 888          `P  )88b   888   888   d88' `88b `P  )88b  d88' `"Y8  888 .8P'
# 888           .oP"888   888   888   888   888  .oP"888  888        888888.
# `88b    ooo  d8(  888   888   888   888   888 d8(  888  888   .o8  888 `88b.
#  `Y8bood8P'  `Y888""8o o888o o888o  `Y8bod8P' `Y888""8o `Y8bod8P' o888o o888o


# .dP"Y8 88  88    db    8888b.  88 88b 88  dP""b8     8b    d8  dP"Yb  8888b.  888888
# `Ybo." 88  88   dPYb    8I  Yb 88 88Yb88 dP   `"     88b  d88 dP   Yb  8I  Yb 88__
# o.`Y8b 888888  dP__Yb   8I  dY 88 88 Y88 Yb  "88     88YbdP88 Yb   dP  8I  dY 88""
# 8bodP' 88  88 dP""""Yb 8888Y"  88 88  Y8  YboodP     88 YY 88  YbodP  8888Y"  888888

def set_overlay(boolean):
    """will toggle off overlay while in renderede view""" 

    #init static variable
    _f = set_overlay
    if (not hasattr(_f,"to_restore")):
        _f.to_restore = []

    if (boolean==True): #== restore

        for space in _f.to_restore:
            try: space.overlay.show_overlays = True
            except: pass #perhaps space do not exists anymore so we need to be careful 
        _f.to_restore = []

    elif (boolean==False):

        for space in all_3d_viewports():
            if (space.shading.type=="RENDERED"):
                if space.overlay.show_overlays: 
                    _f.to_restore.append(space)
                    space.overlay.show_overlays = False

    return None 


SHADING_TYPE_OWNER = object()

def shading_type_callback(*args):
    """update rendered view nodegroup""" 

    #check for rendered view
    is_rdr = is_rendered_view()

    dprint(f"MSGBUS: 'S5 View3DShading.type' -> is_rdr={is_rdr}", depsgraph=True)

    #set/reset overlay
    if (bpy.context.scene.scatter5.update_auto_overlay_rendered):
        set_overlay(not is_rdr)

    #update is rendered view nodegroup
    update_is_rendered_view_nodegroup(value=is_rdr)

    return None 

# 8b    d8  dP"Yb  8888b.  888888      dP""b8    db    88     88     88""Yb    db     dP""b8 88  dP
# 88b  d88 dP   Yb  8I  Yb 88__       dP   `"   dPYb   88     88     88__dP   dPYb   dP   `" 88odP
# 88YbdP88 Yb   dP  8I  dY 88""       Yb       dP__Yb  88  .o 88  .o 88""Yb  dP__Yb  Yb      88"Yb
# 88 YY 88  YbodP  8888Y"  888888      YboodP dP""""Yb 88ood8 88ood8 88oodP dP""""Yb  YboodP 88  Yb

MODE_OWNER = object()

def mode_callback(*args):
    """message bus rendered view check function""" 

    dprint("MSGBUS: 'S5 EditMode'", depsgraph=True)

    #init static variable
    _f = mode_callback
    if (not hasattr(_f,"were_editing")):
        _f.were_editing = [] #keep track of last objects edited
    if (not hasattr(_f,"last_mode")):
        _f.last_mode = "OBJECT" #keep track of blender mode states

    #Scatter5 track surface area of each objects

    current_mode = bpy.context.object.mode

    #if recently was in edit mode, and 
    if ((_f.last_mode=="EDIT") and (current_mode=="OBJECT")):
        dprint("MSGBUS: 'objects.scatter5.estimate_square_area()'", depsgraph=True)
        for o_name in _f.were_editing:
            o = bpy.data.objects.get(o_name)
            if (o is not None):
                o.scatter5.estimate_square_area()

    _f.last_mode = str(current_mode)
    if (current_mode=="EDIT"):
        _f.were_editing = [o.name for o in bpy.context.scene.objects if (o.mode=="EDIT")]

    return None 

# 888888 88""Yb    db    8b    d8 888888     88""Yb 88""Yb  dP"Yb  88""Yb      dP""b8 88  88    db    88b 88  dP""b8 888888
# 88__   88__dP   dPYb   88b  d88 88__       88__dP 88__dP dP   Yb 88__dP     dP   `" 88  88   dPYb   88Yb88 dP   `" 88__
# 88""   88"Yb   dP__Yb  88YbdP88 88""       88"""  88"Yb  Yb   dP 88"""      Yb      888888  dP__Yb  88 Y88 Yb  "88 88""
# 88     88  Yb dP""""Yb 88 YY 88 888888     88     88  Yb  YbodP  88          YboodP 88  88 dP""""Yb 88  Y8  YboodP 888888

CLIP_START_OWNER = object()
CLIP_END_OWNER = object()

def frame_clip_callback(*args):
    """message bus rendered view check function""" 

    dprint("MSGBUS: 'S5 frame_start/end'", depsgraph=True)

    update_frame_start_end_nodegroup()

    return None 

# ooooo                                  .o8       ooooooooo.                          .
# `888'                                 "888       `888   `Y88.                      .o8
#  888          .ooooo.   .oooo.    .oooo888        888   .d88'  .ooooo.   .oooo.o .o888oo
#  888         d88' `88b `P  )88b  d88' `888        888ooo88P'  d88' `88b d88(  "8   888
#  888         888   888  .oP"888  888   888        888         888   888 `"Y88b.    888
#  888       o 888   888 d8(  888  888   888        888         888   888 o.  )88b   888 .
# o888ooooood8 `Y8bod8P' `Y888""8o `Y8bod88P"      o888o        `Y8bod8P' 8""888P'   "888"

#on loading blender files, new file, ect.. used to launch callback, as they won't stick when changing files


def add_msgbusses(): 

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DShading, "type"), # not accurate signal enough, need both msgbus & depsgraph
        owner=SHADING_TYPE_OWNER,
        notify=shading_type_callback,
        args=(None,),
        options={"PERSISTENT"},
        )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=MODE_OWNER,
        notify=mode_callback,
        args=(None,),
        options={"PERSISTENT"},
        )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Scene, "frame_start"),
        owner=CLIP_START_OWNER,
        notify=frame_clip_callback,
        args=(None,),
        options={"PERSISTENT"},
        )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Scene, "frame_end"),
        owner=CLIP_END_OWNER,
        notify=frame_clip_callback,
        args=(None,),
        options={"PERSISTENT"},
        )

    return None 


def clear_msgbusses():

    bpy.msgbus.clear_by_owner(SHADING_TYPE_OWNER)
    bpy.msgbus.clear_by_owner(MODE_OWNER)
    bpy.msgbus.clear_by_owner(CLIP_START_OWNER)
    bpy.msgbus.clear_by_owner(CLIP_END_OWNER)

    return None


def ensure_particle_interface_items():
    """ensure that the particle interface is drawn correctly, it has been implemeted in Geo-Scatter 5.4, and there might be some systems that need the interface to be initiated"""
    
    for o in bpy.data.objects:
        if (o.scatter5.particle_systems and not o.scatter5.particle_interface_items):
            o.scatter5.particle_interface_refresh()
            
    return None 


@persistent
def scatter5_load_post(scene,desp): 

    #debug print
    dprint(f"HANDLER: 'scatter5_load_post'", depsgraph=True)

    #need to add message bus on each
    add_msgbusses() #TODO, better msgbus registration, need to check if not added already perhaps??? unsure if this can be done, msgbus only has a single owner

    #check for warning messages
    from .. ui.ui_notification import notifs_check_1, notifs_check_2
    notifs_check_1()
    notifs_check_2()

    #rebuild library, because biome library is stored in bpy.contewt.window_manager, will need to reload
    bpy.ops.scatter5.reload_biome_library()

    #make sure visibility states are ok
    assert_visibility_states()
    
    #make sure older systems made before Geo-Scatter 5.4 are now drawn
    ensure_particle_interface_items()

    return None


# oooooooooo.  oooo                              .o8                           .oooooo..o
# `888'   `Y8b `888                             "888                          d8P'    `Y8
#  888     888  888   .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b      Y88bo.       .oooo.   oooo    ooo  .ooooo.
#  888oooo888'  888  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P       `"Y8888o.  `P  )88b   `88.  .8'  d88' `88b
#  888    `88b  888  888ooo888  888   888  888   888  888ooo888  888               `"Y88b  .oP"888    `88..8'   888ooo888
#  888    .88P  888  888    .o  888   888  888   888  888    .o  888          oo     .d8P d8(  888     `888'    888    .o
# o888bood8P'  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b         8""88888P'  `Y888""8o     `8'     `Y8bod8P'

#right after saving a .blend

def update_systems_versioning():
    """when saving a .blend, we keep track of a system version. Geo-Scatter use geometry node, and saving in newer blender version will result in forward compatibility issues"""    
    
    #update blender latest version
    from .. utils.str_utils import version_to_float
        
    for p in bpy.context.scene.scatter5.get_all_psys():

        if (p.blender_version==""):
            p.blender_version = bpy.app.version_string
        
        elif ( version_to_float(p.blender_version) < version_to_float(bpy.app.version_string) ):
            p.blender_version = bpy.app.version_string

        continue
    
    return None 


@persistent 
def scatter5_save_post(scene,desp):

    #debug print
    dprint(f"HANDLER: 'scatter5_save_post'", depsgraph=True)

    #keep track of systems blender versions
    update_systems_versioning()

    return None 


# ooooooooo.   oooo                          o8o                   ooooo                          .             oooo  oooo
# `888   `Y88. `888                          `"'                   `888'                        .o8             `888  `888
#  888   .d88'  888  oooo  oooo   .oooooooo oooo  ooo. .oo.         888  ooo. .oo.    .oooo.o .o888oo  .oooo.    888   888
#  888ooo88P'   888  `888  `888  888' `88b  `888  `888P"Y88b        888  `888P"Y88b  d88(  "8   888   `P  )88b   888   888
#  888          888   888   888  888   888   888   888   888        888   888   888  `"Y88b.    888    .oP"888   888   888
#  888          888   888   888  `88bod8P'   888   888   888        888   888   888  o.  )88b   888 . d8(  888   888   888
# o888o        o888o  `V88V"V8P' `8oooooo.  o888o o888o o888o      o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o
#                                d"     YD
#                                "Y88888P'

#right after plugin installation, this is on first blender session init & when clicking on install 

def wait_for_restrict_state(): #BEWARE: this is a function from a bpy.app timer, context might be tricky to handle 
    """wait until bpy.context is not bpy_restrict_state._RestrictContext anymore"""

    if (str(bpy.context).startswith("<bpy_restrict_state")): 
        return 0.01

    #check for warning messages
    from .. ui.ui_notification import notifs_check_1, notifs_check_2
    notifs_check_1()
    notifs_check_2()

    #make sure factory_event_listening_allow property is enabled, if not, prolly because of a crash
    for sc in bpy.data.scenes: 
        if (not sc.scatter5.factory_event_listening_allow):
            sc.scatter5.factory_event_listening_allow = True

    #make sure manual mode uuid are accurate (rare bugfix)
    from ..scattering.update_factory import update_manual_uuid_surfaces
    update_manual_uuid_surfaces(force_update=True)

    #make sure visibility states are ok
    assert_visibility_states()

    #make sure older systems made before Geo-Scatter 5.4 are now drawn
    ensure_particle_interface_items()

    return None


#  .oooooo..o                      oooo   o8o               .        ooooo     ooo                  .o8
# d8P'    `Y8                      `888   `"'             .o8        `888'     `8'                 "888
# Y88bo.      oooo    ooo  .oooo.o  888  oooo   .oooo.o .o888oo       888       8  oo.ooooo.   .oooo888
#  `"Y8888o.   `88.  .8'  d88(  "8  888  `888  d88(  "8   888         888       8   888' `88b d88' `888
#      `"Y88b   `88..8'   `"Y88b.   888   888  `"Y88b.    888         888       8   888   888 888   888
# oo     .d8P    `888'    o.  )88b  888   888  o.  )88b   888 .       `88.    .8'   888   888 888   888
# 8""88888P'      .8'     8""888P' o888o o888o 8""888P'   "888"         `YbodP'     888bod8P' `Y8bod88P"
#             .o..P'                                                                888
#             `Y8P'                                                                o888o

def on_particle_interface_interaction_handler():
    """when user is interacting with system lists"""
    
    #debug print
    dprint(f"HANDLER: 'on_particle_interface_interaction_handler'", depsgraph=True)

    #make sure inner properties that should update via callback are updated
    frame_clip_callback()

    #check for subdivision notif
    from .. ui.ui_notification import notifs_check_2
    notifs_check_2()

    return None

###########################################################################################################
#
#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'
###########################################################################################################


def all_handlers():
    """return a list of handler stored in .blend"""

    return_list = []
    
    for oh in bpy.app.handlers:
        try:
            for h in oh:
                return_list.append(h)
        except: pass
    
    return return_list


def register():

    #add msgbus
    add_msgbusses()

    #add handlers 
    handlers = all_handlers()

    #depsgraph
    if (scatter5_depsgraph not in handlers):
        bpy.app.handlers.depsgraph_update_post.append(scatter5_depsgraph)

    #frame change
    if (scatter5_frame_pre not in handlers):
        bpy.app.handlers.frame_change_pre.append(scatter5_frame_pre)
    if (scatter5_frame_post not in handlers):
        bpy.app.handlers.frame_change_post.append(scatter5_frame_post)
        
    #render
    if (scatter5_render_init not in handlers):
        bpy.app.handlers.render_init.append(scatter5_render_init)
    if (scatter5_render_pre not in handlers):
        bpy.app.handlers.render_pre.append(scatter5_render_pre)
    if (scatter5_render_post not in handlers):
        bpy.app.handlers.render_post.append(scatter5_render_post)
    if (scatter5_render_cancel not in handlers):
        bpy.app.handlers.render_cancel.append(scatter5_render_cancel)
    if (scatter5_render_complete not in handlers):
        bpy.app.handlers.render_complete.append(scatter5_render_complete)

    #on blend open 
    if (scatter5_load_post not in handlers):
        bpy.app.handlers.load_post.append(scatter5_load_post)

    #on blend save 
    if (scatter5_save_post not in handlers):
        bpy.app.handlers.save_post.append(scatter5_save_post)

    #on plugin installation
    bpy.app.timers.register(wait_for_restrict_state)

    return None


def unregister():

    #remove all msgbus
    clear_msgbusses()

    #remove all handlers 
    for h in all_handlers():

        #depsgraph
        if (h.__name__=="scatter5_depsgraph"):
            bpy.app.handlers.depsgraph_update_post.remove(h)

        #frame change
        elif (h.__name__=="scatter5_frame_pre"):
            bpy.app.handlers.frame_change_pre.remove(h)
        elif (h.__name__=="scatter5_frame_post"):
            bpy.app.handlers.frame_change_post.remove(h)

        #render 
        elif (h.__name__=="scatter5_render_init"):
            bpy.app.handlers.render_init.remove(h)
        elif (h.__name__=="scatter5_render_pre"):
            bpy.app.handlers.render_pre.remove(h)
        elif (h.__name__=="scatter5_render_post"):
            bpy.app.handlers.render_post.remove(h)
        elif (h.__name__=="scatter5_render_cancel"):
            bpy.app.handlers.render_cancel.remove(h)
        elif (h.__name__=="scatter5_render_complete"):
            bpy.app.handlers.render_complete.remove(h)
            
        #on blend open 
        elif (h.__name__=="scatter5_load_post"):
            bpy.app.handlers.load_post.remove(h)

        #on blend save 
        elif (h.__name__=="scatter5_save_post"):
            bpy.app.handlers.save_post.remove(h)

        continue

    return None
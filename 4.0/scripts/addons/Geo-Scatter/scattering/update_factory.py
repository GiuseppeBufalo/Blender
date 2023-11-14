
#####################################################################################################
#  oooooooooooo                         .
#  `888'     `8                       .o8
#   888          .oooo.    .ooooo.  .o888oo  .ooooo.  oooo d8b oooo    ooo
#   888oooo8    `P  )88b  d88' `"Y8   888   d88' `88b `888""8P  `88.  .8'
#   888    "     .oP"888  888         888   888   888  888       `88..8'
#   888         d8(  888  888   .o8   888 . 888   888  888        `888'
#  o888o        `Y888""8o `Y8bod8P'   "888" `Y8bod8P' d888b        .8'
#                                                              .o..P'
#                                                              `Y8P'
#####################################################################################################

import bpy, time, datetime, random
from mathutils import Matrix, Vector

from .. resources.translate import translate

from .. utils.extra_utils import dprint
from .. utils.extra_utils import is_rendered_view
from .. utils.event_utils import get_event

#####################################################################################################

#All interactions with Scatter engine nodetree are located in this module

#What's happening in here?
# 1 Settings in particle_settings.py, need update fcts! (for psys or psygroups)
# 2 We generate the update fct with a fct factory
#   That way we can optionally add delay to update fct with wrapper
# 4 Then function goes in Dispatcher 
#   4.1 We gather & exec adequate update fct, all stored in UpdatesRegistry
#   4.2 Optional add effects == send update signals to other properties (alt/sync)

# oooooo   oooooo     oooo
#  `888.    `888.     .8'
#   `888.   .8888.   .8'   oooo d8b  .oooo.   oo.ooooo.  oo.ooooo.   .ooooo.  oooo d8b
#    `888  .8'`888. .8'    `888""8P `P  )88b   888' `88b  888' `88b d88' `88b `888""8P
#     `888.8'  `888.8'      888      .oP"888   888   888  888   888 888ooo888  888
#      `888'    `888'       888     d8(  888   888   888  888   888 888    .o  888
#       `8'      `8'       d888b    `Y888""8o  888bod8P'  888bod8P' `Y8bod8P' d888b
#                                              888        888
#                                             o888o      o888o


def factory(prop_name, delay_support=False, alt_support=True, sync_support=True,):
    """will find and return wrapped function according to propname at parsetime
    delay_support -> is the property supporting the delay wrapper? delay only needed when sliding! therefore always False except for sliders properties in Float/Int/Vector
    alt_support   -> is the property supporting the alt behavior? only `is_random_seed` should not, as it is a false property & may create feedback loop issue otherwise
    sync_support  -> is the property supporting the synchronization feature? `seed` properties do not support it for user convenience.
    """

    def update_fct(self,context):

        #Real Time Update? 
        if ( (bpy.context.scene.scatter5.factory_delay_allow==False) or (delay_support==False) ):
            
            #dprint("factory(update_realtime) ->"+prop_name)
            update_dispatcher(self, prop_name, alt_support=alt_support, sync_support=sync_support,)
            return None 

        #Fixed Interval update? 
        if (bpy.context.scene.scatter5.factory_update_method=="update_delayed"): 
            
            if (bpy.context.scene.scatter5.factory_update_delay==0):
                
                #dprint("factory(update_delayed==0) ->"+prop_name)
                update_dispatcher(self, prop_name, alt_support=alt_support, sync_support=sync_support,)
                return None

            #dprint("factory update_delayed->"+prop_name)
            function_exec_delay(
                interval=bpy.context.scene.scatter5.factory_update_delay,
                function=update_dispatcher, 
                arg=[self, prop_name,], 
                kwarg={"alt_support":alt_support, "sync_support":sync_support,} 
                )
            return None 

        #On mouse release Update? 
        if (bpy.context.scene.scatter5.factory_update_method=="update_on_release"):

            #dprint("factory(update_on_release) ->"+prop_name)
            function_exec_event_release(
                function=update_dispatcher, 
                arg=[self, prop_name,],
                kwarg={"alt_support":alt_support, "sync_support":sync_support,} 
                )
            return None

    return update_fct

def function_exec_delay(interval=0, function=None, arg=[], kwarg={},):
    """add delay to function execution, 
    Note update delay can by avoid by turning the global switch 
    "bpy.context.scene.scatter5.factory_delay_allow" to False"""

    _f = function_exec_delay
    #initialize static attr
    if (not hasattr(_f,"is_running")):
        _f.is_running = False

    #if timer already launched, quit
    if (_f.is_running):
        return None 

    def delay_call():
        """timer used to add delay when calling operator of the function"""

        dprint("PROP_FCT >>> delay_call()")

        with bpy.context.scene.scatter5.factory_update_pause(delay=True):
            function(*arg,**kwarg)

        _f.is_running = False
        return None

    #launching timer
    dprint("PROP_FCT >>> bpy.app.timers.register(delay_call)")
    bpy.app.timers.register(delay_call, first_interval=interval)
    _f.is_running = True
    
    return None 

def function_exec_event_release(function=None, arg=[], kwarg={},):
    """if "LEFTMOUSE PRESS" loop until no more pressed"""

    _f = function_exec_event_release
    #initialize static attr
    if (not hasattr(_f,"is_waiting")):
        _f.is_waiting = False

    #if timer fct is waiting for an exec already, skip
    if (_f.is_waiting):
        return None 

    event = get_event()
    
    #if user is hitting enter, update directly
    if (event.type=="RET"):

        with bpy.context.scene.scatter5.factory_update_pause(delay=True):
            function(*arg,**kwarg)
        
        return None 
        
    def release_call():
        """timer used to add delay when calling operator of the function"""

        dprint("PROP_FCT >>> release_call()")
        
        if (get_event().value!="PRESS"):
            
            with bpy.context.scene.scatter5.factory_update_pause(delay=True):
                function(*arg,**kwarg)

            _f.is_waiting = False
            return None 

        return 0.1

    #if user is tweaking with left mouse click hold, launch timer to detect when he is done
    if (event.value=="PRESS"):

        dprint("PROP_FCT >>> bpy.app.timers.register(release_call)")
        bpy.app.timers.register(release_call)
        _f.is_waiting = True
    
    return None 


#
# oooooooooo.    o8o                                    .             oooo
# `888'   `Y8b   `"'                                  .o8             `888
#  888      888 oooo   .oooo.o oo.ooooo.   .oooo.   .o888oo  .ooooo.   888 .oo.   
#  888      888 `888  d88(  "8  888' `88b `P  )88b    888   d88' `"Y8  888P"Y88b  
#  888      888  888  `"Y88b.   888   888  .oP"888    888   888        888   888  
#  888     d88'  888  o.  )88b  888   888 d8(  888    888 . 888   .o8  888   888  
# o888bood8P'   o888o 8""888P'  888bod8P' `Y888""8o   "888" `Y8bod8P' o888o o888o
#                               888
#                              o888o
#

# Normally all interaction through nodegraph is done via this function, for all psys and groups properties
# except for texture related data (transforms) as this is considered per texture data block
# see the scattering.texture_datablock module

def update_dispatcher(self, prop_name, alt_support=True, sync_support=True,):
    """update nodegroup dispatch, this function is not meant to be used directly, use factory() instead"""

    #NOTE: self is 'psy' or `group` / psy.id_name is 'emitter'
    
    dprint(f"PROP_FCT: tweaking update : {self.name} -> {prop_name}")
    
    #get prop value
    value = getattr(self,prop_name)

    #get keyboard event 
    event = get_event() #TODO is this causing slow downs (launching a ope) ???? will need to check once optimization is at focus.

    #get update function we need from the procedurally generated dict and execute the correct funtion depending on prop_name
    UpdatesRegistry.run_update(self, prop_name, value, event=event)

    #Special ALT & SYNC behaviors for particle systems properties
    if (type(self).__name__=="SCATTER5_PR_particle_systems"):
        
        #Alt Feature
        if ( (alt_support) and (bpy.context.scene.scatter5.factory_alt_allow) and (event.alt) ):
            update_alt(self, prop_name, value,)

        #Synchronize Feature
        if ( (sync_support) and (bpy.context.scene.scatter5.factory_synchronization_allow) ):
            update_sync(self, prop_name, value,)
            
    elif (type(self).__name__=="SCATTER5_PR_particle_groups"):
        pass
    
    return None

def update_alt(psy, prop_name, value,):
    """sync value to all selected psy when user is pressing alt"""

    dprint(f"     >>> S5: update_alt()")

    #turn off alt behavior to avoid feedback loop when batch changing selection settings, 
    #events will return None if factory_event_listening_allow is set to False
    with bpy.context.scene.scatter5.factory_update_pause(event=True):

        #alt for batch support
        emitter = psy.id_data
        psys_sel = emitter.scatter5.get_psys_selected(all_emitters=bpy.context.scene.scatter5.factory_alt_selection_method=="all_emitters")

        #copy active settings for all selected systems
        for p in psys_sel:
            if ( (p!=psy) and (not p.is_locked(prop_name)) ):
                if (getattr(p, prop_name)!=value):
                    setattr(p, prop_name, value,)

    return None 

def update_sync(psy, prop_name, value,):
    """sync all settings while updating, settings get synced in the update factory"""

    #check if channels exists at first place
    if (len(bpy.context.scene.scatter5.sync_channels)==0):
        return None

    #check if there's some stuff to synch with
    #if yes find dict of psy with prop category
    siblings = psy.get_sync_siblings()
    if (len(siblings)==0):
        return None

    dprint(f"     >>> S5: update_sync()")

    #ignore any properties update behavior, such as update delay or hotkeys
    with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=False):

        #synchronize all syblings with given value
        for ch in siblings:
                
            #check if prop is a category that should be ignored
            if (not any( prop_name.startswith(c) for c in ch["categories"]) ):
                continue

            #batch change properties if not set to sync value
            for p in ch["psys"]:

                #no need to update itself
                if (p.name==psy.name):
                    continue

                #avoid updating locked properties
                if (p.is_locked(prop_name)):
                    continue

                #only update if value differ
                current_value = getattr(p, prop_name)
                if (current_value==value):
                    continue

                #update!
                setattr(p, prop_name, value,)
                continue
                
            continue
        
    return None


#   .oooooo.                                              o8o                 oooooooooooo               .
#  d8P'  `Y8b                                             `"'                 `888'     `8             .o8
# 888            .ooooo.  ooo. .oo.    .ooooo.  oooo d8b oooo   .ooooo.        888          .ooooo.  .o888oo
# 888           d88' `88b `888P"Y88b  d88' `88b `888""8P `888  d88' `"Y8       888oooo8    d88' `"Y8   888
# 888     ooooo 888ooo888  888   888  888ooo888  888      888  888             888    "    888         888
# `88.    .88'  888    .o  888   888  888    .o  888      888  888   .o8       888         888   .o8   888 .
#  `Y8bood8P'   `Y8bod8P' o888o o888o `Y8bod8P' d888b    o888o `Y8bod8P'      o888o        `Y8bod8P'   "888"

#various function interacting with properties or nodetrees, used in UpdatesRegistry


def get_enum_idx(item, prop_name, value,):
    """retrieve index of an item from an enum property
    WARNING will not work on dynamic items fct...""" 

    prop = item.bl_rna.properties[prop_name]
    element = prop.enum_items.get(value)
    
    if (element is None):
        print(f"ERROR get_enum_idx(): '{value}' element not found in '{prop_name}' enum")
        return 0
    
    return element.value

def color_convert(value):
    """Avoid Error when setting colors"""

    return (*value,1) if (len(value)==3) else tuple(value) 

def get_node(psy, node_name):
    """get node from psy nodetree"""

    mod = psy.get_scatter_mod()
    assert mod is not None, "Geo-Scatter Engine not Found"
    
    nodes = mod.node_group.nodes
    inner_name = None

    if ("." in node_name):
        node_name,inner_name,*_ = node_name.split(".")

    node = nodes.get(node_name)
    if (node is None):
        print("ERROR: '",node_name,"' not found")
        return None 

    if (inner_name and node.type=="GROUP"):
        node = node.node_tree.nodes.get(inner_name)
        if (node is None):
            print("ERROR: '",node_name,">",inner_name,"' not found")
            return None 

    return node

def node_value(psy, node_name, value=None, entry="output", i=0,):
    """set value in psy nodetree from node name, depending on node entry type"""

    node = get_node(psy, node_name)
    if (node is None): 
        return None 

    if (entry=="output"):
        if (node.outputs[i].default_value!=value):
            node.outputs[i].default_value = value 

    elif (entry=="input"):
        if (node.inputs[i].default_value!=value):
            node.inputs[i].default_value = value

    elif (entry=="vector"):
        if (node.vector!=value):
            node.vector = value

    elif (entry=="integer"):
        if (node.integer!=value):
            node.integer = value

    elif (entry=="boolean"):
        if (node.boolean!=value):
            node.boolean = value

    elif (entry=="string"):
        if (node.string!=value):
            node.string = value

    elif (entry=="attr"):
        if (node.inputs[0].default_value!=value):
            node.inputs[0].default_value = value

    elif (entry=="texture"):
        if (node.inputs[1].default_value!=value):
            node.inputs[1].default_value = value

    return None  

def mute_color(psy, node_name, mute=True,):
    """mute a color of a node in psy nodetree"""

    node = get_node(psy, node_name)
    if (node is None): 
        return None 

    mute = not mute
    if (node.use_custom_color!=mute): 
        node.use_custom_color = mute

    return None 

def mute_node(psy, node_name, mute=True,):
    """mute a node in psy nodetree"""

    node = get_node(psy, node_name)
    if (node is None): 
        return None 

    if (node.mute != mute):
        node.mute = mute

    return None

def node_link(psy, receptor_node_name, emetor_node_name, receptor_socket_idx=0, emetor_socket_idx=0,):
    """link two nodes together in psy nodetree"""

    mod = psy.get_scatter_mod()
    assert mod is not None, "Geo-Scatter Engine not Found"
    
    nodes = mod.node_group.nodes

    #WARNING currently this fct does not support indented node_name

    if (receptor_node_name not in nodes):
        print("ERROR: '",receptor_node_name,"' not found")
        return None 

    if (emetor_node_name not in nodes):
        print("ERROR: '",emetor_node_name,"' not found")
        return None 

    node_in  = nodes[receptor_node_name].inputs[receptor_socket_idx]
    node_out = nodes[emetor_node_name].outputs[emetor_socket_idx]

    # Check if node_out is already linked to node_in
    if any(link.to_socket==node_in for link in node_out.links):
        return None

    #link the two inputs
    mod.node_group.links.new(node_in, node_out)
    
    return None

def set_texture_ptr(psy, prop_name, value,):
    """changing a texture ptr == assigning texture nodetree to a psy texture nodegroup"""

    node = get_node(psy, prop_name)
    if (node is None): 
        return None 

    #make sure texture type, should startwith prefix
    ng_name = value if value.startswith(".TEXTURE ") else f".TEXTURE {value}"
    if (ng_name==f".TEXTURE "):
        ng_name = ".TEXTURE *DEFAULT* MKIV"

    ng = bpy.data.node_groups.get(ng_name)
    if (ng is None):
        print("ERROR: '",ng_name,"' not found")
        return None

    if (node.node_tree!=ng):
        node.node_tree = ng

    return None 

def set_keyword(psy, value, element=None, kw="info_keyword",):
    """update keword node in psy nodetree"""

    if (element is None):
        get_node(psy, kw).string = value
    else:
        #elements == "1=distribution_method 2=space 3=surface singlesurf/multisurf"
        l = get_node(psy, kw).string.split(" ")
        l[element] = value
        get_node(psy, kw).string = " ".join(l)

    return None 

def get_keyword(psy, kw="info_keyword"):
    """get keyword value from psy node"""

    return get_node(psy, kw).string

def random_seed(psy, event, api_is_random="", api_seed="",):
    """random psy function of a nodetree, will assign property"""

    # This BooleanProperty will always be False, it is acting as a function
    if (getattr(psy,api_is_random)==False):
          return None

    setattr(psy,api_is_random,False,)

    scat_scene = bpy.context.scene.scatter5
    emitter = psy.id_data

    #ignore any properties update behavior, such as update delay or hotkeys
    with scat_scene.factory_update_pause(event=True,delay=True,sync=False):

        #alt for batch support
        if (event.alt and scat_scene.factory_alt_allow):
            psys_sel = emitter.scatter5.get_psys_selected(all_emitters=scat_scene.factory_alt_selection_method=="all_emitters")
            for p in psys_sel:
                setattr(p,api_seed,random.randint(0,9999),)
        else:
            setattr(psy,api_seed,random.randint(0,9999),)
    
    return None


# .dP"Y8 88""Yb 888888  dP""b8 88    db    88         88   88 88""Yb 8888b.     db    888888 888888
# `Ybo." 88__dP 88__   dP   `" 88   dPYb   88         88   88 88__dP  8I  Yb   dPYb     88   88__
# o.`Y8b 88"""  88""   Yb      88  dP__Yb  88  .o     Y8   8P 88"""   8I  dY  dP__Yb    88   88""
# 8bodP' 88     888888  YboodP 88 dP""""Yb 88ood8     `YbodP' 88     8888Y"  dP""""Yb   88   888888


def fallremap_getter(prop_name):
    """get remap graph points matrix from node"""

    from .. curve.fallremap import get_matrix

    def getter(self):
        node = get_node(self, f"{prop_name}.fallremap")
        matrix = get_matrix(node.mapping.curves[0], handle=True, string=True,)
        return matrix

    return getter

def fallremap_setter(prop_name):
    """set remap graph matrix from matrix str"""

    from .. curve.fallremap import set_matrix

    def setter(self,matrix):
        node = get_node(self, f"{prop_name}.fallremap")

        set_matrix(node.mapping.curves[0], matrix,)
        node.mute = not node.mute ; node.mute = not node.mute ; node.mapping.update() #trigger update signal
        return None 
        
    return setter

def update_active_camera_nodegroup(scene=None, render=False, force_update=False, self_call=False,):
    """update camera pointer information, this function is runned on depsgraph handlers
    we need to be extra carreful about feedback loop in this fct"""

    #TODO: we are taking a lot of risk in this function. 
    #      Any error could mess up the users camera optimization
    #TODO: we had report on some users "AttributeError: "
    #       Writing to ID classes in this context is not allowed: .Scatter5 Geonode Engine MKIII.003, NodeTree datablock, error setting FunctionNodeInputVector.vector"
    #      it seems that interacting with nodes from a depsgraph update is not recommanded?
    #      Very strange that it is only happening to some users. Only had one report so far, maybe a blender bug.

    #find scene context, we might pass scene via depsgraph handler
    if (scene is None):
        scene = bpy.context.scene
        
    #static vars initialization
    _f = update_active_camera_nodegroup
    #initialize static attr
    if (not hasattr(_f,"is_updating")):
        _f.is_updating = False
    #a force update will reset the updating delay system, to avoid delay system freezing indefinitely, user can kick it. WARNING this also means that it is strictly forbidden to call a force update from a depsgraph loop
    if (force_update):
        _f.is_updating = False
        
    dprint(f"HANDLER->CAM_UPD: - force_update={force_update} - is_updating={_f.is_updating} - self_call={self_call} - render={render}", depsgraph=True,)
        
    #get cam information
    if (render):
          deps = bpy.context.evaluated_depsgraph_get()
          cam = scene.camera.evaluated_get(deps)
          dprint("HANDLER->CAM_UPD: confirm depsgraph evaluation", depsgraph=True,)
    else: cam = scene.camera 
    
    #skip if cam is None
    if (cam is None): 
        dprint("HANDLER->CAM_UPD: canceled - no cam found",depsgraph=True,)
        return None
    
    #skip if function is currently running updates 
    #Dangerous.., if  singleton is not updated properly, will lead to updates dependencies issues
    if (_f.is_updating and not force_update): 
        dprint("HANDLER->CAM_UPD: canceled - In order to avoid depsgraph feedback loop, we had to cancel this update",depsgraph=True,)
        return None 
    
    #get camera transforms
    cam_loc, cam_rot = cam.matrix_world.translation, cam.matrix_world.to_euler()

    #special delayed update methods, we don't want constant update triggers
    if ((not force_update) and (not self_call)):

        #delay update depending on ms. if ms is set to 0, then, constant update flow
        if (scene.scatter5.factory_cam_update_method=="update_delayed"):
            if (scene.scatter5.factory_cam_update_ms!=0):
                function_exec_delay( #using same is_running singleton could create conflict?
                    interval=scene.scatter5.factory_cam_update_ms,
                    function=update_active_camera_nodegroup,
                    arg=[], 
                    kwarg={"self_call":True},
                    )
                return None

        #update apply == will run force update signal
        elif (scene.scatter5.factory_cam_update_method=="update_apply"): 
            return None

        #update when the camera has stopped moving, for this we track camera movement
        elif (scene.scatter5.factory_cam_update_method=="update_on_release"): 

            #initialize static attr
            if (not hasattr(_f,"camera_sum")):
                _f.camera_sum = None
            if (not hasattr(_f,"waiting_for_halt")):
                _f.waiting_for_halt = False

            #don't launch a new instance of the function if already running..
            if (_f.waiting_for_halt):
                dprint("HANDLER->CAM_UPD: canceled - halt loop currently running",depsgraph=True,)
                return None 

            def cam_still_delay():
                """timer used to add delay until cam has stopped moving"""

                cam_loc, cam_rot = cam.matrix_world.translation, cam.matrix_world.to_euler()
                new_sum = sum(cam_loc) + sum(cam_rot)
                    
                #if value change every x ms, it means users is Still moving
                #then we need to continue the timer function..
                if (new_sum!=_f.camera_sum): 
                    _f.camera_sum = new_sum
                    return 0.45

                dprint("HANDLER->CAM_UPD: halt loop finished",depsgraph=True,)
                
                _f.waiting_for_halt = False 
                update_active_camera_nodegroup(self_call=True)
                
                return None

            dprint("HANDLER->CAM_UPD: launching halt loop..",depsgraph=True,)

            #launch an instance of the function
            bpy.app.timers.register(cam_still_delay)
            _f.waiting_for_halt = True 

            return None 
    
    #update psys

    #Needed in order to avoid feedback loop. Changing values below will send an update trigger, and this function react upon update triggers..
    _f.is_updating = True 

    try:

        dprint(f"HANDLER->CAM_UPD: looping all scene.scatter5.get_all_psys():",depsgraph=True,)

        for p in [ p for p in scene.scatter5.get_all_psys() \
                   if (p.s_visibility_cam_allow or p.s_scale_fading_allow or (p.s_display_allow and p.s_display_camdist_allow)) #NOTE: that master_allow not taken into consideration here, todo?
                 ]:

            #change psy node value(s)
        
            #NOTE: FALSE input index value will lead to constant update, need to be extra careful with setting and reading the values below

            mod = p.get_scatter_mod(raise_exception=False)
            if (mod is None): 
                dprint(f"HANDLER->CAM_UPD: skipping a system, couldn't get the mod:",depsgraph=True,)
                continue
            
            nodes = mod.node_group.nodes

            # NOTE: "or (force_update and render)" is needed because of an issue,
            # cam_loc/cam_rot refuse to give us accurate values if evaluated from depsgraph, read give us different value if it is read and written.. quantum bug..

            if ( nodes["s_cam_location"].vector[:] != cam_loc[:]) or (force_update and render):
                # print(nodes["s_cam_location"].vector[:],"=?=",cam_loc[:],"=>",'nodes["s_cam_location"',)
                # print("DEBUG -- s_cam_location -- ",cam_loc)
                nodes["s_cam_location"].vector = cam_loc
                dprint(f"HANDLER->CAM_UPD: 's_cam_location' (force_update={force_update})",depsgraph=True,)
            
            if ( nodes["s_cam_rotation_euler"].vector[:] != cam_rot[:]) or (force_update and render):
                # print(nodes["s_cam_rotation_euler"].vector[:],"=?=",cam_rot[:],"=>",'nodes["s_cam_rotation_euler"',)
                # print("DEBUG -- s_cam_rotation_euler -- ",cam_rot)
                nodes["s_cam_rotation_euler"].vector = cam_rot
                dprint(f"HANDLER->CAM_UPD: 's_cam_rotation_euler' (force_update={force_update})",depsgraph=True,)    

            #per camera cam clipping properties

            if (p.s_visibility_camclip_allow and p.s_visibility_camclip_cam_autofill):

                if ( nodes["s_visibility_cam"].inputs[7].default_value != cam.data.lens):
                    # print(nodes["s_visibility_cam"].inputs[7].default_value,"=?=",active_cam.data.lens,"=>",'nodes["s_visibility_cam"].inputs[7',)
                    # print("DEBUG -- camclip_autofill.lens")
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_lens", cam.data.lens,)
                    dprint(f"HANDLER->CAM_UPD: 's_visibility_camclip_cam_lens' (force_update={force_update})",depsgraph=True,)

                if ( nodes["s_visibility_cam"].inputs[6].default_value != cam.data.sensor_width):
                    # print(nodes["s_visibility_cam"].inputs[6].default_value,"=?=",active_cam.data.sensor_width,"=>",'nodes["s_visibility_cam"].inputs[6',)
                    # print("DEBUG -- camclip_autofill.sensor_width")
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_sensor_width", cam.data.sensor_width,)
                    dprint(f"HANDLER->CAM_UPD: 's_visibility_camclip_cam_sensor_width' (force_update={force_update})",depsgraph=True,)

                if ( nodes["s_visibility_cam"].inputs[8].default_value[:] != (scene.render.resolution_x,scene.render.resolution_y,0)):
                    # print(nodes["s_visibility_cam"].inputs[8].default_value[:],"=?=",(scene.render.resolution_x,scene.render.resolution_y,0),"=>",'nodes["s_visibility_cam"].inputs[8',)
                    # print("DEBUG -- camclip_autofill.res_xy")
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_res_xy", (scene.render.resolution_x,scene.render.resolution_y),)
                    dprint(f"HANDLER->CAM_UPD: 's_visibility_camclip_cam_res_xy' (force_update={force_update})",depsgraph=True,)

                if ( nodes["s_visibility_cam"].inputs[9].default_value[:] != (cam.data.shift_x,cam.data.shift_y,0)):
                    # print(nodes["s_visibility_cam"].inputs[9].default_value[:],"=?=",(active_cam.data.shift_x,active_cam.data.shift_y,0),"=>",'nodes["s_visibility_cam"].inputs[9',)
                    # print("DEBUG -- camclip_autofill.shift_xy")
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_shift_xy", (cam.data.shift_x,cam.data.shift_y),)
                    dprint(f"HANDLER->CAM_UPD: 's_visibility_camclip_cam_shift_xy' (force_update={force_update})",depsgraph=True,)

                if ( nodes["s_visibility_cam"].inputs[10].default_value[:-1] != cam.scatter5.s_visibility_camclip_per_cam_boost_xy[:] ):
                    # print(nodes["s_visibility_cam"].inputs[10].default_value[:-1],"=?=",active_cam.scatter5.s_visibility_camclip_per_cam_boost_xy[:],"=>",'nodes["s_visibility_cam"].inputs[10',)
                    # print("DEBUG -- camclip_autofill.s_visibility_camclip_per_cam_boost_xy")
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_boost_xy", (cam.scatter5.s_visibility_camclip_per_cam_boost_xy),)
                    dprint(f"HANDLER->CAM_UPD: 's_visibility_camclip_cam_boost_xy' (force_update={force_update})",depsgraph=True,)


            #per camera culling distance properties

            if (p.s_visibility_camdist_allow and p.s_visibility_camdist_per_cam_data):

                if ( nodes["s_visibility_cam"].inputs[14].default_value != cam.scatter5.s_visibility_camdist_per_cam_min):
                    # print(nodes["s_visibility_cam"].inputs[14].default_value,"=?=",active_cam.scatter5.s_visibility_camdist_per_cam_min,"=>",'nodes["s_visibility_cam"].inputs[14',)
                    # print("DEBUG -- vis_camdist_per_cam.min")
                    UpdatesRegistry.run_update(p,"s_visibility_camdist_min", cam.scatter5.s_visibility_camdist_per_cam_min,)
                    dprint(f"HANDLER->CAM_UPD: 's_visibility_camdist_per_cam_min' (force_update={force_update})",depsgraph=True,)

                if ( nodes["s_visibility_cam"].inputs[15].default_value != cam.scatter5.s_visibility_camdist_per_cam_max):
                    # print(nodes["s_visibility_cam"].inputs[15].default_value,"=?=",active_cam.scatter5.s_visibility_camdist_per_cam_max,"=>",'nodes["s_visibility_cam"].inputs[15',)
                    # print("DEBUG -- vis_camdist_per_cam.max")
                    UpdatesRegistry.run_update(p,"s_visibility_camdist_max", cam.scatter5.s_visibility_camdist_per_cam_max,)
                    dprint(f"HANDLER->CAM_UPD: 's_visibility_camdist_per_cam_max' (force_update={force_update})",depsgraph=True,)

            #per camera scale fading distance properties 

            if (p.s_scale_fading_allow and p.s_scale_fading_per_cam_data):

                if ( nodes["s_scale_fading"].inputs[3].default_value != cam.scatter5.s_scale_fading_distance_per_cam_min):
                    # print(nodes["s_scale_fading"].inputs[3].default_value,"=?=",active_cam.scatter5.s_scale_fading_distance_per_cam_min,"=>",'nodes["s_scale_fading"].inputs[3',)
                    # print("DEBUG -- per_cam_fading.min")
                    UpdatesRegistry.run_update(p,"s_scale_fading_distance_min", cam.scatter5.s_scale_fading_distance_per_cam_min,)
                    dprint(f"HANDLER->CAM_UPD: 's_scale_fading_distance_per_cam_min' (force_update={force_update})",depsgraph=True,)

                if ( nodes["s_scale_fading"].inputs[4].default_value != cam.scatter5.s_scale_fading_distance_per_cam_max):
                    # print(nodes["s_scale_fading"].inputs[4].default_value,"=?=",active_cam.scatter5.s_scale_fading_distance_per_cam_max,"=>",'nodes["s_scale_fading"].inputs[4',)
                    # print("DEBUG -- per_cam_fading.max")
                    UpdatesRegistry.run_update(p,"s_scale_fading_distance_max", cam.scatter5.s_scale_fading_distance_per_cam_max,)
                    dprint(f"HANDLER->CAM_UPD: 's_scale_fading_distance_per_cam_max' (force_update={force_update})",depsgraph=True,)

            continue 

    except Exception as e:

        print("WARNING: An error occured while we tried to update your camera optimization settings:")    
        print(e)

    _f.is_updating = False

    return None

def update_is_rendered_view_nodegroup(value=None,):
    """update nodegroup"""

    dprint("HANDLER: 'update_is_rendered_view_nodegroup'",depsgraph=True)

    #check needed? perhaps we already have the information
    if (value is None): 
        value = is_rendered_view()

    #change value in nodegroup
    for ng in [ng for ng in bpy.data.node_groups if (ng.name.startswith(".S Handler is rendered")) and (ng.nodes["boolean"].boolean != value) ]:
        ng.nodes["boolean"].boolean = value
        
        dprint("HANDLER: 'update_is_rendered_view_nodegroup'-> Changed value",depsgraph=True)
        
        continue

    return None

def update_manual_uuid_surfaces(force_update=False, flush_uuid_cache:int=None, flush_entire_cache=False,):
    """run uuid update when user is adding/removing objects in collections, run on depsgraph update"""

    #init static variables
    _f = update_manual_uuid_surfaces
    if (not hasattr(_f,"cache") or flush_entire_cache):
        _f.cache = {}
    if (not hasattr(_f,"pause")):
        _f.pause = False

    #avoid running function?  use update_manual_uuid_surfaces.pause from external if needed
    if (_f.pause) and (not force_update):
        return None

    #flush cache of specific psy if needed
    if (flush_uuid_cache is not None): 
        if (flush_uuid_cache in _f.cache):
            del _f.cache[flush_uuid_cache]

    #find all psys with manual mode & multi-surface

    for p in [ p for p in bpy.context.scene.scatter5.get_all_psys() if (not p.hide_viewport) and (p.s_distribution_method=="manual_all") ]:

        #check if cache changed? if so, send update & sample new cache
        cvalue = set(s.name for s in p.get_surfaces())

        if ((p.uuid not in _f.cache) or (_f.cache[p.uuid]!=cvalue)):
            
            #update nodetree uuid equivalence
            dprint("HANDLER: 'update_factory.update_manual_uuid_equivalence()'",)
            _f.cache[p.uuid] = cvalue
            update_manual_uuid_equivalence(p)

            continue

    return None 

def update_manual_uuid_equivalence(psy):
    """set equivalence id from uuid in nodetree, only for multi-surface + manual distribution"""
    
    #avoid feedback loop
    update_manual_uuid_surfaces.pause = True

    #we cannot rely on geometry node `surf_id` as the order might change
    #manual mode will write the contacted surface scatter5.uuid value as per point int attribute
    #we'll find the equivalence from `surf_id`& their uuid values in the nodetree in order to assign correct local to glonal transforms

    #set up nodetree for a depsgraph eval
    #just eval the surfaces as instances, nothing else.
    UpdatesRegistry.s_eval_depsgraph(psy, "s_eval_depsgraph", "surfaces",) #link surfaces as output
    mod = psy.get_scatter_mod()
    nodes = mod.node_group.nodes
    nodes["s_surface_evaluator"].inputs[4].default_value = True #do not realize

    #get id of the surfaces from within the geometry node engine, cannot be deduced & create equivalent dict
    #seems weird, but order of depsgraph instance == order of geometry node collection instance index too (starting at 0)
    i = 0
    equivalence = {}
    for ins in [ ins.object.original for ins in bpy.context.evaluated_depsgraph_get().object_instances if \
                 ( (ins.is_instance) and (ins.parent.original==psy.scatter_obj) and (ins.object.original.name!=psy.scatter_obj.name) ) 
                ]: #we get the surfaces by interacting with the geonode engine
        equivalence[ins.name] = (i, ins.scatter5.uuid,)
        i+=1
        continue

    dprint(f"UPDFCT: equivalence '{psy.name}' : {equivalence}",)

    #restore depsgraph evalto old
    nodes["s_surface_evaluator"].inputs[4].default_value = False #set as realize again
    UpdatesRegistry.s_eval_depsgraph(psy, "s_eval_depsgraph", False,)

    #performance boost while changing nodetree
    _hide_viewport = psy.hide_viewport
    psy.hide_viewport = True

    #update nodetree equivalence nodes! will replace `manual_surface_uuid` with the real id
    ng_equi = nodes["s_distribution_manual"].node_tree.nodes["uuid_equivalence"].node_tree

    #cleanse all noodles 
    ng_equi.links.clear()

    #modify or change existing
    idx = 0
    nodechain = []
    nodechain.append(ng_equi.nodes["Group Input"])
    
    for k,(idx,uuid) in equivalence.items():
        name = f"surf_id {idx}"
        n = ng_equi.nodes.get(name)
        
        if (n is None): 
            n = ng_equi.nodes.new("GeometryNodeGroup")
            n.node_tree = bpy.data.node_groups[".S Replace UUID MKIV"] #need to be correct mk version!!!
            n.name = n.label = name 
        
        n.location.x = (idx+1)*175
        n.location.y = 0
        n.inputs[1].default_value = uuid #search
        n.inputs[2].default_value = idx #replace
        nodechain.append(n)
        continue

    #adjust last output location
    outputnode = ng_equi.nodes["Group Output"]
    nodechain.append(outputnode)
    outputnode.location.x = (idx+2)*175
    outputnode.inputs[1].default_value = idx #update maxlen id

    #create the noodles
    for i,n in enumerate(nodechain): 
        #ignore first element
        if (i==0): 
            continue
        node_in  = nodechain[i].inputs[0]
        node_out = nodechain[i-1].outputs[0]
        ng_equi.links.new(node_in, node_out)
        continue

    #remove excess
    to_remove = [n for n in ng_equi.nodes if (n.name.startswith("surf_id") and (n not in nodechain))]
    for n in to_remove.copy(): 
        ng_equi.nodes.remove(n)

    #avoid feedback loop
    update_manual_uuid_surfaces.pause = False 
    #performance boost 
    psy.hide_viewport = _hide_viewport

    return None 

def update_frame_start_end_nodegroup():
    """update start/end frame nodegroup"""

    scene = bpy.context.scene
    if (not scene):
        return None

    #change value in nodegroup
    for ng in bpy.data.node_groups:

        if (ng.name.startswith(".S Handler Frame")):
            
            if (ng.nodes["frame_start"].integer!=int(scene.frame_start)):
                ng.nodes["frame_start"].integer = scene.frame_start
                did_act = True
            
            if (ng.nodes["frame_end"].integer!=int(scene.frame_end)):
                ng.nodes["frame_end"].integer = scene.frame_end
                did_act = True

        continue
        
    if ("did_act" in locals()):
        dprint("HANDLER: 'update_frame_start_end_nodegroup'", depsgraph=True,)

    return None

def factory_viewport_method_proxy(api, bool_api):
    """special case update fct generator for viewport_method enum ui, we created BoolProperty proxy for interface
    this function is the update function of these properties, they will set the appropiate EnumProperty value"""

    #access self attr
    _f = factory_viewport_method_proxy

    def fct(self, context):

        nonlocal api, bool_api

        #avoid feedback loop
        if (_f.pause):
            return None  
        _f.pause = True

        #dprint(f"UPD: factory_viewport_method_proxy() bool_api={bool_api}")

        #update viewport enum property from bool values
        if (bool_api=="screen"):
            setattr(self,f"{api}_viewport_method","except_rendered")
        elif (bool_api=="shaded"):
            setattr(self,f"{api}_viewport_method","viewport_only")
        elif (bool_api=="render"):
            setattr(self,f"{api}_viewport_method","viewport_and_render")

        #avoid feedback loop
        _f.pause = False

        return None 

    return fct

#define function singleton attr
factory_viewport_method_proxy.pause = False


def ensure_viewport_method_interface(psy, api, value,):
    """ensure values of BoolProperty are in synch with EnumProperty """

    #stop update funcs to avoid feedback loop
    global factory_viewport_method_proxy
    factory_viewport_method_proxy.pause = True
    
    screen = getattr(psy, f"{api}_allow_screen",)
    shaded = getattr(psy, f"{api}_allow_shaded",)
    render = getattr(psy, f"{api}_allow_render",)
    
    #dprint(f"UPD: ensure_viewport_method_interface() value={value}, scr/sh/rdr={screen,shaded,render}")

    #"except_rendered"     == screen
    #"viewport_only"       == screen + shaded
    #"viewport_and_render" == screen + shaded + render

    if (value=="except_rendered"):
        if not screen: setattr(psy, f"{api}_allow_screen", True,)
        if     shaded: setattr(psy, f"{api}_allow_shaded", False,)
        if     render: setattr(psy, f"{api}_allow_render", False,)
    elif (value=="viewport_only"):
        if not screen: setattr(psy, f"{api}_allow_screen", True,)
        if not shaded: setattr(psy, f"{api}_allow_shaded", True,)
        if     render: setattr(psy, f"{api}_allow_render", False,)
    elif (value=="viewport_and_render"):
        if not screen: setattr(psy, f"{api}_allow_screen", True,)
        if not shaded: setattr(psy, f"{api}_allow_shaded", True,)
        if not render: setattr(psy, f"{api}_allow_render", True,)

    #avoid feedback loop
    factory_viewport_method_proxy.pause = False
    return None



# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo oooo d8b oooo    ooo
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   `888""8P  `88.  .8'
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888    888       `88..8'
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 .  888        `888'
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" d888b        .8'
#                        d"     YD                                  .o..P'
#                        "Y88888P'                                  `Y8P'


#this class is never instanced
class UpdatesRegistry():
    """most of our scatter-systems properties update fct are centralized in this class
    some might be generated at parsetime, final result is store in UpdateProperties dict""" 
    
    ################ update fct decorator factory:

    def tag_register(nbr=0):
        """update fct can either be a generator fct or just a direct update fct"""

        def tag_update_decorator(fct):
            """just mark function with tag"""

            fct.register_tag = True
            if (nbr>0):
                fct.generator_nbr = nbr 
            return fct

        return tag_update_decorator

    ################ generator for umask properties

    def codegen_umask_updatefct(scope_ref={}, name=""):
        """code generation, automatize the creation of the update functions for the universal mask system"""

        d = {}

        def _gen_mask_ptr(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=value, entry="input", i=1)
        _gen_mask_ptr.register_tag = True #add tag
        d[f"{name}_mask_ptr"] = _gen_mask_ptr

        def _gen_mask_reverse(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=value, entry="input", i=2)
        _gen_mask_reverse.register_tag = True #add tag
        d[f"{name}_mask_reverse"] = _gen_mask_reverse

        def _gen_mask_method(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=get_enum_idx(p, prop_name, value,), entry="input", i=3)
        _gen_mask_method.register_tag = True #add tag
        d[f"{name}_mask_method"] = _gen_mask_method

        def _gen_mask_color_sample_method(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
        _gen_mask_color_sample_method.register_tag = True #add tag
        d[f"{name}_mask_color_sample_method"] = _gen_mask_color_sample_method

        def _gen_mask_id_color_ptr(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=color_convert(value), entry="input", i=5)
        _gen_mask_id_color_ptr.register_tag = True #add tag
        d[f"{name}_mask_id_color_ptr"] = _gen_mask_id_color_ptr

        def _gen_mask_noise_scale(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=value, entry="input", i=7)
        _gen_mask_noise_scale.register_tag = True #add tag
        d[f"{name}_mask_noise_scale"] = _gen_mask_noise_scale

        def _gen_mask_noise_seed(p, prop_name, value, event=None, bypass=False,): 
            node_value(p, f"{name}.umask", value=value, entry="input", i=8)
        _gen_mask_noise_seed.register_tag = True #add tag
        d[f"{name}_mask_noise_seed"] = _gen_mask_noise_seed

        def _gen_mask_noise_is_random_seed(p, prop_name, value, event=None, bypass=False,): 
            random_seed(p, event, api_is_random=f"{name}_mask_noise_is_random_seed", api_seed=f"{name}_mask_noise_seed")
        _gen_mask_noise_is_random_seed.register_tag = True #add tag
        d[f"{name}_mask_noise_is_random_seed"] = _gen_mask_noise_is_random_seed

        def _gen_mask_noise_brightness(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=value, entry="input", i=9)
        _gen_mask_noise_brightness.register_tag = True #add tag
        d[f"{name}_mask_noise_brightness"] = _gen_mask_noise_brightness

        def _gen_mask_noise_contrast(p, prop_name, value, event=None, bypass=False,):
            node_value(p, f"{name}.umask", value=value, entry="input", i=10)
        _gen_mask_noise_contrast.register_tag = True #add tag
        d[f"{name}_mask_noise_contrast"] = _gen_mask_noise_contrast

        #define objects in dict
        scope_ref.update(d)
        return d

    ################ list of all our updatefunction, can be generator:

    # .dP"Y8 88  88  dP"Yb  Yb        dP   88  88 88 8888b.  888888
    # `Ybo." 88  88 dP   Yb  Yb  db  dP    88  88 88  8I  Yb 88__
    # o.`Y8b 888888 Yb   dP   YbdPYbdP     888888 88  8I  dY 88""
    # 8bodP' 88  88  YbodP     YP  YP      88  88 88 8888Y"  888888

    @tag_register()
    def hide_viewport(p, prop_name, value, event=None, bypass=False,):
        p.scatter_obj.hide_viewport = value
        #also update geonode mod!
        mod = p.get_scatter_mod()
        if (mod is not None):
            mod.show_viewport = not p.hide_viewport

    @tag_register()
    def hide_render(p, prop_name, value, event=None, bypass=False,):
        p.scatter_obj.hide_render = p.hide_render
        #also update geonode mod!
        mod = p.get_scatter_mod()
        if (mod is not None):
            mod.show_render = not p.hide_render

    #  dP""b8  dP"Yb  88      dP"Yb  88""Yb
    # dP   `" dP   Yb 88     dP   Yb 88__dP
    # Yb      Yb   dP 88  .o Yb   dP 88"Yb
    #  YboodP  YbodP  88ood8  YbodP  88  Yb 

    @tag_register()
    def s_color(p, prop_name, value, event=None, bypass=False,):
        p.scatter_obj.color = list(value)+[1]

    # .dP"Y8 88   88 88""Yb 888888    db     dP""b8 888888
    # `Ybo." 88   88 88__dP 88__     dPYb   dP   `" 88__
    # o.`Y8b Y8   8P 88"Yb  88""    dP__Yb  Yb      88""
    # 8bodP' `YbodP' 88  Yb 88     dP""""Yb  YboodP 888888

    @tag_register()
    def s_surface_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_surface_evaluator", value=value=="collection", entry="input", i=1)
        #update keyword info
        set_keyword(p, "multisurf" if (value=="collection") else "singlesurf", element=2,)
        #update dependencies, two methods shares the same 
        if (value in ("emitter","object")):
            node_value(p, "s_surface_evaluator", value= p.id_data if (value=="emitter") else p.s_surface_object, entry="input", i=0)
        #update square area value
        p.get_surfaces_square_area(evaluate="init_only", eval_modifiers=True, get_selection=False,)
    
    @tag_register()
    def s_surface_object(p, prop_name, value, event=None, bypass=False,):
        if (p.s_surface_method=="object"):
            node_value(p, "s_surface_evaluator", value=p.s_surface_object, entry="input", i=0)
        #update square area value
        p.get_surfaces_square_area(evaluate="init_only", eval_modifiers=True, get_selection=False,)

    @tag_register()
    def s_surface_collection(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_surface_evaluator", value=bpy.data.collections.get(p.s_surface_collection), entry="input", i=2)
        #update square area value
        p.get_surfaces_square_area(evaluate="init_only", eval_modifiers=True, get_selection=False,)
        #refresh uuid?
        if (p.s_distribution_method=="manual_all"):
            update_manual_uuid_equivalence(p)

    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8

    @tag_register()
    def s_distribution_method(p, prop_name, value, event=None, bypass=False,):
        #link distribution methods
        node_link(p, prop_name, value,)
        node_link(p, prop_name+"_N", value+"_N",)

        #update nodetree distribution keyword info
        set_keyword(p, value, element=0,)

        #update nodetree local/global distribution keyword info & update dependencies    
        if (value=="random"):
            p.s_distribution_space = p.s_distribution_space
            set_keyword(p, p.s_distribution_space, element=1,)
        elif (value=="clumping"):
            p.s_distribution_clump_space = p.s_distribution_clump_space
            set_keyword(p, p.s_distribution_clump_space, element=1,)
        #every other distribution methods are local only
        else:
            set_keyword(p, "local", element=1,)
            node_value(p, "s_surface_evaluator", value=True, entry="input", i=3)

    #Random Distribution 

    @tag_register()
    def s_distribution_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_surface_evaluator", value=value=="local", entry="input", i=3)
        set_keyword(p, value, element=1,)

    @tag_register()
    def s_distribution_is_count_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_random", value=p.s_distribution_count if (value=="count") else -1, entry="input", i=2)
    
    @tag_register()
    def s_distribution_count(p, prop_name, value, event=None, bypass=False,):
        if (p.s_distribution_is_count_method=="count"):
            node_value(p, "s_distribution_random", value=value, entry="input", i=2)
    
    @tag_register()
    def s_distribution_density(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_random", value=value, entry="input", i=3)
    
    @tag_register()
    def s_distribution_limit_distance_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_random", value=value, entry="input", i=5)
    
    @tag_register()
    def s_distribution_limit_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_random", value=value, entry="input", i=6)
    
    @tag_register()
    def s_distribution_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_random", value=value, entry="input", i=4)
    
    @tag_register()
    def s_distribution_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_seed", )

    #Verts

    #Faces

    #Edges

    @tag_register()
    def s_distribution_edges_selection_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_edges", value=get_enum_idx(p, prop_name, value,)-1, entry="input", i=1)
    
    @tag_register()
    def s_distribution_edges_position_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_edges", value=0 if (value=="center") else 1, entry="input", i=2)

    #Volume

    #@tag_register()
    #def s_distribution_volume_is_count_method(p, prop_name, value, event=None, bypass=False,):
    #    node_value(p, "s_distribution_volume", p.s_distribution_volume_count if (value=="count") else -1, entry="input", i=2)

    #@tag_register() 
    #def s_distribution_volume_count(p, prop_name, value, event=None, bypass=False,):
    #    if (p.s_distribution_volume_is_count_method=="count"):
    #        node_value(p, "s_distribution_volume", value, entry="input", i=2)

    @tag_register()
    def s_distribution_volume_density(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_volume", value=value, entry="input", i=3)
    
    @tag_register()
    def s_distribution_volume_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_volume", value=value, entry="input", i=3)
    
    @tag_register()
    def s_distribution_volume_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_volume_seed", )
    
    @tag_register()
    def s_distribution_volume_limit_distance_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_volume", value=value, entry="input", i=5)
    
    @tag_register()
    def s_distribution_volume_limit_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_volume", value=value, entry="input", i=6)

    #Random Stable 

    @tag_register()
    def s_distribution_stable_uv_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_stable", value=value, entry="input", i=7)
    
    @tag_register()
    def s_distribution_stable_is_count_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_stable", value=p.s_distribution_stable_count if (value=="count") else -1, entry="input", i=2)
    
    @tag_register()
    def s_distribution_stable_count(p, prop_name, value, event=None, bypass=False,):
        if (p.s_distribution_stable_is_count_method=="count"):
            node_value(p, "s_distribution_stable", value=value, entry="input", i=2)
    
    @tag_register()
    def s_distribution_stable_density(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_stable", value=value, entry="input", i=3)
    
    @tag_register()
    def s_distribution_stable_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_stable", value=value, entry="input", i=4)
    
    @tag_register()
    def s_distribution_stable_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_stable_seed", )
    
    @tag_register()
    def s_distribution_stable_limit_distance_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_stable", value=value, entry="input", i=5)
    
    @tag_register()
    def s_distribution_stable_limit_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_stable", value=value, entry="input", i=6)

    #Clump Distribution
    
    @tag_register()
    def s_distribution_clump_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_surface_evaluator", value=value=="local", entry="input", i=3)
        set_keyword(p, value, element=1,)
    
    @tag_register()
    def s_distribution_clump_density(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=3)
    
    @tag_register()
    def s_distribution_clump_limit_distance_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=4)
    
    @tag_register()
    def s_distribution_clump_limit_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=5)
    
    @tag_register()
    def s_distribution_clump_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=6)
    
    @tag_register()
    def s_distribution_clump_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_clump_seed")
    
    @tag_register()
    def s_distribution_clump_max_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=7)
    
    @tag_register()
    def s_distribution_clump_falloff(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=8)
    
    @tag_register()
    def s_distribution_clump_random_factor(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=9)

    @tag_register()
    def s_distribution_clump_children_density(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=10)
    
    @tag_register()
    def s_distribution_clump_children_limit_distance_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=11)
    
    @tag_register()
    def s_distribution_clump_children_limit_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=12)
    
    @tag_register()
    def s_distribution_clump_children_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump", value=value, entry="input", i=13)
    
    @tag_register()
    def s_distribution_clump_children_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_clump_children_seed")
    
    @tag_register()
    def s_distribution_clump_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_distribution_clump.fallremap",mute=not value)
        mute_node(p, "s_distribution_clump.fallnoisy",mute=not value)

    @tag_register()
    def s_distribution_clump_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_distribution_clump.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_distribution_clump.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_clump_fallnoisy_seed")

    # 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
    #  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
    #  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
    # 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'
    
    @tag_register()
    def s_mask_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_mask_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Vgroup
    
    @tag_register()
    def s_mask_vg_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Vg Mask", mute=not value,)
        node_link(p, f"RR_FLOAT s_mask_vg Receptor", f"RR_FLOAT s_mask_vg {value}",)
    
    @tag_register()
    def s_mask_vg_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_vg", value=value, entry="input", i=2)
    
    @tag_register()
    def s_mask_vg_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_vg", value=value, entry="input", i=3)

    #VColor
    
    @tag_register()
    def s_mask_vcol_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Vcol Mask", mute=not value,)
        node_link(p, f"RR_FLOAT s_mask_vcol Receptor", f"RR_FLOAT s_mask_vcol {value}",)
    
    @tag_register()
    def s_mask_vcol_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_vcol", value=value, entry="input", i=2)
    
    @tag_register()
    def s_mask_vcol_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_vcol", value=value, entry="input", i=3)
    
    @tag_register()
    def s_mask_vcol_color_sample_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_vcol", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
    
    @tag_register()
    def s_mask_vcol_id_color_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_vcol", value=color_convert(value), entry="input", i=5)

    #Bitmap 
    
    @tag_register()
    def s_mask_bitmap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Img Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_bitmap Receptor", f"RR_GEO s_mask_bitmap {value}",)
        p.s_mask_bitmap_uv_ptr = p.s_mask_bitmap_uv_ptr
    
    @tag_register()
    def s_mask_bitmap_uv_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_bitmap", value=value, entry="input", i=2)
    
    @tag_register()
    def s_mask_bitmap_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_bitmap", value=bpy.data.images.get(value), entry="input", i=3)
    
    @tag_register()
    def s_mask_bitmap_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_bitmap", value=not value, entry="input", i=4)
    
    @tag_register()
    def s_mask_bitmap_color_sample_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_bitmap", value=get_enum_idx(p, prop_name, value,), entry="input", i=5)
    
    @tag_register()
    def s_mask_bitmap_id_color_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_bitmap", value=color_convert(value), entry="input", i=6)

    #Materials
    
    @tag_register()
    def s_mask_material_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Mat Mask", mute=not value,)
        node_link(p, f"RR_FLOAT s_mask_material Receptor", f"RR_FLOAT s_mask_material {value}",)
    
    @tag_register()
    def s_mask_material_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_material", value=bpy.data.materials.get(value), entry="input", i=2)
    
    @tag_register()
    def s_mask_material_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_material", value=value, entry="input", i=3)
        
    #Curves

    @tag_register()
    def s_mask_curve_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Cur Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_curve Receptor", f"RR_GEO s_mask_curve {value}",)    
    
    @tag_register()
    def s_mask_curve_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_curve", value=value, entry="input", i=1)
    
    @tag_register()
    def s_mask_curve_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_curve", value=value, entry="input", i=2)

    #Boolean
    
    @tag_register()
    def s_mask_boolvol_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Bool Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_boolvol Receptor", f"RR_GEO s_mask_boolvol {value}",)
    
    @tag_register()
    def s_mask_boolvol_coll_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_boolvol", value=bpy.data.collections.get(value), entry="input", i=1)
    
    @tag_register()
    def s_mask_boolvol_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_boolvol", value=value, entry="input", i=2)

    #Upward Obstruction

    @tag_register()
    def s_mask_upward_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Up Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_upward Receptor", f"RR_GEO s_mask_upward {value}",)
    
    @tag_register()
    def s_mask_upward_coll_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_upward", value=bpy.data.collections.get(value), entry="input", i=1)
    
    @tag_register()
    def s_mask_upward_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_mask_upward", value=value, entry="input", i=2)

    # .dP"Y8  dP""b8    db    88     888888
    # `Ybo." dP   `"   dPYb   88     88__
    # o.`Y8b Yb       dP__Yb  88  .o 88""
    # 8bodP'  YboodP dP""""Yb 88ood8 888888
    
    @tag_register()
    def s_scale_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_scale_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Default 
    
    @tag_register()
    def s_scale_default_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Default Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_default Receptor", f"RR_VEC s_scale_default {value}",)
    
    @tag_register()
    def s_scale_default_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_default", value=value=="local_scale", entry="input", i=2)
    
    @tag_register()
    def s_scale_default_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_default", value=value, entry="input", i=3)
    
    @tag_register()
    def s_scale_default_multiplier(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_default", value=value, entry="input", i=4)

    #Random

    @tag_register()
    def s_scale_random_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Random Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_random Receptor", f"RR_VEC s_scale_random {value}",)
    
    @tag_register()
    def s_scale_random_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_random", value=value=="random_uniform", entry="input", i=1)
    
    @tag_register()
    def s_scale_random_factor(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_random", value=value, entry="input", i=2)
    
    @tag_register()
    def s_scale_random_probability(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_random", value=value/100, entry="input", i=3)
    
    @tag_register()
    def s_scale_random_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_random", value=value, entry="input", i=4)
    
    @tag_register()
    def s_scale_random_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_scale_random_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_random",)

    #Shrink 
    
    @tag_register()
    def s_scale_shrink_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Shrink", mute=not value,)
        node_link(p, f"RR_VEC s_scale_shrink Receptor", f"RR_VEC s_scale_shrink {value}",)
    
    @tag_register()
    def s_scale_shrink_factor(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_shrink", value=value, entry="input", i=1)

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_shrink",)

    #Grow

    @tag_register()
    def s_scale_grow_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Grow", mute=not value,)
        node_link(p, f"RR_VEC s_scale_grow Receptor", f"RR_VEC s_scale_grow {value}",)
    
    @tag_register()
    def s_scale_grow_factor(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_grow", value=value, entry="input", i=1)

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_grow",)

    #Fading 
    
    @tag_register()
    def s_scale_fading_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Scale Fading", mute=not value,)
        node_link(p, f"RR_VEC s_scale_fading Receptor", f"RR_VEC s_scale_fading {value}",)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)
    
    @tag_register()
    def s_scale_fading_factor(p, prop_name, value, event=None, bypass=False,):
            node_value(p, "s_scale_fading", value=value, entry="input", i=2)
    
    @tag_register()
    def s_scale_fading_per_cam_data(p, prop_name, value, event=None, bypass=False,):
        if (value==True):
            active_cam = bpy.context.scene.camera
            if (active_cam is not None):
                active_cam.scatter5.s_scale_fading_distance_per_cam_min = active_cam.scatter5.s_scale_fading_distance_per_cam_min 
                active_cam.scatter5.s_scale_fading_distance_per_cam_max = active_cam.scatter5.s_scale_fading_distance_per_cam_max 
        else: 
            node_value(p, "s_scale_fading", value=p.s_scale_fading_distance_min, entry="input", i=3)
            node_value(p, "s_scale_fading", value=p.s_scale_fading_distance_max, entry="input", i=4)
    
    @tag_register()
    def s_scale_fading_distance_min(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_fading", value=value, entry="input", i=3)
    
    @tag_register()
    def s_scale_fading_distance_max(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_fading", value=value, entry="input", i=4)
    
    @tag_register()
    def s_scale_fading_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_scale_fading.fallremap", mute=not value)

    @tag_register()
    def s_scale_fading_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_scale_fading.fallremap_revert",mute=not value)

    #Mirror
    
    @tag_register()
    def s_scale_mirror_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Random Mirror", mute=not value,)
        node_link(p, f"RR_GEO s_scale_mirror Receptor", f"RR_GEO s_scale_mirror {value}",)
    
    @tag_register()
    def s_scale_mirror_is_x(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_mirror", value=value, entry="input", i=1)
    
    @tag_register()
    def s_scale_mirror_is_y(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_mirror", value=value, entry="input", i=2)
    
    @tag_register()
    def s_scale_mirror_is_z(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_mirror", value=value, entry="input", i=3)
    
    @tag_register()
    def s_scale_mirror_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_mirror", value=value, entry="input", i=4)
    
    @tag_register()
    def s_scale_mirror_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_scale_mirror_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_mirror",)

    #Minimum 
    
    @tag_register()
    def s_scale_min_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Min Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_min Receptor", f"RR_VEC s_scale_min {value}",)
        node_link(p, f"RR_GEO s_scale_min Receptor", f"RR_GEO s_scale_min {value}",)
    
    @tag_register()
    def s_scale_min_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_min", value=(value=="s_scale_min_remove"), entry="input", i=2)
    
    @tag_register()
    def s_scale_min_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_min", value=value, entry="input", i=3)

    #Clump Distribution Exlusive 

    @tag_register()
    def s_scale_clump_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Clump Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_clump Receptor", f"RR_VEC s_scale_clump {value}",)
    
    @tag_register()
    def s_scale_clump_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_clump", value=value, entry="input", i=2)

    #Faces Distribution Exlusive 
    
    @tag_register()
    def s_scale_faces_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Face Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_faces Receptor", f"RR_VEC s_scale_faces {value}",)
    
    @tag_register()
    def s_scale_faces_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_faces", value=value, entry="input", i=2)

    #Edges Distribution Exlusive 

    @tag_register()
    def s_scale_edges_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Edge Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_edges Receptor", f"RR_VEC s_scale_edges {value}",)
    
    @tag_register()
    def s_scale_edges_vec_factor(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_scale_edges", value=value, entry="input", i=2)

    # 88""Yb  dP"Yb  888888    db    888888 88  dP"Yb  88b 88
    # 88__dP dP   Yb   88     dPYb     88   88 dP   Yb 88Yb88
    # 88"Yb  Yb   dP   88    dP__Yb    88   88 Yb   dP 88 Y88
    # 88  Yb  YbodP    88   dP""""Yb   88   88  YbodP  88  Y8
        
    @tag_register()
    def s_rot_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_rot_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)
        #specific align Z nodetree set up is a little special
        mute_node(p, "s_rot_align_z_clump", mute=not value,)

    #Align Z

    @tag_register()
    def s_rot_align_z_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Align Normal", mute=not value,)
        node_link(p, f"RR_VEC s_rot_align_z Receptor", f"RR_VEC s_rot_align_z {value}",)
    
    @tag_register()
    def s_rot_align_z_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_z", value=get_enum_idx(p, prop_name, value,), entry="input", i=2)
    
    @tag_register()
    def s_rot_align_z_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_z", value=value, entry="input", i=3)
    
    @tag_register()
    def s_rot_align_z_influence_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_z", value=value, entry="input", i=4)
    
    @tag_register()
    def s_rot_align_z_influence_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_z", value=value, entry="input", i=5)
    
    @tag_register()
    def s_rot_align_z_object(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_z", value=value, entry="input", i=6)
    
    @tag_register()
    def s_rot_align_z_random_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_z", value=value, entry="input", i=7)
    
    @tag_register()
    def s_rot_align_z_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_align_z_random_seed")
    
    @tag_register()
    def s_rot_align_z_clump_allow(p, prop_name, value, event=None, bypass=False,): 
        mute_color(p, "Clump Influence", mute=not value,)
        node_link(p, f"RR_VEC s_rot_align_z_clump Receptor", f"RR_VEC s_rot_align_z_clump {value}",)
    
    @tag_register()
    def s_rot_align_z_clump_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_z_clump", value=value, entry="input", i=2)

    #Align Y

    @tag_register()
    def s_rot_align_y_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Align Tangent", mute=not value,)
        node_link(p, f"RR_VEC s_rot_align_y Receptor", f"RR_VEC s_rot_align_y {value}",)
    
    @tag_register()
    def s_rot_align_y_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_y", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
    
    @tag_register()
    def s_rot_align_y_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_y", value=value, entry="input", i=5)
    
    @tag_register()
    def s_rot_align_y_object(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_y", value=value, entry="input", i=6)
    
    @tag_register()
    def s_rot_align_y_random_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_y", value=value, entry="input", i=7)
    
    @tag_register()
    def s_rot_align_y_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_align_y_random_seed")
    
    @tag_register()
    def s_rot_align_y_downslope_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_y", value=value=="local", entry="input", i=8)
    
    @tag_register()
    def s_rot_align_y_flow_method(p, prop_name, value, event=None, bypass=False,): 
        node_value(p, "s_rot_align_y.flowmap_method", value=get_enum_idx(p, prop_name, value,), entry="integer",)
    
    @tag_register()
    def s_rot_align_y_flow_direction(p, prop_name, value, event=None, bypass=False,): 
        node_value(p, "s_rot_align_y.flow_direction", value=value,)
    
    @tag_register()
    def s_rot_align_y_texture_ptr(p, prop_name, value, event=None, bypass=False,): 
        set_texture_ptr(p, "s_rot_align_y.texture", value)
    
    @tag_register()
    def s_rot_align_y_vcol_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_align_y.vcol_ptr", value=value, entry="attr",)

    #Tilt 

    @tag_register()
    def s_rot_tilt_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Tilt", mute=not value,)
        node_link(p, f"RR_VEC s_rot_tilt Receptor", f"RR_VEC s_rot_tilt {value}",)
    
    @tag_register()
    def s_rot_tilt_dir_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_tilt", value=get_enum_idx(p, prop_name, value,), entry="input", i=1)
    
    @tag_register()
    def s_rot_tilt_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_tilt", value=get_enum_idx(p, prop_name, value,), entry="input", i=2)
    
    @tag_register()
    def s_rot_tilt_noise_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_tilt", value=value, entry="input", i=7)
    
    @tag_register()
    def s_rot_tilt_texture_ptr(p, prop_name, value, event=None, bypass=False,):
        set_texture_ptr(p, "s_rot_tilt.texture", value)
    
    @tag_register()
    def s_rot_tilt_vcol_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_tilt", value=value, entry="input", i=3)
    
    @tag_register()
    def s_rot_tilt_direction(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_tilt", value=value, entry="input", i=4)
    
    @tag_register()
    def s_rot_tilt_force(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_tilt", value=value, entry="input", i=5)
    
    @tag_register()
    def s_rot_tilt_blue_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_tilt", value=1-value, entry="input", i=6)

    codegen_umask_updatefct(scope_ref=locals(), name="s_rot_tilt",)

    #Rot Random
    
    @tag_register()
    def s_rot_random_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Random Rotation", mute=not value,)
        node_link(p, f"RR_VEC s_rot_random Receptor", f"RR_VEC s_rot_random {value}",)
    
    @tag_register()
    def s_rot_random_tilt_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_random", value=value, entry="input", i=1)
    
    @tag_register()
    def s_rot_random_yaw_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_random", value=value, entry="input", i=2)
    
    @tag_register()
    def s_rot_random_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_random", value=value, entry="input", i=3)
    
    @tag_register()
    def s_rot_random_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_random_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_rot_random",)

    #Rot Add

    @tag_register()
    def s_rot_add_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Rotate", mute=not value,)
        node_link(p, f"RR_VEC s_rot_add Receptor", f"RR_VEC s_rot_add {value}",)
    
    @tag_register()
    def s_rot_add_default(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_add", value=value, entry="input", i=1)
    
    @tag_register()
    def s_rot_add_random(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_add", value=value, entry="input", i=2)
    
    @tag_register()
    def s_rot_add_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_add", value=value, entry="input", i=3)
    
    @tag_register()
    def s_rot_add_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_add_seed")
    
    @tag_register()
    def s_rot_add_snap(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_rot_add", value=value, entry="input", i=4)

    codegen_umask_updatefct(scope_ref=locals(), name="s_rot_add",)

    # 88""Yb    db    888888 888888 888888 88""Yb 88b 88 .dP"Y8
    # 88__dP   dPYb     88     88   88__   88__dP 88Yb88 `Ybo."
    # 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88 o.`Y8b
    # 88     dP""""Yb   88     88   888888 88  Yb 88  Y8 8bodP'

    @tag_register()
    def s_pattern_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_pattern_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Pattern 1/2/3
    
    @tag_register(nbr=3)
    def s_patternX_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        mute_color(p, f"Pattern{idx}", mute=not value,)
        node_link(p, f"RR_VEC s_pattern{idx} Receptor", f"RR_VEC s_pattern{idx} {value}",)
        node_link(p, f"RR_GEO s_pattern{idx} Receptor", f"RR_GEO s_pattern{idx} {value}",)
    
    @tag_register(nbr=3)
    def s_patternX_texture_ptr(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        set_texture_ptr(p, f"s_pattern{idx}.texture", value)
    
    @tag_register(nbr=3)
    def s_patternX_color_sample_method(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=get_enum_idx(p, prop_name, value,), entry="input", i=2)
    
    @tag_register(nbr=3)
    def s_patternX_id_color_ptr(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=color_convert(value), entry="input", i=3)
    
    @tag_register(nbr=3)
    def s_patternX_id_color_tolerence(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="input", i=4)
    
    @tag_register(nbr=3)
    def s_patternX_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="input", i=5)
    
    @tag_register(nbr=3)
    def s_patternX_dist_influence(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value/100, entry="input", i=6)
    
    @tag_register(nbr=3)
    def s_patternX_dist_revert(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="input", i=7)
    
    @tag_register(nbr=3)
    def s_patternX_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="input", i=8)
    
    @tag_register(nbr=3)
    def s_patternX_scale_influence(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value/100, entry="input", i=9)
    
    @tag_register(nbr=3)
    def s_patternX_scale_revert(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="input", i=10)

    codegen_umask_updatefct(scope_ref=locals(), name="s_pattern1",)
    codegen_umask_updatefct(scope_ref=locals(), name="s_pattern2",)
    codegen_umask_updatefct(scope_ref=locals(), name="s_pattern3",)
    
    #    db    88""Yb 88  dP"Yb  888888 88  dP""b8
    #   dPYb   88__dP 88 dP   Yb   88   88 dP   `"
    #  dP__Yb  88""Yb 88 Yb   dP   88   88 Yb
    # dP""""Yb 88oodP 88  YbodP    88   88  YboodP

    @tag_register()
    def s_abiotic_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_abiotic_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Elevation
    
    @tag_register()
    def s_abiotic_elev_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Abiotic Elev", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_elev Receptor", f"RR_VEC s_abiotic_elev {value}",)
        node_link(p, f"RR_GEO s_abiotic_elev Receptor", f"RR_GEO s_abiotic_elev {value}",)
    
    @tag_register()
    def s_abiotic_elev_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
    
    @tag_register()
    def s_abiotic_elev_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=(value=="percentage"), entry="input", i=3)
        #need a refactor, but would break users presets)
        prop_mthd = "local" if (p.s_abiotic_elev_method=="percentage") else "global"
        #update values, both local/global properties min/max range share the same nodal inputs  
        setattr(p, f"s_abiotic_elev_min_value_{prop_mthd}", getattr(p, f"s_abiotic_elev_min_value_{prop_mthd}"),)
        setattr(p, f"s_abiotic_elev_min_falloff_{prop_mthd}", getattr(p, f"s_abiotic_elev_min_falloff_{prop_mthd}"),)
        setattr(p, f"s_abiotic_elev_max_value_{prop_mthd}", getattr(p, f"s_abiotic_elev_max_value_{prop_mthd}"),)
        setattr(p, f"s_abiotic_elev_max_falloff_{prop_mthd}", getattr(p, f"s_abiotic_elev_max_falloff_{prop_mthd}"),)
    
    @tag_register()
    def s_abiotic_elev_min_value_local(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="input", i=5)
    
    @tag_register()
    def s_abiotic_elev_min_falloff_local(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="input", i=6)
    
    @tag_register()
    def s_abiotic_elev_max_value_local(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="input", i=7)
    
    @tag_register()
    def s_abiotic_elev_max_falloff_local(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="input", i=8)
    
    @tag_register()
    def s_abiotic_elev_min_value_global(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="input", i=5)
    
    @tag_register()
    def s_abiotic_elev_min_falloff_global(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="input", i=6)
    
    @tag_register()
    def s_abiotic_elev_max_value_global(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="input", i=7)
    
    @tag_register()
    def s_abiotic_elev_max_falloff_global(p, prop_name, value, event=None, bypass=False,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="input", i=8)

    @tag_register()
    def s_abiotic_elev_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_elev.fallremap", mute=not value)
        mute_node(p, "s_abiotic_elev.fallnoisy", mute=not value)
    
    @tag_register()
    def s_abiotic_elev_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_elev.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_elev.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_elev.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_elev.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_elev_fallnoisy_seed")

    @tag_register()
    def s_abiotic_elev_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=value, entry="input", i=9)
    
    @tag_register()
    def s_abiotic_elev_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=value/100, entry="input", i=10)
    
    @tag_register()
    def s_abiotic_elev_dist_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=value, entry="input", i=11)
    
    @tag_register()
    def s_abiotic_elev_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=value, entry="input", i=12)
    
    @tag_register()
    def s_abiotic_elev_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=value/100, entry="input", i=13)
    
    @tag_register()
    def s_abiotic_elev_scale_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_elev", value=value, entry="input", i=14)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_elev",)

    #Slope
    
    @tag_register()
    def s_abiotic_slope_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Abiotic Slope", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_slope Receptor", f"RR_VEC s_abiotic_slope {value}",)
        node_link(p, f"RR_GEO s_abiotic_slope Receptor", f"RR_GEO s_abiotic_slope {value}",)
    
    @tag_register()
    def s_abiotic_slope_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
    
    @tag_register()
    def s_abiotic_slope_absolute(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=9)
    
    @tag_register()
    def s_abiotic_slope_min_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=5)
    
    @tag_register()
    def s_abiotic_slope_min_falloff(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=6)
    
    @tag_register()
    def s_abiotic_slope_max_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=7)
    
    @tag_register()
    def s_abiotic_slope_max_falloff(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=8)

    @tag_register()
    def s_abiotic_slope_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_slope.fallremap", mute=not value)
        mute_node(p, "s_abiotic_slope.fallnoisy", mute=not value)

    @tag_register()
    def s_abiotic_slope_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_slope.fallremap_revert",mute=not value)

    @tag_register()
    def s_abiotic_slope_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_slope.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_abiotic_slope_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_slope.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_abiotic_slope_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_slope.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_abiotic_slope_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_slope_fallnoisy_seed")
    
    @tag_register()
    def s_abiotic_slope_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=10)
    
    @tag_register()
    def s_abiotic_slope_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value/100, entry="input", i=11)
    
    @tag_register()
    def s_abiotic_slope_dist_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=12)

    @tag_register()
    def s_abiotic_slope_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=13)
    
    @tag_register()
    def s_abiotic_slope_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value/100, entry="input", i=14)
    
    @tag_register()
    def s_abiotic_slope_scale_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_slope", value=value, entry="input", i=15)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_slope",)

    #Direction
    
    @tag_register()
    def s_abiotic_dir_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Abiotic Orientation", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_dir Receptor", f"RR_VEC s_abiotic_dir {value}",)
        node_link(p, f"RR_GEO s_abiotic_dir Receptor", f"RR_GEO s_abiotic_dir {value}",)
    
    @tag_register()
    def s_abiotic_dir_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
    
    @tag_register()
    def s_abiotic_dir_direction(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value, entry="input", i=5)
    
    @tag_register()
    def s_abiotic_dir_max(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value, entry="input", i=6)
    
    @tag_register()
    def s_abiotic_dir_treshold(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value, entry="input", i=7)
        
    @tag_register()
    def s_abiotic_dir_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_dir.fallremap", mute=not value)
        mute_node(p, "s_abiotic_dir.fallnoisy", mute=not value)

    @tag_register()
    def s_abiotic_dir_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_dir.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_dir.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_dir.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_dir.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_dir_fallnoisy_seed")

    @tag_register()
    def s_abiotic_dir_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value, entry="input", i=8)
    
    @tag_register()
    def s_abiotic_dir_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value/100, entry="input", i=9)
    
    @tag_register()
    def s_abiotic_dir_dist_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value, entry="input", i=10)
    
    @tag_register()
    def s_abiotic_dir_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value, entry="input", i=11)
    
    @tag_register()
    def s_abiotic_dir_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value/100, entry="input", i=12)
    
    @tag_register()
    def s_abiotic_dir_scale_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_dir", value=value, entry="input", i=13)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_dir",)

    #Curvature 

    @tag_register()
    def s_abiotic_cur_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Abiotic Curvature", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_cur Receptor", f"RR_VEC s_abiotic_cur {value}",)
        node_link(p, f"RR_GEO s_abiotic_cur Receptor", f"RR_GEO s_abiotic_cur {value}",)
    
    @tag_register()
    def s_abiotic_cur_type(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
    
    @tag_register()
    def s_abiotic_cur_max(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="input", i=5)
    
    @tag_register()
    def s_abiotic_cur_treshold(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="input", i=6)
    
    @tag_register()
    def s_abiotic_cur_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_cur.fallremap", mute=not value)
        mute_node(p, "s_abiotic_cur.fallnoisy", mute=not value)
    
    @tag_register()
    def s_abiotic_cur_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_cur.fallremap_revert",mute=not value)

    @tag_register()
    def s_abiotic_cur_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_cur.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_abiotic_cur_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_cur.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_abiotic_cur_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_cur.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_abiotic_cur_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_cur_fallnoisy_seed")

    @tag_register()
    def s_abiotic_cur_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value, entry="input", i=7)
    
    @tag_register()
    def s_abiotic_cur_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="input", i=8)
    
    @tag_register()
    def s_abiotic_cur_dist_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value, entry="input", i=9)
    
    @tag_register()
    def s_abiotic_cur_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value, entry="input", i=10)
    
    @tag_register()
    def s_abiotic_cur_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="input", i=11)
    
    @tag_register()
    def s_abiotic_cur_scale_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_cur", value=value, entry="input", i=12)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_cur",)

    #Border
    
    @tag_register()
    def s_abiotic_border_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Abiotic Border", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_border Receptor", f"RR_VEC s_abiotic_border {value}",)
        node_link(p, f"RR_GEO s_abiotic_border Receptor", f"RR_GEO s_abiotic_border {value}",)
    
    @tag_register()
    def s_abiotic_border_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=(value=="global"), entry="input", i=4)
    
    @tag_register()
    def s_abiotic_border_max(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value, entry="input", i=5)
    
    @tag_register()
    def s_abiotic_border_treshold(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value, entry="input", i=6)

    @tag_register()
    def s_abiotic_border_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_border.fallremap", mute=not value)
        mute_node(p, "s_abiotic_border.fallnoisy", mute=not value)

    @tag_register()
    def s_abiotic_border_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_abiotic_border.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_border.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_border.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_abiotic_border.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_border_fallnoisy_seed")

    @tag_register()
    def s_abiotic_border_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value, entry="input", i=7)
    
    @tag_register()
    def s_abiotic_border_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value/100, entry="input", i=8)
    
    @tag_register()
    def s_abiotic_border_dist_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value, entry="input", i=9)
    
    @tag_register()
    def s_abiotic_border_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value, entry="input", i=10)
    
    @tag_register()
    def s_abiotic_border_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value/100, entry="input", i=11)
    
    @tag_register()
    def s_abiotic_border_scale_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_abiotic_border", value=value, entry="input", i=12)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_border",)

    # 88""Yb 88""Yb  dP"Yb  Yb  dP 88 8b    d8 88 888888 Yb  dP
    # 88__dP 88__dP dP   Yb  YbdP  88 88b  d88 88   88    YbdP
    # 88"""  88"Yb  Yb   dP  dPYb  88 88YbdP88 88   88     8P
    # 88     88  Yb  YbodP  dP  Yb 88 88 YY 88 88   88    dP

    @tag_register()
    def s_proximity_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_proximity_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Object-Repel 1&2

    @tag_register(nbr=2)
    def s_proximity_repelX_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        mute_color(p, f"Repel{idx}", mute=not value,)
        node_link(p, f"RR_VEC1 s_proximity_repel{idx} Receptor", f"RR_VEC1 s_proximity_repel{idx} {value}",)
        node_link(p, f"RR_VEC2 s_proximity_repel{idx} Receptor", f"RR_VEC2 s_proximity_repel{idx} {value}",)
        node_link(p, f"RR_GEO s_proximity_repel{idx} Receptor", f"RR_GEO s_proximity_repel{idx} {value}",)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_coll_ptr(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}", value=bpy.data.collections.get(value), entry="input", i=3)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_type(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}", value=get_enum_idx(p, prop_name, value,), entry="input", i=4)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_max(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}", value=value, entry="input", i=5)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_treshold(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}", value=value, entry="input", i=6)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_volume_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}", value=value, entry="input", i=7)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_volume_method(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}", value=value=="out", entry="input", i=8)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        mute_node(p, f"s_proximity_repel{idx}.fallremap",mute=not value)
        mute_node(p, f"s_proximity_repel{idx}.fallnoisy",mute=not value)

    @tag_register(nbr=2)
    def s_proximity_repelX_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        mute_node(p, f"s_proximity_repel{idx}.fallremap_revert",mute=not value)

    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        random_seed(p, event, api_is_random=prop_name, api_seed=f"s_proximity_repel{idx}_fallnoisy_seed")
    
    @tag_register(nbr=2)
    def s_proximity_repelX_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="input", i=0)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_dist_influence(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="input", i=1)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_dist_revert(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=not value, entry="input", i=2) #reverse needed here #IS THIS  COMPLETELY FALSE?
        node_value(p, f"s_proximity_repel{idx}", value=value, entry="input", i=9)

    @tag_register(nbr=2)
    def s_proximity_repelX_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="input", i=3)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_scale_influence(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="input", i=4)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_scale_revert(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=not value, entry="input", i=5)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_nor_infl_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="input", i=6)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_nor_influence(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="input", i=7)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_nor_revert(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="input", i=8)

    @tag_register(nbr=2)
    def s_proximity_repelX_tan_infl_allow(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="input", i=9)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_tan_influence(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="input", i=10)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_tan_revert(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="input", i=11)

    codegen_umask_updatefct(scope_ref=locals(), name="s_proximity_repel1",)
    codegen_umask_updatefct(scope_ref=locals(), name="s_proximity_repel2",)

    #Outskirt
    
    @tag_register()
    def s_proximity_outskirt_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Outskirt", mute=not value,)
        node_link(p, f"RR_VEC1 s_proximity_outskirt Receptor", f"RR_VEC1 s_proximity_outskirt {value}",)
        node_link(p, f"RR_VEC2 s_proximity_outskirt Receptor", f"RR_VEC2 s_proximity_outskirt {value}",)
        node_link(p, f"RR_GEO s_proximity_outskirt Receptor", f"RR_GEO s_proximity_outskirt {value}",)
    
    @tag_register()
    def s_proximity_outskirt_detection(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt", value=value, entry="input", i=4)
    
    @tag_register()
    def s_proximity_outskirt_precision(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt", value=value, entry="input", i=5)

    @tag_register()
    def s_proximity_outskirt_max(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt", value=value, entry="input", i=6)

    @tag_register()
    def s_proximity_outskirt_treshold(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt", value=value, entry="input", i=7)

    @tag_register()
    def s_proximity_outskirt_fallremap_allow(p, prop_name, value, event=None, bypass=False,):       
        mute_node(p, f"s_proximity_outskirt.fallremap",mute=not value)
        mute_node(p, f"s_proximity_outskirt.fallnoisy",mute=not value)

    @tag_register()
    def s_proximity_outskirt_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, f"s_proximity_outskirt.fallremap_revert",mute=not value)

    @tag_register()
    def s_proximity_outskirt_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_proximity_outskirt_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_proximity_outskirt_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_proximity_outskirt_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed=f"s_proximity_outskirt_fallnoisy_seed")
    
    @tag_register()
    def s_proximity_outskirt_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.influences", value=value, entry="input", i=0)
    
    @tag_register()
    def s_proximity_outskirt_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.influences", value=value/100, entry="input", i=1)
    
    @tag_register()
    def s_proximity_outskirt_dist_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p,f"s_proximity_outskirt.influences", value=value, entry="input", i=2)

    @tag_register()
    def s_proximity_outskirt_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.influences", value=value, entry="input", i=3)
    
    @tag_register()
    def s_proximity_outskirt_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.influences", value=value/100, entry="input", i=4)
    
    @tag_register()
    def s_proximity_outskirt_scale_revert(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_proximity_outskirt.influences", value=value, entry="input", i=5)
    
    # @tag_register()
    # def s_proximity_outskirt_nor_infl_allow(p, prop_name, value, event=None, bypass=False,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value, entry="input", i=6)
    
    # @tag_register()
    # def s_proximity_outskirt_nor_influence(p, prop_name, value, event=None, bypass=False,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value/100, entry="input", i=7)
    
    # @tag_register()
    # def s_proximity_outskirt_nor_revert(p, prop_name, value, event=None, bypass=False,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=not value, entry="input", i=8)

    # @tag_register()
    # def s_proximity_outskirt_tan_infl_allow(p, prop_name, value, event=None, bypass=False,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value, entry="input", i=9)
    
    # @tag_register()
    # def s_proximity_outskirt_tan_influence(p, prop_name, value, event=None, bypass=False,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value/100, entry="input", i=10)
    
    # @tag_register()
    # def s_proximity_outskirt_tan_revert(p, prop_name, value, event=None, bypass=False,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=not value, entry="input", i=11)

    codegen_umask_updatefct(scope_ref=locals(), name="s_proximity_outskirt",)

    # 888888  dP""b8  dP"Yb  .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88__   dP   `" dP   Yb `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88""   Yb      Yb   dP o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 888888  YboodP  YbodP  8bodP'  dP    8bodP'   88   888888 88 YY 88

    @tag_register()
    def s_ecosystem_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_ecosystem_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Affinity

    @tag_register()
    def s_ecosystem_affinity_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Eco Affinity", mute=not value,)
        node_link(p, f"RR_VEC s_ecosystem_affinity Receptor", f"RR_VEC s_ecosystem_affinity {value}",)
        node_link(p, f"RR_GEO s_ecosystem_affinity Receptor", f"RR_GEO s_ecosystem_affinity {value}",)
    
    @tag_register()
    def s_ecosystem_affinity_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.use_global", value=(value=="global"), entry="boolean")
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_ptr(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        obj = bpy.data.objects.get(f"scatter_obj : {value}")
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=obj, entry="input", i=2)
        mute_node(p, f"s_ecosystem_affinity.slot{idx}", mute=(obj is None),)
        #adjust slot interface
        if (value==""):
            if (idx==3):
                if (p.s_ecosystem_affinity_02_ptr==""):
                      p.s_ecosystem_affinity_ui_max_slot = 1
                else: p.s_ecosystem_affinity_ui_max_slot = 2
            elif (idx==2):
                if (p.s_ecosystem_affinity_03_ptr==""):
                    p.s_ecosystem_affinity_ui_max_slot = 1

    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_type(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=get_enum_idx(p, prop_name, value,), entry="input", i=3)
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_max_value(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=value, entry="input", i=4)
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_max_falloff(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=value, entry="input", i=5)
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_limit_distance(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=value, entry="input", i=6)
    
    @tag_register()
    def s_ecosystem_affinity_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_ecosystem_affinity.fallremap",mute=not value)
        mute_node(p, "s_ecosystem_affinity.fallnoisy",mute=not value)

    @tag_register()
    def s_ecosystem_affinity_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_ecosystem_affinity.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_ecosystem_affinity_fallnoisy_seed")
    
    @tag_register()
    def s_ecosystem_affinity_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.influences", value=value, entry="input", i=0)
    
    @tag_register()
    def s_ecosystem_affinity_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.influences", value=value/100, entry="input", i=1)

    @tag_register()
    def s_ecosystem_affinity_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.influences", value=value, entry="input", i=3)
    
    @tag_register()
    def s_ecosystem_affinity_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_affinity.influences", value=value/100, entry="input", i=4)

    codegen_umask_updatefct(scope_ref=locals(), name="s_ecosystem_affinity",)

    #Repulsion

    @tag_register()
    def s_ecosystem_repulsion_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Eco Repulsion", mute=not value,)
        node_link(p, f"RR_VEC s_ecosystem_repulsion Receptor", f"RR_VEC s_ecosystem_repulsion {value}",)
        node_link(p, f"RR_GEO s_ecosystem_repulsion Receptor", f"RR_GEO s_ecosystem_repulsion {value}",)
    
    @tag_register()
    def s_ecosystem_repulsion_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.use_global", value=(value=="global"), entry="boolean")
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_ptr(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        obj = bpy.data.objects.get(f"scatter_obj : {value}")
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=obj, entry="input", i=2)
        mute_node(p, f"s_ecosystem_repulsion.slot{idx}", mute=(obj is None),)
        #adjust slot interface
        if (value==""):
            if (idx==3):
                if (p.s_ecosystem_repulsion_02_ptr==""):
                      p.s_ecosystem_repulsion_ui_max_slot = 1
                else: p.s_ecosystem_repulsion_ui_max_slot = 2
            elif (idx==2):
                if (p.s_ecosystem_repulsion_03_ptr==""):
                    p.s_ecosystem_repulsion_ui_max_slot = 1
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_type(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=get_enum_idx(p, prop_name, value,), entry="input", i=3)
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_max_value(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=value, entry="input", i=4)
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_max_falloff(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[23])
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=value, entry="input", i=5)
    
    @tag_register()
    def s_ecosystem_repulsion_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_ecosystem_repulsion.fallremap",mute=not value)
        mute_node(p, "s_ecosystem_repulsion.fallnoisy",mute=not value)

    @tag_register()
    def s_ecosystem_repulsion_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_ecosystem_repulsion.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_strength(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.fallnoisy", value=value, entry="input", i=1)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.fallnoisy", value=value, entry="input", i=2)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.fallnoisy", value=value, entry="input", i=3)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_ecosystem_repulsion_fallnoisy_seed")

    @tag_register()
    def s_ecosystem_repulsion_dist_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value, entry="input", i=0)
    
    @tag_register()
    def s_ecosystem_repulsion_dist_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value/100, entry="input", i=1)
    
    @tag_register()
    def s_ecosystem_repulsion_scale_infl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value, entry="input", i=3)
    
    @tag_register()
    def s_ecosystem_repulsion_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value/100, entry="input", i=4)

    codegen_umask_updatefct(scope_ref=locals(), name="s_ecosystem_repulsion",)

    # 88""Yb 88   88 .dP"Y8 88  88
    # 88__dP 88   88 `Ybo." 88  88
    # 88"""  Y8   8P o.`Y8b 888888
    # 88     `YbodP' 8bodP' 88  88

    @tag_register()
    def s_push_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_push_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Push Offset

    @tag_register()
    def s_push_offset_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Push Offset", mute=not value,)
        node_link(p, f"RR_GEO s_push_offset Receptor", f"RR_GEO s_push_offset {value}",)

    @tag_register()
    def s_push_offset_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_offset", value=(value=="global"), entry="input", i=1)

    @tag_register()
    def s_push_offset_add_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_offset", value=value, entry="input", i=2)

    @tag_register()
    def s_push_offset_add_random(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_offset", value=value, entry="input", i=3)

    @tag_register()
    def s_push_offset_rotate_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_offset", value=value, entry="input", i=4)

    @tag_register()
    def s_push_offset_rotate_random(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_offset", value=value, entry="input", i=5)

    @tag_register()
    def s_push_offset_scale_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_offset", value=value, entry="input", i=6)

    @tag_register()
    def s_push_offset_scale_random(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_offset", value=value, entry="input", i=7)

    codegen_umask_updatefct(scope_ref=locals(), name="s_push_offset",)

    #Push Direction 

    @tag_register()
    def s_push_dir_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Push Direction", mute=not value,)
        node_link(p, f"RR_GEO s_push_dir Receptor", f"RR_GEO s_push_dir {value}",)

    @tag_register()
    def s_push_dir_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_dir", value=get_enum_idx(p, prop_name, value,), entry="input", i=3)

    @tag_register()
    def s_push_dir_add_value(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_dir", value=value, entry="input", i=4)

    @tag_register()
    def s_push_dir_add_random(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_dir", value=value, entry="input", i=5)

    codegen_umask_updatefct(scope_ref=locals(), name="s_push_dir",)

    #Push Noise 

    @tag_register()
    def s_push_noise_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Push Noise", mute=not value,)
        node_link(p, f"RR_GEO s_push_noise Receptor", f"RR_GEO s_push_noise {value}",)

    @tag_register()
    def s_push_noise_vector(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_noise", value=value, entry="input", i=1)

    @tag_register()
    def s_push_noise_speed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_noise", value=value, entry="input", i=2)

    codegen_umask_updatefct(scope_ref=locals(), name="s_push_noise",)

    #Fall

    @tag_register()
    def s_push_fall_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Push Fall", mute=not value,)
        node_link(p, f"RR_VEC s_push_fall Receptor", f"RR_VEC s_push_fall {value}",)
        node_link(p, f"RR_GEO s_push_fall Receptor", f"RR_GEO s_push_fall {value}",)

    @tag_register()
    def s_push_fall_height(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=2)

    @tag_register()
    def s_push_fall_key1_pos(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=3)

    @tag_register()
    def s_push_fall_key2_pos(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=4)

    @tag_register()
    def s_push_fall_key1_height(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=5)

    @tag_register()
    def s_push_fall_key2_height(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=6)

    @tag_register()
    def s_push_fall_stop_when_initial_z(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=7)

    @tag_register()
    def s_push_fall_turbulence_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=8)

    @tag_register()
    def s_push_fall_turbulence_spread(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=9)

    @tag_register()
    def s_push_fall_turbulence_speed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=10)

    @tag_register()
    def s_push_fall_turbulence_rot_vector(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=11)

    @tag_register()
    def s_push_fall_turbulence_rot_factor(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_push_fall", value=value, entry="input", i=12)

    codegen_umask_updatefct(scope_ref=locals(), name="s_push_fall",)

    ################ Wind 

    @tag_register()
    def s_wind_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_wind_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    # Yb        dP 88 88b 88 8888b.  
    #  Yb  db  dP  88 88Yb88  8I  Yb 
    #   YbdPYbdP   88 88 Y88  8I  dY 
    #    YP  YP    88 88  Y8 8888Y" 

    @tag_register()
    def s_wind_wave_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Wind Wave", mute=not value,)
        node_link(p, f"RR_VEC s_wind_wave Receptor", f"RR_VEC s_wind_wave {value}",)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_wave_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=(value=="global"), entry="input", i=2)

    @tag_register()
    def s_wind_wave_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value=="wind_wave_loopable", entry="input", i=3)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_wave_loopable_cliplength_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=not value, entry="input", i=4)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_wave_loopable_frame_start(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=5)

    @tag_register()
    def s_wind_wave_loopable_frame_end(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=6)

    @tag_register()
    def s_wind_wave_speed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=7)

    @tag_register()
    def s_wind_wave_direction(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=8)

    @tag_register()
    def s_wind_wave_force(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=9)

    @tag_register()
    def s_wind_wave_swinging(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=10)

    @tag_register()
    def s_wind_wave_scale_influence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=11)

    @tag_register()
    def s_wind_wave_texture_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=12)

    @tag_register()
    def s_wind_wave_texture_turbulence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=13)

    @tag_register()
    def s_wind_wave_texture_distorsion(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=14)

    @tag_register()
    def s_wind_wave_texture_brightness(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=15)

    @tag_register()
    def s_wind_wave_texture_contrast(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=16)

    @tag_register()
    def s_wind_wave_dir_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=get_enum_idx(p, prop_name, value), entry="input", i=17)

    @tag_register()
    def s_wind_wave_flowmap_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_wave", value=value, entry="input", i=18)

    codegen_umask_updatefct(scope_ref=locals(), name="s_wind_wave",)

    #Wind Noise

    @tag_register()
    def s_wind_noise_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Wind Noise", mute=not value,)
        node_link(p, f"RR_VEC s_wind_noise Receptor", f"RR_VEC s_wind_noise {value}",)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_noise_space(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_noise", value=(value=="global"), entry="input", i=1)

    @tag_register()
    def s_wind_noise_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_noise", value=value=="wind_noise_loopable", entry="input", i=2)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_noise_loopable_cliplength_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_noise", value=not value, entry="input", i=3)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_noise_loopable_frame_start(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_noise", value=value, entry="input", i=4)

    @tag_register()
    def s_wind_noise_loopable_frame_end(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_noise", value=value, entry="input", i=5)

    @tag_register()
    def s_wind_noise_force(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_noise", value=value, entry="input", i=6)

    @tag_register()
    def s_wind_noise_speed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, f"s_wind_noise", value=value, entry="input", i=7)

    codegen_umask_updatefct(scope_ref=locals(), name="s_wind_noise",)


    # Yb    dP 88 .dP"Y8 88 88""Yb 88 88     88 888888 Yb  dP
    #  Yb  dP  88 `Ybo." 88 88__dP 88 88     88   88    YbdP
    #   YbdP   88 o.`Y8b 88 88""Yb 88 88  .o 88   88     8P
    #    YP    88 8bodP' 88 88oodP 88 88ood8 88   88    dP
    
    @tag_register()
    def s_visibility_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_visibility_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Face Preview

    @tag_register()
    def s_visibility_facepreview_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, "Face Preview", mute=not value,)
        node_link(p, f"RR_FLOAT s_visibility_facepreview Receptor", f"RR_FLOAT s_visibility_facepreview {value}",)

    @tag_register()
    def s_visibility_facepreview_viewport_method(p, prop_name, value, event=None, bypass=False,):
        ensure_viewport_method_interface(p, "s_visibility_facepreview", value,)
        node_value(p, "s_visibility_facepreview", value=get_enum_idx(p, prop_name, value), entry="input", i=4)

    #Viewport %

    @tag_register()
    def s_visibility_view_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p,"% Optimization", mute=not value,) 
        node_link(p, f"RR_FLOAT s_visibility_view Receptor", f"RR_FLOAT s_visibility_view {value}",)

    @tag_register()
    def s_visibility_view_percentage(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_view", value=value/100, entry="input", i=1)

    @tag_register()
    def s_visibility_view_viewport_method(p, prop_name, value, event=None, bypass=False,):
        ensure_viewport_method_interface(p, "s_visibility_view", value,)
        node_value(p, "s_visibility_view", value=get_enum_idx(p, prop_name, value), entry="input", i=2)

    #Camera Optimization 

    @tag_register()
    def s_visibility_cam_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p,"Camera Optimization", mute=not value,) 
        node_link(p, f"RR_GEO s_visibility_cam Receptor", f"RR_GEO s_visibility_cam {value}",)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)

    @tag_register()
    def s_visibility_camclip_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=5)

    @tag_register()
    def s_visibility_camclip_cam_autofill(p, prop_name, value, event=None, bypass=False,):
        if (value==True):
            update_active_camera_nodegroup(force_update=True)
        else:
            p.s_visibility_camclip_cam_res_xy = p.s_visibility_camclip_cam_res_xy
            p.s_visibility_camclip_cam_shift_xy = p.s_visibility_camclip_cam_shift_xy
            p.s_visibility_camclip_cam_lens = p.s_visibility_camclip_cam_lens
            p.s_visibility_camclip_cam_sensor_width = p.s_visibility_camclip_cam_sensor_width
            p.s_visibility_camclip_cam_boost_xy = p.s_visibility_camclip_cam_boost_xy

    @tag_register()
    def s_visibility_camclip_cam_lens(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=7)

    @tag_register()
    def s_visibility_camclip_cam_sensor_width(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=6)

    @tag_register()
    def s_visibility_camclip_cam_res_xy(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=Vector((value[0],value[1],0)), entry="input", i=8)

    @tag_register()
    def s_visibility_camclip_cam_shift_xy(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=Vector((value[0],value[1],0)), entry="input", i=9)

    @tag_register()
    def s_visibility_camclip_cam_boost_xy(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=Vector((value[0],value[1],0)), entry="input", i=10)

    @tag_register()
    def s_visibility_camclip_proximity_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=11)

    @tag_register()
    def s_visibility_camclip_proximity_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=12)

    @tag_register()
    def s_visibility_camdist_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=13)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)

    @tag_register()
    def s_visibility_camdist_min(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=14)

    @tag_register()
    def s_visibility_camdist_max(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=15)

    @tag_register()
    def s_visibility_camdist_fallremap_allow(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_visibility_cam.fallremap",mute=not value)

    @tag_register()
    def s_visibility_camdist_fallremap_revert(p, prop_name, value, event=None, bypass=False,):
        mute_node(p, "s_visibility_cam.fallremap_revert",mute=not value)

    @tag_register()
    def s_visibility_camdist_per_cam_data(p, prop_name, value, event=None, bypass=False,):
        if (value==True):
            active_cam = bpy.context.scene.camera
            if (active_cam is not None):
                active_cam.scatter5.s_visibility_camdist_per_cam_min = active_cam.scatter5.s_visibility_camdist_per_cam_min 
                active_cam.scatter5.s_visibility_camdist_per_cam_max = active_cam.scatter5.s_visibility_camdist_per_cam_max 
        else: 
            node_value(p, "s_visibility_cam", value=p.s_visibility_camdist_min, entry="input", i=14)
            node_value(p, "s_visibility_cam", value=p.s_visibility_camdist_max, entry="input", i=15)

    @tag_register()
    def s_visibility_camoccl_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=16)

    @tag_register()
    def s_visibility_camoccl_threshold(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=value, entry="input", i=17)

    @tag_register()
    def s_visibility_camoccl_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=get_enum_idx(p, prop_name, value), entry="input", i=18)

    @tag_register()
    def s_visibility_camoccl_coll_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_cam", value=bpy.data.collections.get(value), entry="input", i=19)

    @tag_register()
    def s_visibility_cam_viewport_method(p, prop_name, value, event=None, bypass=False,):
        ensure_viewport_method_interface(p, "s_visibility_cam", value,)
        node_value(p, "s_visibility_cam", value=get_enum_idx(p, prop_name, value), entry="input", i=20)

    #Maximum Load

    @tag_register()
    def s_visibility_maxload_allow(p, prop_name, value, event=None, bypass=False,):
        mute_color(p, f"Max Load", mute=not value,)
        node_link(p, f"RR_GEO s_visibility_maxload Receptor", f"RR_GEO s_visibility_maxload {value}",)

    @tag_register()
    def s_visibility_maxload_cull_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_maxload", value=value=="maxload_limit", entry="input", i=1)

    @tag_register()
    def s_visibility_maxload_treshold(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_visibility_maxload", value=value, entry="input", i=2)

    @tag_register()
    def s_visibility_maxload_viewport_method(p, prop_name, value, event=None, bypass=False,):
        ensure_viewport_method_interface(p, "s_visibility_maxload", value,)
        node_value(p, "s_visibility_maxload", value=get_enum_idx(p, prop_name, value), entry="input", i=3)

    # 88 88b 88 .dP"Y8 888888    db    88b 88  dP""b8 88 88b 88  dP""b8
    # 88 88Yb88 `Ybo."   88     dPYb   88Yb88 dP   `" 88 88Yb88 dP   `"
    # 88 88 Y88 o.`Y8b   88    dP__Yb  88 Y88 Yb      88 88 Y88 Yb  "88
    # 88 88  Y8 8bodP'   88   dP""""Yb 88  Y8  YboodP 88 88  Y8  YboodP

    @tag_register()
    def s_instances_method(p, prop_name, value, event=None, bypass=False,):
        ins_points = p.s_instances_method=="ins_points"
        mute_color(p, "Raw Points", mute=not ins_points,)
        node_link(p, f"RR_GEO output_points Receptor", f"RR_GEO output_points {ins_points}",)
        
    @tag_register()
    def s_instances_coll_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="input")

    @tag_register()
    def s_instances_pick_method(p, prop_name, value, event=None, bypass=False,):
        node_link(p, prop_name, value)
        node_link(p, prop_name+" PICK", value+" PICK")
        mute_node(p, "s_instances_pick_scale", mute=(value!="pick_scale"))

    @tag_register()
    def s_instances_seed(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="integer")

    @tag_register()
    def s_instances_is_random_seed(p, prop_name, value, event=None, bypass=False,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_instances_seed")

    @tag_register(nbr=20)
    def s_instances_id_XX_rate(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        node_value(p, "s_instances_pick_rate", value=value/100, entry="input", i=idx)

    @tag_register()
    def s_instances_id_scale_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=get_enum_idx(p, prop_name, value), entry="integer")

    @tag_register(nbr=10)
    def s_instances_id_XX_scale_min(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        idx *=2 
        idx -=1
        node_value(p, "s_instances_pick_scale", value=value, entry="input", i=idx)

    @tag_register(nbr=10)
    def s_instances_id_XX_scale_max(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        idx *=2 
        node_value(p, "s_instances_pick_scale", value=value, entry="input", i=idx)

    @tag_register()
    def s_instances_pick_cluster_projection_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_instances_pick_cluster", value=get_enum_idx(p, prop_name, value), entry="input", i=0)

    @tag_register()
    def s_instances_pick_cluster_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_instances_pick_cluster", value=value, entry="input", i=1)

    @tag_register()
    def s_instances_pick_cluster_blur(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_instances_pick_cluster", value=value, entry="input", i=2)

    @tag_register()
    def s_instances_pick_clump(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="boolean")

    @tag_register(nbr=20)
    def s_instances_id_XX_color(p, prop_name, value, event=None, bypass=False,):
        idx = int(prop_name[15:17])
        node_value(p, "s_instances_pick_color", value=color_convert(value), entry="input", i=idx)

    @tag_register()
    def s_instances_id_color_tolerence(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value,) 

    @tag_register()
    def s_instances_id_color_sample_method(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_instances_is_vcol", value=value=="vcol", entry="boolean")

    @tag_register()
    def s_instances_texture_ptr(p, prop_name, value, event=None, bypass=False,):
        set_texture_ptr(p, f"s_instances_pick_color_textures.texture", value)

    @tag_register()
    def s_instances_vcol_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="attr",)

    # 8888b.  88 .dP"Y8 88""Yb 88        db    Yb  dP
    #  8I  Yb 88 `Ybo." 88__dP 88       dPYb    YbdP
    #  8I  dY 88 o.`Y8b 88"""  88  .o  dP__Yb    8P
    # 8888Y"  88 8bodP' 88     88ood8 dP""""Yb  dP

    @tag_register()
    def s_display_master_allow(p, prop_name, value, event=None, bypass=False,):
        for prop in p.get_s_display_main_features(availability_conditions=False,):
            continue #TODO, this will bug, need nodegroups...
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Display As

    @tag_register()
    def s_display_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="boolean")
        mute_color(p, "Display", mute=not value)
        mute_color(p, "Display Features", mute=not value)
        if (value==True):
            update_is_rendered_view_nodegroup()

    @tag_register()
    def s_display_method(p, prop_name, value, event=None, bypass=False,):
        node_link(p, prop_name, value,)

    @tag_register()
    def s_display_placeholder_type(p, prop_name, value, event=None, bypass=False,):
        placeholder = bpy.data.objects.get(value)
        if (placeholder is None): 
            #attempt to find dupplicates?
            for i in range(9):
                placeholder = bpy.data.objects.get(f"{value}.00{i}")
                if (placeholder is not None):
                    break
        if (placeholder is not None): 
              node_value(p, prop_name, value=placeholder, entry="input")
        else: print("Couldn't find placeholder object data, was it removed from this .blend ?")

    @tag_register()
    def s_display_custom_placeholder_ptr(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="input")

    @tag_register()
    def s_display_placeholder_scale(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="vector")

    @tag_register()
    def s_display_point_radius(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value,)

    @tag_register()
    def s_display_cloud_radius(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value,)

    @tag_register()
    def s_display_cloud_density(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value,)

    @tag_register()
    def s_display_camdist_allow(p, prop_name, value, event=None, bypass=False,):
        node_value(p, prop_name, value=value, entry="boolean")
        mute_color(p, "Closeby Optimization1", mute=not value)
        mute_color(p, "Closeby Optimization2", mute=not value)
        mute_node(p, "s_display_camdist", mute=not value)
        if (value==True):
            update_active_camera_nodegroup(force_update=True)

    @tag_register()
    def s_display_camdist_distance(p, prop_name, value, event=None, bypass=False,):
        node_value(p, "s_display_camdist", value=value, entry="input", i=1)

    @tag_register()
    def s_display_viewport_method(p, prop_name, value, event=None, bypass=False,):
        ensure_viewport_method_interface(p, "s_display", value,)
        node_value(p, "s_display_viewport_method", value=get_enum_idx(p, prop_name, value), entry="input", i=0)

    # 88""Yb 888888  dP""b8 88 88b 88 88b 88 888888 88""Yb  
    # 88__dP 88__   dP   `" 88 88Yb88 88Yb88 88__   88__dP  
    # 88""Yb 88""   Yb  "88 88 88 Y88 88 Y88 88""   88"Yb   
    # 88oodP 888888  YboodP 88 88  Y8 88  Y8 888888 88  Yb  

    @tag_register()
    def s_beginner_default_scale(p, prop_name, value, event=None, bypass=False,):
        if (not p.s_scale_default_allow):
            p.s_scale_default_allow = True
        p.s_scale_default_multiplier = value

    @tag_register()
    def s_beginner_random_scale(p, prop_name, value, event=None, bypass=False,):
        if (not p.s_scale_random_allow):
            p.s_scale_random_allow = True
        p.s_scale_random_factor = [1-value]*3

    @tag_register()
    def s_beginner_random_rot(p, prop_name, value, event=None, bypass=False,):
        if (not p.s_rot_random_allow):
            p.s_rot_random_allow = True
        p.s_rot_random_tilt_value = value * 2.50437
        p.s_rot_random_yaw_value = value * 6.28319
        
    #  dP""b8 88""Yb  dP"Yb  88   88 88""Yb     888888 888888    db    888888 88   88 88""Yb 888888 .dP"Y8 
    # dP   `" 88__dP dP   Yb 88   88 88__dP     88__   88__     dPYb     88   88   88 88__dP 88__   `Ybo." 
    # Yb  "88 88"Yb  Yb   dP Y8   8P 88"""      88""   88""    dP__Yb    88   Y8   8P 88"Yb  88""   o.`Y8b 
    #  YboodP 88  Yb  YbodP  `YbodP' 88         88     888888 dP""""Yb   88   `YbodP' 88  Yb 888888 8bodP' 

    #TODO OPTIMIZATION! 
    # will need to optimize functions to make sure execution is not useless!!
    # Need to check if nodegraph != already equal what we want! 

    @tag_register()
    def s_disable_all_group_features(p, prop_name, value, event=None, bypass=False,):
        """undo all group features (if a psy is not assigned to any groups anymore)"""
        #... keep this function up to date with main group features..
        #if ungroup a group:
        # - mute all mask feature 
        mute_node(p, "s_gr_mask_vg", mute=True,)
        mute_node(p, "s_gr_mask_vcol", mute=True,)
        mute_node(p, "s_gr_mask_bitmap", mute=True,)
        mute_node(p, "s_gr_mask_material", mute=True,)
        mute_node(p, "s_gr_mask_curve", mute=True,)
        mute_node(p, "s_gr_mask_boolvol", mute=True,)
        mute_node(p, "s_gr_mask_upward", mute=True,)
        # - mute all scale features 
        mute_node(p, "s_gr_scale_boost", mute=True,)
        # - mute all pattern feature, and reset texture pointer to avoid virtual users
        mute_node(p, "s_gr_pattern1", mute=True,)
        set_texture_ptr(p, "s_gr_pattern1.texture", "")
        
    ### Distribution
    
    # @tag_register()
    # def s_gr_distribution_master_allow(g, prop_name, value, event=None, bypass=False,):
    #     pass
        
    # @tag_register()
    # def s_gr_distribution_density_boost_allow(g, prop_name, value, event=None, bypass=False,):
    #     pass

    # @tag_register()
    # def s_gr_distribution_density_boost_factor(g, prop_name, value, event=None, bypass=False,):
    #     pass
    
    ### Masks

    @tag_register()
    def s_gr_mask_master_allow(g, prop_name, value, event=None, bypass=False,):
        for prop in g.get_s_gr_mask_main_features(availability_conditions=False,):
            for p in g.get_psy_members():
                mute_node(p, prop.replace("_allow",""), mute=not value,)
    #Vgroup
    
    @tag_register()
    def s_gr_mask_vg_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Vg Gr Mask", mute=not value,)
            node_link(p, f"RR_FLOAT s_gr_mask_vg Receptor", f"RR_FLOAT s_gr_mask_vg {value}",)
    
    @tag_register()
    def s_gr_mask_vg_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vg", value=value, entry="input", i=2)
    
    @tag_register()
    def s_gr_mask_vg_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vg", value=value, entry="input", i=3)

    #VColor
    
    @tag_register()
    def s_gr_mask_vcol_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Vcol Gr Mask", mute=not value,)
            node_link(p, f"RR_FLOAT s_gr_mask_vcol Receptor", f"RR_FLOAT s_gr_mask_vcol {value}",)
    
    @tag_register()
    def s_gr_mask_vcol_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=value, entry="input", i=2)
    
    @tag_register()
    def s_gr_mask_vcol_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=value, entry="input", i=3)
    
    @tag_register()
    def s_gr_mask_vcol_color_sample_method(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=get_enum_idx(g, prop_name, value,), entry="input", i=4)
    
    @tag_register()
    def s_gr_mask_vcol_id_color_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=color_convert(value), entry="input", i=5)
    
    #Bitmap 
    
    @tag_register()
    def s_gr_mask_bitmap_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Img Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_bitmap Receptor", f"RR_GEO s_gr_mask_bitmap {value}",)
        g.s_gr_mask_bitmap_uv_ptr = g.s_gr_mask_bitmap_uv_ptr
    
    @tag_register()
    def s_gr_mask_bitmap_uv_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=value, entry="input", i=2)
    
    @tag_register()
    def s_gr_mask_bitmap_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=bpy.data.images.get(value), entry="input", i=3)
    
    @tag_register()
    def s_gr_mask_bitmap_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=not value, entry="input", i=4)
    
    @tag_register()
    def s_gr_mask_bitmap_color_sample_method(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=get_enum_idx(g, prop_name, value,), entry="input", i=5)
    
    @tag_register()
    def s_gr_mask_bitmap_id_color_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=color_convert(value), entry="input", i=6)
        
    #Materials
    
    @tag_register()
    def s_gr_mask_material_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Mat Gr Mask", mute=not value,)
            node_link(p, f"RR_FLOAT s_gr_mask_material Receptor", f"RR_FLOAT s_gr_mask_material {value}",)
    
    @tag_register()
    def s_gr_mask_material_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_material", value=bpy.data.materials.get(value), entry="input", i=2)
    
    @tag_register()
    def s_gr_mask_material_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_material", value=value, entry="input", i=3)
        
    #Curves

    @tag_register()
    def s_gr_mask_curve_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Cur Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_curve Receptor", f"RR_GEO s_gr_mask_curve {value}",)    
    
    @tag_register()
    def s_gr_mask_curve_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_curve", value=value, entry="input", i=1)
    
    @tag_register()
    def s_gr_mask_curve_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_curve", value=value, entry="input", i=2)

    #Boolean
    
    @tag_register()
    def s_gr_mask_boolvol_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Bool Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_boolvol Receptor", f"RR_GEO s_gr_mask_boolvol {value}",)
    
    @tag_register()
    def s_gr_mask_boolvol_coll_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_boolvol", value=bpy.data.collections.get(value), entry="input", i=1)
    
    @tag_register()
    def s_gr_mask_boolvol_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_boolvol", value=value, entry="input", i=2)

    #Upward Obstruction

    @tag_register()
    def s_gr_mask_upward_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Up Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_upward Receptor", f"RR_GEO s_gr_mask_upward {value}",)
    
    @tag_register()
    def s_gr_mask_upward_coll_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_upward", value=bpy.data.collections.get(value), entry="input", i=1)
    
    @tag_register()
    def s_gr_mask_upward_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_upward", value=value, entry="input", i=2)
        
    ### Scale
    
    @tag_register()
    def s_gr_scale_master_allow(g, prop_name, value, event=None, bypass=False,):
        for prop in g.get_s_gr_scale_main_features(availability_conditions=False,):
            for p in g.get_psy_members():
                mute_node(p, prop.replace("_allow",""), mute=not value,)
                
    @tag_register()
    def s_gr_scale_boost_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, "Group Scale", mute=not value,)
            node_link(p, f"RR_VEC s_gr_scale_boost Receptor", f"RR_VEC s_gr_scale_boost {value}",)
    
    @tag_register()
    def s_gr_scale_boost_value(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_scale_boost", value=value, entry="input", i=1)
            
    @tag_register()
    def s_gr_scale_boost_multiplier(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_scale_boost", value=value, entry="input", i=2)
    
    ### Pattern
    
    @tag_register()
    def s_gr_pattern_master_allow(g, prop_name, value, event=None, bypass=False,):        
        for prop in g.get_s_gr_pattern_main_features(availability_conditions=False,):
            for p in g.get_psy_members():
                mute_node(p, prop.replace("_allow",""), mute=not value,)
                
    #Pattern
    
    @tag_register()
    def s_gr_pattern1_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            mute_color(p, f"Pattern1 Gr", mute=not value,)
            node_link(p, f"RR_VEC s_gr_pattern1 Receptor", f"RR_VEC s_gr_pattern1 {value}",)
            node_link(p, f"RR_GEO s_gr_pattern1 Receptor", f"RR_GEO s_gr_pattern1 {value}",)
    
    @tag_register()
    def s_gr_pattern1_texture_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            set_texture_ptr(p, "s_gr_pattern1.texture", value)
    
    @tag_register()
    def s_gr_pattern1_color_sample_method(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=get_enum_idx(g, prop_name, value,), entry="input", i=2)
    
    @tag_register()
    def s_gr_pattern1_id_color_ptr(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=color_convert(value), entry="input", i=3)
    
    @tag_register()
    def s_gr_pattern1_id_color_tolerence(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="input", i=4)
    
    @tag_register()
    def s_gr_pattern1_dist_infl_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="input", i=5)
    
    @tag_register()
    def s_gr_pattern1_dist_influence(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value/100, entry="input", i=6)
    
    @tag_register()
    def s_gr_pattern1_dist_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="input", i=7)
    
    @tag_register()
    def s_gr_pattern1_scale_infl_allow(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="input", i=8)
    
    @tag_register()
    def s_gr_pattern1_scale_influence(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value/100, entry="input", i=9)
    
    @tag_register()
    def s_gr_pattern1_scale_revert(g, prop_name, value, event=None, bypass=False,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="input", i=10)

    # codegen_umask_updatefct(scope_ref=locals(), name="s_pattern1",)
    
    # 88 88b 88 888888 888888 88""Yb 88b 88    db    88
    # 88 88Yb88   88   88__   88__dP 88Yb88   dPYb   88
    # 88 88 Y88   88   88""   88"Yb  88 Y88  dP__Yb  88  .o
    # 88 88  Y8   88   888888 88  Yb 88  Y8 dP""""Yb 88ood8

    #Internal use only, ex: psy.property_run_update() or class.fct() or class.run_update()
    #NOTE: Hum this has nothing to do here? rigth? Should be in particle_systems property class directly

    @tag_register()
    def s_eval_depsgraph(p, prop_name, value, event=None, bypass=False,):
        #set nodetree for eval depsgraph event
        mute_color(p, f"Depsgraph", mute=value!=False,)
        node_link(p, f"s_eval_depsgraph_method", f"s_eval_depsgraph_{str(value).lower()}_eval",)

    @tag_register()
    def s_simulate_final_render(p, prop_name, value, event=None, bypass=False,):
        #mute a node in viewport method evaluation ng to simulate the final render
        for ng in bpy.data.node_groups:
            if (ng.name.startswith(".S Viewport Method MK")):
                ng.nodes["Boolean Math.008"].mute = value

    #  dP""b8 888888 88b 88 888888 88""Yb    db    888888 888888
    # dP   `" 88__   88Yb88 88__   88__dP   dPYb     88   88__
    # Yb  "88 88""   88 Y88 88""   88"Yb   dP__Yb    88   88""
    #  YboodP 888888 88  Y8 888888 88  Yb dP""""Yb   88   888888

    #Generate Dict at parsetime

    #list all update functions of this class, by looking at tag
    UpdateFcts = { k:v for k,v in locals().items() if (callable(v) and hasattr(v,"register_tag")) }

    #generated update dictionary
    UpdateProperties = {}
    for k,v in UpdateFcts.items():
        
        #no need to generate fcts?
        if (not hasattr(v,"generator_nbr")):
            if (k not in UpdateProperties):
                UpdateProperties[k]=v
            continue            
    
        #generate a fct from given name convention?
        if (("XX" in k) and (0<v.generator_nbr<100)):
            for i in range(v.generator_nbr):
                _k = k.replace("XX",f"{i+1:02}")
                if (_k not in UpdateProperties):
                    UpdateProperties[_k]=v
            continue
        elif (("X" in k) and (0<v.generator_nbr<10)):
            for i in range(v.generator_nbr):
                _k = k.replace("X",f"{i+1}")
                if (_k not in UpdateProperties):
                    UpdateProperties[_k]=v
            continue

        #else raise error
        raise Exception(f"For generator, please use X or XX convention, make sure {v.generator_nbr} number can fit")

    #wdebug print (at regtime)
    if False:
        print(UpdateProperties)

    #    db     dP""b8  dP""b8 888888 .dP"Y8 .dP"Y8
    #   dPYb   dP   `" dP   `" 88__   `Ybo." `Ybo."
    #  dP__Yb  Yb      Yb      88""   o.`Y8b o.`Y8b
    # dP""""Yb  YboodP  YboodP 888888 8bodP' 8bodP'

    #access to UpdateProperties from outer modules:

    @classmethod
    def run_update(cls, self, prop_name, value, event=None, bypass=False,):
        """run update function equivalence from given propname, return True if propname found else False"""

        fct = cls.UpdateProperties.get(prop_name)

        if (fct is None):
            return False

        fct(self, prop_name, value, event=event, bypass=bypass,)

        return True


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = ()
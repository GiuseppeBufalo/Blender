

import bpy

from mathutils import Vector

from .. resources.translate import translate
from .. resources.icons import cust_icon

from .. utils.str_utils import word_wrap
from .. utils.extra_utils import dprint
from .. utils.event_utils import get_event
from .. utils.draw_utils import add_font, clear_all_fonts
from .. utils.coll_utils import create_scatter5_collections, create_new_collection
from .. utils.create_utils import lock_transform

from .. widgets.infobox import SC5InfoBox, generic_infobox_setup


#   .oooooo.                        .o88o.        .oooooo.             oooo                        oooo                .    o8o
#  d8P'  `Y8b                       888 `"       d8P'  `Y8b            `888                        `888              .o8    `"'
# 888           .ooooo.   .ooooo.  o888oo       888           .oooo.    888   .ooooo.  oooo  oooo   888   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.
# 888          d88' `88b d88' `88b  888         888          `P  )88b   888  d88' `"Y8 `888  `888   888  `P  )88b    888   `888  d88' `88b `888P"Y88b
# 888          888   888 888ooo888  888         888           .oP"888   888  888        888   888   888   .oP"888    888    888  888   888  888   888
# `88b    ooo  888   888 888    .o  888         `88b    ooo  d8(  888   888  888   .o8  888   888   888  d8(  888    888 .  888  888   888  888   888
#  `Y8bood8P'  `Y8bod8P' `Y8bod8P' o888o         `Y8bood8P'  `Y888""8o o888o `Y8bod8P'  `V88V"V8P' o888o `Y888""8o   "888" o888o `Y8bod8P' o888o o888o


class SCATTER5_OT_property_coef(bpy.types.Operator):

    bl_idname = "scatter5.property_coef"
    bl_label = "Coef Calculation"
    bl_description = translate("Multiply/ Divide/ Add/ Subtract the value above by a given coefitient. hold [ALT] do the operation on every selected scatter-systems by using the active system coefitient")
    bl_options     = {'INTERNAL','UNDO'}

    operation : bpy.props.StringProperty() # + - * /
    coef : bpy.props.FloatProperty()
    prop : bpy.props.StringProperty()

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel = emitter.scatter5.get_psys_selected(all_emitters=scat_scene.factory_alt_selection_method=="all_emitters")

        def calculate(val, coef, operation):

            if (operation=="+"):
                if (type(val)==Vector):
                    coef = Vector((coef,coef,coef))
                return val + coef
            elif (operation=="-"):
                if (type(val)==Vector):
                    coef = Vector((coef,coef,coef))
                return val - coef
            elif (operation=="*"):
                return val * coef
            elif (operation=="/"): 
                if coef==0:
                    return val
                return val / coef

        #alt for batch support
        event = get_event(nullevent=not scat_scene.factory_alt_allow)

        #ignore any properties update behavior, such as update delay or hotkeys, avoid feedback loop 
        with scat_scene.factory_update_pause(event=True,delay=True,sync=False):        

            #get context psys
            psys = psys_sel if ((event.alt) and (scat_scene.factory_alt_allow)) else [psy_active]
            
            for p in psys:
                
                #get calculated value for each psys 
                value = calculate(getattr(p, self.prop), self.coef, self.operation)

                #avoid float to int error (duh)
                if type(getattr(p, self.prop))==int:
                    value = int(value)

                #set value to prop 
                setattr(p, self.prop, value)

                continue

        return {'FINISHED'}


#   .oooooo.             oooo  oooo             .o.             .o8      o8o                          .                                               .
#  d8P'  `Y8b            `888  `888            .888.           "888      `"'                        .o8                                             .o8
# 888           .ooooo.   888   888           .8"888.      .oooo888     oooo oooo  oooo   .oooo.o .o888oo ooo. .oo.  .oo.    .ooooo.  ooo. .oo.   .o888oo
# 888          d88' `88b  888   888          .8' `888.    d88' `888     `888 `888  `888  d88(  "8   888   `888P"Y88bP"Y88b  d88' `88b `888P"Y88b    888
# 888          888   888  888   888         .88ooo8888.   888   888      888  888   888  `"Y88b.    888    888   888   888  888ooo888  888   888    888
# `88b    ooo  888   888  888   888        .8'     `888.  888   888      888  888   888  o.  )88b   888 .  888   888   888  888    .o  888   888    888 .
#  `Y8bood8P'  `Y8bod8P' o888o o888o      o88o     o8888o `Y8bod88P"     888  `V88V"V8P' 8""888P'   "888" o888o o888o o888o `Y8bod8P' o888o o888o   "888"
#                                                                        888
#                                                                    .o. 88P
#                                                                    `Y888P

# #NOTE should this be runned when user is changing -> TODO scene_callback

# def manage_scene_s5_viewlayers():
#     """When working with multiple scene(s), the Geo-Scatter 5 collection, containing all the scatter-system(s) data created by scatter will be present in your scene, 
#     run this operator to hide the viewlayers not used in the current scene."""

#     from .. utils.coll_utils import exclude_view_layers
#     scene = bpy.context.scene
#     scat_scene = scene.scatter5
                
#     scatter_collections = [c for c in scene.collection.children_recursive if c.name.startswith("psy : ")]

#     if (len(scatter_collections)==0):
#         return None  

#     #get all psys collection names for this context scene
#     all_psys_coll = [ f"psy : {p.name}" for p in scat_scene.get_all_psys() ]

#     for coll in scatter_collections:
#         did = exclude_view_layers(coll, scenes=[scene], hide=(coll.name not in all_psys_coll),)
#         if (did==True) and ("did_act" not in locals()):
#             did_act = True
        
#     if ("did_act" in locals()):
#         dprint("HANDLER: 'manage_scene_s5_viewlayers'", depsgraph=True,)

#     return None 

# class SCATTER5_OT_refresh_psy_viewlayers(bpy.types.Operator):

#     bl_idname      = "scatter5.refresh_psy_viewlayers"
#     bl_label       = translate("")
#     bl_description = translate("When working with multiple scene(s), the Geo-Scatter 5 collection, containing all the scatter-system(s) data created by scatter will be present in your scene, run this operator to hide the viewlayers not used in the current scene.")
#     bl_options     = {'INTERNAL', 'UNDO'}

#     def execute(self, context):

#         manage_scene_s5_viewlayers()

#         return {'FINISHED'}


# ooooooooo.                                    .         .oooooo..o               .       .
# `888   `Y88.                                .o8        d8P'    `Y8             .o8     .o8
#  888   .d88'  .ooooo.   .oooo.o  .ooooo.  .o888oo      Y88bo.       .ooooo.  .o888oo .o888oo
#  888ooo88P'  d88' `88b d88(  "8 d88' `88b   888         `"Y8888o.  d88' `88b   888     888
#  888`88b.    888ooo888 `"Y88b.  888ooo888   888             `"Y88b 888ooo888   888     888
#  888  `88b.  888    .o o.  )88b 888    .o   888 .      oo     .d8P 888    .o   888 .   888 .
# o888o  o888o `Y8bod8P' 8""888P' `Y8bod8P'   "888"      8""88888P'  `Y8bod8P'   "888"   "888"



class SCATTER5_OT_reset_settings(bpy.types.Operator):

    bl_idname      = "scatter5.reset_settings"
    bl_label       = translate("Reset Settings")
    bl_description = translate("Reset the settings of this category to the default values")
    bl_options     = {'INTERNAL', 'UNDO'}

    single_category : bpy.props.StringProperty()

    def find_default(self, api, string_set):
        """find default value of a property"""

        pro = api.bl_rna.properties[string_set] 

        if ( (pro.type=="ENUM") or (pro.type=="STRING") or (pro.type=="BOOLEAN") ):
            return pro.default

        elif ( (pro.type=="FLOAT") or (pro.type=="INT") ):
            return pro.default if (pro.array_length==0) else pro.default_array

        elif (pro.type=="POINTER"): 
            return None #Object pointers are None by default

        return None

    def execute(self, context):
        
        scat_scene = context.scene.scatter5
        emitter = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()

        if (psy_active is None):
            return {'FINISHED'}
        if (psy_active.is_locked(self.single_category)):
            return {'FINISHED'}

        #ignore any properties update behavior, such as update delay or hotkeys
        with scat_scene.factory_update_pause(event=True,delay=True,sync=False):

            #hide for optimization 
            did_hide = None 
            if (not psy_active.hide_viewport):
                psy_active.hide_viewport = did_hide = True

            for s in [k for k in psy_active.bl_rna.properties.keys() if k.startswith(self.single_category) ]:
                try:
                    default_value = self.find_default(psy_active,s)
                    setattr(psy_active, s, default_value)
                except Exception as e:
                    print(f"S5, couldn't reset this value: {s}")
                    print(e)

            #restore optimization
            if (did_hide is not None):
                psy_active.hide_viewport = False
                
        return {'FINISHED'}


# oooooooooo.    o8o                      .o8       oooo                  .oooooo..o               .       .
# `888'   `Y8b   `"'                     "888       `888                 d8P'    `Y8             .o8     .o8
#  888      888 oooo   .oooo.o  .oooo.    888oooo.   888   .ooooo.       Y88bo.       .ooooo.  .o888oo .o888oo
#  888      888 `888  d88(  "8 `P  )88b   d88' `88b  888  d88' `88b       `"Y8888o.  d88' `88b   888     888
#  888      888  888  `"Y88b.   .oP"888   888   888  888  888ooo888           `"Y88b 888ooo888   888     888
#  888     d88'  888  o.  )88b d8(  888   888   888  888  888    .o      oo     .d8P 888    .o   888 .   888 .
# o888bood8P'   o888o 8""888P' `Y888""8o  `Y8bod8P' o888o `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"   "888"


class SCATTER5_OT_disable_main_settings(bpy.types.Operator):

    bl_idname = "scatter5.disable_main_settings"
    bl_label = translate("Disable Procedural Settings")
    bl_description = translate("Disable Procedural Settings")
    bl_options = {'INTERNAL', 'UNDO'}
    
    mode : bpy.props.StringProperty(default="active", options={"SKIP_SAVE",},)
    emitter_name : bpy.props.StringProperty()

    @classmethod
    def poll(cls, context, ):
        return True
    
    def execute(self, context):

        if self.emitter_name:
              emitter = bpy.data.objects.get(self.emitter_name)
              self.emitter_name=""
        else: emitter = bpy.context.scene.scatter5.emitter

        if (self.mode=="active"):
              psys = [ emitter.scatter5.get_psy_active() ]
        else: psys = emitter.scatter5.get_psys_selected()

        for p in psys:
            for k in p.bl_rna.properties.keys():
                if (k.endswith("master_allow")):
                    if (k=="s_display_master_allow"):
                        continue #everything except display
                    setattr(p, k, False)
            
        return {'FINISHED'}

#   .oooooo.   oooo                                       ooooo                                                     .
#  d8P'  `Y8b  `888                                       `888'                                                   .o8
# 888           888   .ooooo.   .oooo.   ooo. .oo.         888  ooo. .oo.  .oo.   oo.ooooo.   .ooooo.  oooo d8b .o888oo
# 888           888  d88' `88b `P  )88b  `888P"Y88b        888  `888P"Y88bP"Y88b   888' `88b d88' `88b `888""8P   888
# 888           888  888ooo888  .oP"888   888   888        888   888   888   888   888   888 888   888  888       888
# `88b    ooo   888  888    .o d8(  888   888   888        888   888   888   888   888   888 888   888  888       888 .
#  `Y8bood8P'  o888o `Y8bod8P' `Y888""8o o888o o888o      o888o o888o o888o o888o  888bod8P' `Y8bod8P' d888b      "888"
#                                                                                  888
#                                                                                 o888o

class SCATTER5_OT_clean_unused_import_data(bpy.types.Operator):

    bl_idname      = "scatter5.clean_unused_import_data"
    bl_label       = translate("Removed any unused object(s) located in the 'Geo-Scatter Import' Collection")
    bl_description = translate("Removed any unused object(s) located in the 'Geo-Scatter Import' Collection")
    bl_options     = {'INTERNAL', 'UNDO'}

    def execute(self, context):

        import_coll = bpy.data.collections.get("Geo-Scatter Import")
        if (import_coll is None):
            raise Exception("It seems that you didn't import anything yet?")

        used_objs = []
        for sc in bpy.data.scenes:
            for coll in sc.collection.children_recursive:
                if (coll.name!=import_coll.name):
                    for o in coll.objects:
                        if (o not in used_objs):
                            used_objs.append(o)

        for o in import_coll.objects:
            if (o not in used_objs):
                bpy.data.meshes.remove(o.data)

        return {'FINISHED'}



# ooooo     ooo                  .o8       ooooo      ooo                 .o8                .
# `888'     `8'                 "888       `888b.     `8'                "888              .o8
#  888       8  oo.ooooo.   .oooo888        8 `88b.    8   .ooooo.   .oooo888   .ooooo.  .o888oo oooo d8b  .ooooo.   .ooooo.   .oooo.o
#  888       8   888' `88b d88' `888        8   `88b.  8  d88' `88b d88' `888  d88' `88b   888   `888""8P d88' `88b d88' `88b d88(  "8
#  888       8   888   888 888   888        8     `88b.8  888   888 888   888  888ooo888   888    888     888ooo888 888ooo888 `"Y88b.
#  `88.    .8'   888   888 888   888        8       `888  888   888 888   888  888    .o   888 .  888     888    .o 888    .o o.  )88b
#    `YbodP'     888bod8P' `Y8bod88P"      o8o        `8  `Y8bod8P' `Y8bod88P" `Y8bod8P'   "888" d888b    `Y8bod8P' `Y8bod8P' 8""888P'
#                888
#               o888o


class SCATTER5_OT_fix_nodetrees(bpy.types.Operator):
    """fix missing/broken/older geonode engine nodegroups and their modifiers"""

    bl_idname = "scatter5.fix_nodetrees"
    bl_label = translate("Fix Plugin Nodetrees ")
    bl_description = translate("Remove the plugin engine nodetrees, and re-apply them to fix any versioning or broken nodes error")
    bl_options = {'INTERNAL', 'UNDO'}

    force_update : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    #TODO this operator is a big mess, not documented.. 

    def execute(self, context):

        #NOTE sadly this process will create a lot of MK.001, as blender import will not reuse nodegroups sadly

        from .. import utils
        from .. __init__ import bl_info
        from .. resources import directories
        
        engine_version = bl_info['engine_version']
        engine_nbr = bl_info['engine_nbr']

        print("")
        print("SCATTER5: Updating to the latest nodetree version : ",f"{engine_version}")

        all_psys = bpy.context.scene.scatter5.get_all_psys()

        #search for all psy we need to update, either we force update all, or we try to get latest scatter mod engine, 
        #if not engine found, means that psy is using old version & need an update
        psys_needing_upd = all_psys if (self.force_update) else [ p for p in all_psys if (p.get_scatter_mod() is None) ]

        #hide all psys
        did_hide = []
        for p in all_psys:
            if (p.hide_viewport==False): 
                p.hide_viewport = True 
                did_hide.append(p.name)

        #force update all geonode engines ? then we remove the original engine node and their nodegroups
        if (self.force_update):

            #remove engine node
            old_nodetree = bpy.data.node_groups.get(f".{engine_version}")
            if (old_nodetree):
                bpy.data.node_groups.remove(old_nodetree)
                
            #remove dependent ng as well
            for nng in bpy.data.node_groups: 
                if ((nng.name.startswith(".S ")) and (engine_nbr in nng.name)):
                    bpy.data.node_groups.remove(nng)
                continue

            #we force the update 
            psys_needing_upd = all_psys

        #importing latest Scatter Engine Nodetree, normally this is done automatically in import_and_add_geonode() however we need to have the engine first to get the default texture
        print(f"   -Importing the latest the Scatter Engine Nodetree")
        
        utils.import_utils.import_geonodes( directories.addon_engine_blend, [f".{engine_version}"], link=False, )
        engine = bpy.data.node_groups[f".{engine_version}"]
        engine.use_fake_user = True

        #about the scatter_texture_nodetrees, the also need an update! replace all .texture nodes by new one
        print(f"   -Updating the Scatter Textures data(s) to latest version")
        
        all_textures_ng = [ ng for ng in bpy.data.node_groups if ng.name.startswith(".TEXTURE") and not ng.name.startswith(".TEXTURE *DEFAULT") ]
        
        for ng in all_textures_ng.copy():

            d = ng.scatter5.texture.get_texture_dict()
            name = ng.scatter5.texture.user_name
            bpy.data.node_groups.remove(ng)

            print(f"         -Updating : ",name)
            
            ng = bpy.data.node_groups.get(".TEXTURE *DEFAULT* MKIV").copy() #availale because we imported the engine above
            ng.scatter5.texture.apply_texture_dict(d)
            ng.scatter5.texture.user_name = name 

            continue

        #for all psys needing an update.. 
        #remove it's current modifier and add a new one

        print(f"   -Updating Scatter System(s) to latest version")

        for p in psys_needing_upd.copy():

            print(f"         -Updating : ",p.name)
            print(f"             -Removing old scatter-engine modifier")

            o = p.scatter_obj 

            #remove all mods 
            for m in o.modifiers: 
                o.modifiers.remove(m)

            #create new geonode mod and import latest nodetree 
            print(f"             -Set up new scatter-engine modifier")
            m = utils.import_utils.import_and_add_geonode(o,
                mod_name=bl_info["engine_version"],
                node_name=f".{engine_version}",
                blend_path=directories.addon_engine_blend,
                copy=True,
                show_viewport=False,
                unique_nodegroups=[
                    "s_distribution_manual",
                    "s_distribution_manual.uuid_equivalence",
                    "s_scale_random",
                    "s_scale_grow",
                    "s_scale_shrink",
                    "s_scale_mirror",
                    "s_rot_align_y",
                    "s_rot_random",
                    "s_rot_add",
                    "s_rot_tilt",
                    "s_abiotic_elev",
                    "s_abiotic_slope",
                    "s_abiotic_dir",
                    "s_abiotic_cur",
                    "s_abiotic_border",
                    "s_pattern1",
                    "s_pattern2",
                    "s_pattern3",
                    "s_gr_pattern1",
                    "s_ecosystem_affinity",
                    "s_ecosystem_repulsion",
                    "s_proximity_repel1",
                    "s_proximity_repel2",
                    "s_push_offset",
                    "s_push_dir",
                    "s_push_noise",
                    "s_push_fall",
                    "s_wind_wave",
                    "s_wind_noise",
                    "s_instances_pick_color_textures",
                    "s_visibility_cam",
                    ], #NOTE: also need to update params in bpy.ops.scatter5.fix_nodetrees()
                )

            #update nodetree versioning information
            print(f"             -Updating Versionning information")

            version_tuple = bl_info['version'][:2] #'5.1' for ex
            p.addon_version = f"{version_tuple[0]}.{version_tuple[1]}"
            p.blender_version = bpy.app.version_string

            continue

        #update signal, might avoid crash 
        print(f"   -Refreshing Scene")

        bpy.context.view_layer.update()
        dg = context.evaluated_depsgraph_get()
        dg.update()

        #update nodetrees values
        print(f"   -Refreshing All Plugin Properties")

        for p in all_psys:
            print(f"         -Refreshing : ",p.name)
            p.refresh_nodetree()
            continue

        #Scatter5.3 introduced uuid per psy 
        import random
        for p in all_psys: 
            if (p.uuid==0):
                p.uuid = random.randint(-2_147_483_647,2_147_483_647)
            continue
        
        #restore all psys initial hide 
        if (did_hide):
            for p in all_psys: 
                if (p.name in did_hide):
                    p.hide_viewport = False
                continue

        #remove warning message 
        from .. ui.ui_notification import notifs_check_1
        notifs_check_1()
        
        #update all emitter interfaces data
        print("   -Reload all interfaces")

        for o in bpy.data.objects:
            if (o.scatter5.particle_systems):
                o.scatter5.particle_interface_refresh()
            continue

        #bugfix, potentially the camera clipping function can be left undefinitely waiting because of this operator
        from . import update_factory 
        if (hasattr(update_factory.update_active_camera_nodegroup,"is_updating")):
            update_factory.update_active_camera_nodegroup.is_updating = False

        print("   -Conversion Done!\n\n")
        return {'FINISHED'}


class SCATTER5_OT_fix_scatter_obj(bpy.types.Operator):
    """re attach potentially broken scatter-obj to the scatter system settings"""

    bl_idname = "scatter5.fix_scatter_obj"
    bl_label = translate("Fix scatter_obj issues")
    bl_description = translate("Fix scatter_obj issues")
    bl_options = {'INTERNAL', 'UNDO'}
    
    def execute(self, context):

        #ensure Geo-Scatter collection exists
        create_scatter5_collections()

        for p in bpy.context.scene.scatter5.get_all_psys():
            emitter = p.id_data
            
            #create scatter obj if not exists yet
            
            scatter_obj_name = "scatter_obj : "+p.name
            scatter_obj = bpy.data.objects.get(scatter_obj_name)
            
            if scatter_obj is None: 
                
                #create new scatter obj
                scatter_obj = bpy.data.objects.new(scatter_obj_name, bpy.data.meshes.new(scatter_obj_name), )
                
                #scatter_obj should never be selectable by user, not needed & outline is bad for performance
                scatter_obj.hide_select = True

                #scatter_obj should always be locked with null transforms
                lock_transform(scatter_obj)

                #we need to leave traces of the original emitter, in case of dupplication we need to identify the double
                scatter_obj.scatter5.original_emitter = emitter 
        
            #ensure in psy coll exists
            
            geonode_coll_name = "psy : "+p.name
            geonode_coll = bpy.data.collections.get(geonode_coll_name)
            
            if (geonode_coll is None):
                geonode_coll = create_new_collection(geonode_coll_name, parent_name="Geo-Scatter Geonode",)
                
            if (geonode_coll.name not in bpy.data.collections["Geo-Scatter Geonode"].children):
                bpy.data.collections["Geo-Scatter Geonode"].children.link(geonode_coll)
                
            #ensure scatter obj in psy collection 
            
            if (scatter_obj.name not in geonode_coll.objects):
                geonode_coll.objects.link(scatter_obj)
                
            #re-attach scatter_obj to psy 
            
            if (p.scatter_obj is None):
                p.scatter_obj = scatter_obj
                            
            continue 
        
        #then set up nodetrees according to settings
        bpy.ops.scatter5.fix_nodetrees()
            
        return {'FINISHED'}
    

#  .oooooo..o                                           o8o      .
# d8P'    `Y8                                           `"'    .o8
# Y88bo.       .ooooo.   .ooooo.  oooo  oooo  oooo d8b oooo  .o888oo oooo    ooo
#  `"Y8888o.  d88' `88b d88' `"Y8 `888  `888  `888""8P `888    888    `88.  .8'
#      `"Y88b 888ooo888 888        888   888   888      888    888     `88..8'
# oo     .d8P 888    .o 888   .o8  888   888   888      888    888 .    `888'
# 8""88888P'  `Y8bod8P' `Y8bod8P'  `V88V"V8P' d888b    o888o   "888"     .8'
#                                                                    .o..P'
#                                                                    `Y8P'


class SCATTER5_OT_popup_security(bpy.types.Operator):

    bl_idname = "scatter5.popup_security"
    bl_label = translate("Information")+":"
    bl_description = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    scatter : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    total_scatter : bpy.props.IntProperty(default=-1, options={"SKIP_SAVE",},) #if -1, will compute the amount accurately

    poly : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    emitter : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_00 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_01 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_02 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_03 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_04 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_05 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_06 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_07 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_08 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_09 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_10 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_11 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_12 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_13 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_14 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_15 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_16 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_17 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_18 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_19 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    #biome with more than 20 layers? get outta here

    #scatter
    s_visibility_hide_system : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)
    s_visibility_hide_system_False : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    s_visibility_view_allow : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    s_visibility_cam_allow : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    #poly
    s_set_bounding_box : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)
    s_display_allow : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    def invoke(self, context, event):
    
        emitter = bpy.data.objects[self.emitter]

        #gather context psys passed
        self.psys = []
        for i in range(20): 
            name = getattr(self,f"psy_name_{i:02}")
            if (name!=""):
                p = emitter.scatter5.particle_systems[name]
                self.psys.append(p)
            continue

        #count total amount of pts created
        if (self.scatter):
            if (self.total_scatter==-1):
                self.total_scatter = 0
                for p in self.psys:
                    self.total_scatter += p.get_scatter_count(state="render") #this operation might take a long time when reaching 10M+ instances

        #invoke interface
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def description(cls, context, properties): 
        return properties.description
        
    def draw(self, context):

        from .. ui import ui_templates

        layout = self.layout

        box, is_open = ui_templates.box_panel(self, layout,         
            prop_str= "ui_dialog_popup", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_dialog_popup");BOOL_VALUE(1)
            icon= "FAKE_USER_ON",
            name= translate("Security Warnings"),
            )
        if is_open:

            if (self.scatter):

                txtblock = box.column()
                txtblock.scale_y = 0.9
                txt = txtblock.row()
                txt.label(text=translate("Heavy Scatter Detected!"), icon="INFO",)
                word_wrap(layout=txtblock, alignment="LEFT", max_char=53, active=True, string=translate("This scatter generated")+f" {self.total_scatter:,} "+translate("instances, more than the security threshold! Define the security measures:"),)

                opts = box.column()
                opts.scale_y = 0.9
                opts.separator(factor=0.4)

                #hide?
                if (self.s_visibility_view_allow or self.s_visibility_cam_allow):
                    prop = opts.row()                    
                    prop.enabled = False
                    prop.prop(self, "s_visibility_hide_system_False", text=translate("Hide the scatter-system(s)"),)
                else: 
                    opts.prop(self, "s_visibility_hide_system", text=translate("Hide the scatter-system(s)"),)

                #viewport % optimization?
                opts.prop(self, "s_visibility_view_allow", text=translate("Hide 90% of the instances"),)

                #camera optimization?
                prop = opts.row()
                prop.enabled = (context.scene.camera is not None)
                prop.prop(self, "s_visibility_cam_allow", text=translate("Hide instances invisible to camera"),)

                opts.separator(factor=0.4)

                pass

            if (self.poly):

                txtblock = box.column()
                txtblock.scale_y = 0.9
                txt = txtblock.row()
                txt.label(text=translate("Heavy Object Detected!"), icon="INFO",)
                word_wrap(layout=txtblock, alignment="LEFT", max_char=53, active=True, string=translate("Object(s) in your scatter had more polygons than the security threshold! Define the security measures:"),)

                opts = box.column()
                opts.scale_y = 0.9
                opts.separator(factor=0.4)

                #object bounding box?
                opts.prop(self, "s_set_bounding_box", text=translate("Set object(s) “Bounds”"),)

                #display as?
                opts.prop(self, "s_display_allow", text=translate("Set scatter(s) “Display As”"),)

                opts.separator(factor=0.4)

                pass

            txtblock = box.column()
            txtblock.scale_y = 0.9
            txt = txtblock.row()
            txt.label(text=translate("Did you know?"), icon="INFO",)
            word_wrap(layout=txtblock, alignment="LEFT", max_char=53, active=True, string=translate("Displaying a lot of polygons in the viewport can freeze blender! If you do not wish to see this menu, feel free to disable or change the security thresholds located in the “Create” panel.\n"),)

        return None

    def execute(self, context):

        if (self.poly):

            if (not self.s_set_bounding_box):
                for p in self.psys:
                    for ins in p.get_instance_objs():
                        ins.display_type = 'TEXTURED'

            if (self.s_display_allow):
                for p in self.psys:
                    if (not p.s_display_allow):
                        p.s_display_allow = True
                        p.s_display_method = "cloud"

        if (self.scatter):

            if (self.s_visibility_view_allow):
                for p in self.psys:
                    p.s_visibility_view_allow = True 
                    p.s_visibility_view_percentage = 90

            if (self.s_visibility_cam_allow):
                for p in self.psys:
                    p.s_visibility_cam_allow = True
                    p.s_visibility_camclip_allow = True
                    p.s_visibility_camclip_cam_boost_xy = (0.1,0.1)
                    p.s_visibility_camdist_allow = True

            if (self.s_visibility_cam_allow or self.s_visibility_view_allow or not self.s_visibility_hide_system):
                for p in self.psys:
                    p.hide_viewport = False

        return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (
    
    SCATTER5_OT_reset_settings,
    SCATTER5_OT_disable_main_settings,
    SCATTER5_OT_clean_unused_import_data,
    SCATTER5_OT_fix_nodetrees,
    SCATTER5_OT_fix_scatter_obj,
    SCATTER5_OT_property_coef,
    SCATTER5_OT_popup_security,
    
    )

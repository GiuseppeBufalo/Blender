
#####################################################################################################
#
# ooo        ooooo            o8o                    .oooooo..o               .       .    o8o
# `88.       .888'            `"'                   d8P'    `Y8             .o8     .o8    `"'
#  888b     d'888   .oooo.   oooo  ooo. .oo.        Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
#  8  `888'   888   .oP"888   888   888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
#  8    Y     888  d8(  888   888   888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
# o8o        o888o `Y888""8o o888o o888o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                                                                           d"     YD
#                                                                                                           "Y88888P'
#
######################################################################################################

import bpy
import os 
import random

from .. resources.translate import translate

from .. resources import directories

#####################################################################################################
#
#   .oooooo.    .o8           o8o                         .
#  d8P'  `Y8b  "888           `"'                       .o8
# 888      888  888oooo.     oooo  .ooooo.   .ooooo.  .o888oo
# 888      888  d88' `88b    `888 d88' `88b d88' `"Y8   888
# 888      888  888   888     888 888ooo888 888         888
# `88b    d88'  888   888     888 888    .o 888   .o8   888 .
#  `Y8bood8P'   `Y8bod8P'     888 `Y8bod8P' `Y8bod8P'   "888"
#                          888888
#
#####################################################################################################

from . particle_settings import SCATTER5_PR_particle_systems
from . mask_settings import SCATTER5_PR_procedural_vg
from .. scattering.selection import upd_particle_systems_idx
from .. scattering import update_factory
'''
from . manual_settings import SCATTER5_manual_physics_brush_object_properties
'''

class SCATTER5_PR_Object(bpy.types.PropertyGroup): 
    """scat_object = bpy.context.object.scatter5"""
    
    # 88   88 88   88 88 8888b.
    # 88   88 88   88 88  8I  Yb
    # Y8   8P Y8   8P 88  8I  dY
    # `YbodP' `YbodP' 88 8888Y"

    #(sadly blender does not support native uuid)

    def get_uuid(self):
        """generate uuid once on first read"""

        uuids = bpy.context.scene.scatter5.uuids
        uuid = {e.owner:e.uuid for e in uuids}.get(self.id_data)

        if (uuid is None): 

            #print("generating uuid..")

            while True:
                uuid = random.randint(-2_147_483_647,2_147_483_647)
                if (uuid not in [e.uuid for e in uuids]):
                    break
                print("1 chance in 4billion...")
                continue 

            #Be Carreful max range! 
            #>>> ValueError: bpy_struct: item.attr = val:  value not in 'int' range ((-2147483647 - 1), 2147483647)

            #add uuid & ownerto global list
            new = uuids.add()
            new.owner = self.id_data
            new.uuid = uuid

        return uuid

    uuid : bpy.props.IntProperty(
        get=get_uuid,
        description="random id between -2.147.483.647 & 2.147.483.647",
        )

    # 88""Yb    db    88""Yb 888888 88  dP""b8 88     888888     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8 .dP"Y8
    # 88__dP   dPYb   88__dP   88   88 dP   `" 88     88__       `Ybo."  YbdP  `Ybo."   88   88__   88b  d88 `Ybo."
    # 88"""   dP__Yb  88"Yb    88   88 Yb      88  .o 88""       o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88 o.`Y8b
    # 88     dP""""Yb 88  Yb   88   88  YboodP 88ood8 888888     8bodP'  dP    8bodP'   88   888888 88 YY 88 8bodP'

    particle_systems : bpy.props.CollectionProperty(type=SCATTER5_PR_particle_systems) #Children Collection
    
    particle_systems_idx : bpy.props.IntProperty(
        update=upd_particle_systems_idx,
        )

    def get_psy_active(self):
        """return the active particle system of this emitter, will return bpy.types.Object or None"""

        if (len(self.particle_systems)==0):
            return None 

        l = [p for p in self.particle_systems if p.active]
        if (len(l)==0):
            return None

        #very unlikely to have many psys active simultaneously, in fact, best to raise error i it is the case?
        return l[0]

    def get_psys_selected(self, all_emitters=False,): 
        """return the selected particle systems of this emitter, note that active psy is not considered as selected, will return a list"""

        if all_emitters:
              emitters = bpy.context.scene.scatter5.get_all_emitters()
        else: emitters = [self.id_data]

        psys_sel = [p for e in emitters for p in e.scatter5.particle_systems if p.sel]

        return psys_sel

    def add_psy_virgin(self, psy_name="", psy_color=None, psy_hide=True, deselect_all=False, instances=[], surfaces=[],):
        """create virgin psy. Set up the collections, assign scatter_obj & geonodes, set addon_version, base name and color, 
        assign surfaces & instances, will always be hidden by defaylt""" 

        from .. import utils

        emitter = self.id_data
        scat_scene = bpy.context.scene.scatter5
        psys = emitter.scatter5.particle_systems

        #create scatter default collection
        utils.coll_utils.create_scatter5_collections()

        #deselect everything but new psys
        if (deselect_all):
            for p in psys: 
                p.sel=False

        #create new scatter obj
        scatter_obj_name = f"scatter_obj : {psy_name}"
        scatter_obj = bpy.data.objects.new(scatter_obj_name, bpy.data.meshes.new(scatter_obj_name), )
        
        #scatter_obj should never be selectable by user, not needed & outline is bad for performance
        scatter_obj.hide_select = True

        #scatter_obj should always be locked with null transforms
        utils.create_utils.lock_transform(scatter_obj)

        #we need to leave traces of the original emitter, in case of dupplication we need to identify the double
        scatter_obj.scatter5.original_emitter = emitter 
        
        #deduce psy_name from scatter obj, prefix will be done automatically by blender 
        psy_name = scatter_obj.name.split("scatter_obj : ")[1]

        #each scatter_obj should be in a psy collection
        geonode_coll = utils.coll_utils.create_new_collection(
            f"psy : {psy_name}",
            parent_name="Geo-Scatter Geonode",
            exclude_scenes=[sc for sc in bpy.data.scenes if sc.name!=bpy.context.scene.name],
            prefix=True,
            )
        geonode_coll.objects.link(scatter_obj)

        #add new psy data
        p = psys.add() 

        #assign scatter obj
        p.scatter_obj = scatter_obj
        
        #set name
        p.name = psy_name
        p.name_bis = psy_name

        #hide on creation? better for performance..
        p.scatter_obj.hide_viewport = psy_hide
        p.hide_viewport = psy_hide 

        #set uuid
        p.uuid = random.randint(-2_147_483_647,2_147_483_647)

        #set color if defined
        if (psy_color is not None):
            p.s_color = psy_color

        #set version 
        from .. __init__ import bl_info
        engine_version = bl_info["engine_version"]
        version_tuple = bl_info['version'][:2] #'5.1' for ex
        p.addon_version = f"{version_tuple[0]}.{version_tuple[1]}"
        p.blender_version = bpy.app.version_string
        
        #update particle list idx 
        emitter.scatter5.particle_systems_idx = len(emitter.scatter5.particle_systems)-1 #will also set .active & .sel property correctly

        #add geonode scatter engine modifier to scatter object, note that some nodegroups need to always be unique
        m = utils.import_utils.import_and_add_geonode(
            p.scatter_obj,
            mod_name=engine_version,
            node_name=f".{engine_version}",
            blend_path=directories.addon_engine_blend,
            show_viewport=(not psy_hide),
            copy=True,
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
                ], #NOTE: also need to update this list in bpy.ops.scatter5.update_nodetrees()
            )

        #assign surfaces:

        #TODO we might need to filter what user add in there?

        if (len(surfaces)==0):
            p.s_surface_method = "emitter"

        elif (len(surfaces)==1):
            if (surfaces[0] is emitter):
                p.s_surface_method = "emitter"
            else:
                p.s_surface_method = "object"
                p.s_surface_object = surfaces[0]

        elif (len(surfaces)>1):
            #create new surface collection
            surfaces_coll = utils.coll_utils.create_new_collection(f"ScatterSurfaces", parent_name="Geo-Scatter Surfaces", prefix=True)
            #add surfaces to collection
            for surf in surfaces: 
                if (surf.name not in surfaces_coll.objects):
                    surfaces_coll.objects.link(surf)
            #assign pointers
            p.s_surface_method = "collection"
            p.s_surface_collection = surfaces_coll.name

        #assign instances: 

        #create new instance collection
        instance_coll = utils.coll_utils.create_new_collection(f"ins_col : {p.name}", parent_name="Geo-Scatter Ins Col", prefix=True)
       
        #add instances in collection
        if (len(instances)!=0):
            for inst in instances:                
                if (inst.name not in instance_coll.objects): 
                    instance_coll.objects.link(inst)        

        #assign pointers
        p.s_instances_coll_ptr = instance_coll

        return p

    # .dP"Y8  dP"Yb  88   88    db    88""Yb 888888        db    88""Yb 888888    db
    # `Ybo." dP   Yb 88   88   dPYb   88__dP 88__         dPYb   88__dP 88__     dPYb
    # o.`Y8b Yb b dP Y8   8P  dP__Yb  88"Yb  88""        dP__Yb  88"Yb  88""    dP__Yb
    # 8bodP'  `"YoYo `YbodP' dP""""Yb 88  Yb 888888     dP""""Yb 88  Yb 888888 dP""""Yb
    
    #deeply linked with psy.get_surfaces_square_area

    estimated_square_area : bpy.props.FloatProperty(default=-1)

    def estimate_square_area(self, eval_modifiers=True, get_selection=False, update_property=True,):
        """get the m² of this object mesh (mods not evaluated),  carreful, might be slow, do not run in real time""" 

        from .. utils.extra_utils import dprint
        
        o = self.id_data
        object_area = 0

        #this function can only work for mesh surfaces
        if (o.type!="MESH"): #TODO might need to support curveobject or metaball
            self.estimated_square_area = 0
            dprint(f"FCT: 'bpy.data.objects[`{o.name}`].scatter5.estimate_square_area() == (type!=MESH)'", depsgraph=False)
            return 0

        #evaluate mods?
        if eval_modifiers:
              depsgraph = bpy.context.evaluated_depsgraph_get()
              eo = o.evaluated_get(depsgraph)
              ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph,)
        else: ob = o.data

        ob.calc_loop_triangles()
        
        import numpy as np 

        #get square area value
        tri_area = np.zeros(len(ob.loop_triangles), dtype=np.float, )
        ob.loop_triangles.foreach_get('area', tri_area, )

        #selection influence?
        if (get_selection):
            tri_sel = np.asarray([float(ob.polygons[t.polygon_index].select) for t in ob.loop_triangles])
            tri_area *= tri_sel #if tri in sel *1 else *0

        object_area = np.sum(tri_area)

        #Check for NaN values
        if (np.isnan(object_area)):
            tri_area = tri_area[~(np.isnan(tri_area))]
            object_area = np.sum(tri_area)

        dprint(f"FCT: 'bpy.data.objects[`{o.name}`].scatter5.estimate_square_area() == {object_area}m²'", depsgraph=False)

        #write result? if selection method never write
        if ( update_property and not get_selection):
            self.estimated_square_area = object_area

        return object_area

    # 888888    db     dP""b8 888888     88""Yb 88""Yb 888888 Yb    dP 88 888888 Yb        dP
    # 88__     dPYb   dP   `" 88__       88__dP 88__dP 88__    Yb  dP  88 88__    Yb  db  dP
    # 88""    dP__Yb  Yb      88""       88"""  88"Yb  88""     YbdP   88 88""     YbdPYbdP
    # 88     dP""""Yb  YboodP 888888     88     88  Yb 888888    YP    88 888888    YP  YP
            
    s_visibility_facepreview_area : bpy.props.FloatProperty(
        description="needed to estimate future psy density",
        default=0,
        )

    # 88""Yb 888888 88""Yb      dP""b8    db    8b    d8 888888 88""Yb    db        .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8
    # 88__dP 88__   88__dP     dP   `"   dPYb   88b  d88 88__   88__dP   dPYb       `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."
    # 88"""  88""   88"Yb      Yb       dP__Yb  88YbdP88 88""   88"Yb   dP__Yb      o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b
    # 88     888888 88  Yb      YboodP dP""""Yb 88 YY 88 888888 88  Yb dP""""Yb     8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'

    #scale fading 

    s_scale_fading_distance_per_cam_min : bpy.props.FloatProperty(
        name=translate("Min"),
        default=30,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )
    s_scale_fading_distance_per_cam_max : bpy.props.FloatProperty(
        name=translate("Max"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )

    #culling distance 

    s_visibility_camdist_per_cam_min : bpy.props.FloatProperty(
        name=translate("Min"),
        default=10,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )
    s_visibility_camdist_per_cam_max : bpy.props.FloatProperty(
        name=translate("Max"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )

    # 88""Yb 88""Yb  dP"Yb   dP""b8 888888 8888b.  88   88 88""Yb    db    88         8b    d8    db    .dP"Y8 88  dP
    # 88__dP 88__dP dP   Yb dP   `" 88__    8I  Yb 88   88 88__dP   dPYb   88         88b  d88   dPYb   `Ybo." 88odP
    # 88"""  88"Yb  Yb   dP Yb      88""    8I  dY Y8   8P 88"Yb   dP__Yb  88  .o     88YbdP88  dP__Yb  o.`Y8b 88"Yb
    # 88     88  Yb  YbodP   YboodP 888888 8888Y"  `YbodP' 88  Yb dP""""Yb 88ood8     88 YY 88 dP""""Yb 8bodP' 88  Yb

    mask_systems : bpy.props.CollectionProperty(type=SCATTER5_PR_procedural_vg) #Children Collection
    mask_systems_idx : bpy.props.IntProperty()

    # .dP"Y8  dP""b8    db    888888 888888 888888 88""Yb      dP"Yb  88""Yb  88888
    # `Ybo." dP   `"   dPYb     88     88   88__   88__dP     dP   Yb 88__dP     88
    # o.`Y8b Yb       dP__Yb    88     88   88""   88"Yb      Yb   dP 88""Yb o.  88
    # 8bodP'  YboodP dP""""Yb   88     88   888888 88  Yb      YbodP  88oodP "bodP'

    original_emitter : bpy.props.PointerProperty( #Keep Track of original emitter, in case of user dupplicating object data, it might cause BS 
        description="is needed when dupplicating an object, it will also dupplicate every object properties, coulld be solved more elegantly if blender had real uuid",
        type=bpy.types.Object, 
        )

    def get_psy_from_scatter_obj(self):
        """find back psy from a scatter_obj"""

        obj = self.id_data
        psy_name = obj.replace("scatter_obj : ","")
        
        for p in self.original_emitter.scatter5.particle_systems:
            if (p.name==psy_name):
                return p

        return None 
    
    '''
    # manual physics brush private properties for simulation objects.. used only during simulation while brush is running, hope i did not add some circular dependency..
    manual_physics_brush_object_properties: bpy.props.PointerProperty(type=SCATTER5_manual_physics_brush_object_properties, )
    '''

#####################################################################################################
#
#  .oooooo..o
# d8P'    `Y8
# Y88bo.       .ooooo.   .ooooo.  ooo. .oo.    .ooooo.
#  `"Y8888o.  d88' `"Y8 d88' `88b `888P"Y88b  d88' `88b
#      `"Y88b 888       888ooo888  888   888  888ooo888
# oo     .d8P 888   .o8 888    .o  888   888  888    .o
# 8""88888P'  `Y8bod8P' `Y8bod8P' o888o o888o `Y8bod8P'
#
#####################################################################################################


from . manual_settings import SCATTER5_PR_scene_manual
from . ops_settings import SCATTER5_PR_operators
from .. scattering.emitter import poll_emitter
from .. scattering.synchronize import SCATTER5_PR_sync_channels


#some related class functions:

def upd_emitter(self,context):
    if (self.emitter is not None):
        self.emitter.scatter5.estimate_square_area()
    return None

def upd_s_master_seed(self,context):
    for ng in bpy.data.node_groups:
        if (ng.name.startswith(".S Master Seed MKIII")):
            ng.nodes["s_master_seed"].integer = self.s_master_seed
    return None


class SCATTER5_PR_uuids(bpy.types.PropertyGroup): 
    """uuids = bpy.context.scene.scatter5.uuids[i]"""

    uuid : bpy.props.IntProperty()
    owner : bpy.props.PointerProperty(type=bpy.types.Object)


class SCATTER5_PR_Scene(bpy.types.PropertyGroup): 
    """scat_scene = bpy.context.scene.scatter5"""

    # 88   88 88   88 88 8888b.
    # 88   88 88   88 88  8I  Yb
    # Y8   8P Y8   8P 88  8I  dY
    # `YbodP' `YbodP' 88 8888Y"

    #need to have a global list where all unique uuid are registered

    uuids : bpy.props.CollectionProperty(type=SCATTER5_PR_uuids)

    # 888888 8b    d8 88 888888 888888 888888 88""Yb
    # 88__   88b  d88 88   88     88   88__   88__dP
    # 88""   88YbdP88 88   88     88   88""   88"Yb
    # 888888 88 YY 88 88   88     88   888888 88  Yb

    #emitter terrain target workflow, the emitter is used to store scatter-systems

    emitter : bpy.props.PointerProperty( 
        type=bpy.types.Object, 
        poll=poll_emitter,
        description=translate("Emitter target object. We will store settings on this object, you'll need to set this emitter target active in order to access the scatter-system(s) settings within the interface. By default we will use the emitter mesh-data as the surface object, however you can choose other surface object(s) if needed."),
        update=upd_emitter, #estimate square area when changing active object
        )
    emitter_pinned : bpy.props.BoolProperty( #pinned mode
        default=False, 
        description=translate("pin emitter object"),
        )

    # 88""Yb    db    88""Yb 888888 88  dP""b8 88     888888     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8 .dP"Y8
    # 88__dP   dPYb   88__dP   88   88 dP   `" 88     88__       `Ybo."  YbdP  `Ybo."   88   88__   88b  d88 `Ybo."
    # 88"""   dP__Yb  88"Yb    88   88 Yb      88  .o 88""       o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88 o.`Y8b
    # 88     dP""""Yb 88  Yb   88   88  YboodP 88ood8 888888     8bodP'  dP    8bodP'   88   888888 88 YY 88 8bodP'

    def get_all_emitters(self):
        """return list of all emitters in context scene"""
        return [e for e in self.id_data.objects if len(e.scatter5.particle_systems)]

    def get_all_psys(self):
        """return a list of all psys in context scene"""
        return [p for e in self.get_all_emitters() for p in e.scatter5.particle_systems]

    def get_psy_by_name(self,name):
        """get a psy by it's given name"""
        for p in self.get_all_psys():
            if (p.name==name):
                return p
        return None

    #  dP""b8 88   88 88
    # dP   `" 88   88 88
    # Yb  "88 Y8   8P 88
    #  YboodP `YbodP' 88

    ui_enabled : bpy.props.BoolProperty(default=True)

    # 8b    d8    db    88b 88 88   88    db    88
    # 88b  d88   dPYb   88Yb88 88   88   dPYb   88
    # 88YbdP88  dP__Yb  88 Y88 Y8   8P  dP__Yb  88  .o
    # 88 YY 88 dP""""Yb 88  Y8 `YbodP' dP""""Yb 88ood8

    manual : bpy.props.PointerProperty(type=SCATTER5_PR_scene_manual)

    # .dP"Y8 Yb  dP 88b 88  dP""b8
    # `Ybo."  YbdP  88Yb88 dP   `"
    # o.`Y8b   8P   88 Y88 Yb
    # 8bodP'  dP    88  Y8  YboodP

    sync_channels : bpy.props.CollectionProperty(type=SCATTER5_PR_sync_channels) #Children Collection
    sync_channels_idx : bpy.props.IntProperty()

    #  dP"Yb  88""Yb 888888 88""Yb    db    888888  dP"Yb  88""Yb
    # dP   Yb 88__dP 88__   88__dP   dPYb     88   dP   Yb 88__dP
    # Yb   dP 88"""  88""   88"Yb   dP__Yb    88   Yb   dP 88"Yb
    #  YbodP  88     888888 88  Yb dP""""Yb   88    YbodP  88  Yb

    operators : bpy.props.PointerProperty(type=SCATTER5_PR_operators)

    # 88     88 .dP"Y8 888888 888888 88""Yb
    # 88     88 `Ybo."   88   88__   88__dP
    # 88  .o 88 o.`Y8b   88   88""   88"Yb
    # 88ood8 88 8bodP'   88   888888 88  Yb

    lister_show_color : bpy.props.BoolProperty(
        default=True,
        name=translate("Display Color"),
        )
    lister_show_stats_count : bpy.props.BoolProperty(
        default=False,
        name=translate("Instance Count Stats"),
        )
    lister_show_stats_surface : bpy.props.BoolProperty(
        default=False,
        name=translate("Surfaces Stats"),
        )
    lister_show_selection : bpy.props.BoolProperty(
        default=True,
        name=translate("Select"),
        )
    lister_show_render_state : bpy.props.BoolProperty(
        default=True,
        name=translate("Render States"),
        )
    lister_show_lock : bpy.props.BoolProperty(
        default=False,
        name=translate("Lock"),
        )
    lister_show_visibility : bpy.props.BoolProperty(
        default=False,
        name=translate("Visibility Features"),
        )
    lister_show_display : bpy.props.BoolProperty(
        default=False,
        name=translate("Display Features"),
        )

    # 8b    d8    db    .dP"Y8 888888 888888 88""Yb     .dP"Y8 888888 888888 8888b.
    # 88b  d88   dPYb   `Ybo."   88   88__   88__dP     `Ybo." 88__   88__    8I  Yb
    # 88YbdP88  dP__Yb  o.`Y8b   88   88""   88"Yb      o.`Y8b 88""   88""    8I  dY
    # 88 YY 88 dP""""Yb 8bodP'   88   888888 88  Yb     8bodP' 888888 888888 8888Y"
    
    s_master_seed : bpy.props.IntProperty(
        name=translate("Master Seed"),
        default=0,
        min=0,
        description=translate("The master seed influence every seeds used by Geo-Scatter in this .blend file"),
        update=upd_s_master_seed,
        )

    # 88 8b    d8 88""Yb  dP"Yb  88""Yb 888888
    # 88 88b  d88 88__dP dP   Yb 88__dP   88
    # 88 88YbdP88 88"""  Yb   dP 88"Yb    88
    # 88 88 YY 88 88      YbodP  88  Yb   88
    
    objects_import_method : bpy.props.EnumProperty(
        name=translate("Import Method"),
        default="APPEND", 
        items=( ("APPEND",translate("Append"),"","APPEND_BLEND",1),
                ("LINK",translate("Link"),"","LINK_BLEND",2),
              ),
        )

    # 88   88 88""Yb 8888b.     db    888888 888888
    # 88   88 88__dP  8I  Yb   dPYb     88   88__
    # Y8   8P 88"""   8I  dY  dP__Yb    88   88""
    # `YbodP' 88     8888Y"  dP""""Yb   88   888888

    #Warning, 3 important properties ahead, first one not available in interface, and this is quite dangerious because internally will be toggled on/off, if error, scene is corrupted
    
    #global switch for "get_event()" fct
    factory_event_listening_allow : bpy.props.BoolProperty(
        default=True,
        )
    #for sync_channels right above
    factory_synchronization_allow : bpy.props.BoolProperty(
        description=translate("The settings synchronization feature allows you to create synch channels for linking scatter-system(s) settings categories together"),
        default=False,
        )
    #update_methods right below
    factory_delay_allow : bpy.props.BoolProperty( 
        default=False,
        description=translate("When tweaking any slider property in blender, the sofware will constantly recompute the scene. This behavior can cause issues when toying with heavy to compute sliders. In order to avoid this behavior we implemented parametric sliders update-behavior in our plugin.\nNote that due to a blender bug, this option works bests if the chosen surface(s) do not contains the emitter object"),
        )

    class factory_update_pause(object):
        """updating a scatter5 tweaking property will trigger the event/delay/sync modifiers, 
        use this 'with' obj to avoid triggering such behavior when changing properties, it will update context.scene globals use the return value to restore"""

        def __init__(self, event=False, delay=False, sync=False, ):
            self._e,self._d,self._s = None,None,None
            self.event,self.delay,self.sync = event,delay,sync
            return None 

        def __enter__(self):
            scat_scene = bpy.context.scene.scatter5
            if (self.event):
                self._e = bool(scat_scene.factory_event_listening_allow)
                scat_scene.factory_event_listening_allow = False
            if (self.delay):
                self._d = bool(scat_scene.factory_delay_allow)
                scat_scene.factory_delay_allow = False
            if (self.sync):
                self._s = bool(scat_scene.factory_synchronization_allow)
                scat_scene.factory_synchronization_allow = False
            return None 

        def __exit__(self,*args):
            scat_scene = bpy.context.scene.scatter5
            if (self._e is not None):
                scat_scene.factory_event_listening_allow = self._e
            if (self._d is not None):
                scat_scene.factory_delay_allow = self._d
            if (self._s is not None):
                scat_scene.factory_synchronization_allow = self._s
            return None 

    factory_update_method : bpy.props.EnumProperty(
        name=translate("Method"),
        default= "update_on_release",
        description= translate("Change how the active particle system refresh the viewport when you are tweaking the settings"),
        items= ( ("update_delayed" ,translate("Fixed Interval"), translate("refresh viewport every x miliseconds"), 1),
                 ("update_on_release" ,translate("On Halt") ,translate("refresh viewport when the mouse button is released"), 2),
                 #("update_apply" ,translate("Manual") ,translate("refresh viewport when clicking on the refresh button"), 3),
               ),
        )
    factory_update_delay : bpy.props.FloatProperty(
        name=translate("Refresh Rate"),
        default=0.25,
        max=2,
        min=0,
        step=3,
        precision=3,
        subtype="TIME",
        unit="TIME",
        description=translate("Delay of the update when tweaking the system(s) settings"),
        )
    update_cam_dummy : bpy.props.BoolProperty(
        get=lambda s: True,
        description=translate("In order to optimize your scatter, a lot of optimization features might be based on the active camera. Unfortunately moving this camera in real time will trigger a constant refresh of all dependent scatter-system(s). Therefore it is a good idea to control the refresh method of the active camera individually"),
        )
    factory_cam_update_method : bpy.props.EnumProperty(
        name=translate("Method"),
        default= "update_on_release",
        description= translate("In order to optimize your scatter, a lot of optimization features might be based on the active camera. Unfortunately moving this camera in real time will trigger a constant refresh of all dependent scatter-system(s). Therefore it is a good idea to control the refresh method of the active camera individually")+"\n\n"+translate("Choose the update method below:"),
        items= ( ("update_delayed", translate("Fixed Interval") ,translate("Send an update signal automatically when the camera move, at given refreshrate. Set the rate to 0 for a real time experience"),0 ),
                 ("update_on_release", translate("On Halt") ,translate("Send an update signal automatically only when we detected that the camera stopped moving for a brief amount of time"),1 ),
                 ("update_apply", translate("Manual") ,translate("Send an update signal only when enabling a camera related feature or when clicking on the refresh button"),2 ),
               ),
        )
    factory_cam_update_ms : bpy.props.FloatProperty(
        name=translate("Refresh Rate (sec)"),
        default=0.35,
        max=2,
        min=0,
        step=3,
        precision=3,
        )
    factory_alt_allow : bpy.props.BoolProperty( #global control over event listening and tweaking delay, only for dev 
        default=True,
        description= translate("When pressing ALT while changing a scatter-system property, Geo-Scatter will automatically apply the value to all selected scatter-system"),
        )
    factory_alt_selection_method : bpy.props.EnumProperty(
        name=translate("Selection"),
        default= "active_emitter",
        description= translate("Change how the active particle system refresh the viewport when you are tweaking the settings"),
        items= ( ("active_emitter", translate("Active Emitter"), translate("apply value to selected scatter-system from active emitter"), 1),
                 ("all_emitters", translate("All Emitters"), translate("apply value to all selected scatter-system of this scene"), 2),
               ),
        )
    # update_draw_outline : bpy.props.BoolProperty( #TODO, this does not make a lot of sense anymore in multi-surface workflow
    #     default=False,
    #     description= translate("Draw an overlay on the active system"),
    #     )
    # update_auto_manage_viewlayers : bpy.props.BoolProperty(
    #     default=True,
    #     description=translate("Automatically adjust scatter-system(s) viewlayers depending the context scene, happening automatically when interacting with a system list."),
    #     )
    update_auto_overlay_rendered : bpy.props.BoolProperty(
        default=False,
        description= translate("Automatically hide the overlay once in rendered view. Drawing a contour overlay on objects such as a scatter is very bad for your viewport performance. Cycles rendered is very good with high poly object and the outline can potentially cancel this benefit"),
        )

    # 8888b.  88   88 8b    d8 8b    d8 Yb  dP
    #  8I  Yb 88   88 88b  d88 88b  d88  YbdP
    #  8I  dY Y8   8P 88YbdP88 88YbdP88   8P
    # 8888Y"  `YbodP' 88 YY 88 88 YY 88  dP

    #dummy properties mostly used for gui 

    dummy_bool_full : bpy.props.BoolProperty(
        get=lambda s: True
        )

    dummy_bool_empty : bpy.props.BoolProperty(
        get=lambda s: False
        )
    dummy_idx : bpy.props.IntProperty(
        default=-1,
        min=-1,
        max=-1,
        )
    dummy_global_only_surfaces : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Only Global space is available for this feature when working with many surfaces"),
        default= "global", 
        items= ( ("global", translate("Global"), translate(""), "WORLD",1 ),
                 ("global_bis", translate("Global"), translate(""), "WORLD",2 ),
               ),
        )
    dummy_local_only_dist : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Only Local space is available for this feature"),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("local_bis", translate("Local"), translate(""), "ORIENTATION_LOCAL",2 ),
               ),
        )

    # 88     88 88""Yb 88""Yb    db    88""Yb Yb  dP
    # 88     88 88__dP 88__dP   dPYb   88__dP  YbdP
    # 88  .o 88 88""Yb 88"Yb   dP__Yb  88"Yb    8P
    # 88ood8 88 88oodP 88  Yb dP""""Yb 88  Yb  dP

    library_item_size : bpy.props.FloatProperty(
        default=7.0,
        min=5,
        max=15,
        name=translate("Item Size")
        )
    library_typo_limit : bpy.props.IntProperty(
        default=40,
        min=4,
        max=100,
        name=translate("Typo Limit"),
        )
    library_adaptive_columns : bpy.props.BoolProperty(
        name=translate("Adaptive Columns"),
        default=True,
        )
    library_columns : bpy.props.IntProperty(
        default=4,
        min=1,
        max=40,
        soft_max=10,
        name=translate("Number of Columns"),
        )
    library_search : bpy.props.StringProperty(
        default="",
        )

#####################################################################################################
#
# oooooo   oooooo     oooo  o8o                    .o8
#  `888.    `888.     .8'   `"'                   "888
#   `888.   .8888.   .8'   oooo  ooo. .oo.    .oooo888   .ooooo.  oooo oooo    ooo
#    `888  .8'`888. .8'    `888  `888P"Y88b  d88' `888  d88' `88b  `88. `88.  .8'
#     `888.8'  `888.8'      888   888   888  888   888  888   888   `88..]88..8'
#      `888'    `888'       888   888   888  888   888  888   888    `888'`888'
#       `8'      `8'       o888o o888o o888o `Y8bod88P" `Y8bod8P'     `8'  `8'
#
#####################################################################################################


from .. ui.biome_library import SCATTER5_PR_library
from .. ui.biome_library import SCATTER5_PR_folder_navigation

from . gui_settings import SCATTER5_PR_ui


class SCATTER5_PR_Window(bpy.types.PropertyGroup):
    """bpy.context.window_manager.scatter5
    WindoWManager props will reset on each session, never register undo"""

    #biome interface, internal storage of items
    library : bpy.props.CollectionProperty(type=SCATTER5_PR_library) #Children Collection
    folder_navigation : bpy.props.CollectionProperty(type=SCATTER5_PR_folder_navigation) #Children Collection
    folder_navigation_idx : bpy.props.IntProperty()

    #all ui related props, all are registered procedurally
    ui : bpy.props.PointerProperty(type=SCATTER5_PR_ui) 

    #keep track of our modals ops
    mode : bpy.props.StringProperty(
        default="", 
        description="mode currently used: DRAW_AREA | MANUAL | PSY_MODAL | FACE_SEL", #TODO, not consistant with this isn't it? 
        )

    #plugin manager category
    category_manager : bpy.props.EnumProperty(
        default = "prefs",
        items = ( ("library" ,translate("Biomes") ,"",),
                  ("market" ,translate("Scatpack") ,"",),
                  None,
                  ("stats",translate("Lister") ,"",),
                  ("prefs" ,translate("Preferences") ,"",),
                ),
        )

    """
    #creation operator settings category
    category_creation_operator : bpy.props.EnumProperty(
        default="operator",
        items= ( ("operator" ,translate("Operator") ,translate("List of settings applying uniquely to this operator"),),
                 ("generic" ,translate("Generic") ,translate("List of settings applying on every single creation operators located in this panel"),),
                ),
        )
    """


#####################################################################################################
#
# ooooo      ooo                 .o8              .oooooo.
# `888b.     `8'                "888             d8P'  `Y8b
#  8 `88b.    8   .ooooo.   .oooo888   .ooooo.  888           oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.
#  8   `88b.  8  d88' `88b d88' `888  d88' `88b 888           `888""8P d88' `88b `888  `888   888' `88b
#  8     `88b.8  888   888 888   888  888ooo888 888     ooooo  888     888   888  888   888   888   888
#  8       `888  888   888 888   888  888    .o `88.    .88'   888     888   888  888   888   888   888
# o8o        `8  `Y8bod8P' `Y8bod88P" `Y8bod8P'  `Y8bood8P'   d888b    `Y8bod8P'  `V88V"V8P'  888bod8P'
#                                                                                             888
#                                                                                            o888o
#####################################################################################################


from .. scattering.texture_datablock import SCATTER5_PR_node_texture


class SCATTER5_PR_node_group(bpy.types.PropertyGroup): 
    """bpy.data.node_groups[i].scatter5"""

    #where we store scatter5 texture data 
    
    texture : bpy.props.PointerProperty(type=SCATTER5_PR_node_texture)

#####################################################################################################
#
# ooooooooooooo                                      oooo         o8o
# 8'   888   `8                                      `888         `"'
#      888      oooo oooo    ooo  .ooooo.   .oooo.    888  oooo  oooo  ooo. .oo.    .oooooooo
#      888       `88. `88.  .8'  d88' `88b `P  )88b   888 .8P'   `888  `888P"Y88b  888' `88b
#      888        `88..]88..8'   888ooo888  .oP"888   888888.     888   888   888  888   888
#      888         `888'`888'    888    .o d8(  888   888 `88b.   888   888   888  `88bod8P'
#     o888o         `8'  `8'     `Y8bod8P' `Y888""8o o888o o888o o888o o888o o888o `8oooooo.
#                                                                                  d"     YD
#                                                                                  "Y88888P'
#####################################################################################################

import bpy
import random

from .. __init__ import bl_info

from .. import scattering

from .. resources.translate import translate

from . gui_settings import SCATTER5_PR_popovers_dummy_class


# 88   88 88""Yb 8888b.     db    888888 888888     888888  dP""b8 888888 .dP"Y8
# 88   88 88__dP  8I  Yb   dPYb     88   88__       88__   dP   `"   88   `Ybo."
# Y8   8P 88"""   8I  dY  dP__Yb    88   88""       88""   Yb        88   o.`Y8b
# `YbodP' 88     8888Y"  dP""""Yb   88   888888     88      YboodP   88   8bodP'


#some related class functions: (most update functions are in the update_factory module)

def upd_group(self, context):
    """update function of p.group, will refresh all group properties accordingly"""
    
    p = self

    if (p.group==""):
        p.property_run_update("s_disable_all_group_features", True,)
        
    else:    
        #Add new group properties!
        g = p.id_data.scatter5.particle_groups.get(p.group)
        if (g is None):
            g = p.id_data.scatter5.particle_groups.add()
            g.name = p.group

        #Optimize this operation 
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):
            #Ensure group properties values or disable the group settings of these psys
            g.refresh_nodetree()

    return None

def upd_lock(self, context):

    if (self.lock==True):
        self.lock = False
        v = (not self.is_all_locked())
        
        for k in self.bl_rna.properties.keys():
            if (k.endswith("_locked")):
                setattr(self,k,v)
            continue

    return None 

def upd_euler_to_direction_prop(self_name, prop_name,):
        
    def _self_euler_to_dir(self,context):

        from mathutils import Vector
        
        e = getattr(self, self_name)
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
    
        setattr(self, prop_name, v)
        return None

    return _self_euler_to_dir

def get_surfaces_match_attr(self, attr_type,):
    """return a function that once executed will return a list of common vertex-groups across all surfaces of this psy/groups
    implementation:
        - note that this function has been implemented as following `lambda s,c,e: s.get_surfaces_match_attr("uv")(s, c, e)` for properties, in order to access self, a bit convulated eraps
        - note that this function is heavily used in interface, to provide feedback on user field not being shared across all surface
        - note that this surface is able to also work with all surfaces of a psy AND all surfaces of a group (==many psys)
    """
    assert attr_type in ["vg","vcol","uv","mat"]

    #first find surfaces! surfaces of group or psy!
    surfaces = self.get_surfaces()

    #return function that will return empty list if no surfaces
    if (not surfaces):
        return lambda s,c,e: []
    
    #else return filter function for our surfaces
    def filter_fct(s, c, edit_text):

        nonlocal attr_type, surfaces

        #return list of common vertex-group across all surfaces
        if (attr_type=="vg"): 
            return set.intersection(*map(set, [ [d.name for d in o.vertex_groups if (edit_text in d.name)] for o in surfaces ] ))

        #return list of common color-attributes across all surfaces
        elif (attr_type=="vcol"): 
            return set.intersection(*map(set, [ [d.name for d in o.data.color_attributes if (edit_text in d.name)] for o in surfaces ] ))

        #return list of common uv-maps across all surfaces
        elif (attr_type=="uv"): 
            return set.intersection(*map(set, [ [d.name for d in o.data.uv_layers if (edit_text in d.name)] for o in surfaces ] ))

        #return list of common materials across all surfaces
        elif (attr_type=="mat"): 
            return set.intersection(*map(set, [ [d.name for d in o.data.materials if (d is not None and edit_text in d.name)] for o in surfaces ] ))

    return filter_fct


#  dP""b8  dP"Yb  8888b.  888888      dP""b8 888888 88b 88
# dP   `" dP   Yb  8I  Yb 88__       dP   `" 88__   88Yb88
# Yb      Yb   dP  8I  dY 88""       Yb  "88 88""   88 Y88
#  YboodP  YbodP  8888Y"  888888      YboodP 888888 88  Y8


#generate code of feature mask properties 

def codegen_featuremask_properties(scope_ref={}, name="name"):
    """generate the redudant the properies declaration of featuremasks"""

    d = {}

    prop_name = f"{name}_mask_ptr"
    d[prop_name] = bpy.props.StringProperty(
        name=translate("Attribute Pointer"),
        description=translate("Search across all surface(s) for shared attributes\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vcol" if (getattr(s,f"{name}_mask_method")=="mask_vcol") else "vg")(s, c, e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory(prop_name,),
        )

    prop_name = f"{name}_mask_reverse"
    d[prop_name] = bpy.props.BoolProperty(
        name=translate("Reverse"),
        default=False,
        update=scattering.update_factory.factory(prop_name,),
        )

    prop_name = f"{name}_mask_method"
    d[prop_name] = bpy.props.EnumProperty(
        name=translate("Mask Method"), 
        description=translate("Universal feature-mask method, choose how you'd like to mask the context feature."),
        default="none", 
        items=( ("none",translate("None"),"","",0),
                ("mask_vg",translate("Vertex-Group"),"","",1),
                ("mask_vcol",translate("Color-Attribute"),"","",2),
                ("mask_noise",translate("Noise"),"","",4),
              ),
        update=scattering.update_factory.factory(prop_name,),
        )

    prop_name = f"{name}_mask_color_sample_method"
    d[prop_name] = bpy.props.EnumProperty(
        name=translate("Color Sampling"), 
        description=translate("Choose how you'd like to sample the mask color to a black/white normalized array of values."),
        default="id_greyscale", 
        items=( ("id_greyscale", translate("Greyscale"), "", "NONE", 0,),
                ("id_red", translate("Red Channel"), "", "NONE", 1,),
                ("id_green", translate("Green Channel"), "", "NONE", 2,),
                ("id_blue", translate("Blue Channel"), "", "NONE", 3,),
                ("id_black", translate("Pure Black"), "", "NONE", 4,),
                ("id_white", translate("Pure White"), "", "NONE", 5,),
                ("id_picker", translate("Color Match"), "", "NONE", 6,),
                ("id_hue", translate("Hue"), "", "NONE", 7,),
                ("id_saturation", translate("Saturation"), "", "NONE", 8,),
                ("id_value", translate("Value"), "", "NONE", 9,),
                ("id_lightness", translate("Lightness"), "", "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), "", "NONE", 11,),
              ),
        update=scattering.update_factory.factory(prop_name,),
        )

    prop_name = f"{name}_mask_id_color_ptr"
    d[prop_name] = bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        default=(1,0,0),
        subtype="COLOR",
        min=0,
        max=1,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )

    prop_name = f"{name}_mask_noise_scale"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.2,
        min=0,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )

    prop_name = f"{name}_mask_noise_seed"
    d[prop_name] = bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory(prop_name, delay_support=True, sync_support=False,),
        )

    prop_name = f"{name}_mask_noise_is_random_seed"
    d[prop_name] = bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory(prop_name, alt_support=False, sync_support=False,),
        )

    prop_name = f"{name}_mask_noise_brightness"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Brightness"),
        default=1,
        min=0,
        soft_max=2,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )

    prop_name = f"{name}_mask_noise_contrast"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Contrast"),
        default=3,
        min=0,
        soft_max=5,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )

    #define objects in dict
    scope_ref.update(d)
    return d

def codegen_properties_by_idx(scope_ref={}, name="my_propXX", nbr=20, items={}, property_type=None, delay_support=False, alt_support=True, sync_support=True,):
    """this fun goal is to generate the redudant the properies declaration"""

    d = {}

    for i in (n+1 for n in range(nbr)):

        #adjust propname depending on index
        if ("XX" in name):
            prop_name = name.replace("XX",f"{i:02}")
        elif ("X" in name):
            prop_name = name.replace("X",f"{i}")
        else:
            raise Exception("codegen_properties_by_idx() forgot to use the XX or X kewords")

        kwargs = items.copy()

        #special case if defaults need to differ depending on number 
        if "default" in kwargs:
            if type(kwargs["default"]) is list:
                kwargs["default"] = kwargs["default"][i-1]

        #adjust label depending on index
        if ("name" in kwargs.keys()):
            to_replace = "XX" if ("XX" in kwargs["name"]) else "X" if ("X" in kwargs["name"]) else ""
            if (to_replace):        
                kwargs["name"] = kwargs["name"].replace(to_replace, f" {i}")

        #add update method, update function keyward is always the same as the property name
        kwargs["update"] = scattering.update_factory.factory(prop_name, delay_support=delay_support, alt_support=alt_support, sync_support=sync_support)

        #add property to dict
        d[prop_name] = property_type(**kwargs)

        continue
        
    #define objects in dict
    scope_ref.update(d)
    return d


# ooooooooo.                          .    o8o            oooo
# `888   `Y88.                      .o8    `"'            `888
#  888   .d88'  .oooo.   oooo d8b .o888oo oooo   .ooooo.   888   .ooooo.   .oooo.o
#  888ooo88P'  `P  )88b  `888""8P   888   `888  d88' `"Y8  888  d88' `88b d88(  "8
#  888          .oP"888   888       888    888  888        888  888ooo888 `"Y88b.
#  888         d8(  888   888       888 .  888  888   .o8  888  888    .o o.  )88b
# o888o        `Y888""8o d888b      "888" o888o `Y8bod8P' o888o `Y8bod8P' 8""888P'



class SCATTER5_PR_particle_systems(bpy.types.PropertyGroup): 
    """bpy.context.object.scatter5.particle_systems, will be stored on emitter"""

    #  dP""b8 888888 88b 88 888888 88""Yb 88  dP""b8
    # dP   `" 88__   88Yb88 88__   88__dP 88 dP   `"
    # Yb  "88 88""   88 Y88 88""   88"Yb  88 Yb
    #  YboodP 888888 88  Y8 888888 88  Yb 88  YboodP
    
    name : bpy.props.StringProperty(
        default="",
        update=scattering.rename.rename_particle,
        )
    
    name_bis : bpy.props.StringProperty(
        description="important for renaming function, avoid name collision",
        default="",
        )

    uuid : bpy.props.IntProperty(
        description="uuid generated in add_psy_virgin, should never be 0, internal purpose",
        default=0,
        ) 

    # 88   88 888888 88 88     88 888888 Yb  dP
    # 88   88   88   88 88     88   88    YbdP
    # Y8   8P   88   88 88  .o 88   88     8P
    # `YbodP'   88   88 88ood8 88   88    dP

    scatter_obj : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        description="Instance generator object. An object locked on scene origin where we'll generate points & instances, this is where our geometry node engine is located. This object might contain custom generated points such as vertices created by manual mode or cache information. This property is ready-only",
        )

    def get_scatter_mod(self, strict=True, raise_exception=True,):
        """get 'Geo-Scatter Engine MK..' modifiers latest version from scatter_obj"""

        #only latest version only?
        if (strict): 
            return self.scatter_obj.modifiers.get(bl_info["engine_version"])

        for m in self.scatter_obj.modifiers: 
            if (m.name.startswith("Geo-Scatter Engine")):
                return m 
            if (m.name.startswith("Scatter5 Geonode Engine")):
                return m

        if (raise_exception):
            raise Exception("Couldn't find any of Geoscatter modifiers")
        
        return None

    # .dP"Y8 888888 88     888888  dP""b8 888888 88  dP"Yb  88b 88
    # `Ybo." 88__   88     88__   dP   `"   88   88 dP   Yb 88Yb88
    # o.`Y8b 88""   88  .o 88""   Yb        88   88 Yb   dP 88 Y88
    # 8bodP' 888888 88ood8 888888  YboodP   88   88  YbodP  88  Y8
    
    active : bpy.props.BoolProperty( 
        default=False,
        description="ready only! auto-updated by `psy.particle_interface_idx` update function `on_particle_interface_interaction()`",
        )
    sel : bpy.props.BoolProperty(
        default=False,
        description=translate("Select/Deselect a scatter-system\nThe act of selection in Geo-Scatter is very important, as operators might act on the selected-system(s), and also because you can press the ALT key while changing a property value to apply the value of the settings to all the selected system(s) simultaneously!"),
        )

    # Yb    dP 888888 88""Yb .dP"Y8 88  dP"Yb  88b 88 88 88b 88  dP""b8
    #  Yb  dP  88__   88__dP `Ybo." 88 dP   Yb 88Yb88 88 88Yb88 dP   `"
    #   YbdP   88""   88"Yb  o.`Y8b 88 Yb   dP 88 Y88 88 88 Y88 Yb  "88
    #    YP    888888 88  Yb 8bodP' 88  YbodP  88  Y8 88 88  Y8  YboodP

    addon_type : bpy.props.StringProperty(
        default=bl_info["name"],
        description="Scatter system created with Geo-Scatter or Biome-Reader ?",
        )
    addon_version : bpy.props.StringProperty(
        default="5.0", #lower possible by default, as we added this prop on Geo-Scatter 5.1, shall be fine for all users psys data
        description="Scatter version upon with this scatter-system was created",
        )
    blender_version : bpy.props.StringProperty(
        default="3.0", #lower possible by default, as we added this prop on Geo-Scatter 5.2, could also be 3.1 
        description="Blender version upon with this scatter-system was created",
        )
    
    def addon_version_is_valid(self):
        """verify if this psy version is adequate to the current addon version"""
        
        from .. utils.str_utils import version_to_float
        #scatter system need always to be up to date with the major releases, 
        #if the scatter was created with a lower version of the plugin, we changed the nodetree in newer version, and this system needs and update
        #if the scatter was created with a higher version of the plugin, the current interface will simply not be possible, illegal action by user
        return version_to_float(self.addon_version,truncated=True,) == version_to_float(bl_info['version'],truncated=True,)
    
    def blender_version_is_valid(self):
        """verify if this psy blender version is adequate to the current version of blender the user is using"""
        
        from .. utils.str_utils import version_to_float
        #blender version upon which the geometry-node nodetree was created from always need to be lower or equal of current blender version
        #if user brings nodetrees saved in a future version of blender, the data will be corrupted forever
        return version_to_float(self.blender_version,truncated=True,) <= version_to_float(bpy.app.version_string,truncated=True,)
    
    # 88""Yb 888888 8b    d8  dP"Yb  Yb    dP 888888
    # 88__dP 88__   88b  d88 dP   Yb  Yb  dP  88__
    # 88"Yb  88""   88YbdP88 Yb   dP   YbdP   88""
    # 88  Yb 888888 88 YY 88  YbodP     YP    888888

    def remove_psy(self): #best to use bpy.ops.scatter5.remove_system()
                          #NOTE: will need to use particle_interface_refresh() after this operator
    
        emitter = self.id_data

        #save selection 
        save_sel = [p.name for p in emitter.scatter5.get_psys_selected() ]

        #remove scatter object 
        if (self.scatter_obj is not None): 
            bpy.data.meshes.remove(self.scatter_obj.data)

        #remove scatter geonode_coll collection
        geonode_coll = bpy.data.collections.get(f"psy : {self.name}")
        if (geonode_coll is not None):
            bpy.data.collections.remove(geonode_coll)

        #remove scatter instance_coll (if not used by another psy)
        instance_coll = bpy.data.collections.get(f"ins_col : {self.name}")
        if (instance_coll is not None):
            if (self.s_instances_coll_ptr==instance_coll):

                from .. scattering.instances import collection_users

                if (len(collection_users(instance_coll))==1):
                    bpy.data.collections.remove(instance_coll)

        #find idx from name in order to remove
        for i,p in enumerate(emitter.scatter5.particle_systems):
            if (p.name==self.name):
                emitter.scatter5.particle_systems.remove(i)
                break

        #restore selection needed, when we change active index, default behavior == reset selection and select active
        for p in save_sel:
            if (p in emitter.scatter5.particle_systems):
                emitter.scatter5.particle_systems[p].sel = True

        return None

    # .dP"Y8 88  88  dP"Yb  Yb        dP   88  88 88 8888b.  888888
    # `Ybo." 88  88 dP   Yb  Yb  db  dP    88  88 88  8I  Yb 88__
    # o.`Y8b 888888 Yb   dP   YbdPYbdP     888888 88  8I  dY 88""
    # 8bodP' 88  88  YbodP     YP  YP      88  88 88 8888Y"  888888

    hide_viewport : bpy.props.BoolProperty(
        default=False, 
        description=translate("Hide/Unhide a scatter-system from viewport"),
        update=scattering.update_factory.factory("hide_viewport", sync_support=False,),
        )
        
    hide_render : bpy.props.BoolProperty(
        default=False, 
        description=translate("Hide/Unhide a scatter-system from render"),
        update=scattering.update_factory.factory("hide_render", sync_support=False,),
        )

    #  dP""b8 88""Yb  dP"Yb  88   88 88""Yb     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # dP   `" 88__dP dP   Yb 88   88 88__dP     `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # Yb  "88 88"Yb  Yb   dP Y8   8P 88"""      o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    #  YboodP 88  Yb  YbodP  `YbodP' 88         8bodP'  dP    8bodP'   88   888888 88 YY 88

    group : bpy.props.StringProperty(
        default="",
        description="we'll automatically create and assign the group items by updating this prop. EmptyField==NoGroup. Note that you might want to run emitter.particle_interface_refresh() after use. ",
        update=upd_group,
        )
    
    def get_group(self):
        """get group of which this system (self) is a member of, will return None if not part of any groups"""
        
        emitter = self.id_data
        for g in emitter.scatter5.particle_groups:
            if (g.name==self.group):
                return g
            
        return None

    # 88      dP"Yb   dP""b8 88  dP     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88     dP   Yb dP   `" 88odP      `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88  .o Yb   dP Yb      88"Yb      o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 88ood8  YbodP   YboodP 88  Yb     8bodP'  dP    8bodP'   88   888888 88 YY 88

    #lock settings, we just do not draw interface, and we need to be carreful, add conditions on operators that modify settings, ex copy paste, synchronize, preset/reset ect... 

    lock : bpy.props.BoolProperty(
        default=False,
        description=translate("Lock/unlock all settings of this scatter-system, locking means that the values will be be read only."),
        update=upd_lock,
        )

    #each categories also have their own lock properties

    def is_locked(self,propname):
        """check if given keys, can be full propname or just category name, is locked"""

        _locked_api = ""
        for cat in ("s_surface","s_distribution","s_mask","s_rot","s_scale","s_pattern","s_abiotic","s_proximity","s_ecosystem","s_push","s_wind","s_visibility","s_instances","s_display",):
            if (cat in propname):
                _locked_api = cat + "_locked"
                break
        _locked_api = self.get(_locked_api)
        return False if (_locked_api is None) else _locked_api

    def is_all_locked(self,):
        """check if all categories are locked (mainly used to display lock icon in GUI)"""

        return all( self.get(k) for k,v in self.bl_rna.properties.items() if k.endswith("_locked") )

    def lock_all(self,):
        """lock all property categories"""

        for k in self.bl_rna.properties.keys():
            if (k.endswith("_locked")):
                setattr(self,k,True)

        return None

    def unlock_all(self,):
        """unlock all property categories"""

        for k in self.bl_rna.properties.keys():
            if (k.endswith("_locked")):
                setattr(self,k,False)

        return None 

    # 888888 88""Yb 888888 888888 8888P 888888     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88__   88__dP 88__   88__     dP  88__       `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88""   88"Yb  88""   88""    dP   88""       o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 88     88  Yb 888888 888888 d8888 888888     8bodP'  dP    8bodP'   88   888888 88 YY 88

    freeze : bpy.props.BoolProperty( #TODO LATER
        default=False,
        )

    # .dP"Y8 Yb  dP 88b 88  dP""b8 88  88     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # `Ybo."  YbdP  88Yb88 dP   `" 88  88     `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # o.`Y8b   8P   88 Y88 Yb      888888     o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 8bodP'  dP    88  Y8  YboodP 88  88     8bodP'  dP    8bodP'   88   888888 88 YY 88

    def is_synchronized(self, s_category, consider_allow_state=True,):
        """check if the psy is being synchronized"""

        emitter       = self.id_data
        scat_scene    = bpy.context.scene.scatter5 
        sync_channels = scat_scene.sync_channels

        if (consider_allow_state):
            if (not scat_scene.factory_synchronization_allow):
                return False

        return any( ch.psy_settings_in_channel(self.name, s_category,) for ch in sync_channels )

    def get_sync_siblings(self,):
        """get information about what is sync with what"""

        d = []
        scat_scene = bpy.context.scene.scatter5 
        sync_channels = scat_scene.sync_channels

        for ch in sync_channels:
            if ch.psy_in_channel(self.name):
                category_list=ch.category_list()
                if (len(category_list)!=0):
                    d.append({ "channel":ch.name, "categories":category_list, "psys":ch.get_sibling_members(), })
        return d

    #  dP""b8    db    888888 888888  dP""b8  dP"Yb  88""Yb Yb  dP     88   88 .dP"Y8 888888 8888b.
    # dP   `"   dPYb     88   88__   dP   `" dP   Yb 88__dP  YbdP      88   88 `Ybo." 88__    8I  Yb
    # Yb       dP__Yb    88   88""   Yb  "88 Yb   dP 88"Yb    8P       Y8   8P o.`Y8b 88""    8I  dY
    #  YboodP dP""""Yb   88   888888  YboodP  YbodP  88  Yb  dP        `YbodP' 8bodP' 888888 8888Y"

    def is_category_used(self, s_category):
        """check if the given property category is active"""

        #nothing can possible be used if there are no surfaces
        if (len(self.get_surfaces())==0):
            return False

        #these categories are always used
        elif (s_category in ("s_surface","s_distribution")): 
            return True

        #this category has special requirement in order to be used         
        elif (s_category=="s_instances"): 
            if (self.s_instances_method=="ins_collection"):
                if ( (self.s_instances_coll_ptr is not None) and len(self.s_instances_coll_ptr.objects)!=0 ):
                    return True
            return False

        if (not getattr(self, f"{s_category}_master_allow")):
            return False

        try:
            method_name = f"get_{s_category}_main_features"
            method = getattr(self, method_name)
            main_features = method()
        except:
            raise Exception("BUG: categories not set up correctly")

        return any( getattr(self,sett) for sett in main_features )

    # .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8     88""Yb 888888 888888 88""Yb 888888 .dP"Y8 88  88
    # `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."     88__dP 88__   88__   88__dP 88__   `Ybo." 88  88
    # o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b     88"Yb  88""   88""   88"Yb  88""   o.`Y8b 888888
    # 8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'     88  Yb 888888 88     88  Yb 888888 8bodP' 88  88
    
    def property_run_update(self, prop_name, value,):
        """directly run the property update task function (== changing nodetree) w/o changing any property value, and w/o going in the update fct wrapper/dispatcher"""

        return scattering.update_factory.UpdatesRegistry.run_update(self, prop_name, value, bypass=True,)

    def property_nodetree_refresh(self, prop_name,):
        """refresh this property value"""

        return self.property_run_update(prop_name, getattr(self,prop_name),)

    def refresh_nodetree(self,): 
        """for every settings, make sure nodetree is updated"""

        settings = [k for k in self.bl_rna.properties.keys() if k.startswith("s_")]
        for s in settings:
            self.property_nodetree_refresh(s,)

        return None

    #  dP""b8 888888 888888      dP""b8  dP"Yb  88   88 88b 88 888888 
    # dP   `" 88__     88       dP   `" dP   Yb 88   88 88Yb88   88   
    # Yb  "88 88""     88       Yb      Yb   dP Y8   8P 88 Y88   88   
    #  YboodP 888888   88        YboodP  YbodP  `YbodP' 88  Y8   88   

    scatter_count_viewport : bpy.props.IntProperty(
        default=-1,
        )
    scatter_count_viewport_consider_hidden : bpy.props.IntProperty(
        default=-1,
        )
    scatter_count_maxload_active : bpy.props.BoolProperty(
        default=False,
        )
    scatter_count_render : bpy.props.IntProperty(
        default=-1,
        )

    # def get_naive_count_realtime(self):
    #     """get count in real time, only for viewport, might be too slow if millions of points, also, will not work for point cloud display"""
    #     return len([_ for ins in bpy.context.evaluated_depsgraph_get().object_instances if (ins.is_instance and ins.parent and ins.parent.original==self.scatter_obj)])

    def get_depsgraph_count(self, attrs=[], ):
        """get an attribute of this scatter-system scatter-obj in evaluated depsgraph, 
        input a list of attr names you wish to get, you'll recieve a list of values back
        mode enum in 'scatterpoint' or 'pointcloud' """

        alist = [] 

        #nodetree to mesh
        self.property_run_update("s_eval_depsgraph", "scatterpoint",)

        #grab values
        depsgraph = bpy.context.evaluated_depsgraph_get()
        e = self.scatter_obj.evaluated_get(depsgraph)

        for name in attrs:
            att = e.data.attributes.get(name)
            
            if (att is None):
                  alist.append([None])
                  continue

            alist.append([att.data[0].value])
            continue

        #restore mesh state 
        self.property_run_update("s_eval_depsgraph", False,)

        return alist

    def get_scatter_count(self, state="viewport", viewport_unhide=True):
        """evaluate the psy particle count (will unhide psy if it was hidden) slow! do not in real time"""

        #if have multiple psy to get particle count, might be faster to run evaluated_depsgraph_get() once for all psys at once. see -> "scatter5.estimate"

        #Need to unhide a sys?
        was_hidden = self.hide_viewport 
        if (was_hidden and viewport_unhide):
            self.hide_viewport = False

        #set fake render state by overriding all our visibility features?
        if (state=="render"):

            if (self.hide_render):
                count = 0
            else:
                #fake render state for visibility features
                self.property_run_update("s_simulate_final_render", True,)
                #get nodetree attr
                attrs = self.get_depsgraph_count(attrs=["scatter_count"],)
                #get count
                count = attrs[0][0] if (attrs[0]!=[None]) else 0
                #restore fake render state for visibility features
                self.property_run_update("s_simulate_final_render", False,)

            #update props
            self.scatter_count_render = count

        #or direct eval from viewport?
        elif (state=="viewport"):

            #get nodetree attr
            attrs = self.get_depsgraph_count(attrs=["scatter_count","befmaxload_count"],)

            #check if maxload feature is being used
            if (attrs[1]==[None]):
                  self.scatter_count_maxload_active=False
            elif (attrs[1][0]==attrs[0][0]):
                  self.scatter_count_maxload_active=False
            else: self.scatter_count_maxload_active=True

            #get count 
            count = attrs[0][0] if (attrs[0]!=[None]) else 0

            #special case, if shutdown, will always leave one visible...
            if (self.scatter_count_maxload_active and (count==1)): 
                count = 0

            #update props
            self.scatter_count_viewport = count
            uncount = 0 if was_hidden else count
            self.scatter_count_viewport_consider_hidden = uncount

        #restore hidden ?
        if (was_hidden and viewport_unhide):
            self.hide_viewport = True
                
        return count

    def get_scatter_density(self, refresh_square_area=True,):
        """evaluate psy density /m² of this scatter system independently of , will remove masks and optimizations temporarily -- CARREFUL MIGHT BE SLOW -- DO NOT RUN IN REAL TIME"""

        p = self
        g = self.get_group()

        #Will need to disable all this, as they have an non-rerpresentative impact ond density
        to_disable = [
            "s_mask_vg_allow",
            "s_mask_vcol_allow",
            "s_mask_bitmap_allow",
            "s_mask_curve_allow",
            "s_mask_boolvol_allow",
            "s_mask_upward_allow",
            "s_mask_material_allow",
            "s_proximity_repel1_allow",
            "s_proximity_repel2_allow",
            "s_ecosystem_affinity_allow",
            "s_ecosystem_repulsion_allow",
            "s_visibility_facepreview_allow",
            "s_visibility_view_allow",
            "s_visibility_cam_allow",
            "s_visibility_maxload_allow",
            "s_display_allow",
            ]
        if (g is not None): 
            to_disable += [
                "s_gr_mask_vg_allow",
                "s_gr_mask_vcol_allow",
                "s_gr_mask_bitmap_allow",
                "s_gr_mask_curve_allow",
                "s_gr_mask_boolvol_allow",
                "s_gr_mask_material_allow",
                "s_gr_mask_upward_allow",
                ]

        #temprorarily disable mask features for psys or groups
        to_re_enable = []
        for prp in to_disable:
            e = g if prp.startswith("s_gr_") else p
            if (getattr(e,prp)==True):
                setattr(e,prp,False)
                to_re_enable = prp
            continue

        #get square area 
        if (refresh_square_area):
              square_area = p.get_surfaces_square_area(evaluate="recalculate", eval_modifiers=True, get_selection=False,)
        else: square_area = p.get_surfaces_square_area(evaluate="gather",)

        #get density 
        count = p.get_scatter_count(state='viewport',)
        density = round(count/square_area,4)

        #re-enabled the temporarily disabled
        for prp in to_re_enable:
            e = g if prp.startswith("s_gr_") else p
            setattr(e,prp,True)
            continue

        return density
    
    #  dP""b8  dP"Yb  88      dP"Yb  88""Yb
    # dP   `" dP   Yb 88     dP   Yb 88__dP
    # Yb      Yb   dP 88  .o Yb   dP 88"Yb
    #  YboodP  YbodP  88ood8  YbodP  88  Yb 
    
    s_color : bpy.props.FloatVectorProperty(
        description=translate("Display Color, change the display color of the scatter-object. Set the viewport shading color to 'Object' to visualize the display color of your system(s)"),
        subtype="COLOR",
        min=0,
        max=1,
        update=scattering.update_factory.factory("s_color",),
        )

    # .dP"Y8 88   88 88""Yb 888888    db     dP""b8 888888
    # `Ybo." 88   88 88__dP 88__     dPYb   dP   `" 88__
    # o.`Y8b Y8   8P 88"Yb  88""    dP__Yb  Yb      88""
    # 8bodP' `YbodP' 88  Yb 88     dP""""Yb  YboodP 888888

    ###################### This category of settings keyword is : "s_surface"

    s_surface_locked : bpy.props.BoolProperty(
        description=translate("Lock/Unlock Settings"),
        )

    # def get_s_surface_main_features(self, availability_conditions=True,):
    #     return []

    # s_surface_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Enable this category"),
    #     description=translate("Mute all features of this category"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_surface_master_allow", sync_support=False,),
    #     )

    ########## ##########

    s_surface_method : bpy.props.EnumProperty(
        name=translate("Surface Method"),
        description=translate("Choose the surface(s) upon which the points will be distributed by your chosen distribution algorithm"),
        default= "emitter", 
        items= ( ("emitter",   translate("Emitter Object"), translate("Distribute points only on the surface of your emitter object mesh."), "INIT_ICON:W_EMITTER", 0, ),
                 ("object",   translate("Single Object"), translate("Distribute points on the surface of any chosen object. This leads to a non-linear workflow where the emitter is only used to store your scattering settings."), "INIT_ICON:W_SURFACE_SINGLE", 1, ),
                 ("collection", translate("Multi-Object(s)"), translate("Distribute points on the surface(s) of all objects in given collection. This leads to a non-linear workflow where the emitter is only used to store your scattering settings."), "INIT_ICON:W_SURFACE_MULTI", 2, ),
               ),
        update=scattering.update_factory.factory("s_surface_method"),
        )
    s_surface_object : bpy.props.PointerProperty(
        type=bpy.types.Object,
        description=translate("Chosen Surface"),
        update=scattering.update_factory.factory("s_surface_object"),
        )
    s_surface_collection : bpy.props.StringProperty( #so triggered here, whi is it not coll_ptr????? grrrr
        default="",
        description=translate("Chosen Surface(s)"),
        update=scattering.update_factory.factory("s_surface_collection"),
        )
    passctxt_s_surface_collection : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)


    def get_surfaces(self):
        """return a list of surface object(s)"""

        if (self.s_surface_method=="emitter"):
            return [self.id_data]

        if (self.s_surface_method=="object"):
            return [self.s_surface_object] if (self.s_surface_object is not None) else []

        if (self.s_surface_method=="collection"):
            coll = bpy.data.collections.get(self.s_surface_collection)
            return coll.objects[:] if (coll is not None) else []

        return []

    def get_surfaces_match_attr(self, attr_type,):
        """gather matching attributes accross all surfaces used"""
        global get_surfaces_match_attr 
        return get_surfaces_match_attr(self, attr_type,) #defined outside, so it's also accessible by codegen function

    def get_surfaces_square_area(self, evaluate="gather", eval_modifiers=True, get_selection=False,):
        """will gather or optionally refresh each obj of the surfaces: object.scatter5.estimated_square_area"""

        total_area = 0
        for s in self.get_surfaces():
            object_area = 0

            #just get each values, do not refresh?
            if (evaluate=="gather"):
                object_area = s.scatter5.estimated_square_area

            #refresh each surfaces area?
            elif (evaluate=="recalculate"):
                object_area = s.scatter5.estimate_square_area(eval_modifiers=eval_modifiers, get_selection=get_selection, update_property=True,)
            
            #refresh only if surface area has not been initiated yet (because is -1)
            elif (evaluate=="init_only"):
                object_area = s.scatter5.estimated_square_area
                if (object_area==-1):
                    object_area = s.scatter5.estimate_square_area(eval_modifiers=eval_modifiers, get_selection=get_selection, update_property=True,)

            total_area += object_area
            continue

        return total_area

    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8

    ###################### This category of settings keyword is : "s_distribution"

    s_distribution_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    # def get_s_distribution_main_features(self, availability_conditions=True,):
    #     return []

    # s_distribution_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Enable this category"),
    #     description=translate("Mute all features of this category"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_distribution_master_allow", sync_support=False,),
    #     )
    
    ########## ##########

    s_distribution_method : bpy.props.EnumProperty(
        name=translate("Distribution Method"),
        description=translate("Choose your distribution algorithm"),
        default="random", 
        items=( ("random",        translate("Random"),        translate("Random distribution algorithm, with optional poisson disk sampling feature to limit distances in-between the generated points"), "INIT_ICON:W_DISTRANDOM", 1),
                ("clumping",      translate("Clump"),         translate("Variation of the random distribution algorithm, with the added benefit of a secondary distribution (children) generated nearby the first generated batch of points (parents). This distribution method is offering additional scale/orientation options. By default, each instances tangent will be aligned toward the center of the parent point."), "INIT_ICON:W_DISTCLUMP",2),
                ("verts",         translate("Per Vertex"),    translate("Distribution per vertex"), "INIT_ICON:W_DISTVERTS",3),
                ("faces",         translate("Per Face"),      translate("Distribution per face center. This distribution method is offering an additional option: the ability to scale depending on the face size. By default, each instances normal will be aligned to the face normal, each tangent will be aligned toward the first adjacent face-edge found."), "INIT_ICON:W_DISTFACES",4),
                ("edges",         translate("Per Edge"),      translate("Distribution per edge. This distribution have subtype modes, please read the subtype description for more information"), "INIT_ICON:W_DISTEDGES",5),
                ("volume",        translate("In Volume"),     translate("Distribute points inside the volume of the given surface(s) mesh, if found. If your surface do not have a volume, you can use the random distribution algorithm with offset features."), "INIT_ICON:W_DISTVOLUME", 6),
                ("manual_all",    translate("Manual"),        translate("Manual mode is a whole new distribution workflow consisting of manually placing points upon chosen surface(s) local space, with the help of many brushes that can have influence on density, scale, rotation or instancing id! Please note that all procedural features can still interact with manual mode. If you'd like a manual only-experience, make sure to disable all procedural features."), "INIT_ICON:W_DISTMANUAL",8),
                ("random_stable", translate("Deform Stable"), translate("Variation of the random distribution algorithm, with the added benefit of having a stable seed that will always stay consistent even on animated/deformed surface(s). The distribution is based on the given UV space, make sure that the uv-map attribute is shared across all your surface(s)."), "INIT_ICON:W_DISTDEFORM",12),
                # Spotlight Project ->spotlight like scattering
                # Localized Radius ->bounding box or empties with radius, randomly throwing rays in there 
                # pixel
                # bezier area
                # empties
                # clean
                # curve
               ),
        update=scattering.update_factory.factory("s_distribution_method"),
        )
    # s_distribution_two_sided : bpy.props.BoolProperty(
    #     name=translate("Two Sided Distribution"),
    #     description=translate("Distribute on both face-sides of the emitting surface"),
    #     default= False, 
    #     update=scattering.update_factory.factory("s_distribution_two_sided"),
    #     )
    
    ########## ########## Random #wrong naming convention here... 

    s_distribution_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space, the distribution density parameter will always be based on your surface(s) area, If you'd like the density to stay consistent even when the surface(s) are animated, choose local, if you'd like the density to be measured globally, choose the global option."),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_space"),
        )
    s_distribution_is_count_method : bpy.props.EnumProperty(
        default="density", 
        items= ( ("density", translate("Density"), translate("Define how many instances should be distributed per square meter unit"),),
                 ("count", translate("Count"),  translate("Choose how many instances will be distributed in total (before any other features may affect this count).\nNote that the amount may be un-precise under 50 points"),),
               ),
        update=scattering.update_factory.factory("s_distribution_is_count_method"),
        )
    s_distribution_count : bpy.props.IntProperty(
        name=translate("Instance Count"),
        default=0,
        min=0,
        soft_max=1_000_000,
        max=99_999_999,
        update=scattering.update_factory.factory("s_distribution_count", delay_support=True,),
        )
    s_distribution_density : bpy.props.FloatProperty(
        name=translate("Instances /m²"), 
        default=0, 
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_density", delay_support=True,),
        )
    s_distribution_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_seed", delay_support=True, sync_support=False,),
        )
    s_distribution_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_is_random_seed", alt_support=False, sync_support=False,),
        )
    s_distribution_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_limit_distance_allow",),
        )
    s_distribution_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        subtype="DISTANCE",
        default=0.2,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_limit_distance", delay_support=True,),
        )
    s_distribution_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal [ALT] shortcut to execute the same operation on all selected system(s) simultaneously"),
        default=2,
        min=0,
        update=scattering.update_factory.factory("s_distribution_coef", delay_support=True,),
        )

    ########## ########## Faces

    ########## ########## Verts

    ########## ########## Edges

    s_distribution_edges_selection_method : bpy.props.EnumProperty(
        name=translate("Selection"),
        description=translate("Choose On which edges the instances will spawn"),
        default="all", 
        items= ( ("all",         translate("All"),          translate("Spawn instances on every edges"), "VIEW_PERSPECTIVE",0),
                 ("unconnected", translate("Un-Connected"), translate("Spawn instances only on edges that aren't connected to faces"), "UNLINKED",1),
                 ("boundary",    translate("Boundary"),     translate("Spawn instances only on boundary edges"), "MOD_EDGESPLIT",2),
               ),
        update=scattering.update_factory.factory("s_distribution_edges_selection_method"),
        )
    s_distribution_edges_position_method : bpy.props.EnumProperty(
        name=translate("Position"),
        description=translate("Choose the position & orientation of the instances on the context edge"),
        default= "center", 
        items= ( ("center",  translate("Center"), translate("Place instances on center of edges. By default the instances tangent will face toward the other vertex."), "INIT_ICON:W_DISTEDGESMIDDLE", 0),
                 ("start",  translate("Along"),  translate("Place instances center of edges. By default the instances normal will be oriented alongside the edge."), "INIT_ICON:W_DISTEDGESSTART", 1),
               ),
        update=scattering.update_factory.factory("s_distribution_edges_position_method"),
        )

    ########## ########## Volume

    s_distribution_volume_is_count_method : bpy.props.EnumProperty( #too buggy for current algo
        default="density", 
        items= ( ("density", translate("Density"), translate("Define how many instances should be distributed per square meter unit"),),
                 ("count", translate("Count"),  translate("Define how many instances should be distributed in total, before limit-distance or masks are computed."),),
               ),
        update=scattering.update_factory.factory("s_distribution_volume_is_count_method"),
        )
    s_distribution_volume_count : bpy.props.IntProperty( #too buggy for current algo
        name=translate("Instance Count"),
        default=0,
        min=0,
        soft_max=1_000_000,
        max=99_999_999,
        update=scattering.update_factory.factory("s_distribution_volume_count", delay_support=True,),
        )
    s_distribution_volume_density : bpy.props.FloatProperty(
        name=translate("Instances /m²"), 
        default=100,
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_volume_density", delay_support=True,),
        )
    s_distribution_volume_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_volume_seed", delay_support=True, sync_support=False,),
        )
    s_distribution_volume_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_volume_is_random_seed", alt_support=False, sync_support=False,),
        )
    s_distribution_volume_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_volume_limit_distance_allow",),
        )
    s_distribution_volume_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        subtype="DISTANCE",
        default=0.5,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_volume_limit_distance", delay_support=True,),
        )
    s_distribution_volume_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal [ALT] shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        update=scattering.update_factory.factory("s_distribution_volume_coef", delay_support=True,),
        )

    ########## ########## Random Stable

    s_distribution_stable_uv_ptr : bpy.props.StringProperty(
        default="UVMap",
        name=translate("UV-Map Pointer"),
        description=translate("Stable Uv-space from which the distribution will be computed. Search across all surface(s) for shared Uvmap\nWill highlight red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("uv")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_distribution_stable_uv_ptr",),
        )
    s_distribution_stable_is_count_method : bpy.props.EnumProperty(
        default="density", 
        items= ( ("density", translate("Density"), translate("Define how many instances should be distributed per square meter unit"),),
                 ("count", translate("Count"),  translate("Define how many instances should be distributed in total, before limit-distance or masks are computed."),),
               ),
        update=scattering.update_factory.factory("s_distribution_stable_is_count_method"),
        )
    s_distribution_stable_count : bpy.props.IntProperty(
        name=translate("Instance Count"),
        default=0,
        min=0,
        soft_max=1_000_000,
        max=99_999_999,
        update=scattering.update_factory.factory("s_distribution_stable_count", delay_support=True,),
        )
    s_distribution_stable_density : bpy.props.FloatProperty(
        name=translate("Instance /UVm²"), 
        default=50, 
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_stable_density", delay_support=True,),
        )
    s_distribution_stable_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_stable_seed", delay_support=True, sync_support=False,),
        )
    s_distribution_stable_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_stable_is_random_seed", alt_support=False, sync_support=False,),
        )
    s_distribution_stable_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_stable_limit_distance_allow",),
        )
    s_distribution_stable_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        default=0.02,
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_stable_limit_distance", delay_support=True,),
        )
    s_distribution_stable_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal [ALT] shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        update=scattering.update_factory.factory("s_distribution_stable_coef", delay_support=True,),
        )

    ########## ########## Clumps 

    s_distribution_clump_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space, the distribution density parameter will always be based on your surface(s) area, If you'd like the density to stay consistent even when the surface(s) are animated, choose local, if you'd like the density to be measured globally, choose the global option."),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_clump_space"),
        )
    s_distribution_clump_density : bpy.props.FloatProperty(
        name=translate("Clump /m²"), 
        default=0.15,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_density", delay_support=True,),
        )
    s_distribution_clump_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_limit_distance_allow",),
        )
    s_distribution_clump_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        subtype="DISTANCE",
        default=0,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_limit_distance", delay_support=True,),
        )
    s_distribution_clump_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0,
        update=scattering.update_factory.factory("s_distribution_clump_seed", delay_support=True, sync_support=False,),
        )
    s_distribution_clump_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_is_random_seed", alt_support=False, sync_support=False,),
        )
    s_distribution_clump_max_distance : bpy.props.FloatProperty(
        name=translate("Min Distance"),
        description=translate("Reach distance of the clump before the transition starts"),
        subtype="DISTANCE",
        default=0.7,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_max_distance", delay_support=True,),
        )
    s_distribution_clump_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Falloff transistion distance"),
        subtype="DISTANCE",
        default=0.5,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_falloff", delay_support=True,),
        )
    s_distribution_clump_random_factor : bpy.props.FloatProperty(
        name=translate("Random"),
        description=translate("Randomize the distance reach by multiplying the distance by a random float, ranging from 1 to chosen ratio"),
        default=1,
        min=0,
        soft_max=10,
        update=scattering.update_factory.factory("s_distribution_clump_random_factor", delay_support=True,),
        )
    #child
    s_distribution_clump_children_density : bpy.props.FloatProperty(
        name=translate("Children /m²"), 
        default=15,
        min=0,
        update=scattering.update_factory.factory("s_distribution_clump_children_density", delay_support=True,),
        )
    s_distribution_clump_children_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_children_limit_distance_allow",),
        )
    s_distribution_clump_children_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("With this option enabled, you'll limit the probability of having points distributed near each other. This technique use the the poisson-disk sampling algorithm under the hood to adjust points that spawned too close to each other. Be warned this feature slows-down performance and is only approximative to a given radius distance from the origin of the points"),
        subtype="DISTANCE",
        default=0.2, 
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_children_limit_distance", delay_support=True,),
        )
    s_distribution_clump_children_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_children_seed", delay_support=True, sync_support=False,),
        )
    s_distribution_clump_children_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_children_is_random_seed", alt_support=False, sync_support=False,),
        )
    #remap
    s_distribution_clump_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_fallremap_allow",),
        )
    s_distribution_clump_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_fallremap_revert",),
        )
    s_distribution_clump_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_strength", delay_support=True,),
        )
    s_distribution_clump_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_scale", delay_support=True,),
        )
    s_distribution_clump_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_distribution_clump_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_distribution_clump_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_distribution_clump.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_distribution_clump.fallremap"),
        )

    # 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
    #  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
    #  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
    # 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'

    ###################### This category of settings keyword is : "s_mask"
    ###################### this category is Not supported by Preset
    ###################### Same set of properties for groups

    s_mask_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_mask_main_features(self, availability_conditions=True,):
        r = ["s_mask_vg_allow", "s_mask_vcol_allow", "s_mask_bitmap_allow", "s_mask_curve_allow", "s_mask_boolvol_allow","s_mask_upward_allow", "s_mask_material_allow",]
        if (not availability_conditions):
            return r
        if (self.s_distribution_method=="volume"):
            return ["s_mask_curve_allow", "s_mask_boolvol_allow","s_mask_upward_allow",]
        return r

    s_mask_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_mask_master_allow", sync_support=False,),
        )

    ########## ########## Vgroups

    s_mask_vg_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Group Mask"),
        description=translate("Mask-out your instances with the help of a vertex-group"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_vg_allow"),
        )
    s_mask_vg_ptr : bpy.props.StringProperty(
        name=translate("Vertex-Group Pointer"),
        description=translate("Search across all surface(s) for shared vertex-group\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vg")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_vg_ptr"),
        )
    s_mask_vg_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_vg_revert"),
        )

    ########## ########## VColors
    
    s_mask_vcol_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Color Mask"), 
        description=translate("Mask-out your instances with the help of a color-attribute, specify which color-channel to sample"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_vcol_allow"),
        )
    s_mask_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all surface(s) for shared color attributes\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vcol")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_vcol_ptr"),
        )
    s_mask_vcol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_vcol_revert"),
        )
    s_mask_vcol_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to consider the color values in order to influence the distribution, by default the colors will be simply converted to black and white"),
        default="id_greyscale", 
        items=( ("id_greyscale", translate("Greyscale"), "", "NONE", 0,),
                ("id_red", translate("Red Channel"), "", "NONE", 1,),
                ("id_green", translate("Green Channel"), "", "NONE", 2,),
                ("id_blue", translate("Blue Channel"), "", "NONE", 3,),
                ("id_black", translate("Pure Black"), "", "NONE", 4,),
                ("id_white", translate("Pure White"), "", "NONE", 5,),
                ("id_picker", translate("Color Match"), "", "NONE", 6,),
                ("id_hue", translate("Hue"), "", "NONE", 7,),
                ("id_saturation", translate("Saturation"), "", "NONE", 8,),
                ("id_value", translate("Value"), "", "NONE", 9,),
                ("id_lightness", translate("Lightness"), "", "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), "", "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_mask_vcol_color_sample_method"),
        )
    s_mask_vcol_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_mask_vcol_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Bitmap 

    s_mask_bitmap_allow : bpy.props.BoolProperty( 
        name=translate("Image Mask"), 
        description=translate("Mask-out your instances with the help of an image texture, don't forget to save the image in your blend file!"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_bitmap_allow"),
        )
    s_mask_bitmap_uv_ptr : bpy.props.StringProperty(
        default="UVMap",
        name=translate("UV-Map Pointer"),
        description=translate("Search across all surface(s) for shared Uvmap\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("uv")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_bitmap_uv_ptr"),
        )
    s_mask_bitmap_ptr : bpy.props.StringProperty(
        update=scattering.update_factory.factory("s_mask_bitmap_ptr"),
        )
    s_mask_bitmap_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_bitmap_revert"),
        )
    s_mask_bitmap_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to consider the color values in order to influence the distribution, by default the colors will be simply converted to black and white"),
        default="id_greyscale",
        items=( ("id_greyscale", translate("Greyscale"), "", "NONE", 0,),
                ("id_red", translate("Red Channel"), "", "NONE", 1,),
                ("id_green", translate("Green Channel"), "", "NONE", 2,),
                ("id_blue", translate("Blue Channel"), "", "NONE", 3,),
                ("id_black", translate("Pure Black"), "", "NONE", 4,),
                ("id_white", translate("Pure White"), "", "NONE", 5,),
                ("id_picker", translate("Color Match"), "", "NONE", 6,),
                ("id_hue", translate("Hue"), "", "NONE", 7,),
                ("id_saturation", translate("Saturation"), "", "NONE", 8,),
                ("id_value", translate("Value"), "", "NONE", 9,),
                ("id_lightness", translate("Lightness"), "", "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), "", "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_mask_bitmap_color_sample_method"),
        )
    s_mask_bitmap_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_mask_bitmap_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Material

    s_mask_material_allow : bpy.props.BoolProperty( 
        name=translate("Material ID Mask"), 
        description=translate("Mask-out instances that are not distributed upon the selected material slot"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_material_allow"),
        )
    s_mask_material_ptr : bpy.props.StringProperty(
        name=translate("Material Pointer: The faces assigned to chosen material slot will be used as a culling mask"),
        description=translate("Search across all surface(s) for shared Materials\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("mat")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_material_ptr"),
        )
    s_mask_material_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_material_revert"),
        )
    
    ########## ########## Curves

    s_mask_curve_allow : bpy.props.BoolProperty( 
        name=translate("Bezier-Area Mask"), 
        description=translate("Mask-out instances that are inside the area of a closed bezier-curve."),
        default=False, 
        update=scattering.update_factory.factory("s_mask_curve_allow"),
        )
    s_mask_curve_ptr : bpy.props.PointerProperty(
        name=translate("Bezier-Curve Pointer"),
        type=bpy.types.Object, 
        poll=lambda s,o: o.type=="CURVE",
        update=scattering.update_factory.factory("s_mask_curve_ptr"),
        )
    s_mask_curve_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_curve_revert"),
        )

    ########## ########## Boolean Volume

    s_mask_boolvol_allow : bpy.props.BoolProperty( 
        name=translate("Boolean Mask"), 
        description=translate("Mask-out your instances located inside objects-volume from given collection"),
        default=False,
        update=scattering.update_factory.factory("s_mask_boolvol_allow"),
        )
    s_mask_boolvol_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        update=scattering.update_factory.factory("s_mask_boolvol_coll_ptr"),
        )
    passctxt_s_mask_boolvol_coll_ptr : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)
    s_mask_boolvol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_boolvol_revert"),
        )

    ########## ########## Upward Obstruction

    s_mask_upward_allow : bpy.props.BoolProperty( 
        name=translate("Upward-Obstruction Mask"), 
        description=translate("Mask-out your instances located underneath objects inside given collection"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_upward_allow"),
        )
    s_mask_upward_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        update=scattering.update_factory.factory("s_mask_upward_coll_ptr"),
        )
    passctxt_s_mask_upward_coll_ptr : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)
    s_mask_upward_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_mask_upward_revert"),
        )

    # .dP"Y8  dP""b8    db    88     888888
    # `Ybo." dP   `"   dPYb   88     88__
    # o.`Y8b Yb       dP__Yb  88  .o 88""
    # 8bodP'  YboodP dP""""Yb 88ood8 888888

    ###################### This category of settings keyword is : "s_scale"

    s_scale_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_scale_main_features(self, availability_conditions=True,): 
        r = ["s_scale_default_allow", "s_scale_random_allow", "s_scale_min_allow", "s_scale_mirror_allow", "s_scale_shrink_allow", "s_scale_grow_allow", "s_scale_fading_allow"]
        if (not availability_conditions):
            return r + ["s_scale_clump_allow","s_scale_faces_allow","s_scale_edges_allow"]
        if (self.s_distribution_method=="clumping"):
            r.append("s_scale_clump_allow")
        elif (self.s_distribution_method=="faces"):
            r.append("s_scale_faces_allow")
        elif (self.s_distribution_method=="edges"):
            r.append("s_scale_edges_allow")
        if (self.s_instances_method=="ins_points"):
            r.remove("s_scale_mirror_allow")
        return r

    s_scale_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_scale_master_allow", sync_support=False,),
        )

    ########## ########## Default 

    s_scale_default_allow : bpy.props.BoolProperty(
        name=translate("Default Scale"), 
        description=translate("Define the default Scale of your distributed points."),
        default=False, 
        update=scattering.update_factory.factory("s_scale_default_allow"),
        )
    s_scale_default_space : bpy.props.EnumProperty(
        name=translate("Reference"),
        description=translate("Do you wish your instances to scale according to your surface(s) ? If so please choose local, if you'd like your instances to be accurate relatively to the scene space, please choose the global option"),
        default="local_scale",
        items= ( ("local_scale", translate("Local"), "",  "ORIENTATION_LOCAL",1 ),
                 ("global_scale", translate("Global"), "", "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_scale_default_space"),
        )
    s_scale_default_value : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        subtype="XYZ", 
        default=(1,1,1), 
        update=scattering.update_factory.factory("s_scale_default_value", delay_support=True,),
        )
    s_scale_default_multiplier : bpy.props.FloatProperty(
        name=translate("Factor"),
        default=1,
        soft_max=5,
        soft_min=0,
        update=scattering.update_factory.factory("s_scale_default_multiplier", delay_support=True,),
        )
    s_scale_default_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal [ALT] shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        update=scattering.update_factory.factory("s_scale_default_coef", delay_support=True,),
        )

    ########## ########## Random

    s_scale_random_allow : bpy.props.BoolProperty(
        name=translate("Random Scale"), 
        description=translate("Randomly change the scale of your instances"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_random_allow"),
        )
    s_scale_random_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        subtype="XYZ", 
        default=(0.33,0.33,0.33), 
        soft_min=0,
        soft_max=2,
        update=scattering.update_factory.factory("s_scale_random_factor", delay_support=True,),
        )
    s_scale_random_probability : bpy.props.FloatProperty(
        name=translate("Probability"),
        description=translate("Define the probability rate, a rate ranging toward 0% means that less instances will be influenced by the scaling factor, a probability rate ranging toward 100% means that most instances will get affected by the scaling factor"),
        subtype="PERCENTAGE",
        default=50,
        min=0,
        max=99, 
        update=scattering.update_factory.factory("s_scale_random_probability", delay_support=True,),
        )
    s_scale_random_method : bpy.props.EnumProperty(
        name=translate("Randomization Method"),
        default="random_uniform",
        items= ( ("random_uniform", translate("Uniform"), translate("Influence the scale of your instances toward given factor by uniformly scaling the X/Y/Z values"), 1 ),
                 ("random_vectorial",  translate("Vectorial"), translate("Influence the scale of your instances toward given factor individually per X/Y/Z axis"), 2 ),
               ),
        update=scattering.update_factory.factory("s_scale_random_method",),
        )
    s_scale_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_scale_random_seed", delay_support=True, sync_support=False,),
        )
    s_scale_random_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_scale_random_is_random_seed", alt_support=False, sync_support=False,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_random",)

    ########## ########## Shrink

    s_scale_shrink_allow : bpy.props.BoolProperty(
        name=translate("Shrink Mask"), 
        description=translate("Influences your instances with a shrinking effect, meant to be used with a mask for precisely defining the effect area"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_shrink_allow"),
        )
    s_scale_shrink_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        subtype="XYZ",
        default=(0.1,0.1,0.1),
        soft_min=0,
        soft_max=1,
        update=scattering.update_factory.factory("s_scale_shrink_factor", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_shrink",)

    ########## ########## Grow

    s_scale_grow_allow : bpy.props.BoolProperty(
        name=translate("Grow Mask"), 
        description=translate("Influences your instances with a growth effect, meant to be used with a mask for precisely defining the effect area"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_grow_allow"),
        )
    s_scale_grow_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        subtype="XYZ",
        default=(3,3,3),
        soft_min=1,
        soft_max=5,
        update=scattering.update_factory.factory("s_scale_grow_factor", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_grow",)

    ########## ########## Mirrorring 

    s_scale_mirror_allow : bpy.props.BoolProperty(
        name=translate("Random Mirror"),
        description=translate("Hide the repetition of the instances models, with the help of a random a random mirror effect, by scaling by -1  on selected axis)"),
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_allow"),
        )
    s_scale_mirror_is_x : bpy.props.BoolProperty(
        default=True,
        update=scattering.update_factory.factory("s_scale_mirror_is_x"),
        )
    s_scale_mirror_is_y : bpy.props.BoolProperty(
        default=True,
        update=scattering.update_factory.factory("s_scale_mirror_is_y"),
        )
    s_scale_mirror_is_z : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_is_z"),
        ) 
    
    s_scale_mirror_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        update=scattering.update_factory.factory("s_scale_mirror_seed", delay_support=True, sync_support=False,),
        )
    s_scale_mirror_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_is_random_seed", alt_support=False, sync_support=False,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_mirror",)

    ########## ########## Minimal 

    s_scale_min_allow : bpy.props.BoolProperty(
        name=translate("Minimal Scale"),
        description=translate("Remove or remap the instances scale values that are below chosen threshold"),
        default=False,
        update=scattering.update_factory.factory("s_scale_min_allow",),
        )
    s_scale_min_method : bpy.props.EnumProperty(
        name=translate("Minimal Filter Method"),
        default="s_scale_min_lock",
        items=( ("s_scale_min_lock"  ,translate("Adjusting")  ,translate("If instance scale goes below given threshold, re-adjust it to fit minimal value") ),
                ("s_scale_min_remove",translate("Removing") ,translate("If instance scale goes below given threshold, remove the instance") ),
              ),
        update=scattering.update_factory.factory("s_scale_min_method"),
        )
    s_scale_min_value : bpy.props.FloatProperty(
        name=translate("Threshold"),
        default=0.05,
        soft_min=0,
        soft_max=10, 
        update=scattering.update_factory.factory("s_scale_min_value", delay_support=True,),
        )

    ########## ########## Scale Fading

    s_scale_fading_allow : bpy.props.BoolProperty(
        name=translate("Scale Fading"), 
        description=translate("Fade-away the scale of the instances depending on the passing distance of the active camera. This feature is especially useful if you'd like to emphase the perspective of your shot"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_fading_allow"),
        )
    s_scale_fading_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        subtype="XYZ",
        default=(2,2,1.5),
        soft_min=0, soft_max=5,
        update=scattering.update_factory.factory("s_scale_fading_factor", delay_support=True,),
        )
    s_scale_fading_per_cam_data : bpy.props.BoolProperty(
        default=False,
        description=translate("Use variable distance depending on your active cameras"),
        update=scattering.update_factory.factory("s_scale_fading_per_cam_data"),
        )
    s_scale_fading_distance_min : bpy.props.FloatProperty(
        name=translate("Minimal"),
        default=30,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_scale_fading_distance_min", delay_support=True,),
        )
    s_scale_fading_distance_max : bpy.props.FloatProperty(
        name=translate("Maximal"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_scale_fading_distance_max", delay_support=True,),
        )
    #remap
    s_scale_fading_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_fading_fallremap_allow",),
        )
    s_scale_fading_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_scale_fading_fallremap_revert",),
        )
    s_scale_fading_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_scale_fading.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_scale_fading.fallremap"),
        )

    ########## ########## Clump Special  

    s_scale_clump_allow : bpy.props.BoolProperty(
        name=translate("Clump Scale"), 
        description=translate("Influence the scale of instances depending on how far they are from the clump center"),
        default=True, 
        update=scattering.update_factory.factory("s_scale_clump_allow"),
        )
    s_scale_clump_value : bpy.props.FloatProperty(
        name=translate("Factor"), 
        default=0.3, min=0, max=1,  
        update=scattering.update_factory.factory("s_scale_clump_value", delay_support=True,),
        )

    ########## ########## Faces Special 

    s_scale_faces_allow : bpy.props.BoolProperty(
        name=translate("Face Scale Influence"), 
        description=translate("Scale each instances dependeing on the surface(s) of their faces area. The scaling factor is stable, based on the largest face area found"), 
        default=False, 
        update=scattering.update_factory.factory("s_scale_faces_allow"),
        )
    s_scale_faces_value : bpy.props.FloatProperty(
        name=translate("Multiplier"), 
        default=0.3, min=0,  
        update=scattering.update_factory.factory("s_scale_faces_value", delay_support=True,),
        )

    ########## ########## Edges Special 

    s_scale_edges_allow : bpy.props.BoolProperty(
        name=translate("Edge Scale Influence"), 
        description=translate("Scale each instances depending on their surface(s) edges length. The scaling factor is stable, based on the longest edge found"), 
        default=False, 
        update=scattering.update_factory.factory("s_scale_edges_allow"),
        )
    s_scale_edges_vec_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"), 
        default=(1.3,1.3,1.3),
        subtype="XYZ",
        soft_min=0,  
        update=scattering.update_factory.factory("s_scale_edges_vec_factor", delay_support=True,),
        )

    # 88""Yb  dP"Yb  888888    db    888888 88  dP"Yb  88b 88
    # 88__dP dP   Yb   88     dPYb     88   88 dP   Yb 88Yb88
    # 88"Yb  Yb   dP   88    dP__Yb    88   88 Yb   dP 88 Y88
    # 88  Yb  YbodP    88   dP""""Yb   88   88  YbodP  88  Y8

    ###################### This category of settings keyword is : "s_rot"

    s_rot_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_rot_main_features(self, availability_conditions=True,):
        return ["s_rot_align_z_allow", "s_rot_align_y_allow", "s_rot_random_allow", "s_rot_add_allow", "s_rot_tilt_allow",]

    s_rot_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_rot_master_allow", sync_support=False,),
        )

    ########## ########## Align Z

    s_rot_align_z_allow : bpy.props.BoolProperty(
        name=translate("Instance Normal Alignment"), 
        description=translate("Define your instance normal, also called the instance +Z axis, or instance upward direction, by aligning toward a chosen axis. Note that this feature will override the default alignment of your distribution method"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_allow"),
        )
    s_rot_align_z_method : bpy.props.EnumProperty(
        name=translate("Normal Axis"), 
        description=translate("Define your instance normal, also called the instance +Z axis, or instance upward direction, by aligning toward a chosen axis. Note that this feature will override the default alignment of your distribution method"),
        default= "meth_align_z_normal",
        items= ( ("meth_align_z_normal", translate("Surface Normal"), translate("Align each instances normals (+Z axis) toward the surface normal of the surface(s)"), "NORMALS_FACE", 0 ),
                 ("meth_align_z_local", translate("Local Z"), translate("Align each instances normals (+Z axis) toward the local +Z axis of surface(s)"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_z_global", translate("Global Z"), translate("Align each instances normals (+Z axis) toward the global +Z axis of the scene-world"), "WORLD", 2),
                 ("meth_align_z_object", translate("Object"), translate("Align each instances normals (+Z axis) toward the origin point of the chosen object"), "EYEDROPPER", 4),
                 ("meth_align_z_random", translate("Random"), translate("Align each instances normals (+Z axis) randomly"), "INIT_ICON:W_DICE", 5 ),
                 ("meth_align_z_origin", translate("Origin"), translate("Align each instances normals (+Z axis) toward the origin point of the surface(s)"),"TRACKER", 6 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_z_method"),
        )
    s_rot_align_z_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse alignment axis"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_revert"),
        )
    s_rot_align_z_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=1, #need to be different from y_random_seed otherwise axis conflict
        min=0, 
        update=scattering.update_factory.factory("s_rot_align_z_random_seed", delay_support=True, sync_support=False,),
        )
    s_rot_align_z_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_align_z_is_random_seed", alt_support=False, sync_support=False,),
        )
    s_rot_align_z_influence_allow : bpy.props.BoolProperty(
        name=translate("Vertical Influence"), 
        description=translate("Toggle this feature if you'd like your current alignment to be influenced in up/down direction"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_influence_allow"),
        )
    s_rot_align_z_influence_value : bpy.props.FloatProperty( #was 's_rot_align_z_method_mix' in beta, now legacy property 
        name=translate("Influence"), 
        description=translate("1.0 means a complete alignment with +Z. A Value of 0.0 represents no influences at all. You are able to reach for negative values as well."),
        default=0.7,
        min=-1,
        max=1,
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_z_influence_value", delay_support=True,),
        )
    s_rot_align_z_object  : bpy.props.PointerProperty(
        name=translate("Object"),
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_rot_align_z_object"),
        )
    s_rot_align_z_clump_allow : bpy.props.BoolProperty(
        description=translate("Align the clump-distribution childrens normals toward the clump center"), 
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_clump_allow"),
        )
    s_rot_align_z_clump_value : bpy.props.FloatProperty(
        name=translate("Direction"), 
        default=-0.5,
        soft_min=-2,
        soft_max=2,
        update=scattering.update_factory.factory("s_rot_align_z_clump_value", delay_support=True,),
        )

    ########## ########## Align Y

    s_rot_align_y_allow : bpy.props.BoolProperty(
        name=translate("Instance Tangent Alignment"), 
        description=translate("Define your instance tangent, also called the instance +Y axis, or instance forward direction, by aligning toward a chosen axis. Note that this feature will override the default alignment of your chosen distribution method"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_y_allow"),
        )
    s_rot_align_y_method : bpy.props.EnumProperty(
        name=translate("Tangent Axis"), 
        description=translate("Define your instance tangent, also called the instance +Y axis, or instance forward direction, by aligning toward a chosen axis. Note that this feature will override the default alignment of your chosen distribution method"),
        default= "meth_align_y_local",
        items= ( ("meth_align_y_downslope", translate("Downslope"), translate("Align each instances tangent (+Y axis) toward the slope downward direction of the surface(s)"), "SORT_ASC", 0 ),
                 ("meth_align_y_local", translate("Local Y"), translate("Align each instances tangent (+Y axis) toward the local +Y axis of the surface(s)"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_y_global", translate("Global Y"), translate("Align each instances tangent (+Y axis) toward the global +Y axis of the scene-world"), "WORLD", 2 ),
                 ("meth_align_y_boundary", translate("Boundary"), translate("Align each instances tangent (+Y axis) toward the nearest mesh boundary-edge of the surface(s)"), "MOD_EDGESPLIT", 3 ),
                 ("meth_align_y_object", translate("Object"), translate("Align each instances tangent (+Y axis) toward the origin point of the chosen object"), "EYEDROPPER", 4 ),
                 ("meth_align_y_flow", translate("Flowmap"), translate("Align each instances tangent (+Y axis) with the chosen flowmap directional information"), "ANIM", 5 ),
                 ("meth_align_y_random", translate("Random"), translate("Align each instances tangent (+Y axis) randomly"), "INIT_ICON:W_DICE", 6 ),
                 ("meth_align_y_origin", translate("Origin"), translate("Align each instances tangent (+Y axis) toward the origin point of the surface(s)"), "TRACKER", 7 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_method"),
        )
    s_rot_align_y_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse alignment axis"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_y_revert"),
        )
    s_rot_align_y_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_rot_align_y_random_seed", delay_support=True, sync_support=False,),
        )
    s_rot_align_y_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_align_y_is_random_seed", alt_support=False, sync_support=False,),
        )
    s_rot_align_y_object : bpy.props.PointerProperty(
        name=translate("Object"),
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_rot_align_y_object"),
        )
    s_rot_align_y_downslope_space : bpy.props.EnumProperty(
        name=translate("Reference"),
        description=translate("Evaluate the slope on a local or global space?"),
        default="local", 
        items= ( ("local", translate("Local"),"",  "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), "", "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_downslope_space",),
        )
    s_rot_align_y_flow_method : bpy.props.EnumProperty(
        name= translate("Flowmap Method"),  
        default= "flow_vcol",
        items= ( ("flow_vcol", translate("Vertex Colors"), translate(""), "VPAINT_HLT",0),
                 ("flow_text", translate("Texture Data"),  translate(""), "NODE_TEXTURE",1),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_flow_method"),
        )
    s_rot_align_y_flow_direction : bpy.props.FloatProperty(
        name=translate("Direction"),  
        subtype="ANGLE",
        default=0, 
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_y_flow_direction"),
        )
    s_rot_align_y_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_rot_align_y_texture_ptr",),
        )
    s_rot_align_y_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all surface(s) for shared color attributes\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vcol")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_rot_align_y_vcol_ptr",),
        )

    ########## ########## Random Rotation 

    s_rot_random_allow : bpy.props.BoolProperty(
        name=translate("Random Rotation"), 
        description=translate("Randomly rotate your instances, Yaw or Tilt available"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_random_allow"),
        )
    s_rot_random_tilt_value : bpy.props.FloatProperty(
        name=translate("Tilt"), 
        subtype="ANGLE",
        default=0.3490659,
        update=scattering.update_factory.factory("s_rot_random_tilt_value", delay_support=True,),
        )
    s_rot_random_yaw_value : bpy.props.FloatProperty(
        name=translate("Yaw"), 
        subtype="ANGLE",
        default=6.28,
        update=scattering.update_factory.factory("s_rot_random_yaw_value", delay_support=True,),
        )
    s_rot_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_rot_random_seed", delay_support=True, sync_support=False,),
        )
    s_rot_random_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_random_is_random_seed", alt_support=False, sync_support=False,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_rot_random",)

    ########## ########## Added Rotation

    s_rot_add_allow : bpy.props.BoolProperty(
        name=translate("Default Rotation Values"),
        description=translate("Rotate your instances with a defined euler rotation angle, added random and snapping options available"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_add_allow"),
        )
    s_rot_add_default : bpy.props.FloatVectorProperty(
        name=translate("Add Angle"),
        subtype="EULER",
        default=(0,0,0), 
        update=scattering.update_factory.factory("s_rot_add_default", delay_support=True,),
        )
    s_rot_add_random : bpy.props.FloatVectorProperty(
        name=translate("Add Random Angle"),
        subtype="EULER",
        default=(0,0,0), 
        update=scattering.update_factory.factory("s_rot_add_random", delay_support=True,),
        )
    s_rot_add_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_rot_add_seed", delay_support=True, sync_support=False,),
        )
    s_rot_add_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_rot_add_is_random_seed", alt_support=False, sync_support=False,),
        )
    s_rot_add_snap : bpy.props.FloatProperty(
        default=0,
        name=translate("Snap"), 
        subtype="ANGLE",
        min=0,
        soft_max=6.283185, #=360d
        update=scattering.update_factory.factory("s_rot_add_snap", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_rot_add",)

    ########## ########## Tilt

    s_rot_tilt_allow : bpy.props.BoolProperty(
        name=translate("Tilting"),
        description=translate("Tilt your instances toward a defined direction"), 
        default=False, 
        update=scattering.update_factory.factory("s_rot_tilt_allow"),
        )
    s_rot_tilt_dir_method : bpy.props.EnumProperty(
        name=translate("Direction"),  
        default="flowmap",
         items=( ("fixed", translate("Fixed"), translate("Tilt your instances uniformly toward given direction"), "CURVE_PATH", 0),
                 ("flowmap", translate("Flowmap"), translate("Tilt your instances with a given flowmap information"), "DECORATE_DRIVER", 1),
                 ("noise", translate("Noise"), translate("Tilt your instances with a generated flowmap, the flowmap is based on a simple colored noise texture"), "FORCE_VORTEX", 2),
               ),
        update=scattering.update_factory.factory("s_rot_tilt_dir_method"),
        )
    s_rot_tilt_method : bpy.props.EnumProperty(
        name=translate("Flowmap Method"),  
        default="tilt_vcol",
        items=( ("tilt_vcol", translate("Vertex Colors"), translate(""), "VPAINT_HLT", 0),
                ("tilt_text", translate("Texture Data"),  translate(""), "NODE_TEXTURE", 1),
              ),
        update=scattering.update_factory.factory("s_rot_tilt_method"),
        )
    s_rot_tilt_noise_scale : bpy.props.FloatProperty(
        name=translate("Scale"),  
        default=0.1, min=0, soft_max=2,
        update=scattering.update_factory.factory("s_rot_tilt_noise_scale"),
        )
    s_rot_tilt_direction : bpy.props.FloatProperty(
        name=translate("Direction"),
        description=translate("Rotate the tilting direction"),
        subtype="ANGLE",
        default=0,
        precision=3,
        update=scattering.update_factory.factory("s_rot_tilt_direction"),
        )
    s_rot_tilt_force : bpy.props.FloatProperty(
        name=translate("Tilt"), 
        description=translate("Define the tilting angle"),
        subtype="ANGLE",
        default=0.7,
        soft_min=-1.5708,
        soft_max=1.5708,
        update=scattering.update_factory.factory("s_rot_tilt_force"),
        )
    s_rot_tilt_blue_influence : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Influence the strength of the tilt by looking at the blue channel of the given flowmap"),
        default=1,
        soft_min=0,
        soft_max=1,
        update=scattering.update_factory.factory("s_rot_tilt_blue_influence"),
        )
    s_rot_tilt_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_rot_tilt_texture_ptr",),
        )
    s_rot_tilt_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all surface(s) for shared color attributes\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vcol")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_rot_tilt_vcol_ptr",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_rot_tilt",)

    # 88""Yb    db    888888 888888 888888 88""Yb 88b 88 .dP"Y8
    # 88__dP   dPYb     88     88   88__   88__dP 88Yb88 `Ybo."
    # 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88 o.`Y8b
    # 88     dP""""Yb   88     88   888888 88  Yb 88  Y8 8bodP'

    ###################### This category of settings keyword is : "s_pattern"
    ###################### These are per nodegroups pattern settings: other params are stored per texture data block!

    s_pattern_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_pattern_main_features(self, availability_conditions=True,):
        return ["s_pattern1_allow", "s_pattern2_allow","s_pattern3_allow",]

    s_pattern_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_pattern_master_allow", sync_support=False,),
        )

    ########## ########## Pattern Slots

    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_allow", property_type=bpy.props.BoolProperty, nbr=3, items={
        "description":translate("Influence your instances scale and density with a scatter-texture datablock"),
        "default":False,
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_texture_ptr", property_type=bpy.props.StringProperty, nbr=3, items={
        "description":"Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_color_sample_method", property_type=bpy.props.EnumProperty, nbr=3, items={
        "name":translate("Color Sampling"),
        "description":translate("Define how consider translate the color values in order to influence the distribution, by default the colors will be simply converted to black and white"),
        "default":"id_greyscale", 
        "items":( ("id_greyscale", translate("Greyscale"), "", "NONE", 0,),
                  ("id_red", translate("Red Channel"), "", "NONE", 1,),
                  ("id_green", translate("Green Channel"), "", "NONE", 2,),
                  ("id_blue", translate("Blue Channel"), "", "NONE", 3,),
                  ("id_black", translate("Pure Black"), "", "NONE", 4,),
                  ("id_white", translate("Pure White"), "", "NONE", 5,),
                  ("id_picker", translate("Color Match"), "", "NONE", 6,),
                  ("id_hue", translate("Hue"), "", "NONE", 7,),
                  ("id_saturation", translate("Saturation"), "", "NONE", 8,),
                  ("id_value", translate("Value"), "", "NONE", 9,),
                  ("id_lightness", translate("Lightness"), "", "NONE", 10,),
                  ("id_alpha", translate("Alpha Channel"), "", "NONE", 11,),
                ),
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_id_color_ptr", property_type=bpy.props.FloatVectorProperty, nbr=3, delay_support=True, items={
        "name":translate("ID Value"),
        "subtype":"COLOR",
        "min":0,
        "max":1,
        "default":(1,0,0),
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_id_color_tolerence", property_type=bpy.props.FloatProperty, nbr=3, delay_support=True, items={
        "name":translate("Tolerence"),
        "default":0.15, 
        "soft_min":0, 
        "soft_max":1,
        },)
    #Feature Influence
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_dist_infl_allow", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Enable Influence"), 
        "default":True, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_dist_influence", property_type=bpy.props.FloatProperty, nbr=3, delay_support=True, items={
        "name":translate("Density"),
        "description":translate("Influence the density of your distributed points, you'll be able to adjust the intensity of the influence by changing this slider"),
        "default":100,
        "subtype":"PERCENTAGE", 
        "min":0, 
        "max":100, 
        "precision":1, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_dist_revert", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Reverse Influence"), 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_scale_infl_allow", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Enable Influence"), 
        "default":True, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_scale_influence", property_type=bpy.props.FloatProperty, nbr=3, delay_support=True, items={
        "name":translate("Scale"),
        "description":translate("Influence the scale of your distributed points, you'll be able to adjust the intensity of the influence by changing this slider"),
        "default":70, 
        "subtype":"PERCENTAGE", 
        "min":0, 
        "max":100, 
        "precision":1, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_scale_revert", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Reverse Influence"), 
        },)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_pattern1",)
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_pattern2",)
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_pattern3",)

    #    db    88""Yb 88  dP"Yb  888888 88  dP""b8
    #   dPYb   88__dP 88 dP   Yb   88   88 dP   `"
    #  dP__Yb  88""Yb 88 Yb   dP   88   88 Yb
    # dP""""Yb 88oodP 88  YbodP    88   88  YboodP

    ###################### This category of settings keyword is : "s_abiotic"

    s_abiotic_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_abiotic_main_features(self, availability_conditions=True,):
        r = ["s_abiotic_elev_allow", "s_abiotic_slope_allow", "s_abiotic_dir_allow", "s_abiotic_cur_allow", "s_abiotic_border_allow",]
        if (not availability_conditions):
            return r
        if (self.s_distribution_method=="volume"):
            return ["s_abiotic_elev_allow",]
        return r

    s_abiotic_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_abiotic_master_allow", sync_support=False,),
        )

    ########## ########## Elevation

    s_abiotic_elev_allow : bpy.props.BoolProperty(
        description=translate("Filter instances depending on their location on the Z axis"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_elev_allow",),
        )
    s_abiotic_elev_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        description=translate("Effect space. If you'd like this effect to be stable even when the surface(s) are rotated or scaled please choose the local option. If you'd like to compute this effect on the scene-world please choose the global option."),
        default="local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate(""), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_elev_space",),
        )
    s_abiotic_elev_method : bpy.props.EnumProperty(   
        name=translate("Elevation Method"),
        default="percentage", 
        items= ( ("percentage", translate("Percentage"),translate("The altitude will be normalized from min/max altitude range found"), "INIT_ICON:W_PERCENTAGE",0 ),
                 ("altitude", translate("Altitude"), translate("Use Raw altitude unit"), "INIT_ICON:W_MEASURE_HEIGHT",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_elev_method",),
        )
    #percentage parameters (need a refactor, but would break users presets)
    s_abiotic_elev_min_value_local : bpy.props.FloatProperty(
        name=translate("Minimal"),
        subtype="PERCENTAGE",
        default=0,
        min=0, 
        max=100,  
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_value_local", delay_support=True,),
        )
    s_abiotic_elev_min_falloff_local : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="PERCENTAGE",
        default=0,
        min=0, 
        max=100, 
        soft_max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_falloff_local", delay_support=True,),
        ) 
    s_abiotic_elev_max_value_local : bpy.props.FloatProperty(
        name=translate("Maximal"),
        subtype="PERCENTAGE",
        default=75,
        min=0, 
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_value_local", delay_support=True,),
        ) 
    s_abiotic_elev_max_falloff_local : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="PERCENTAGE",
        default=5,
        min=0, 
        max=100, 
        soft_max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_falloff_local", delay_support=True,),
        )
    #altitude parameters (need a refactor, but would break users presets)
    s_abiotic_elev_min_value_global : bpy.props.FloatProperty(
        name=translate("Minimal"),
        subtype="DISTANCE",
        default=0,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_value_global", delay_support=True,),
        )
    s_abiotic_elev_min_falloff_global : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="DISTANCE",
        default=0,
        min=0, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_falloff_global", delay_support=True,),
        ) 
    s_abiotic_elev_max_value_global : bpy.props.FloatProperty(
        name=translate("Maximal"),
        subtype="DISTANCE",
        default=10,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_value_global", delay_support=True,),
        ) 
    s_abiotic_elev_max_falloff_global : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="DISTANCE",
        default=0,
        min=0, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_falloff_global", delay_support=True,),
        ) 
    #remap
    s_abiotic_elev_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_elev_fallremap_allow",),
        )
    s_abiotic_elev_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_elev_fallremap_revert",),
        )
    s_abiotic_elev_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_elev_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_elev_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_abiotic_elev_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_abiotic_elev_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_elev.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_elev.fallremap"),
        )
    #Feature Influence
    s_abiotic_elev_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_elev_dist_infl_allow",),)
    s_abiotic_elev_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_elev_dist_influence", delay_support=True,),)
    s_abiotic_elev_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_elev_dist_revert",),)
    s_abiotic_elev_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_elev_scale_infl_allow",),)
    s_abiotic_elev_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_elev_scale_influence", delay_support=True,),)
    s_abiotic_elev_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_elev_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_elev",)

    ########## ########## Slope

    s_abiotic_slope_allow : bpy.props.BoolProperty(
        description=translate("Filter instances depending on the surface(s) slope angle"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_slope_allow",),
        )
    s_abiotic_slope_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        description=translate("Effect space. If you'd like this effect to be stable even when the surface(s) are rotated or scaled please choose the local option. If you'd like to compute this effect on the scene-world please choose the global option."),
        default="local", 
        items= ( ("local", translate("Local"),"", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_slope_space",),
        )
    s_abiotic_slope_absolute : bpy.props.BoolProperty(
        default=True,
        description=translate("Consider negative slope degree values as positive"),
        update=scattering.update_factory.factory("s_abiotic_slope_absolute"),
        )
    #parameters
    s_abiotic_slope_min_value : bpy.props.FloatProperty(
        name=translate("Minimal"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_min_value", delay_support=True,),
        )
    s_abiotic_slope_min_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708, 
        soft_max=0.349066, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_min_falloff", delay_support=True,),
        ) 
    s_abiotic_slope_max_value : bpy.props.FloatProperty(
        name=translate("Maximal"),
        subtype="ANGLE",
        default=0.2617994, #15 degrees
        min=0, 
        max=1.5708,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_max_value", delay_support=True,),
        ) 
    s_abiotic_slope_max_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708, 
        soft_max=0.349066, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_max_falloff", delay_support=True,),
        ) 
    #remap
    s_abiotic_slope_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_slope_fallremap_allow",),
        )
    s_abiotic_slope_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_slope_fallremap_revert",),
        )
    s_abiotic_slope_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_slope_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_slope_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_abiotic_slope_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_abiotic_slope_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_slope.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_slope.fallremap"),
        )
    #Feature Influence
    s_abiotic_slope_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_slope_dist_infl_allow",),)
    s_abiotic_slope_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_slope_dist_influence", delay_support=True,),)
    s_abiotic_slope_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_slope_dist_revert",),)
    s_abiotic_slope_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_slope_scale_infl_allow",),)
    s_abiotic_slope_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_slope_scale_influence", delay_support=True,),)
    s_abiotic_slope_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_slope_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_slope",)

    ########## ########## Direction

    s_abiotic_dir_allow : bpy.props.BoolProperty(
        description=translate("Filter instances depending on the surface(s) orientation"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_dir_allow",),
        )
    s_abiotic_dir_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        description=translate("Effect space. If you'd like this effect to be stable even when the surface(s) are rotated or scaled please choose the local option. If you'd like to compute this effect on the scene-world please choose the global option."),
        default="local", 
        items= ( ("local", translate("Local"),"", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_dir_space",),
        )
    s_abiotic_dir_direction : bpy.props.FloatVectorProperty(
        default=(0.701299, 0.493506, 0.514423),
        subtype="DIRECTION",
        update=scattering.update_factory.factory("s_abiotic_dir_direction", delay_support=True,),
        )
    s_abiotic_dir_direction_euler : bpy.props.FloatVectorProperty( 
        subtype="EULER",
        update=upd_euler_to_direction_prop("s_abiotic_dir_direction_euler", "s_abiotic_dir_direction",),
        )

    s_abiotic_dir_max : bpy.props.FloatProperty(
        name=translate("Maximal"),
        subtype="ANGLE",
        default=0.261799,
        soft_min=0, 
        soft_max=1, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_max", delay_support=True,),
        ) 
    s_abiotic_dir_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        subtype="ANGLE",
        default=0.0872665,
        soft_min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_treshold", delay_support=True,),
        ) 
    #remap
    s_abiotic_dir_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_dir_fallremap_allow",),
        )
    s_abiotic_dir_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_dir_fallremap_revert",),
        )
    s_abiotic_dir_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_dir_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_dir_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_abiotic_dir_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_abiotic_dir_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_dir.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_dir.fallremap"),
        )
    #Feature Influence
    s_abiotic_dir_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_dir_dist_infl_allow",),)
    s_abiotic_dir_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_dir_dist_influence", delay_support=True,),)
    s_abiotic_dir_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_dir_dist_revert",),)
    s_abiotic_dir_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_dir_scale_infl_allow",),)
    s_abiotic_dir_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_dir_scale_influence", delay_support=True,),)
    s_abiotic_dir_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_dir_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_dir",)

    ########## ########## Edge Curvature

    s_abiotic_cur_allow : bpy.props.BoolProperty(
        description=translate("Filter instances depending on the surface(s) curvature angle (concavity or convexity or both). Note that this feature might be slow to compute if your emitter terrain has a lot of polygons."),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_cur_allow",),
        )
    s_abiotic_cur_type : bpy.props.EnumProperty(   
        name=translate("Type"),
        default="convex", 
        items= ( ("convex", translate("Convex"), translate("Use convex angles, areas rounding outward"), "SPHERECURVE",0 ),
                 ("concave", translate("Concave"), translate("Use concave angles, areas rounding inward"), "SHARPCURVE",1 ),
                 ("both", translate("Curvature"), translate("Use both concave and convex angles"), "FORCE_HARMONIC",2 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_cur_type",),
        )
    s_abiotic_cur_max: bpy.props.FloatProperty(
        name=translate("Maximal"),
        default=55,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_max", delay_support=True,),
        )
    s_abiotic_cur_treshold: bpy.props.FloatProperty(
        name=translate("Transition"),
        default=0,
        subtype="PERCENTAGE",
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_treshold", delay_support=True,),
        )
    #remap
    s_abiotic_cur_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_cur_fallremap_allow",),
        )
    s_abiotic_cur_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_cur_fallremap_revert",),
        )
    s_abiotic_cur_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_cur_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_cur_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_abiotic_cur_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_abiotic_cur_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_cur.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_cur.fallremap"),
        )
    #Feature Influence
    s_abiotic_cur_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_cur_dist_infl_allow",),)
    s_abiotic_cur_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_cur_dist_influence", delay_support=True,),)
    s_abiotic_cur_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_cur_dist_revert",),)
    s_abiotic_cur_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_cur_scale_infl_allow",),)
    s_abiotic_cur_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_cur_scale_influence", delay_support=True,),)
    s_abiotic_cur_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_cur_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_cur",)

    ########## ########## Edge Border

    s_abiotic_border_allow : bpy.props.BoolProperty(
        description=translate("Filter instances depending on how close they are from the surface(s) mesh boundary edges"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_border_allow",),
        )
    s_abiotic_border_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        default="local", 
        items= ( ("local", translate("Local"),"", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_border_space",),
        )
    s_abiotic_border_max : bpy.props.FloatProperty(
        name=translate("Minimal"), #too late to change property name
        description=translate("Minimal distance defining the border range."),
        default=1,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_abiotic_border_max", delay_support=True,),
        )
    s_abiotic_border_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a transition distance after the maximal distance defined."),
        default=0.5,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_abiotic_border_treshold", delay_support=True,),
        )
    #remap
    s_abiotic_border_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_border_fallremap_allow",),
        )
    s_abiotic_border_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_border_fallremap_revert",),
        )
    s_abiotic_border_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_border_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_border_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_abiotic_border_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_abiotic_border_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_border.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_border.fallremap"),
        )
    #Feature Influence
    s_abiotic_border_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_border_dist_infl_allow",),)
    s_abiotic_border_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_border_dist_influence", delay_support=True,),)
    s_abiotic_border_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_border_dist_revert",),)
    s_abiotic_border_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_border_scale_infl_allow",),)
    s_abiotic_border_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_border_scale_influence", delay_support=True,),)
    s_abiotic_border_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_border_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_border",)

    #Edge Watershed Later? 

    #Edge Data Later ? 
    
    # 88""Yb 88""Yb  dP"Yb  Yb  dP 88 8b    d8 88 888888 Yb  dP
    # 88__dP 88__dP dP   Yb  YbdP  88 88b  d88 88   88    YbdP
    # 88"""  88"Yb  Yb   dP  dPYb  88 88YbdP88 88   88     8P
    # 88     88  Yb  YbodP  dP  Yb 88 88 YY 88 88   88    dP

    ###################### This category of settings keyword is : "s_proximity"

    s_proximity_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_proximity_main_features(self, availability_conditions=True,):
        return ["s_proximity_repel1_allow", "s_proximity_repel2_allow", "s_proximity_outskirt_allow",]

    s_proximity_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_proximity_master_allow", sync_support=False,),
        )

    ########## ########## Object-Repel 1

    s_proximity_repel1_allow : bpy.props.BoolProperty( 
        description=translate("Influence instances density/scale/orientations depending on how close/far they are from the items contained in chosen collection"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel1_allow",),
        )
    #treshold
    s_proximity_repel1_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        update=scattering.update_factory.factory("s_proximity_repel1_coll_ptr"),
        )
    passctxt_s_proximity_repel1_coll_ptr : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)
    s_proximity_repel1_type : bpy.props.EnumProperty(   
        name=translate("Proximity Contact"),
        default="mesh", 
        items= ( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far, the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),
                 ("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),
                 ("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),
                 ("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),
                 ("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 )
               ),
        update=scattering.update_factory.factory("s_proximity_repel1_type",),
        )
    s_proximity_repel1_volume_allow : bpy.props.BoolProperty( 
        description=translate("Only keep areas located inside or outside the volumes of the chosen objects.\nNote that the reverse influence toggle will not be able to reverse this effect."),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel1_volume_allow",),
        )
    s_proximity_repel1_volume_method : bpy.props.EnumProperty(   
        default="out",
        items= ( ("in",  translate("Inside"), translate("Only keep areas located inside or outside the volumes of the chosen objects.\nNote that the reverse influence toggle will not be able to reverse this effect."),"",0), 
                 ("out", translate("Outside"),translate("Only keep areas located inside or outside the volumes of the chosen objects.\nNote that the reverse influence toggle will not be able to reverse this effect."),"",1)
               ),
        update=scattering.update_factory.factory("s_proximity_repel1_volume_method",),
        )
    s_proximity_repel1_max : bpy.props.FloatProperty(
        name=translate("Minimal"), #too late to change property name
        description=translate("Minimal distance reached until the transition starts"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel1_max", delay_support=True,),
        )
    s_proximity_repel1_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("The transition distance will attenuate the influence of this effect over the scatter"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel1_treshold", delay_support=True,),
        )
    #remap
    s_proximity_repel1_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel1_fallremap_allow",),
        )
    s_proximity_repel1_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel1_fallremap_revert",),
        )
    s_proximity_repel1_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_strength", delay_support=True,),
        )
    s_proximity_repel1_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_scale", delay_support=True,),
        )
    s_proximity_repel1_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_proximity_repel1_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_proximity_repel1_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_proximity_repel1.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_proximity_repel1.fallremap"),
        )
    #Feature Influence
    s_proximity_repel1_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_repel1_dist_infl_allow",),)
    s_proximity_repel1_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_dist_influence", delay_support=True,),)
    s_proximity_repel1_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_dist_revert",),)
    s_proximity_repel1_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel1_scale_infl_allow",),)
    s_proximity_repel1_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=0, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_scale_influence", delay_support=True,),)
    s_proximity_repel1_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_scale_revert",),)
    s_proximity_repel1_nor_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel1_nor_infl_allow",),)
    s_proximity_repel1_nor_influence: bpy.props.FloatProperty(name=translate("Normal"), default=0, subtype="PERCENTAGE", soft_min=-100, soft_max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_nor_influence", delay_support=True,),)
    s_proximity_repel1_nor_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_nor_revert",),)
    s_proximity_repel1_tan_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel1_tan_infl_allow",),)
    s_proximity_repel1_tan_influence: bpy.props.FloatProperty(name=translate("Tangent"), default=0, subtype="PERCENTAGE", soft_min=-100, soft_max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_tan_influence", delay_support=True,),)
    s_proximity_repel1_tan_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_tan_revert",),)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_proximity_repel1",)

    ########## ########## Object-Repel 2

    s_proximity_repel2_allow : bpy.props.BoolProperty( 
        description=translate("Influence instances density/scale/orientations depending on how close/far they are from the items contained in chosen collection"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel2_allow",),
        )
    #treshold
    s_proximity_repel2_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        update=scattering.update_factory.factory("s_proximity_repel2_coll_ptr"),
        )
    passctxt_s_proximity_repel2_coll_ptr : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)
    s_proximity_repel2_type : bpy.props.EnumProperty(   
        name=translate("Proximity Contact"),
        default="mesh", 
        items= ( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far, the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),
                 ("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),
                 ("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),
                 ("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),
                 ("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 )
               ),
        update=scattering.update_factory.factory("s_proximity_repel2_type",),
        )
    s_proximity_repel2_volume_allow : bpy.props.BoolProperty( 
        description=translate("Only keep areas located inside or outside the volumes of the chosen objects.\nNote that the reverse influence toggle will not be able to reverse this effect."),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel2_volume_allow",),
        )
    s_proximity_repel2_volume_method : bpy.props.EnumProperty(   
        default="out",
        items= ( ("in",  translate("Inside"), translate("Only keep areas located inside or outside the volumes of the chosen objects.\nNote that the reverse influence toggle will not be able to reverse this effect."),"",0), 
                 ("out", translate("Outside"),translate("Only keep areas located inside or outside the volumes of the chosen objects.\nNote that the reverse influence toggle will not be able to reverse this effect."),"",1)
               ),
        update=scattering.update_factory.factory("s_proximity_repel2_volume_method",),
        )
    s_proximity_repel2_max : bpy.props.FloatProperty(
        name=translate("Minimal"), #too late to change property name
        description=translate("Minimal distance reached until the transition starts"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel2_max", delay_support=True,),
        )
    s_proximity_repel2_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("The transition distance will attenuate the influence of this effect over the scatter"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel2_treshold", delay_support=True,),
        )
    #remap
    s_proximity_repel2_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel2_fallremap_allow",),
        )
    s_proximity_repel2_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel2_fallremap_revert",),
        )
    s_proximity_repel2_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_strength", delay_support=True,),
        )
    s_proximity_repel2_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_scale", delay_support=True,),
        )
    s_proximity_repel2_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_proximity_repel2_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_proximity_repel2_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_proximity_repel2.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_proximity_repel2.fallremap"),
        )
    #Feature Influence
    s_proximity_repel2_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_repel2_dist_infl_allow",),)
    s_proximity_repel2_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_dist_influence", delay_support=True,),)
    s_proximity_repel2_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_dist_revert",),)
    s_proximity_repel2_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel2_scale_infl_allow",),)
    s_proximity_repel2_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=0, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_scale_influence", delay_support=True,),)
    s_proximity_repel2_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_scale_revert",),)
    s_proximity_repel2_nor_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel2_nor_infl_allow",),)
    s_proximity_repel2_nor_influence: bpy.props.FloatProperty(name=translate("Normal"), default=0, subtype="PERCENTAGE", soft_min=-100, soft_max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_nor_influence", delay_support=True,),)
    s_proximity_repel2_nor_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_nor_revert",),)
    s_proximity_repel2_tan_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel2_tan_infl_allow",),)
    s_proximity_repel2_tan_influence: bpy.props.FloatProperty(name=translate("Tangent"), default=0, subtype="PERCENTAGE", soft_min=-100, soft_max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_tan_influence", delay_support=True,),)
    s_proximity_repel2_tan_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_tan_revert",),)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_proximity_repel2",)

    ########## ########## Outskirt 

    s_proximity_outskirt_allow : bpy.props.BoolProperty(
        name=translate("Outskirt Transition"), 
        description=translate("Procedurally create a transition effect at the outskirts of your distribution. The outskirt areas are the areas located in the outer part of the distribution.\n\nNote that it is easier to identify outskirts if the distribution abrubtly ends, if the distribution already has a smooth transition toward points-free zones the algorithm will have more difficulty finding these areas.\n\nNote that this feature is much slower to compute than usual."),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_outskirt_allow",),
        )
    s_proximity_outskirt_detection : bpy.props.FloatProperty(
        name=translate("Distance"),
        description=translate("Minimal distance between points in order to recognize grouped points areas"),
        default=0.7,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_detection", delay_support=True,),
        )
    s_proximity_outskirt_precision : bpy.props.FloatProperty(
        name=translate("Precision"),
        description=translate("Precision of the algorithm will, more precision means slower performances"),
        default=0.7,
        min=0.1,
        max=1,
        update=scattering.update_factory.factory("s_proximity_outskirt_precision", delay_support=True,),
        )
    s_proximity_outskirt_max : bpy.props.FloatProperty(
        name=translate("Minimal"), #too late to change property name
        description=translate("Minimal distance reached until the transition starts"),
        default=0,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_max", delay_support=True,),
        )
    s_proximity_outskirt_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        default=2,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_treshold", delay_support=True,),
        )
    #remap
    s_proximity_outskirt_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_outskirt_fallremap_allow",),
        )
    s_proximity_outskirt_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_proximity_outskirt_fallremap_revert",),
        )
    s_proximity_outskirt_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_strength", delay_support=True,),
        )
    s_proximity_outskirt_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_scale", delay_support=True,),
        )
    s_proximity_outskirt_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_proximity_outskirt_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_proximity_outskirt_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_proximity_outskirt.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_proximity_outskirt.fallremap"),
        )
    #Feature Influence
    s_proximity_outskirt_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_outskirt_dist_infl_allow",),)
    s_proximity_outskirt_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_dist_influence", delay_support=True,),)
    s_proximity_outskirt_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_dist_revert",),)
    s_proximity_outskirt_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_outskirt_scale_infl_allow",),)
    s_proximity_outskirt_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=70, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_scale_influence", delay_support=True,),)
    s_proximity_outskirt_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_scale_revert",),)
    # s_proximity_outskirt_nor_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_outskirt_nor_infl_allow",),)
    # s_proximity_outskirt_nor_influence: bpy.props.FloatProperty(name=translate("Normal"), default=0, subtype="PERCENTAGE", soft_min=-100, soft_max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_nor_influence", delay_support=True,),)
    # s_proximity_outskirt_nor_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_nor_revert",),)
    # s_proximity_outskirt_tan_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_outskirt_tan_infl_allow",),)
    # s_proximity_outskirt_tan_influence: bpy.props.FloatProperty(name=translate("Tangent"), default=0, subtype="PERCENTAGE", soft_min=-100, soft_max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_tan_influence", delay_support=True,),)
    # s_proximity_outskirt_tan_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_tan_revert",),)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_proximity_outskirt",)

    #Curves for 5.1?

    # s_proximity_curve_allow : bpy.props.BoolProperty( 
    #     name=translate("Proximity by Bezier-Curve"), 
    #     default=False, 
    #     update=scattering.update_factory.factory("s_proximity_curve_allow",),
    #     )

    # 888888  dP""b8  dP"Yb  .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88__   dP   `" dP   Yb `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88""   Yb      Yb   dP o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 888888  YboodP  YbodP  8bodP'  dP    8bodP'   88   888888 88 YY 88

    ###################### This category of settings keyword is : "s_ecosystem"

    s_ecosystem_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_ecosystem_main_features(self, availability_conditions=True,):
        return ["s_ecosystem_affinity_allow", "s_ecosystem_repulsion_allow",]

    s_ecosystem_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_ecosystem_master_allow", sync_support=False,),
        )

    def get_s_ecosystem_psy_match(self, context, edit_text):
        """return list of local scatter-systems, used for prop_search"""
        
        return [ p.name for p in self.id_data.scatter5.particle_systems if ((edit_text in p.name) and (p.name!=self.name)) ]

    ########## ##########  Affinity

    s_ecosystem_affinity_allow : bpy.props.BoolProperty(
        name=translate("Ecosystem Affinity"), 
        description=translate("Generate dynamic ecosystems with the help of affinity rules. Define if this scatter-system need to be located only around other scatter-system(s)"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_affinity_allow",),
        )
    s_ecosystem_affinity_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("The ecosystem features are based on distance unit, Would you like to sample this distance in the global scene space, or at a local object space? If you'd like to have a stable distribution while the surface(s) are re-scaled, please choose the local option"),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_affinity_space"),
        )
    #slots properties
    s_ecosystem_affinity_ui_max_slot : bpy.props.IntProperty(default=1,max=3,min=1)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_ptr", nbr=3, items={"name":translate("Scatter System"),"search":get_s_ecosystem_psy_match,"search_options":{'SUGGESTION','SORT'}}, property_type=bpy.props.StringProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_type", nbr=3, items={"name":translate("Proximity Contact"),"default":"origin","items":( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far, the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 )),}, property_type=bpy.props.EnumProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_max_value", nbr=3, items={"name":translate("Minimal"),"description":translate("Minimal distance reached until the transition starts"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_max_falloff", nbr=3, items={"name":translate("Transition"),"description":translate("The transition distance will attenuate the influence of this effect over the scatter"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_limit_distance", nbr=3, items={"name":translate("Limit Collision"),"description":translate("Avoid instances nearby the chosen scatter-system instances"),"default":0,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    #remap
    s_ecosystem_affinity_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallremap_allow",),
        )
    s_ecosystem_affinity_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallremap_revert",),
        )
    s_ecosystem_affinity_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_strength", delay_support=True,),
        )
    s_ecosystem_affinity_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_scale", delay_support=True,),
        )
    s_ecosystem_affinity_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_ecosystem_affinity_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_ecosystem_affinity_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_ecosystem_affinity.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_ecosystem_affinity.fallremap"),
        )
    #Feature Influence
    s_ecosystem_affinity_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_affinity_dist_infl_allow",),)
    s_ecosystem_affinity_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_affinity_dist_influence", delay_support=True,),)
    s_ecosystem_affinity_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_affinity_scale_infl_allow",),)
    s_ecosystem_affinity_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=50, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_affinity_scale_influence", delay_support=True,),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_ecosystem_affinity",)

    ########## ##########  Repulsion

    s_ecosystem_repulsion_allow : bpy.props.BoolProperty(
        name=translate("Ecosystem Repulsion"), 
        description=translate("Generate dynamic ecosystems with the help of repulsion rules. Define if this scatter-system needs to avoid being near other scatter-system(s)"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_repulsion_allow",),
        )
    s_ecosystem_repulsion_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("The ecosystem features are based on distance unit, Would you like to sample this distance in the global scene space, or at a local object space? If you'd like to have a stable distribution while the surface(s) are re-scaled, please choose the local option."),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_repulsion_space"),
        )
    #slots properties
    s_ecosystem_repulsion_ui_max_slot : bpy.props.IntProperty(default=1,max=3,min=1)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_ptr", nbr=3, items={"name":translate("Scatter System"),"search":get_s_ecosystem_psy_match,"search_options":{'SUGGESTION','SORT'}}, property_type=bpy.props.StringProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_type", nbr=3, items={"name":translate("Proximity Contact"),"default":"origin","items":( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far, the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 ),),}, property_type=bpy.props.EnumProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_max_value", nbr=3, items={"name":translate("Minimal"),"description":translate("Minimal distance reached until the transition starts"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_max_falloff", nbr=3, items={"name":translate("Transition"),"description":translate("The transition distance will attenuate the influence of this effect over the scatter"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    #remap
    s_ecosystem_repulsion_fallremap_allow : bpy.props.BoolProperty(
        description=translate("Control the transition falloff by remapping the values"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallremap_allow",),
        )
    s_ecosystem_repulsion_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallremap_revert",),
        )
    s_ecosystem_repulsion_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Overlay the distance transition with a defined noise. Great to make the transition looks less uniform and more natural. Set this value to 0 in order to disable the feature."),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_strength", delay_support=True,),
        )
    s_ecosystem_repulsion_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"), 
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_scale", delay_support=True,),
        )
    s_ecosystem_repulsion_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        min=0,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_seed", delay_support=True, sync_support=False,)
        )
    s_ecosystem_repulsion_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_is_random_seed", alt_support=False, sync_support=False,)
        )
    s_ecosystem_repulsion_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_ecosystem_repulsion.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_ecosystem_repulsion.fallremap"),
        )
    #Feature Influence
    s_ecosystem_repulsion_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_repulsion_dist_infl_allow",),)
    s_ecosystem_repulsion_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distributed points density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_repulsion_dist_influence", delay_support=True,),)
    s_ecosystem_repulsion_scale_infl_allow : bpy.props.BoolProperty(name=translate("Allow Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_repulsion_scale_infl_allow",),)
    s_ecosystem_repulsion_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed points scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=50, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_repulsion_scale_influence", delay_support=True,),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_ecosystem_repulsion",)

    # 88""Yb 88   88 .dP"Y8 88  88
    # 88__dP 88   88 `Ybo." 88  88
    # 88"""  Y8   8P o.`Y8b 888888
    # 88     `YbodP' 8bodP' 88  88

    ###################### This category of settings keyword is : "s_push"

    s_push_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_push_main_features(self, availability_conditions=True,):
        return ["s_push_offset_allow", "s_push_dir_allow", "s_push_noise_allow", "s_push_fall_allow",]

    s_push_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_push_master_allow", sync_support=False,),
        )

    ########## ########## Push Offset

    s_push_offset_allow : bpy.props.BoolProperty(
        description=translate("Transform the positions of your instances in space"),
        default=False,
        update=scattering.update_factory.factory("s_push_offset_allow",),
        )
    s_push_offset_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Are transformations based on local or global space? If you'd like this effect to be stable when the object is being animated, please choose the local option."),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_push_offset_space"),
        )
    s_push_offset_add_value : bpy.props.FloatVectorProperty(
        name=translate("Offset"),
        default=(0,0,0),
        subtype="XYZ",
        unit="LENGTH",
        update=scattering.update_factory.factory("s_push_offset_add_value", delay_support=True,),
        )
    s_push_offset_add_random : bpy.props.FloatVectorProperty(
        name=translate("Random"),
        default=(0,0,0),
        subtype="XYZ",
        unit="LENGTH",
        update=scattering.update_factory.factory("s_push_offset_add_random", delay_support=True,),
        )
    s_push_offset_rotate_value : bpy.props.FloatVectorProperty(
        name=translate("Rotate"),
        default=(0,0,0),
        subtype="XYZ",
        unit="ROTATION",
        update=scattering.update_factory.factory("s_push_offset_rotate_value", delay_support=True,),
        )
    s_push_offset_rotate_random : bpy.props.FloatVectorProperty(
        name=translate("Random"),
        default=(0,0,0),
        subtype="XYZ",
        unit="ROTATION",
        update=scattering.update_factory.factory("s_push_offset_rotate_random", delay_support=True,),
        )
    s_push_offset_scale_value : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        default=(1,1,1),
        subtype="XYZ",
        update=scattering.update_factory.factory("s_push_offset_scale_value", delay_support=True,),
        )
    s_push_offset_scale_random : bpy.props.FloatVectorProperty(
        name=translate("Random"),
        default=(0,0,0),
        subtype="XYZ",
        update=scattering.update_factory.factory("s_push_offset_scale_random", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_offset",)

    ########## ########## Push Direction

    s_push_dir_allow : bpy.props.BoolProperty(
        description=translate("Push your instances along a defined axis"),
        default=False,
        update=scattering.update_factory.factory("s_push_dir_allow",),
        )
    s_push_dir_method : bpy.props.EnumProperty(
         name=translate("Axis"),
         default= "push_normal", 
         items= ( ("push_normal", translate("Surface Normal"), "", "NORMALS_FACE", 0),
                  ("push_point",  translate("Instances Normal"), "", "SNAP_NORMAL", 1),
                  ("push_local",  translate("Local Z"), "", "ORIENTATION_LOCAL", 2),
                  ("push_global", translate("Global Z"), "", "WORLD", 3),
                  # more for 5.1?
                ),
         update=scattering.update_factory.factory("s_push_dir_method"),
         )
    s_push_dir_add_value : bpy.props.FloatProperty(
        name=translate("Reach"),
        default=1,
        precision=3,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_dir_add_value", delay_support=True,),
        )
    s_push_dir_add_random : bpy.props.FloatProperty(
        name=translate("Random"),
        default=0,
        precision=3,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_dir_add_random", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_dir",)

    #more method for 5.1 ?

    # s_push_dir_object_ptr  : bpy.props.PointerProperty(
    #     name=translate("Object"),
    #     type=bpy.types.Object, 
    #     update=scattering.update_factory.factory("s_push_dir_object_ptr"),
    #     )
    # s_push_dir_normalize : bpy.props.BoolProperty(
    #     name=translate("Vector Normalization"),
    #     default=True,
    #     update=scattering.update_factory.factory("s_push_dir_normalize"),
    #     )
    # s_push_dir_custom_direction : bpy.props.FloatVectorProperty(
    #     default=(0,0,1),
    #     subtype="DIRECTION",
    #     update=scattering.update_factory.factory("s_push_dir_custom_direction", delay_support=True,),
    #     )

    ########## ########## Push Noise 

    s_push_noise_allow : bpy.props.BoolProperty(
        description=translate("Add a random animated noise to the locations of instances in space"),
        default=False,
        update=scattering.update_factory.factory("s_push_noise_allow"),
        )
    s_push_noise_vector : bpy.props.FloatVectorProperty(
        name=translate("Spread"),
        default=(1,1,1),
        subtype="XYZ_LENGTH",
        update=scattering.update_factory.factory("s_push_noise_vector", delay_support=True,),
        )
    s_push_noise_speed : bpy.props.FloatProperty(
        name=translate("Speed"),
        default=1,
        soft_min=0,
        soft_max=5,
        update=scattering.update_factory.factory("s_push_noise_speed", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_noise",)

    ########## ########## Fall Effect

    s_push_fall_allow : bpy.props.BoolProperty(
        description=translate("Add an animated leaf falling effect on your instances locations"),
        default=False,
        update=scattering.update_factory.factory("s_push_fall_allow"),
        )
    s_push_fall_height : bpy.props.FloatProperty(
        name=translate("Fall Distance"),
        default=20,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_height", delay_support=True,),
        )
    s_push_fall_key1_pos : bpy.props.IntProperty(
        name=translate("Frame"),
        default=0,
        update=scattering.update_factory.factory("s_push_fall_key1_pos", delay_support=True,),
        )
    s_push_fall_key1_height : bpy.props.FloatProperty(
        name=translate("Height"),
        default=5,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_key1_height", delay_support=True,),
        )
    s_push_fall_key2_pos : bpy.props.IntProperty(
        name=translate("Frame"),
        default=100,
        update=scattering.update_factory.factory("s_push_fall_key2_pos", delay_support=True,),
        )
    s_push_fall_key2_height : bpy.props.FloatProperty(
        name=translate("Height"),
        default=-5,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_key2_height", delay_support=True,),
        )
    s_push_fall_stop_when_initial_z : bpy.props.BoolProperty(
        default=True,
        update=scattering.update_factory.factory("s_push_fall_stop_when_initial_z"),
        )
    s_push_fall_turbulence_allow : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_push_fall_turbulence_allow"),
        )
    s_push_fall_turbulence_spread : bpy.props.FloatVectorProperty(
        name=translate("Spread"),
        default=(1.0,1.0,0.5),
        subtype="XYZ_LENGTH",
        update=scattering.update_factory.factory("s_push_fall_turbulence_spread", delay_support=True,),
        )
    s_push_fall_turbulence_speed : bpy.props.FloatProperty(
        name=translate("Speed"),
        default=1,
        min=0,
        soft_max=4,
        update=scattering.update_factory.factory("s_push_fall_turbulence_speed", delay_support=True,),
        )
    s_push_fall_turbulence_rot_vector : bpy.props.FloatVectorProperty(
        name=translate("Rotation"),
        default=(0.5,0.5,0.5),
        subtype="EULER",
        update=scattering.update_factory.factory("s_push_fall_turbulence_rot_vector", delay_support=True,),
        )
    s_push_fall_turbulence_rot_factor : bpy.props.FloatProperty(
        name=translate("Rotation Factor"),
        default=1,
        soft_min=0,
        soft_max=1,
        update=scattering.update_factory.factory("s_push_fall_turbulence_rot_factor", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_fall",)

    # Yb        dP 88 88b 88 8888b.  
    #  Yb  db  dP  88 88Yb88  8I  Yb 
    #   YbdPYbdP   88 88 Y88  8I  dY 
    #    YP  YP    88 88  Y8 8888Y"  

    ###################### This category of settings keyword is : "s_wind"

    s_wind_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_wind_main_features(self, availability_conditions=True,):
        return ["s_wind_wave_allow", "s_wind_noise_allow",]

    s_wind_master_allow : bpy.props.BoolProperty(
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_wind_master_allow", sync_support=False,),
        )

    ########## ########## Wind Wave

    s_wind_wave_allow : bpy.props.BoolProperty(
        description=translate("Add a wind-wave effects by tilting the normals of your instances. An animated noise texture will be used to control the wind wave aspect and speed"),
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_allow",),
        )
    s_wind_wave_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("If the wind direction should be parented to the surface(s) space please choose local, if the wind direction should be uniform across all surface(s) please choose the global option"),
        default= "global", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_wind_wave_space"),
        )

    s_wind_wave_method : bpy.props.EnumProperty(
        name=translate("Animation"),
        default= "wind_wave_constant", 
        items= ( ("wind_wave_constant", translate("Fixed"), translate("The wind animation seed is reliable, fixed in time with no regard to loop-ability"), "TRACKING_FORWARDS_SINGLE", 0,),
                 ("wind_wave_loopable", translate("Loop-able"), translate("The wind animation will seamlessly loop itself. The loop automatically adapts to your clip length, changing the clip start/end frames will recalculate the loop"), "MOD_DASH", 1,),
               ),
        update=scattering.update_factory.factory("s_wind_wave_method",),
        ) 
    s_wind_wave_loopable_cliplength_allow : bpy.props.BoolProperty(
        default=False,
        description=translate("By default the animation loop will automatically adapt & recalculate depending on your start/end frames. Use this option if you'd like to define the min/max frames yourself"),
        update=scattering.update_factory.factory("s_wind_wave_loopable_cliplength_allow"),
        )
    s_wind_wave_loopable_frame_start : bpy.props.IntProperty(
        min=0, default=0,
        update=scattering.update_factory.factory("s_wind_wave_loopable_frame_start", delay_support=True,),
        )
    s_wind_wave_loopable_frame_end : bpy.props.IntProperty(
        min=0, default=200,
        update=scattering.update_factory.factory("s_wind_wave_loopable_frame_end", delay_support=True,),
        )

    s_wind_wave_speed : bpy.props.FloatProperty(
        name=translate("Speed"), 
        default=1.0, 
        soft_min=0.001, 
        soft_max=5, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_speed", delay_support=True,),
        )
    s_wind_wave_force : bpy.props.FloatProperty(
        name=translate("Strength"), 
        default=1, 
        soft_min=0, 
        soft_max=3, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_force", delay_support=True,),
        )
    s_wind_wave_swinging : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_swinging",),
        description=translate("The wind effect will swing particle back and forth instead of unilaterally inclining them"),
        )
    s_wind_wave_scale_influence : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_scale_influence",),
        description=translate("Smaller/taller instances are less/more affected by the wind force"),
        )
    s_wind_wave_texture_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.1,
        update=scattering.update_factory.factory("s_wind_wave_texture_scale", delay_support=True,),
        )
    s_wind_wave_texture_turbulence : bpy.props.FloatProperty(
        name=translate("Turbulence"),
        default=0,
        soft_min=0,
        soft_max=10,
        update=scattering.update_factory.factory("s_wind_wave_texture_turbulence", delay_support=True,),
        )
    s_wind_wave_texture_distorsion : bpy.props.FloatProperty(
        name=translate("Distortion"),
        default=0,
        soft_min=0,
        soft_max=3,
        update=scattering.update_factory.factory("s_wind_wave_texture_distorsion", delay_support=True,),
        )
    s_wind_wave_texture_brightness : bpy.props.FloatProperty(
        name=translate("Brightness"),
        default=1,
        min=0, 
        soft_max=2,
        update=scattering.update_factory.factory("s_wind_wave_texture_brightness", delay_support=True,),
        )
    s_wind_wave_texture_contrast : bpy.props.FloatProperty(
        name=translate("Contrast"),
        default=1.5,
        min=0, 
        soft_max=5,
        update=scattering.update_factory.factory("s_wind_wave_texture_contrast", delay_support=True,),
        )

    s_wind_wave_dir_method : bpy.props.EnumProperty(
         name=translate("Wind Direction"),
         description=translate("Direction of the tilt effect and wind wave texture translation"),
         default= "fixed", 
         items= ( ("fixed", translate("Fixed Direction"), "", "CURVE_PATH", 0),
                  ("vcol",  translate("Vertex-Color Flowmap"), "", "DECORATE_DRIVER", 1),
                ),
         update=scattering.update_factory.factory("s_wind_wave_dir_method"),
         )
    s_wind_wave_direction : bpy.props.FloatProperty(
        name=translate("Direction"), 
        subtype="ANGLE",
        default=0.87266, 
        soft_min=-6.283185, 
        soft_max=6.283185, #=360d
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_direction", delay_support=True,),
        )
    s_wind_wave_flowmap_ptr : bpy.props.StringProperty(
        default="",
        update=scattering.update_factory.factory("s_wind_wave_flowmap_ptr"),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_wind_wave",)

    ########## ########## Wind Noise

    s_wind_noise_allow : bpy.props.BoolProperty(
        description=translate("Add a random turbulence wind-noise effect by tilting the instances back-and-forth at a random rate"),
        default=False,
        update=scattering.update_factory.factory("s_wind_noise_allow",),
        )
    s_wind_noise_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("If the wind direction should be parented to the surface(s) space please choose local, if the wind direction should be uniform across all surface(s) please choose the global option"),
        default= "global", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate(""), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_wind_noise_space"),
        )

    s_wind_noise_method : bpy.props.EnumProperty(
        name=translate("Animation"),
        default= "wind_noise_constant", 
        items= ( ("wind_noise_constant", translate("Fixed"), translate("The wind animation seed is reliable, fixed in time with no regard to loop-ability"), "TRACKING_FORWARDS_SINGLE", 0,),
                 ("wind_noise_loopable", translate("Loop-able"), translate("The wind animation will seamlessly loop itself. The loop automatically adapts to your clip length, changing the clip start/end frames will recalculate the loop"), "MOD_DASH", 1,),
               ),
        update=scattering.update_factory.factory("s_wind_noise_method"),
        ) 
    s_wind_noise_loopable_cliplength_allow : bpy.props.BoolProperty(
        default=False,
        description=translate("By default the animation loop will automatically adapt & recalculate depending on your start/end frames. Use this option if you'd like to define the min/max frames yourself"),
        update=scattering.update_factory.factory("s_wind_noise_loopable_cliplength_allow"),
        )
    s_wind_noise_loopable_frame_start : bpy.props.IntProperty(
        min=0, default=0,
        update=scattering.update_factory.factory("s_wind_noise_loopable_frame_start", delay_support=True,),
        )
    s_wind_noise_loopable_frame_end : bpy.props.IntProperty(
        min=0, default=200,
        update=scattering.update_factory.factory("s_wind_noise_loopable_frame_end", delay_support=True,),
        )

    s_wind_noise_force : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Define the force of the wind noisy turbulence"),
        default=0.5, 
        soft_min=0, 
        soft_max=3, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_noise_force", delay_support=True,),
        )
    s_wind_noise_speed : bpy.props.FloatProperty(
        name=translate("Speed"), 
        description=translate("Define the speed of the wind noisy turbulence. Note that if the animation method is set to loop, it might be impossible to achieve the desired speed."),
        default=1, 
        soft_min=0.001, 
        soft_max=10, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_noise_speed", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_wind_noise",)

    # Yb    dP 88 .dP"Y8 88 88""Yb 88 88     88 888888 Yb  dP
    #  Yb  dP  88 `Ybo." 88 88__dP 88 88     88   88    YbdP
    #   YbdP   88 o.`Y8b 88 88""Yb 88 88  .o 88   88     8P
    #    YP    88 8bodP' 88 88oodP 88 88ood8 88   88    dP

    ###################### This category of settings keyword is : "s_visibility"
    ###################### this category is Not supported by Preset

    s_visibility_locked   : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_visibility_main_features(self, availability_conditions=True,):
        r = ["s_visibility_facepreview_allow","s_visibility_view_allow", "s_visibility_cam_allow", "s_visibility_maxload_allow",]
        if (not availability_conditions):
            return r
        if (self.s_distribution_method=="volume"):
            r.remove("s_visibility_facepreview_allow")
        return r

    s_visibility_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_visibility_master_allow", sync_support=False,),
        )

    ########## ########## Just for UI... 

    s_visibility_statistics_allow : bpy.props.BoolProperty(
        default=True,
        description=translate("Compute the visibility statistics of this scatter-system. (This toggle exists only for cosmetic)"),
        )

    ########## ########## Only show on selected faces

    s_visibility_facepreview_allow : bpy.props.BoolProperty( 
        default=False,
        name=translate("Distribution Preview"),
        description=translate("Preview your distribution only on the given surface(s) faces (this optimization method is great when dealing with large terrains)"),
        update=scattering.update_factory.factory("s_visibility_facepreview_allow"),
        )

    s_visibility_facepreview_allow_screen : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled only when working on the viewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_facepreview","screen"),) #ui purpose
    s_visibility_facepreview_allow_shaded : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled when working in the viewport & also during rendered-view. The final render will not be impacted"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_facepreview","shaded"),) #ui purpose
    s_visibility_facepreview_allow_render : bpy.props.BoolProperty(default=False, description=translate("This optimization feature will be enabled at all time, also during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_facepreview","render"),) #ui purpose
    s_visibility_facepreview_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="viewport_only",
        items= ( ("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_facepreview_viewport_method"),
        )

    ########## ########## Remove % of particles

    s_visibility_view_allow : bpy.props.BoolProperty( 
        default=False,
        name=translate("Percentage Reduction"),
        description=translate("Lower the distribution density from a chosen removal-rate"),
        update=scattering.update_factory.factory("s_visibility_view_allow"),
        )
    s_visibility_view_percentage : bpy.props.FloatProperty(
        name=translate("Rate"),
        subtype="PERCENTAGE",
        default=80,
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_visibility_view_percentage", delay_support=True,),
        )

    s_visibility_view_allow_screen : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled only when working on the viewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_view","screen"),) #ui purpose
    s_visibility_view_allow_shaded : bpy.props.BoolProperty(default=False, description=translate("This optimization feature will be enabled when working in the viewport & also during rendered-view. The final render will not be impacted"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_view","shaded"),) #ui purpose
    s_visibility_view_allow_render : bpy.props.BoolProperty(default=False, description=translate("This optimization feature will be enabled at all time, also during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_view","render"),) #ui purpose
    s_visibility_view_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="except_rendered",
        items= ( ("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_view_viewport_method"),
        )

    ########## ########## Camera Optimization

    s_visibility_cam_allow : bpy.props.BoolProperty( 
        default=False,
        name=translate("Camera Optimizations"),
        description=translate("Remove points not visible by the camera"),
        update=scattering.update_factory.factory("s_visibility_cam_allow"),
        )

    #Frustrum 

    s_visibility_camclip_allow : bpy.props.BoolProperty(
        default=True,
        name=translate("Frustum Culling"),
        description=translate("Only show instances whose origins are located inside the active-camera frustum volume"),
        update=scattering.update_factory.factory("s_visibility_camclip_allow"),
        )
    s_visibility_camclip_cam_autofill : bpy.props.BoolProperty(
        default=True,
        name=translate("Automatically define the frustrum cone"),
        description=translate("Compute the frustrum volume automatically on the active camera, if not checked, please define the frustrum properties"),
        update=scattering.update_factory.factory("s_visibility_camclip_cam_autofill"),
        )
    s_visibility_camclip_cam_lens : bpy.props.FloatProperty( #handler will bypass these settings
        name=translate("Lens"),
        default=50,
        subtype="DISTANCE_CAMERA",
        min=1,
        soft_max=5_000, 
        update=scattering.update_factory.factory("s_visibility_camclip_cam_lens", delay_support=True,),
        )
    s_visibility_camclip_cam_sensor_width : bpy.props.FloatProperty( #handler will bypass these settings
        name=translate("Sensor"),
        default=36,
        subtype="DISTANCE_CAMERA",
        min=1,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camclip_cam_sensor_width", delay_support=True,),
        )
    s_visibility_camclip_cam_res_xy : bpy.props.FloatVectorProperty( #handler will bypass these settings
        name=translate("Resolution"),
        subtype="XYZ",
        size=2,
        default=(1920,1080),
        precision=0,
        update=scattering.update_factory.factory("s_visibility_camclip_cam_res_xy", delay_support=True,),
        )
    s_visibility_camclip_cam_shift_xy : bpy.props.FloatVectorProperty( #handler will bypass these settings
        name=translate("Shift"),
        subtype="XYZ",
        size=2,
        default=(0,0),
        soft_min=-2,
        soft_max=2, 
        precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_cam_shift_xy", delay_support=True,),
        )
    s_visibility_camclip_cam_boost_xy : bpy.props.FloatVectorProperty(
        name=translate("FOV Boost"),
        subtype="XYZ",
        size=2,
        default=(0,0),
        soft_min=-2,
        soft_max=2, 
        precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_cam_boost_xy", delay_support=True,),
        )
    s_visibility_camclip_proximity_allow : bpy.props.BoolProperty(
        default=False,
        name=translate("Near Camera Radius"),
        description=translate("Reveal some instances originalgeometry near the camera"),
        update=scattering.update_factory.factory("s_visibility_camclip_proximity_allow"),
        )
    s_visibility_camclip_proximity_distance : bpy.props.FloatProperty(
        name=translate("Distance"),
        description=translate("Distance radius that will reveal the original geometry of your instances display"),
        default=4,
        subtype="DISTANCE",
        min=0,
        soft_max=20, 
        update=scattering.update_factory.factory("s_visibility_camclip_proximity_distance", delay_support=True,),
        )

    #Distance 

    s_visibility_camdist_allow: bpy.props.BoolProperty(
        default=False,
        name=translate("Camera Distance Culling"),
        description=translate("Only show instances close to the active-camera"),
        update=scattering.update_factory.factory("s_visibility_camdist_allow"),
        )
    s_visibility_camdist_per_cam_data: bpy.props.BoolProperty(
        default=False,
        name=translate("Per camera settings"),
        description=translate("Use variable distance depending on your active cameras"),
        update=scattering.update_factory.factory("s_visibility_camdist_per_cam_data"),
        )
    s_visibility_camdist_min : bpy.props.FloatProperty(
        name=translate("Minimal"),
        default=10,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camdist_min", delay_support=True,),
        )
    s_visibility_camdist_max : bpy.props.FloatProperty(
        name=translate("Maximal"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camdist_max", delay_support=True,),
        )
    #remap
    s_visibility_camdist_fallremap_allow : bpy.props.BoolProperty(
        default=False, 
        name=translate("Camera Distance Culling Remap"),
        description=translate("Control the transition falloff by remapping the values"),
        update=scattering.update_factory.factory("s_visibility_camdist_fallremap_allow",),
        )
    s_visibility_camdist_fallremap_revert : bpy.props.BoolProperty(
        default=False,
        update=scattering.update_factory.factory("s_visibility_camdist_fallremap_revert",),
        )
    s_visibility_camdist_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_visibility_cam.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_visibility_cam.fallremap"),
        )

    #Occlusion

    s_visibility_camoccl_allow : bpy.props.BoolProperty(
        default=False,
        name=translate("Camera Occlusion"),
        description=translate("Remove instances unseen by the camera, because they are located on hidden areas of the surface(s) or behind given objects"),
        update=scattering.update_factory.factory("s_visibility_camoccl_allow"),
        )
    s_visibility_camoccl_threshold : bpy.props.FloatProperty(
        name=translate("Threshold"),
        default=0.01,
        subtype="DISTANCE",
        min=0,
        soft_max=20, 
        update=scattering.update_factory.factory("s_visibility_camoccl_threshold", delay_support=True,),
        )
    s_visibility_camoccl_method : bpy.props.EnumProperty(
        name=translate("Occlusion Method"),
        default="surface_only",
        items= [ ("surface_only", translate("Surface Only"), translate("Mask instances whose origins are located on occluded surfaces"),"",0),
                 ("obj_only", translate("Colliders Only"), translate("Mask instances whose origins are occluded by a given collection of objects"),"",1),
                 ("both",    translate("Surface & Colliders"), translate("Mask instances whose origins are occluded by the terrain surface & by a given collection of objects"),"",2),
               ],
        update=scattering.update_factory.factory("s_visibility_camoccl_method"),
        )
    s_visibility_camoccl_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        update=scattering.update_factory.factory("s_visibility_camoccl_coll_ptr"),
        )
    passctxt_s_visibility_camoccl_coll_ptr : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)

    s_visibility_cam_allow_screen : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled only when working on the viewport, not during rendered view nor the final render."), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_cam","screen"),) #ui purpose
    s_visibility_cam_allow_shaded : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled when working in the viewport & also during rendered-view. The final render will not be impacted"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_cam","shaded"),) #ui purpose
    s_visibility_cam_allow_render : bpy.props.BoolProperty(default=False, description=translate("This optimization feature will be enabled at all time, also during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_cam","render"),) #ui purpose
    s_visibility_cam_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="viewport_only",
        items= ( ("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_cam_viewport_method"),
        )

    ########## ########## Maximum load

    s_visibility_maxload_allow : bpy.props.BoolProperty( 
        default=False,
        name=translate("Maximum Load"),
        description=translate("Define the maximum amount of instances visible on screen"),
        update=scattering.update_factory.factory("s_visibility_maxload_allow"),
        )
    s_visibility_maxload_cull_method : bpy.props.EnumProperty(
        name=translate("What to do once the chosen instance count threshold is reached?"),
        default="maxload_limit",
        items= [ ("maxload_limit", translate("Limit"),translate("Limit how many instances are visible on screen. The total amount of instances produced by this scatter-system will never exceed the given threshold."),),
                 ("maxload_shutdown", translate("Shutdown"),translate("If total amount of instances produced by this scatter-system goes beyond given threshold, we will shutdown the visibility of this system entirely"),),
               ],
        update=scattering.update_factory.factory("s_visibility_maxload_cull_method"),
        )
    s_visibility_maxload_treshold : bpy.props.IntProperty(
        name=translate("Max Instances"),
        description=translate("The system will either limit or shut down what's visible, approximately above the chosen threshold"),
        min=1,
        soft_min=1_000,
        soft_max=9_999_999,
        default=199_000,
        update=scattering.update_factory.factory("s_visibility_maxload_treshold", delay_support=True,),
        )

    s_visibility_maxload_allow_screen : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled only when working on the viewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_maxload","screen"),) #ui purpose
    s_visibility_maxload_allow_shaded : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled when working in the viewport & also during rendered-view. The final render will not be impacted"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_maxload","shaded"),) #ui purpose
    s_visibility_maxload_allow_render : bpy.props.BoolProperty(default=False, description=translate("This optimization feature will be enabled at all time, also during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_maxload","render"),) #ui purpose
    s_visibility_maxload_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="viewport_only",
        items= ( ("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_maxload_viewport_method"),
        )

    # 88 88b 88 .dP"Y8 888888    db    88b 88  dP""b8 88 88b 88  dP""b8
    # 88 88Yb88 `Ybo."   88     dPYb   88Yb88 dP   `" 88 88Yb88 dP   `"
    # 88 88 Y88 o.`Y8b   88    dP__Yb  88 Y88 Yb      88 88 Y88 Yb  "88
    # 88 88  Y8 8bodP'   88   dP""""Yb 88  Y8  YboodP 88 88  Y8  YboodP

    ###################### This category of settings keyword is : "s_instances"

    s_instances_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    # def get_s_instances_main_features(self, availability_conditions=True,):
    #     return []

    # s_instances_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Enable this category"),
    #     description=translate("Mute all features of this category"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_instances_master_allow", sync_support=False,),
    #     )

    ########## ##########

    def get_instance_objs(self):
        """get all objects used by this particle instancing method"""
            
        instances = [] 

        if (self.s_instances_method=="ins_collection"):
            if (self.s_instances_coll_ptr):
                for o in self.s_instances_coll_ptr.objects:
                    if (o not in instances):
                        instances.append(o)

        return instances 
    
    def get_instancing_info(self, raw_data=False, loc_data=False, processed_data=False,): 
        """get information about the depsgraph instances for this system
        3 info type available:
        - raw_data: get the raw depsgraph information ( instance.object.original and instance.matrix_world )
        - loc_data: get only the locations of the instances
        - processed_data: get a comprehensive dict with "instance_ name", "location", "rotation_euler (radians)", "scale" as keys
        """
        
        #Note, fastest way to access all these data is via as_pointer(), however, speed does not matter here 
        
        scatter_obj = self.scatter_obj
        if (scatter_obj is None):
            raise Exception("No Scatter Obj Found")

        deps_data = [ ( i.object.original, i.matrix_world.copy() ) for i in bpy.context.evaluated_depsgraph_get().object_instances 
                if ( (i.is_instance) and (i.parent.original==scatter_obj) ) ]

        #return raw depsgraph option
        if (raw_data):
            return deps_data

        #return array of loc option
        elif (loc_data):
            data = []
            
            for i, v in enumerate(deps_data):
                _, m = v
                l, _, _ = m.decompose()
                
                data.append(l)
                continue
            
            return data
        
        #return processed dict option
        elif (processed_data):
            data = {}
            
            for i, v in enumerate(deps_data):
                b, m = v
                l, r, s = m.decompose()
                e = r.to_euler('XYZ', )

                data[str(i)]= {"name":b.name, "location":tuple(l), "rotation_euler":tuple(e[:]), "scale":tuple(s),}
                continue 
            
            return data
        
        raise Exception("Please Choose a named argument") 

    ########## ##########

    s_instances_method : bpy.props.EnumProperty( #maybe for later?
        name=translate("Instance Method"),
        default= "ins_collection", 
        items= ( ("ins_collection", translate("Collection"), translate("Spawn objects contained in a given collection into the distributed points with a chosen spawn method algorithm"), "OUTLINER_COLLECTION", 0,),
                 ("ins_points", translate("None"), translate("Skip the instancing part, and output the raw points generated by our plugin scatter-engine. Useful if you would like to add your own instancing rules with geometry nodes without interfering with our workflow, to do so, add a new geonode modifier right after our Geo-Scatter Engine modifier on your scatter object). Please note that our display system and random mirror features won't be available."), "PANEL_CLOSE", 1,),
               ),
        update=scattering.update_factory.factory("s_instances_method"),
        ) 
    s_instances_coll_ptr : bpy.props.PointerProperty( #TODO, no longer rely on collection... need more flexible system
        name=translate("Collection Pointer"),
        type=bpy.types.Collection,
        update=scattering.update_factory.factory("s_instances_coll_ptr"),
        )
    s_instances_list_idx : bpy.props.IntProperty() #for list template
    
    s_instances_pick_method : bpy.props.EnumProperty( #only for ins_collection
        name=translate("Spawn Method"),
        default= "pick_random", 
        items= ( ("pick_random", translate("Random"), translate("Randomly assign the instances from the object-list below to the scattered points"), "OBJECT_DATA", 0,),
                 ("pick_rate", translate("Probability"), translate("Assign instances to the generated points based on a defined probability rate per instances"), "MOD_HUE_SATURATION", 1,),
                 ("pick_scale", translate("Scale"), translate("Assign instances based on the generated points scale"), "OBJECT_ORIGIN", 2,),
                 ("pick_color", translate("Color Sampling"), translate("Assign instances to the generated points based on a given color attribute (vertex-color or texture)"), "COLOR", 3,),
                 ("pick_idx", translate("Manual Index"), translate("Assign instances based on manual mode index attribute brush"), "LINENUMBERS_ON", 4,),
                 ("pick_cluster", translate("Clusters"), translate("Assign instance to the generated points by packing them in clusters"), "CON_OBJECTSOLVER", 5,),
               ),
        update=scattering.update_factory.factory("s_instances_pick_method"),
        )
    #for pick_random & pick_rate
    s_instances_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        default=0,
        min=0, 
        update=scattering.update_factory.factory("s_instances_seed", delay_support=True, sync_support=False,),
        )
    s_instances_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        default=False,
        update=scattering.update_factory.factory("s_instances_is_random_seed", alt_support=False, sync_support=False,),
        )
    #for pick_rate
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_rate", nbr=20, items={"default":0,"min":0,"max":100,"subtype":"PERCENTAGE","name":translate("Probability"),"description":translate("Set this object spawn rate, objects above will over-shadow those located below in an alphabetically sorted list")}, property_type=bpy.props.IntProperty, delay_support=True,)
    #for pick_scale
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_scale_min", nbr=20, items={"default":0,"soft_min":0,"soft_max":3,"name":translate("Scale Range Min"),"description":translate("Assign instance to scattered points fitting the given range, objects above will over-shadow those located below in an alphabetically sorted list")}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_scale_max", nbr=20, items={"default":0,"soft_min":0,"soft_max":3,"name":translate("Scale Range Max"),"description":translate("Assign instance to scattered points fitting the given range, objects above will over-shadow those located below in an alphabetically sorted list")}, property_type=bpy.props.FloatProperty, delay_support=True,)
    s_instances_id_scale_method : bpy.props.EnumProperty(
        name=translate("Scale Method"),
        default= "fixed_scale",
        items= ( ("fixed_scale", translate("Frozen Scale"), translate("Reset all instances scale to 1"),"FREEZE",0),
                 ("dynamic_scale", translate("Dynamic Scale"), translate("Rescale Items dynamically depending on given range"),"LIGHT_DATA",1),
                 ("default_scale", translate("Default Scale"), translate("Leave Scale as it is"),"OBJECT_ORIGIN",2),
               ),
        update=scattering.update_factory.factory("s_instances_id_scale_method"),
        )
    #for pick color
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_color", nbr=20, items={"default":(1,0,0),"subtype":"COLOR","min":0,"max":1,"name":translate("Color"),"description":translate("Assign this instance to the corresponding color sampled")}, property_type=bpy.props.FloatVectorProperty, delay_support=True,)
    #for pick_cluster
    s_instances_pick_cluster_projection_method : bpy.props.EnumProperty(
        name=translate("Projection Method"),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate(""), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_instances_pick_cluster_projection_method"),
        )
    s_instances_pick_cluster_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.3,
        min=0,
        update=scattering.update_factory.factory("s_instances_pick_cluster_scale", delay_support=True,),
        )
    s_instances_pick_cluster_blur : bpy.props.FloatProperty(
        name=translate("Jitter"),
        default=0.5,
        min=0,
        max=3,
        update=scattering.update_factory.factory("s_instances_pick_cluster_blur", delay_support=True,),
        )
    s_instances_pick_clump : bpy.props.BoolProperty(
        default=False, 
        name=translate("Use Clumps as Clusters"),
        description=translate("This option appears if you are using clump distribution method, it will allow you to assign each instance to individual clumps"),
        update=scattering.update_factory.factory("s_instances_pick_clump"),
        )

    s_instances_id_color_tolerence : bpy.props.FloatProperty(
        name=translate("Tolerence"),
        default=0.3,
        min=0,
        soft_max=3,
        update=scattering.update_factory.factory("s_instances_id_color_tolerence", delay_support=True,), 
        )

    s_instances_id_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Source"),
        default= "vcol", 
        items= ( ("vcol", translate("Vertex Colors"), "", "VPAINT_HLT", 1,),
                 ("text", translate("Texture Data"), "", "NODE_TEXTURE", 2,),
               ),
        update=scattering.update_factory.factory("s_instances_id_color_sample_method"),
        ) 
    s_instances_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_instances_texture_ptr",),
        )
    s_instances_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all surface(s) for shared color attributes\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vcol")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_instances_vcol_ptr"),
        )

    # 8888b.  88 .dP"Y8 88""Yb 88        db    Yb  dP
    #  8I  Yb 88 `Ybo." 88__dP 88       dPYb    YbdP
    #  8I  dY 88 o.`Y8b 88"""  88  .o  dP__Yb    8P
    # 8888Y"  88 8bodP' 88     88ood8 dP""""Yb  dP

    ###################### This category of settings keyword is : "s_display"
    ###################### this category is Not supported by Preset

    s_display_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_display_main_features(self, availability_conditions=True,):
        return ["s_display_allow",]

    s_display_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_display_master_allow", sync_support=False,),
        )

    ########## ########## Display as

    s_display_allow : bpy.props.BoolProperty( 
        description=translate("Display your instances as something else on screen. Useful for work-optimization purpose in order to reduce the triangle count drawn in real time by your GPU"),
        default=False,
        update=scattering.update_factory.factory("s_display_allow",),
        )
    s_display_method : bpy.props.EnumProperty(
        name=translate("Display as"),
        default= "placeholder", 
        items= ( ("bb", translate("Bounding-Box"), translate("Display your instances as a their solid bounding-box"), "CUBE",1 ),
                 ("convexhull", translate("Convex-Hull"), translate("Display your instances as their computed convexhull geometry. Note that the convex-hull is computed in real time and might be slow to compute"), "MESH_ICOSPHERE",2 ),
                 ("placeholder", translate("Placeholder"), translate("Display your instances as another object, choose from a set of pre-made low poly objects"), "MOD_CLOTH",3 ),
                 ("placeholder_custom", translate("Custom Placeholder"), translate("Display your instances as another object, choose your own custom object"), "MOD_CLOTH",4 ),
                 ("point", translate("Single Point"), translate("Display your instances as a single point"), "LAYER_ACTIVE",5 ),
                 ("cloud", translate("Point-Cloud"), translate("Display your instances as a generated point-cloud"), "OUTLINER_OB_POINTCLOUD",7 ),
               ),
        update=scattering.update_factory.factory("s_display_method"),
        )
    s_display_placeholder_type : bpy.props.EnumProperty(
        name=translate("Placeholder Type"),
        default="SCATTER5_placeholder_pyramidal_square",
        items=( ("SCATTER5_placeholder_extruded_triangle",     translate("Extruded Triangle") ,""     ,"INIT_ICON:W_placeholder_extruded_triangle", 1 ),
                ("SCATTER5_placeholder_extruded_square",       translate("Extruded Square") ,""       ,"INIT_ICON:W_placeholder_extruded_square", 2 ),
                ("SCATTER5_placeholder_extruded_pentagon",     translate("Extruded Pentagon") ,""     ,"INIT_ICON:W_placeholder_extruded_pentagon", 3 ),
                ("SCATTER5_placeholder_extruded_hexagon",      translate("Extruded Hexagon") ,""      ,"INIT_ICON:W_placeholder_extruded_hexagon", 4 ),
                ("SCATTER5_placeholder_extruded_decagon",      translate("Extruded Decagon") ,""      ,"INIT_ICON:W_placeholder_extruded_decagon", 5 ),
                ("SCATTER5_placeholder_pyramidal_triangle",    translate("Pyramidal Triangle") ,""    ,"INIT_ICON:W_placeholder_pyramidal_triangle", 6 ),
                ("SCATTER5_placeholder_pyramidal_square",      translate("Pyramidal Square") ,""      ,"INIT_ICON:W_placeholder_pyramidal_square", 7 ),
                ("SCATTER5_placeholder_pyramidal_pentagon",    translate("Pyramidal Pentagon") ,""    ,"INIT_ICON:W_placeholder_pyramidal_pentagon", 8 ),
                ("SCATTER5_placeholder_pyramidal_hexagon",     translate("Pyramidal Hexagon") ,""     ,"INIT_ICON:W_placeholder_pyramidal_hexagon", 9 ),
                ("SCATTER5_placeholder_pyramidal_decagon",     translate("Pyramidal Decagon") ,""     ,"INIT_ICON:W_placeholder_pyramidal_decagon", 10 ),
                ("SCATTER5_placeholder_flat_triangle",         translate("Flat Triangle") ,""         ,"INIT_ICON:W_placeholder_flat_triangle", 11 ),
                ("SCATTER5_placeholder_flat_square",           translate("Flat Square") ,""           ,"INIT_ICON:W_placeholder_flat_square", 12 ),
                ("SCATTER5_placeholder_flat_pentagon",         translate("Flat Pentagon") ,""         ,"INIT_ICON:W_placeholder_flat_pentagon", 13 ),
                ("SCATTER5_placeholder_flat_hexagon",          translate("Flat Hexagon") ,""          ,"INIT_ICON:W_placeholder_flat_hexagon", 14 ),
                ("SCATTER5_placeholder_flat_decagon",          translate("Flat Decagon") ,""          ,"INIT_ICON:W_placeholder_flat_decagon", 15 ),
                ("SCATTER5_placeholder_card_triangle",         translate("Card Triangle") ,""         ,"INIT_ICON:W_placeholder_card_triangle", 16 ),
                ("SCATTER5_placeholder_card_square",           translate("Card Square") ,""           ,"INIT_ICON:W_placeholder_card_square", 17 ),
                ("SCATTER5_placeholder_card_pentagon",         translate("Card Pentagon") ,""         ,"INIT_ICON:W_placeholder_card_pentagon", 18 ),
                ("SCATTER5_placeholder_hemisphere_01",         translate("Hemisphere 01") ,""         ,"INIT_ICON:W_placeholder_hemisphere_01", 19 ),
                ("SCATTER5_placeholder_hemisphere_02",         translate("Hemisphere 02") ,""         ,"INIT_ICON:W_placeholder_hemisphere_02", 20 ),
                ("SCATTER5_placeholder_hemisphere_03",         translate("Hemisphere 03") ,""         ,"INIT_ICON:W_placeholder_hemisphere_03", 21 ),
                ("SCATTER5_placeholder_hemisphere_04",         translate("Hemisphere 04") ,""         ,"INIT_ICON:W_placeholder_hemisphere_04", 22 ),
                ("SCATTER5_placeholder_lowpoly_pine_01",       translate("Lowpoly Pine 01") ,""       ,"INIT_ICON:W_placeholder_lowpoly_pine_01", 23 ),
                ("SCATTER5_placeholder_lowpoly_pine_02",       translate("Lowpoly Pine 02") ,""       ,"INIT_ICON:W_placeholder_lowpoly_pine_02", 24 ),
                ("SCATTER5_placeholder_lowpoly_pine_03",       translate("Lowpoly Pine 03") ,""       ,"INIT_ICON:W_placeholder_lowpoly_pine_03", 25 ),
                ("SCATTER5_placeholder_lowpoly_pine_04",       translate("Lowpoly Pine 04") ,""       ,"INIT_ICON:W_placeholder_lowpoly_pine_04", 26 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_01", translate("Lowpoly Coniferous 01") ,"" ,"INIT_ICON:W_placeholder_lowpoly_coniferous_01", 27 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_02", translate("Lowpoly Coniferous 02") ,"" ,"INIT_ICON:W_placeholder_lowpoly_coniferous_02", 28 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_03", translate("Lowpoly Coniferous 03") ,"" ,"INIT_ICON:W_placeholder_lowpoly_coniferous_03", 29 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_04", translate("Lowpoly Coniferous 04") ,"" ,"INIT_ICON:W_placeholder_lowpoly_coniferous_04", 30 ),
                ("SCATTER5_placeholder_lowpoly_coniferous_05", translate("Lowpoly Coniferous 05") ,"" ,"INIT_ICON:W_placeholder_lowpoly_coniferous_05", 31 ),
                ("SCATTER5_placeholder_lowpoly_sapling_01",    translate("Lowpoly Sapling 01"),""     ,"INIT_ICON:W_placeholder_lowpoly_sapling_01", 32 ),
                ("SCATTER5_placeholder_lowpoly_sapling_02",    translate("Lowpoly Sapling 02"),""     ,"INIT_ICON:W_placeholder_lowpoly_sapling_02", 33 ),
                ("SCATTER5_placeholder_lowpoly_cluster_01",    translate("Lowpoly Cluster 01") ,""    ,"INIT_ICON:W_placeholder_lowpoly_cluster_01", 34 ),
                ("SCATTER5_placeholder_lowpoly_cluster_02",    translate("Lowpoly Cluster 02") ,""    ,"INIT_ICON:W_placeholder_lowpoly_cluster_02", 35 ),
                ("SCATTER5_placeholder_lowpoly_cluster_03",    translate("Lowpoly Cluster 03") ,""    ,"INIT_ICON:W_placeholder_lowpoly_cluster_03", 36 ),
                ("SCATTER5_placeholder_lowpoly_cluster_04",    translate("Lowpoly Cluster 04") ,""    ,"INIT_ICON:W_placeholder_lowpoly_cluster_04", 37 ),
                ("SCATTER5_placeholder_lowpoly_plant_01",      translate("Lowpoly Plant 01") ,""      ,"INIT_ICON:W_placeholder_lowpoly_plant_01", 38 ),
                ("SCATTER5_placeholder_lowpoly_plant_02",      translate("Lowpoly Plant 02") ,""      ,"INIT_ICON:W_placeholder_lowpoly_plant_02", 39 ),
                ("SCATTER5_placeholder_lowpoly_plant_03",      translate("Lowpoly Plant 03") ,""      ,"INIT_ICON:W_placeholder_lowpoly_plant_03", 40 ),
                ("SCATTER5_placeholder_lowpoly_plant_04",      translate("Lowpoly Plant 04") ,""      ,"INIT_ICON:W_placeholder_lowpoly_plant_04", 41 ),
                ("SCATTER5_placeholder_lowpoly_plant_05",      translate("Lowpoly Plant 05") ,""      ,"INIT_ICON:W_placeholder_lowpoly_plant_05", 42 ),
                ("SCATTER5_placeholder_lowpoly_plant_06",      translate("Lowpoly Plant 06") ,""      ,"INIT_ICON:W_placeholder_lowpoly_plant_06", 43 ),
                ("SCATTER5_placeholder_lowpoly_plant_07",      translate("Lowpoly Plant 07") ,""      ,"INIT_ICON:W_placeholder_lowpoly_plant_07", 44 ),
                ("SCATTER5_placeholder_lowpoly_flower_01",     translate("Lowpoly Flower 01"),""      ,"INIT_ICON:W_placeholder_lowpoly_flower_01", 45 ),
                ("SCATTER5_placeholder_lowpoly_flower_02",     translate("Lowpoly Flower 02"),""      ,"INIT_ICON:W_placeholder_lowpoly_flower_02", 46 ),
                ("SCATTER5_placeholder_lowpoly_flower_03",     translate("Lowpoly Flower 03"),""      ,"INIT_ICON:W_placeholder_lowpoly_flower_03", 47 ),
                ("SCATTER5_placeholder_lowpoly_flower_04",     translate("Lowpoly Flower 04"),""      ,"INIT_ICON:W_placeholder_lowpoly_flower_04", 48 ),
                ("SCATTER5_placeholder_helper_empty_stick",    translate("Helper Empty Stick") ,""    ,"INIT_ICON:W_placeholder_helper_empty_stick", 49 ),
                ("SCATTER5_placeholder_helper_empty_arrow",    translate("Helper Empty Arrow") ,""    ,"INIT_ICON:W_placeholder_helper_empty_arrow", 50 ),
                ("SCATTER5_placeholder_helper_empty_axis",     translate("Helper Empty Axis") ,""     ,"INIT_ICON:W_placeholder_helper_empty_axis", 51 ),
                ("SCATTER5_placeholder_helper_colored_axis",   translate("Helper Colored Axis") ,""   ,"INIT_ICON:W_placeholder_helper_colored_axis", 52 ),
                ("SCATTER5_placeholder_helper_colored_cube",   translate("Helper Colored Cube") ,""   ,"INIT_ICON:W_placeholder_helper_colored_cube", 53 ),
                ("SCATTER5_placeholder_helper_y_arrow",        translate("Helper Tangent Arrow") ,""  ,"INIT_ICON:W_placeholder_helper_y_arrow", 54 ),
               ),
        update=scattering.update_factory.factory("s_display_placeholder_type"),
        )
    s_display_custom_placeholder_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_display_custom_placeholder_ptr",),
        )
    s_display_placeholder_scale : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        subtype="XYZ", 
        default=(0.3,0.3,0.3), 
        update=scattering.update_factory.factory("s_display_placeholder_scale", delay_support=True,),
        )
    s_display_point_radius : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.3,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_display_point_radius", delay_support=True,),
        )
    s_display_cloud_radius : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.1,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_display_cloud_radius", delay_support=True,),
        )
    s_display_cloud_density : bpy.props.FloatProperty(
        name=translate("Density"),
        default=10,
        min=0,
        update=scattering.update_factory.factory("s_display_cloud_density", delay_support=True,),
        )
    s_display_camdist_allow: bpy.props.BoolProperty(
        default=False,
        name=translate("Reveal Near Instance Camera"),
        description=translate("Disable the display method for instances close to the active camera"),
        update=scattering.update_factory.factory("s_display_camdist_allow"),
        )
    s_display_camdist_distance : bpy.props.FloatProperty(
        name=translate("Distance"),
        default=5,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_display_camdist_distance", delay_support=True,),
        )

    s_display_allow_screen : bpy.props.BoolProperty(default=True, description=translate("This optimization feature will be enabled only when working on the viewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_display","screen"),) #ui purpose
    s_display_allow_shaded : bpy.props.BoolProperty(default=False, description=translate("This optimization feature will be enabled when working in the viewport & also during rendered-view. The final render will not be impacted"), update=scattering.update_factory.factory_viewport_method_proxy("s_display","shaded"),) #ui purpose
    s_display_allow_render : bpy.props.BoolProperty(default=False, description=translate("This optimization feature will be enabled at all time, also during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_display","render"),) #ui purpose
    s_display_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="except_rendered",
        items= ( ("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_display_viewport_method"),
        )

    # 88""Yb 888888  dP""b8 88 88b 88 88b 88 888888 88""Yb  
    # 88__dP 88__   dP   `" 88 88Yb88 88Yb88 88__   88__dP  
    # 88""Yb 88""   Yb  "88 88 88 Y88 88 Y88 88""   88"Yb   
    # 88oodP 888888  YboodP 88 88  Y8 88  Y8 888888 88  Yb  

    s_beginner_default_scale: bpy.props.FloatProperty(
        soft_max=5,
        soft_min=0,
        default=1,
        description=translate("Multiplier for your instances XYZ scale"),
        update=scattering.update_factory.factory("s_beginner_default_scale", delay_support=True,),
        )

    s_beginner_random_scale : bpy.props.FloatProperty(
        default=0, 
        min=0,
        max=1,
        description=translate("Randomize the XYZ scale of your instances"),
        update=scattering.update_factory.factory("s_beginner_random_scale",),
        )

    s_beginner_random_rot : bpy.props.FloatProperty(
        default=0, 
        min=0,
        max=1,
        description=translate("Randomize the XYZ rotation of your instances"),
        update=scattering.update_factory.factory("s_beginner_random_rot",),
        )



#   .oooooo.
#  d8P'  `Y8b
# 888           oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.   .oooo.o
# 888           `888""8P d88' `88b `888  `888   888' `88b d88(  "8
# 888     ooooo  888     888   888  888   888   888   888 `"Y88b.
# `88.    .88'   888     888   888  888   888   888   888 o.  )88b
#  `Y8bood8P'   d888b    `Y8bod8P'  `V88V"V8P'  888bod8P' 8""888P'
#                                               888
#                                              o888o

#About group implementation:
#Groups are implemented via python properties update behavior
#on a scatter engine level, the group settings are just regular settings!
#group behavior is just added on an interface and property level


class SCATTER5_PR_particle_groups(bpy.types.PropertyGroup): 
    """bpy.context.object.scatter5.particle_groups, will be stored on emitter"""

    # 88""Yb .dP"Y8 Yb  dP .dP"Y8 
    # 88__dP `Ybo."  YbdP  `Ybo." 
    # 88"""  o.`Y8b   8P   o.`Y8b 
    # 88     8bodP'  dP    8bodP' 
    
    def get_psy_members(self):
        """list all psys being members given group"""
        
        emitter = self.id_data
        psys = emitter.scatter5.particle_systems
        
        return [ p for p in psys if (p.group==self.name) ]
    
    def property_run_update(self, prop_name, value,):
        """directly run the property update task function (== changing nodetree) w/o changing any property value, and w/o going in the update fct wrapper/dispatcher"""

        return scattering.update_factory.UpdatesRegistry.run_update(self, prop_name, value, bypass=True,)

    def property_nodetree_refresh(self, prop_name,):
        """refresh this property value"""

        return self.property_run_update(prop_name, getattr(self,prop_name),)

    def refresh_nodetree(self,):
        """for every settings, make sure nodetrees of psys members are updated"""

        settings = [k for k in self.bl_rna.properties.keys() if k.startswith("s_")]
        for s in settings:
            self.property_nodetree_refresh(s,)
            continue
        
        return None
    
    # 88b 88    db    8b    d8 888888 
    # 88Yb88   dPYb   88b  d88 88__   
    # 88 Y88  dP__Yb  88YbdP88 88""   
    # 88  Y8 dP""""Yb 88 YY 88 888888  
    
    def upd_name(self,context):
        """special update name function for renaming a group"""

        emitter = self.id_data

        #should only happend on creation
        if (self.name_bis==""):
            self.name_bis=self.name
            return None

        #deny update if no changes detected 
        if (self.name==self.name_bis):
            return None 
        
        #deny update if empty name 
        elif ( (self.name=="") or self.name.startswith(" ") ):
            self.name = self.name_bis
            bpy.ops.scatter5.popup_menu(msgs=translate("Name cannot be None, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
            return None
        
        #deny update if name already taken by another scatter_obj 
        elif (self.name in [g.name_bis for g in emitter.scatter5.particle_groups]):
            self.name = self.name_bis
            bpy.ops.scatter5.popup_menu(msgs=translate("This name is taken, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
            return None

        #rename group psys
        for p in emitter.scatter5.particle_systems:
            if (p.group!=""):
                if (p.group==self.name_bis):
                    p.group = self.name
            continue

        #rename interface names
        for itm in emitter.scatter5.particle_interface_items:
            if (itm.interface_group_name!=""):
                if (itm.interface_group_name==self.name_bis):
                    itm.interface_group_name = self.name
            continue

        #change name_bis name
        self.name_bis = self.name 

        return None

    name : bpy.props.StringProperty(
        default="",
        update=upd_name,
        )

    name_bis : bpy.props.StringProperty(
        description="important for renaming function, avoid name collision",
        default="",
        )

    # 88   88 88      dP"Yb  88""Yb 888888 88b 88 
    # 88   88 88     dP   Yb 88__dP 88__   88Yb88 
    # Y8   8P 88     Yb   dP 88"""  88""   88 Y88 
    # `YbodP' 88      YbodP  88     888888 88  Y8 
    
    def upd_open(self,context):
        """open/close the group system"""

        emitter = self.id_data

        #save selection, as this operation might f up sel
        save_sel = emitter.scatter5.get_psys_selected()[:]

        if (self.open):
            
            #if we are opening a collection, we need to add back the psys item before refresh,
            #otherwise interface will consider them as new items and will set them active, we don't what that behavior

            all_uuids = [ itm.interface_item_psy_uuid for itm in emitter.scatter5.particle_interface_items if (itm.interface_item_type=="SCATTER") ]
            
            for p in emitter.scatter5.particle_systems:
                if ((p.group!="") and (p.group==self.name)):
                    if (p.uuid not in all_uuids):
                        itm = emitter.scatter5.particle_interface_items.add()
                        itm.interface_item_type = "SCATTER"
                        itm.interface_item_psy_uuid = p.uuid
                continue 

        #refresh interface
        emitter.scatter5.particle_interface_refresh()

        #restore selection
        [ setattr(p,"sel",p in save_sel) for p in emitter.scatter5.particle_systems ]

        return None

    open : bpy.props.BoolProperty(
        default=True,
        update=upd_open,
        )

    #  dP""b8    db    888888 888888  dP""b8  dP"Yb  88""Yb Yb  dP     88   88 .dP"Y8 888888 8888b.
    # dP   `"   dPYb     88   88__   dP   `" dP   Yb 88__dP  YbdP      88   88 `Ybo." 88__    8I  Yb
    # Yb       dP__Yb    88   88""   Yb  "88 Yb   dP 88"Yb    8P       Y8   8P o.`Y8b 88""    8I  dY
    #  YboodP dP""""Yb   88   888888  YboodP  YbodP  88  Yb  dP        `YbodP' 8bodP' 888888 8888Y"
    
    def is_category_used(self, s_category): #version for group systems == simplified
        """check if the given property category is active"""

        if (not getattr(self, f"{s_category}_master_allow")):
            return False

        try:
            method_name = f"get_{s_category}_main_features"
            method = getattr(self, method_name)
            main_features = method()
        except:
            raise Exception("BUG: categories not set up correctly")

        return any( getattr(self,sett) for sett in main_features )

    # .dP"Y8 88   88 88""Yb 888888    db     dP""b8 888888
    # `Ybo." 88   88 88__dP 88__     dPYb   dP   `" 88__
    # o.`Y8b Y8   8P 88"Yb  88""    dP__Yb  Yb      88""
    # 8bodP' `YbodP' 88  Yb 88     dP""""Yb  YboodP 888888
    
    def get_surfaces(self):
        """return a list of surface object(s)"""
        return set( s for p in self.get_psy_members() for s in p.get_surfaces() )

    def get_surfaces_match_attr(self, attr_type,):
        """gather matching attributes accross all surfaces used"""
        global get_surfaces_match_attr 
        return get_surfaces_match_attr(self, attr_type,) #defined outside, so it's also accessible by codegen function
    
    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8

    # def get_s_gr_distribution_main_features(self, availability_conditions=True,):
    #     return ["s_gr_distribution_density_boost_allow"]

    # s_gr_distribution_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Enable this category"),
    #     description=translate("Mute all features of this category"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_gr_distribution_master_allow",),
    #     )
    # s_gr_distribution_density_boost_allow : bpy.props.BoolProperty(
    #     description=translate("Boost the density of all scatters contained in this group by a given percentage (if the distribution methods allows it)"),
    #     default=False,
    #     update=scattering.update_factory.factory("s_gr_distribution_density_boost_allow"),
    #     )
    # s_gr_distribution_density_boost_factor : bpy.props.FloatProperty(
    #     name=translate("Factor"),
    #     soft_max=2, soft_min=0, default=1,
    #     update=scattering.update_factory.factory("s_gr_distribution_density_boost_factor", delay_support=True,),
    #     )

    # 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
    #  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
    #  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
    # 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'

    def get_s_gr_mask_main_features(self, availability_conditions=True,):
        return ["s_gr_mask_vg_allow", "s_gr_mask_vcol_allow", "s_gr_mask_bitmap_allow", "s_gr_mask_curve_allow", "s_gr_mask_boolvol_allow", "s_gr_mask_material_allow", "s_gr_mask_upward_allow",]

    s_gr_mask_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_gr_mask_master_allow",),
        )

    ########## ########## Vgroups

    s_gr_mask_vg_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Group Mask"),
        description=translate("Mask-out your instances with the help of a vertex-group"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_vg_allow"),
        )
    s_gr_mask_vg_ptr : bpy.props.StringProperty(
        name=translate("Vertex-Group Pointer"),
        description=translate("Search across all surface(s) for shared vertex-group\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vg")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_vg_ptr"),
        )
    s_gr_mask_vg_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_gr_mask_vg_revert"),
        )

    ########## ########## VColors
    
    s_gr_mask_vcol_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Color Mask"), 
        description=translate("Mask-out your instances with the help of a color-attribute, specify which color-channel to sample"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_vcol_allow"),
        )
    s_gr_mask_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all surface(s) for shared color attributes\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("vcol")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_vcol_ptr"),
        )
    s_gr_mask_vcol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_gr_mask_vcol_revert"),
        )
    s_gr_mask_vcol_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to consider the color values in order to influence the distribution, by default the colors will be simply converted to black and white"),
        default="id_greyscale", 
        items=( ("id_greyscale", translate("Greyscale"), "", "NONE", 0,),
                ("id_red", translate("Red Channel"), "", "NONE", 1,),
                ("id_green", translate("Green Channel"), "", "NONE", 2,),
                ("id_blue", translate("Blue Channel"), "", "NONE", 3,),
                ("id_black", translate("Pure Black"), "", "NONE", 4,),
                ("id_white", translate("Pure White"), "", "NONE", 5,),
                ("id_picker", translate("Color Match"), "", "NONE", 6,),
                ("id_hue", translate("Hue"), "", "NONE", 7,),
                ("id_saturation", translate("Saturation"), "", "NONE", 8,),
                ("id_value", translate("Value"), "", "NONE", 9,),
                ("id_lightness", translate("Lightness"), "", "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), "", "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_gr_mask_vcol_color_sample_method"),
        )
    s_gr_mask_vcol_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_gr_mask_vcol_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Bitmap 

    s_gr_mask_bitmap_allow : bpy.props.BoolProperty( 
        name=translate("Image Mask"), 
        description=translate("Mask-out your instances with the help of an image texture, don't forget to save the image in your blend file!"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_bitmap_allow"),
        )
    s_gr_mask_bitmap_uv_ptr : bpy.props.StringProperty(
        default="UVMap",
        name=translate("UV-Map Pointer"),
        description=translate("Search across all surface(s) for shared Uvmap\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("uv")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_bitmap_uv_ptr"),
        )
    s_gr_mask_bitmap_ptr : bpy.props.StringProperty(
        update=scattering.update_factory.factory("s_gr_mask_bitmap_ptr"),
        )
    s_gr_mask_bitmap_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_gr_mask_bitmap_revert"),
        )
    s_gr_mask_bitmap_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to consider the color values in order to influence the distribution, by default the colors will be simply converted to black and white"),
        default="id_greyscale",
        items=( ("id_greyscale", translate("Greyscale"), "", "NONE", 0,),
                ("id_red", translate("Red Channel"), "", "NONE", 1,),
                ("id_green", translate("Green Channel"), "", "NONE", 2,),
                ("id_blue", translate("Blue Channel"), "", "NONE", 3,),
                ("id_black", translate("Pure Black"), "", "NONE", 4,),
                ("id_white", translate("Pure White"), "", "NONE", 5,),
                ("id_picker", translate("Color Match"), "", "NONE", 6,),
                ("id_hue", translate("Hue"), "", "NONE", 7,),
                ("id_saturation", translate("Saturation"), "", "NONE", 8,),
                ("id_value", translate("Value"), "", "NONE", 9,),
                ("id_lightness", translate("Lightness"), "", "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), "", "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_gr_mask_bitmap_color_sample_method"),
        )
    s_gr_mask_bitmap_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0, max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_gr_mask_bitmap_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Material

    s_gr_mask_material_allow : bpy.props.BoolProperty( 
        name=translate("Material ID Mask"), 
        description=translate("Mask-out instances that are not distributed upon the selected material slot"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_material_allow"),
        )
    s_gr_mask_material_ptr : bpy.props.StringProperty(
        name=translate("Material Pointer: The faces assigned to chosen material slot will be used as a culling mask"),
        description=translate("Search across all surface(s) for shared Materials\nIt Will highlight in red if the attribute is not shared across your surface(s)."),
        search=lambda s,c,e: s.get_surfaces_match_attr("mat")(s,c,e),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_material_ptr"),
        )
    s_gr_mask_material_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_gr_mask_material_revert"),
        )
    
    ########## ########## Curves

    s_gr_mask_curve_allow : bpy.props.BoolProperty( 
        name=translate("Bezier-Area Mask"), 
        description=translate("Mask-out instances that are inside the area of a closed bezier-curve."),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_curve_allow"),
        )
    s_gr_mask_curve_ptr : bpy.props.PointerProperty(
        name=translate("Bezier-Curve Pointer"),
        type=bpy.types.Object, 
        poll=lambda s,o: o.type=="CURVE",
        update=scattering.update_factory.factory("s_gr_mask_curve_ptr"),
        )
    s_gr_mask_curve_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_gr_mask_curve_revert"),
        )

    ########## ########## Boolean Volume

    s_gr_mask_boolvol_allow : bpy.props.BoolProperty( 
        name=translate("Boolean Mask"), 
        description=translate("Mask-out your instances located inside objects-volume from given collection"),
        default=False,
        update=scattering.update_factory.factory("s_gr_mask_boolvol_allow"),
        )
    s_gr_mask_boolvol_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        update=scattering.update_factory.factory("s_gr_mask_boolvol_coll_ptr"),
        )
    passctxt_s_gr_mask_boolvol_coll_ptr : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)
    s_gr_mask_boolvol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_gr_mask_boolvol_revert"),
        )

    ########## ########## Upward Obstruction

    s_gr_mask_upward_allow : bpy.props.BoolProperty( 
        name=translate("Upward-Obstruction Mask"), 
        description=translate("Mask-out your instances located underneath objects inside given collection"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_upward_allow"),
        )
    s_gr_mask_upward_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        update=scattering.update_factory.factory("s_gr_mask_upward_coll_ptr"),
        )
    passctxt_s_gr_mask_upward_coll_ptr : bpy.props.PointerProperty(type=SCATTER5_PR_popovers_dummy_class, description="needed for GUI drawing..",)
    s_gr_mask_upward_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        update=scattering.update_factory.factory("s_gr_mask_upward_revert"),
        )
    
    # .dP"Y8  dP""b8    db    88     888888
    # `Ybo." dP   `"   dPYb   88     88__
    # o.`Y8b Yb       dP__Yb  88  .o 88""
    # 8bodP'  YboodP dP""""Yb 88ood8 888888

    def get_s_gr_scale_main_features(self, availability_conditions=True,):
        return ["s_gr_scale_boost_allow"]

    s_gr_scale_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_gr_scale_master_allow"),
        )
    s_gr_scale_boost_allow : bpy.props.BoolProperty(
        description=translate("Boost the scale attribute of all scatters contained in this group by a given percentage"),
        default=False,
        update=scattering.update_factory.factory("s_gr_scale_boost_allow"),
        )
    s_gr_scale_boost_value : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        subtype="XYZ", 
        default=(1,1,1), 
        soft_min=0,
        soft_max=5,
        update=scattering.update_factory.factory("s_gr_scale_boost_value", delay_support=True,),
        )
    s_gr_scale_boost_multiplier : bpy.props.FloatProperty(
        name=translate("Factor"),
        soft_max=5,
        soft_min=0,
        default=1,
        update=scattering.update_factory.factory("s_gr_scale_boost_multiplier", delay_support=True,),
        )

    # 88""Yb    db    888888 888888 888888 88""Yb 88b 88 .dP"Y8
    # 88__dP   dPYb     88     88   88__   88__dP 88Yb88 `Ybo."
    # 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88 o.`Y8b
    # 88     dP""""Yb   88     88   888888 88  Yb 88  Y8 8bodP'

    def get_s_gr_pattern_main_features(self, availability_conditions=True,):
        return ["s_gr_pattern1_allow"]

    s_gr_pattern_master_allow : bpy.props.BoolProperty( 
        name=translate("Enable this category"),
        description=translate("Mute all features of this category"),
        default=True, 
        update=scattering.update_factory.factory("s_gr_pattern_master_allow"),
        )

    s_gr_pattern1_allow : bpy.props.BoolProperty(
        description=translate("Influence your instances scale and density with a scatter-texture datablock"),
        default=False,
        update=scattering.update_factory.factory("s_gr_pattern1_allow"),
        )
    s_gr_pattern1_texture_ptr : bpy.props.StringProperty(
        description="Internal property that will update a TEXTURE_NODE node tree from given nodetree name, used for presets and most importantly copy/paste or synchronization",
        update=scattering.update_factory.factory("s_gr_pattern1_texture_ptr"),
        )
    s_gr_pattern1_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how consider translate the color values in order to influence the distribution, by default the colors will be simply converted to black and white"),
        default="id_greyscale", 
        items=( ("id_greyscale", translate("Greyscale"), "", "NONE", 0,),
                ("id_red", translate("Red Channel"), "", "NONE", 1,),
                ("id_green", translate("Green Channel"), "", "NONE", 2,),
                ("id_blue", translate("Blue Channel"), "", "NONE", 3,),
                ("id_black", translate("Pure Black"), "", "NONE", 4,),
                ("id_white", translate("Pure White"), "", "NONE", 5,),
                ("id_picker", translate("Color Match"), "", "NONE", 6,),
                ("id_hue", translate("Hue"), "", "NONE", 7,),
                ("id_saturation", translate("Saturation"), "", "NONE", 8,),
                ("id_value", translate("Value"), "", "NONE", 9,),
                ("id_lightness", translate("Lightness"), "", "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), "", "NONE", 11,),
               ),
        update=scattering.update_factory.factory("s_gr_pattern1_color_sample_method"),
        )
    s_gr_pattern1_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        subtype="COLOR",
        min=0,
        max=1,
        default=(1,0,0),
        update=scattering.update_factory.factory("s_gr_pattern1_id_color_ptr"),
        )
    s_gr_pattern1_id_color_tolerence : bpy.props.FloatProperty(
        name=translate("Tolerence"),
        default=0.15, 
        soft_min=0, 
        soft_max=1,
        update=scattering.update_factory.factory("s_gr_pattern1_id_color_tolerence"),
        )
    #Feature Influence
    s_gr_pattern1_dist_infl_allow : bpy.props.BoolProperty(
        name=translate("Enable Influence"), 
        default=True,
        update=scattering.update_factory.factory("s_gr_pattern1_dist_infl_allow"),
        )
    s_gr_pattern1_dist_influence : bpy.props.FloatProperty(
        name=translate("Density"),
        default=100,
        subtype="PERCENTAGE", 
        min=0, 
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_gr_pattern1_dist_influence", delay_support=True,),
        )
    s_gr_pattern1_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_gr_pattern1_dist_revert"), 
        )
    s_gr_pattern1_scale_infl_allow : bpy.props.BoolProperty(
        name=translate("Enable Influence"), 
        default=True,
        update=scattering.update_factory.factory("s_gr_pattern1_scale_infl_allow"),
        )
    s_gr_pattern1_scale_influence : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=70, 
        subtype="PERCENTAGE", 
        min=0, 
        max=100, 
        precision=1, 
        update=scattering.update_factory.factory("s_gr_pattern1_scale_influence", delay_support=True,),
        )
    s_gr_pattern1_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"), 
        update=scattering.update_factory.factory("s_gr_pattern1_scale_revert"),
        )
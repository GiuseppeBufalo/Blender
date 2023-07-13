
#####################################################################################################
#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o
#####################################################################################################

import bpy
import os 

from .. resources.translate import translate

from .. resources import directories


# hereby are listed all de-centralized settings related to operators
# `f_` stands for `future_` aka the future visibility/display or masks

#####################################################################################################


#some related class functions:

def poll_closed_curve_type(self, object):
    return ( (object.type=="CURVE") and (object.data.splines[0].use_cyclic_u==True) )


def upd_thumbcrea_use_current_blend_path(self,context):
  if (not self.thumbcrea_use_current_blend_path):
      return None
  if (not bpy.data.is_saved):
        p = "None"
  else: p = bpy.data.filepath
  self.thumbcrea_custom_blend_path = p
  return None

#####################################################################################################

class SCATTER5_PR_save_operator_preset(bpy.types.PropertyGroup): 
    """scat_op = bpy.context.scene.scatter5.operators.save_operator_preset
    decentralized settings of SCATTER5_OT_save_operator_preset"""

    #Directory

    precrea_overwrite : bpy.props.BoolProperty(
        name=translate("Overwrite files?"),
        default=False,
        )
    precrea_creation_directory : bpy.props.StringProperty(
        name=translate("Overwrite if already exists"),
        default=directories.lib_presets, 
        )

    #preset related

    precrea_use_random_seed : bpy.props.BoolProperty(
        name=translate("Use Random Seed Values"),
        description=translate("automatically randomize the seed values of all seed properties"),
        default=True, 
        )
    precrea_texture_is_unique : bpy.props.BoolProperty(
        name=translate("Create Unique Textures"),
        description=translate("When creating a texture data, Geo-Scatter will by default always create a new texture data. If this option is set to False, Geo-Scatter will use the same texture data, if found in the user .blend"),
        default=True, 
        )
    precrea_texture_random_loc : bpy.props.BoolProperty(
        name=translate("Random Textures Translation"),
        description=translate("When creating a texture data, Geo-Scatter will randomize the location vector, useful to guarantee patch uniqueness location. Disable this option if you are using a texture that have an influence on multiple particle systems."),
        default=True, 
        )
    precrea_auto_render : bpy.props.BoolProperty(
        name=translate("Render thumbnail"),
        description=translate("automatically render the thumbnail of the preset afterwards"),
        default=False, 
        )

class SCATTER5_PR_save_biome_to_disk_dialog(bpy.types.PropertyGroup): 
    """scat_op = bpy.context.scene.scatter5.operators.save_biome_to_disk_dialog
    decentralized settings of SCATTER5_OT_save_biome_to_disk_dialog"""

    #Directory
    biocrea_overwrite : bpy.props.BoolProperty(
        name=translate("Overwrite files?"),
        default=False,
        )
    biocrea_creation_directory : bpy.props.StringProperty(
        default=os.path.join(directories.lib_biomes,"MyBiomes"),
        )

    #preset related
    biocrea_use_random_seed : bpy.props.BoolProperty(
        name=translate("Use random seed values"),
        description=translate("automatically randomize the seed values of all seed properties"),
        default=True,
        )
    biocrea_texture_is_unique : bpy.props.BoolProperty(
        name=translate("Create unique textures"),
        description=translate("When creating a texture data, Geo-Scatter will by default always create a new texture data. If this option is set to False, Geo-Scatter will use the same texture data, if found in the user .blend"),
        default=True,
        )
    biocrea_texture_random_loc : bpy.props.BoolProperty(
        name=translate("Random textures translation"),
        description=translate("When creating a texture data, Geo-Scatter will randomize the location vector, useful to guarantee patch uniqueness location. Disable this option if you are using a texture that have an influence on multiple particle systems."),
        default=True,
        )

    #use biome display
    biocrea_use_biome_display : bpy.props.BoolProperty(
        name=translate("Encode display settings"),
        description=translate("In Geo-Scatter 5 You can replace your instances with placeholders, by toggling this option, Geo-Scatter will also encode the placeholder settings. (If using custom placeholder, scatter5 will automatically export the object for you, note that if you decide to use your own .blend file you will need to make sure tha tthe placeholder object is present in your .blend)."),
        default=True,
        )

    #biome information
    biocrea_biome_name : bpy.props.StringProperty(
        name=translate("Name"),
        default="My Biome",
        )
    biocrea_file_keywords : bpy.props.StringProperty(
        name=translate("Keywords"),
        default="Some, Examples, Of, Keywords, Use, Coma,",
        )
    biocrea_keyword_from_instances : bpy.props.BoolProperty(
        name=translate("Instances as keywords"),
        description=translate("Automatically add the instances names as new keywords"),
        default=True,
        )
    biocrea_file_author : bpy.props.StringProperty(
        name=translate("Author"),
        default="BD3D",
        )
    biocrea_file_website : bpy.props.StringProperty(
        name=translate("Website"),
        default="https://geoscatter.com/biomes.html",
        )
    biocrea_file_description : bpy.props.StringProperty(
        name=translate("Description"),
        default="this is a custom biome i made! :-)",
        )
    
    #biome instance export 
    biocrea_external_blend_allow : bpy.props.BoolProperty(
        name=translate("Use existing .blend files"),
        description=translate("By default the biome saving operator will export your instances in a new .blend file, perhaps you are creating biomes for a library that needs to stored it's assets elsewhere? If this is the case, enable this option then enter the name of the blend file from where these instances are stored."),
        default=False,
        )
    biocrea_storage_type : bpy.props.EnumProperty(
        name=translate("Storage Method"),
        description=translate("Please tell us how your blend files are stored"),
        default="centralized", 
        items=( ("centralized" ,translate("One Centralized .blend") ,translate("Objects used by this biome are centralized in one and only .blend file, you will need to tell us thename of this file."),),
                ("individual" ,translate("Individual .blends") ,translate("Objects used by this biome are all made of individual blend file. In order to use this option all of your instances objects needs to be LINKED, that way we will automatically find the .blend source. Note that importing from many various blend sources is slower than the centralized method."),),
              ),
        )
    biocrea_centralized_blend : bpy.props.StringProperty(
        default="my_library.blend",
        )

    #reload previews
    biocrea_auto_reload_all  : bpy.props.BoolProperty(
        default=True,
        name=translate("Reload library afterwards"),
        )

    """
    biocrea_centralized_blend_search_from_addon_directory : bpy.props.BoolProperty(
       name=translate(".Blend located in addon Directory?"),
       description=translate("Perhaps your centralized .blend is located within an addon? if it is the case, toggle this option, scatter will search for a .blend with such name in the addon folder."),
       default=False,
       )
    """

    #biome export gui steps
    biocrea_creation_steps : bpy.props.IntProperty(
        default=0,
        )

class SCATTER5_PR_generate_thumbnail(bpy.types.PropertyGroup): 
    """scat_op = bpy.context.scene.scatter5.operators.generate_thumbnail
    decentralized settings of SCATTER5_OT_generate_thumbnail"""

    thumbcrea_camera_type : bpy.props.EnumProperty(
        name=translate("Distance"),
        default="cam_small", 
        items=( ("cam_forest" ,translate("Far") ,""),
                ("cam_plant" ,translate("Medium") ,""),
                ("cam_small" ,translate("Near") ,""),
              ),
        )
    thumbcrea_placeholder_type : bpy.props.EnumProperty(
        name=translate("Instance"),
        default="SCATTER5_placeholder_extruded_square", 
        items=(("SCATTER5_placeholder_extruded_triangle",     translate("Extruded Triangle") ,""     ,"MESH_CUBE", 1 ),
               ("SCATTER5_placeholder_extruded_square",       translate("Extruded Square") ,""       ,"MESH_CUBE", 2 ),
               ("SCATTER5_placeholder_extruded_pentagon",     translate("Extruded Pentagon") ,""     ,"MESH_CUBE", 3 ),
               ("SCATTER5_placeholder_extruded_hexagon",      translate("Extruded Hexagon") ,""      ,"MESH_CUBE", 4 ),
               ("SCATTER5_placeholder_extruded_decagon",      translate("Extruded Decagon") ,""      ,"MESH_CUBE", 5 ),
               ("SCATTER5_placeholder_pyramidal_triangle",    translate("Pyramidal Triangle") ,""    ,"MESH_CONE", 6 ),
               ("SCATTER5_placeholder_pyramidal_square",      translate("Pyramidal Square") ,""      ,"MESH_CONE", 7 ),
               ("SCATTER5_placeholder_pyramidal_pentagon",    translate("Pyramidal Pentagon") ,""    ,"MESH_CONE", 8 ),
               ("SCATTER5_placeholder_pyramidal_hexagon",     translate("Pyramidal Hexagon") ,""     ,"MESH_CONE", 9 ),
               ("SCATTER5_placeholder_pyramidal_decagon",     translate("Pyramidal Decagon") ,""     ,"MESH_CONE", 10 ),
               ("SCATTER5_placeholder_flat_triangle",         translate("Flat Triangle") ,""         ,"SNAP_FACE", 11 ),
               ("SCATTER5_placeholder_flat_square",           translate("Flat Square") ,""           ,"SNAP_FACE", 12 ),
               ("SCATTER5_placeholder_flat_pentagon",         translate("Flat Pentagon") ,""         ,"SNAP_FACE", 13 ),
               ("SCATTER5_placeholder_flat_hexagon",          translate("Flat Hexagon") ,""          ,"SNAP_FACE", 14 ),
               ("SCATTER5_placeholder_flat_decagon",          translate("Flat Decagon") ,""          ,"SNAP_FACE", 15 ),
               ("SCATTER5_placeholder_card_triangle",         translate("Card Triangle") ,""         ,"MESH_PLANE", 16 ),
               ("SCATTER5_placeholder_card_square",           translate("Card Square") ,""           ,"MESH_PLANE", 17 ),
               ("SCATTER5_placeholder_card_pentagon",         translate("Card Pentagon") ,""         ,"MESH_PLANE", 18 ),
               ("SCATTER5_placeholder_hemisphere_01",         translate("Hemisphere 01") ,""         ,"MESH_ICOSPHERE", 19 ),
               ("SCATTER5_placeholder_hemisphere_02",         translate("Hemisphere 02") ,""         ,"MESH_ICOSPHERE", 20 ),
               ("SCATTER5_placeholder_hemisphere_03",         translate("Hemisphere 03") ,""         ,"MESH_ICOSPHERE", 21 ),
               ("SCATTER5_placeholder_hemisphere_04",         translate("Hemisphere 04") ,""         ,"MESH_ICOSPHERE", 22 ),
               ("SCATTER5_placeholder_lowpoly_pine_01",       translate("Lowpoly Pine 01") ,""       ,"LIGHT_POINT", 23 ),
               ("SCATTER5_placeholder_lowpoly_pine_02",       translate("Lowpoly Pine 02") ,""       ,"LIGHT_POINT", 24 ),
               ("SCATTER5_placeholder_lowpoly_coniferous_01", translate("Lowpoly Coniferous 01") ,"" ,"LIGHT_POINT", 25 ),
               ("SCATTER5_placeholder_lowpoly_coniferous_02", translate("Lowpoly Coniferous 02") ,"" ,"LIGHT_POINT", 26 ),
               ("SCATTER5_placeholder_lowpoly_coniferous_03", translate("Lowpoly Coniferous 03") ,"" ,"LIGHT_POINT", 27 ),
               ("SCATTER5_placeholder_lowpoly_coniferous_04", translate("Lowpoly Coniferous 04") ,"" ,"LIGHT_POINT", 28 ),
               #("SCATTER5_placeholder_lowpoly_sapling_01",    translate("Lowpoly Sapling 01"),""     ,"LIGHT_POINT", 29 ), #Do not make sense to render all this below
               #("SCATTER5_placeholder_lowpoly_sapling_02",    translate("Lowpoly Sapling 02"),""     ,"LIGHT_POINT", 30 ),
               #("SCATTER5_placeholder_lowpoly_cluster_01",    translate("Lowpoly Cluster 01") ,""    ,"STICKY_UVS_LOC", 31 ),
               #("SCATTER5_placeholder_lowpoly_cluster_02",    translate("Lowpoly Cluster 02") ,""    ,"STICKY_UVS_LOC", 32 ),
               #("SCATTER5_placeholder_lowpoly_cluster_03",    translate("Lowpoly Cluster 03") ,""    ,"STICKY_UVS_LOC", 33 ),
               #("SCATTER5_placeholder_lowpoly_cluster_04",    translate("Lowpoly Cluster 04") ,""    ,"STICKY_UVS_LOC", 34 ),
               #("SCATTER5_placeholder_lowpoly_plant_01",      translate("Lowpoly Plant 01") ,""      ,"OUTLINER_OB_HAIR", 35 ),
               #("SCATTER5_placeholder_lowpoly_plant_02",      translate("Lowpoly Plant 02") ,""      ,"OUTLINER_OB_HAIR", 36 ),
               #("SCATTER5_placeholder_lowpoly_plant_03",      translate("Lowpoly Plant 03") ,""      ,"OUTLINER_OB_HAIR", 38 ),
               #("SCATTER5_placeholder_lowpoly_flower_01",     translate("Lowpoly Flower 01"),""      ,"OUTLINER_OB_HAIR", 39 ),
               #("SCATTER5_placeholder_lowpoly_flower_02",     translate("Lowpoly Flower 02"),""      ,"OUTLINER_OB_HAIR", 40 ),
               #("SCATTER5_placeholder_helper_empty_stick",    translate("Helper Empty Stick") ,""    ,"EMPTY_ARROWS", 41 ),
               #("SCATTER5_placeholder_helper_empty_arrow",    translate("Helper Empty Arrow") ,""    ,"EMPTY_ARROWS", 42 ),
               #("SCATTER5_placeholder_helper_empty_axis",     translate("Helper Empty Axis") ,""     ,"EMPTY_ARROWS", 43 ),
               #("SCATTER5_placeholder_helper_colored_axis",   translate("Helper Colored Axis") ,""   ,"EMPTY_ARROWS", 44 ),
               #("SCATTER5_placeholder_helper_colored_cube",   translate("Helper Colored Cube") ,""   ,"EMPTY_ARROWS", 45 ),
               ("SCATTER5_placeholder_helper_y_arrow",        translate("Helper Tangent Arrow") ,""  ,"EMPTY_ARROWS", 46 ),
              ),
        )
    thumbcrea_placeholder_color : bpy.props.FloatVectorProperty( 
        name=translate("Color"),
        default=(1,0,0.5),
        min=0,
        max=1,
        subtype="COLOR",
        )
    thumbcrea_placeholder_scale : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        subtype="XYZ", 
        default=(0.25,0.25,0.25), 
        )
    thumbcrea_use_current_blend_path  : bpy.props.BoolProperty(
        default=False,
        name=translate("Use current blend file"),
        update=upd_thumbcrea_use_current_blend_path,
        )
    thumbcrea_custom_blend_path  : bpy.props.StringProperty(
        name=translate("Blend Path"),
        description=translate("Geo-Scatter will open this .blend add the biome on the emitter named below then launch a render."),
        default=os.path.join(directories.addon_thumbnail,"custom_biome_icons.blend"),
        )
    thumbcrea_custom_blend_emitter : bpy.props.StringProperty(
        name=translate("Emit. Name"),
        description=translate("Enter the emitter name from the blend above please."),
        default="Ground",
        )
    thumbcrea_render_iconless : bpy.props.BoolProperty(
        default=False,
        name=translate("Render all biomes with no preview"),
        )
    thumbcrea_auto_reload_all : bpy.props.BoolProperty(
        default=True,
        name=translate("Reload library afterwards"),
        )

class SCATTER5_PR_objects(bpy.types.PropertyGroup):

    name : bpy.props.StringProperty(
        get=lambda self: self.object.name if (self.object is not None) else ""
        )
    object : bpy.props.PointerProperty(
        type=bpy.types.Object,
        )


#TODO maybe later we'll define instances list like we do with f_surfaces...
"""
class Inherit_f_instances:

    f_instances : bpy.props.CollectionProperty(
        type=SCATTER5_PR_objects,
        ) #internal use by SCATTER5_OT_define_objects

    #default is define in the end

    f_instances_method : bpy.props.EnumProperty(
        name=translate("Which objects would you like to distribute?"),
        default="define",
        items=( ("selection",translate("Use Current Selection"),translate("The object(s) currently selected will become the future instances of your scatter-system"),"RESTRICT_SELECT_OFF",1),
                ("define",translate("Define When Called"),translate("Upon scattering, we will ask to select your future instances"),"BORDERMOVE",2),
              ),
        )

    f_selection_method #TODO move in here and make define default???????
"""

class Inherit_f_surfaces:

    f_surfaces : bpy.props.CollectionProperty(
        type=SCATTER5_PR_objects,
        ) #internal use by SCATTER5_OT_define_objects + creation panel popovers
    
    f_surface_method : bpy.props.EnumProperty(
        name=translate("Method"),
        default="emitter", 
        items=( ("emitter",translate("Emitter"),translate("Distribute instances only on the surface of your emitter object."),"INIT_ICON:W_EMITTER",1),
                ("object",translate("Single Object"),translate("Distribute instances on the surface of any chosen object. This leads to a non-linear workflow."),"INIT_ICON:W_SURFACE_SINGLE",2),
                ("collection",translate("Multi-Object(s)"),translate("Distribute instances on the surface(s) of all objects in given collection. This leads to a non-linear workflow."),"INIT_ICON:W_SURFACE_MULTI",3),
                #("define",translate("Define When Called"),translate("Upon scattering, we will ask to select your future instances"),"BORDERMOVE",4),
              ),#for SCATTER5_OT_define_objects later perhaps?
        )
    f_surface_object : bpy.props.PointerProperty(
        type=bpy.types.Object,
        description=translate("Non-Linear Surface"),
        )

    def get_f_surfaces(self):
        """return a list of surface object(s)"""

        if (self.f_surface_method=="emitter"):
            return [bpy.context.scene.scatter5.emitter]

        elif (self.f_surface_method=="object"):
            return [self.f_surface_object] if (self.f_surface_object is not None) else []

        elif (self.f_surface_method=="collection"):
            return [e.object for e in self.f_surfaces if (e.object is not None)]

        return []

    def add_selection(self):
        """add the viewport selection to the list of surfaces"""

        for o in bpy.context.selected_objects:
            if (o.type!="MESH"):
                continue
            if (o in [o.object for o in self.f_surfaces]):
                continue
            #add obj to surfaces
            x = self.f_surfaces.add()
            x.object = o
            #refresh squarea area
            o.scatter5.estimate_square_area()
            continue

        return None 


class Inherit_f_mask_settings: 

    f_mask_action_method : bpy.props.EnumProperty(
        name=translate("Masking Operation"),
        default="none", 
        items=( ("none",translate("None"),"","PANEL_CLOSE",1),
                ("assign",translate("Assign Mask"),"","EYEDROPPER",2),
                ("paint",translate("Paint Mask"),"","BRUSH_DATA",3),
              ),
        )
    f_mask_action_type : bpy.props.EnumProperty(
        name=translate("Mask Type"),
        default="vg", 
        items=( ("vg",translate("Vertex-group"),"","GROUP_VERTEX",1),
                ("bitmap",translate("Image"),"","IMAGE_DATA",2),
                ("curve",translate("Bezier-Area"),"","CURVE_BEZCIRCLE",3),
              ),
        )
    f_mask_assign_vg : bpy.props.StringProperty(
        default="",
        )
    f_mask_assign_bitmap : bpy.props.StringProperty(
        default="",
        )
    f_mask_assign_curve_area : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        poll=poll_closed_curve_type,
        )
    f_mask_assign_reverse : bpy.props.BoolProperty(
        default=False,
        )
    f_mask_paint_vg : bpy.props.StringProperty(
        default="",
        )
    f_mask_paint_bitmap : bpy.props.StringProperty(
        default="",
        )
    f_mask_paint_curve_area : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        poll=poll_closed_curve_type,
        )

class Inherit_f_visibility_settings:

    f_visibility_hide_viewport : bpy.props.BoolProperty(
        default=False,
        )
    f_visibility_facepreview_allow : bpy.props.BoolProperty(
        default=False,
        )
    f_visibility_view_allow : bpy.props.BoolProperty(
        default=False,
        )
    f_visibility_view_percentage : bpy.props.FloatProperty(
        name=translate("Rate"),
        default=80,
        subtype="PERCENTAGE",
        min=0,
        max=100, 
        )
    f_visibility_cam_allow : bpy.props.BoolProperty(
        default=False,
        name=translate("Camera Optimizations"),
        )
    f_visibility_camclip_allow : bpy.props.BoolProperty(
        default=True,
        name=translate("Frustum Culling"),
        description=translate("Only show instances inside the active-camera frustum volume"),
        )
    f_visibility_camclip_cam_boost_xy : bpy.props.FloatProperty(
        name=translate("FOV Boost"),
        default=0.04,
        soft_min=-2,
        soft_max=2, 
        precision=3,
        )
    f_visibility_camdist_allow : bpy.props.BoolProperty(
        default=False,
        name=translate("Distance Culling"),
        description=translate("Only show close to the camera"),
        )
    f_visibility_camdist_min : bpy.props.FloatProperty(
        name=translate("Falloff Min"),
        default=10,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        )
    f_visibility_camdist_max : bpy.props.FloatProperty(
        name=translate("Falloff Max"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        )
    f_visibility_maxload_allow : bpy.props.BoolProperty( 
        description=translate("Define the maximal amount of instances you are able to see in the viewport"),
        default=False,
        )
    f_visibility_maxload_cull_method : bpy.props.EnumProperty(
        name=translate("What to do once reaching chosen instance count threshold?"),
        default="maxload_limit",
        items=( ("maxload_limit", translate("Limit"),translate("Limit how many instances are visible on screen. The total amount of instances produced by this scatter-system will never exceed the given threshold."),),
                ("maxload_shutdown", translate("Shutdown"),translate("If total amount of instances produced by this scatter-system goes beyond given threshold, we will shutdown the visibility of this system entirely"),),
              ),
        )
    f_visibility_maxload_treshold : bpy.props.IntProperty(
        description=translate("The system will either limit or shutdown what's visible, approximately above the chosen threshold"),
        name=translate("Max Instances"),
        min=1,
        soft_min=1_000,
        soft_max=9_999_999,
        default=199_000,
        )

class Inherit_f_display_settings:

    f_display_allow : bpy.props.BoolProperty(
        default=False,
        )
    f_display_method : bpy.props.EnumProperty(
        name=translate("Display as"),
        default="placeholder", 
        items=( ("bb", translate("Bounding-Box"), translate(""), "CUBE",1 ),
                ("convexhull", translate("Convex-Hull"), translate(""), "MESH_ICOSPHERE",2 ),
                ("placeholder", translate("Placeholder"), translate(""), "MOD_CLOTH",3 ),
                ("placeholder_custom", translate("Custom Placeholder"), translate(""), "MOD_CLOTH",4 ),
                ("point", translate("Single Point"), translate(""), "LAYER_ACTIVE",5 ),
                ("cloud", translate("Point-Cloud"), translate(""), "OUTLINER_OB_POINTCLOUD",7 ),
              ),
        )
    f_display_custom_placeholder_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        )
    f_display_bounding_box : bpy.props.BoolProperty(
        default=False,
        )

class Inherit_f_security_settings:

    f_sec_count_allow : bpy.props.BoolProperty(
        default=True,
        )
    f_sec_count : bpy.props.IntProperty(
        default=199_000,
        min=1_000,
        description=translate("This threshold value represents the maximal visible particle count. If threshold reached on scattering operation, Geo-Scatter will automatically hide your particle system.")
        )
    f_sec_verts_allow : bpy.props.BoolProperty(
        default=True,
        )
    f_sec_verts : bpy.props.IntProperty(
        default=199_000,
        min=1_000,
        description=translate("This threshold value represents the maximal allowed vertex count of your future instance(s). If the threshold has been reached during the scattering operation, Geo-Scatter will automatically set your instance(s) display as wired bounding box.")
        )

class SCATTER5_PR_creation_operators(bpy.types.PropertyGroup, Inherit_f_visibility_settings, Inherit_f_display_settings, Inherit_f_security_settings, Inherit_f_surfaces,):
    """scat_op = bpy.context.scene.scatter5.operators.create_operators
    shared decentralized settings of most creation panel operators"""

    #+f_surfaces
    #+f_visibility
    #+f_display
    #+f_sec

    pass


class SCATTER5_PR_creation_operator_add_psy_density(bpy.types.PropertyGroup, Inherit_f_mask_settings,):
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_density
    decentralized settings of SCATTER5_OT_add_psy_density"""

    #density options

    f_distribution_density : bpy.props.FloatProperty(
        name=translate("Instances"), 
        default=10,
        min=0,
        precision=3,
        )
    f_density_scale : bpy.props.EnumProperty(
        name=translate("Density Scale"),
        default="m", 
        items=( ("cm", translate("/ cm²"), "",),
                ("m", translate("/ m²"), "",),
                ("ha", translate("/ ha"), "",),
                ("km", translate("/ km²"), "",),
              ),
        )

    #selection method 

    selection_mode : bpy.props.EnumProperty(
        name=translate("Selection Method"),
        default="viewport", 
        items=( ("viewport", translate("Viewport Selection"), translate("Scatter the selected compatible objects found in the viewport"), "VIEW3D",1 ),
                ("browser", translate("Browser Selection"), translate("Scatter the selected object found in the asset browser"), "ASSET_MANAGER",2 ),
              ),
        )

    #+f_mask


class SCATTER5_PR_creation_operator_add_psy_preset(bpy.types.PropertyGroup, Inherit_f_mask_settings,): 
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_preset
    decentralized settings of SCATTER5_OT_add_psy_preset"""

    #used mostly in creation interface, 
    #args will be passed from interface to operator

    preset_path : bpy.props.StringProperty(
        default="Please Choose a Preset",
        subtype="FILE_PATH",
        ) 
    preset_name : bpy.props.StringProperty(
        name=translate("Display Name"),
        description=translate("Future name of your particle system."),
        default="Default Preset",
        )
    preset_color : bpy.props.FloatVectorProperty( #default color used for preset_find_color if nothing found. only used for GUI
        name=translate("Display Color"),
        description=translate("Future color of your particle system."),
        default=(1,1,1),
        min=0,
        max=1,
        subtype="COLOR",
        )
    preset_find_name : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the name of the first selected instance object as the name of your future scatter-system, instead of the preset name"),
        )
    preset_find_color : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the first material display color of your fist selected instance object as the color of your future scatter-system, instead of the preset color"),
        )

    #estimate in interface directly 

    estimated_preset_density : bpy.props.FloatProperty(
        name=translate("Estimated Instances /m²"),
        default=0,
        )
    estimated_preset_keyword : bpy.props.StringProperty(
        default="",
        ) #in order to estimate the final density we need keyword information

    #selection method 

    selection_mode : bpy.props.EnumProperty(
        name=translate("Selection Method"),
        default="viewport", 
        items=( ("viewport", translate("Viewport Selection"), translate("Scatter the selected compatible objects found in the viewport"), "VIEW3D",1 ),
                ("browser", translate("Browser Selection"), translate("Scatter the selected object found in the asset browser"), "ASSET_MANAGER",2 ),
              ),
        )

    #+f_mask


class SCATTER5_PR_creation_operator_add_psy_manual(bpy.types.PropertyGroup,):
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_manual
    decentralized settings of SCATTER5_OT_add_psy_manual"""

    #special rotatin options for manual

    f_rot_random_allow : bpy.props.BoolProperty(
        default=True,
        description=translate("Enable the random rotation procedural setting directly upon creation"),
        )
    f_scale_random_allow : bpy.props.BoolProperty(
        default=True,
        description=translate("Enable the random scale procedural setting directly upon creation"),
        )

    #selection method 

    selection_mode : bpy.props.EnumProperty(
        name=translate("Selection Method"),
        default="viewport", 
        items=( ("viewport", translate("Viewport Selection"), translate("Scatter the selected compatible objects found in the viewport"), "VIEW3D",1 ),
                ("browser", translate("Browser Selection"), translate("Scatter the selected object found in the asset browser"), "ASSET_MANAGER",2 ),
              ),
        )


class SCATTER5_PR_creation_operator_add_psy_modal(bpy.types.PropertyGroup, Inherit_f_mask_settings,):
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_modal
    decentralized settings of the add_psy_modal series of operators"""

    #define default density

    f_distribution_density : bpy.props.FloatProperty(
        name=translate("Instances/m²"), 
        default=3,
        min=0,
        precision=3,
        )

    #+f_mask (using method&type, hidden from user, used by operator)


class SCATTER5_PR_creation_operator_load_biome(bpy.types.PropertyGroup, Inherit_f_mask_settings,):
    """scat_op = bpy.context.scene.scatter5.operators.load_biome
    decentralized settings of SCATTER5_OT_load_biome"""

    #biomes progress

    progress_bar : bpy.props.FloatProperty(
        default=0,
        subtype="PERCENTAGE",
        soft_min=0, 
        soft_max=100, 
        precision=0,
        )
    progress_label : bpy.props.StringProperty(
        default="",
        )
    progress_context : bpy.props.StringProperty(
        default="",
        )

    #special display for biomes 

    f_display_biome_allow : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the display method encoded in the biome file"),
        )

    #+f_mask


class SCATTER5_PR_operators(bpy.types.PropertyGroup): 
    """scat_ops = bpy.context.scene.scatter5.operators"""

    save_operator_preset : bpy.props.PointerProperty(type=SCATTER5_PR_save_operator_preset)
    save_biome_to_disk_dialog : bpy.props.PointerProperty(type=SCATTER5_PR_save_biome_to_disk_dialog)
    generate_thumbnail : bpy.props.PointerProperty(type=SCATTER5_PR_generate_thumbnail)
    
    create_operators : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operators)
    add_psy_preset   : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_preset)
    add_psy_density  : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_density)
    add_psy_manual   : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_manual)
    add_psy_modal    : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_modal)
    load_biome       : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_load_biome)



#####################################################################################################
# 
# ooo        ooooo                    oooo             ooooo         o8o               .
# `88.       .888'                    `888             `888'         `"'             .o8
#  888b     d'888   .oooo.    .oooo.o  888  oooo        888         oooo   .oooo.o .o888oo
#  8 Y88. .P  888  `P  )88b  d88(  "8  888 .8P'         888         `888  d88(  "8   888
#  8  `888'   888   .oP"888  `"Y88b.   888888.          888          888  `"Y88b.    888
#  8    Y     888  d8(  888  o.  )88b  888 `88b.        888       o  888  o.  )88b   888 .
# o8o        o888o `Y888""8o 8""888P' o888o o888o      o888ooooood8 o888o 8""888P'   "888"
# 
#####################################################################################################



import bpy

from .. resources.icons import cust_icon
from .. resources.translate import translate



#####################################################################################################



class SCATTER5_PR_procedural_vg(bpy.types.PropertyGroup):  #registered in .properties
    """bpy.context.scene.scatter5.emitter.scatter5.mask_systems"""

    name       : bpy.props.StringProperty() # Vg name
    user_name  : bpy.props.StringProperty() # User Name, gui purpose
    type       : bpy.props.StringProperty() # Type must be same name as mask module name! 
    icon       : bpy.props.StringProperty() # Defined by the type
    mod_list   : bpy.props.StringProperty() # List of modifiers related to this mask  (separated by '_!#!_')
    obj_list   : bpy.props.StringProperty() # List of objects related to this mask  (separated by '_!#!_')
    coll_list  : bpy.props.StringProperty() # List of collections related to this mask  (separated by '_!#!_')
    anim       : bpy.props.BoolProperty(description=translate("Recalculate this mask for each frame during animation"))
    open_main  : bpy.props.BoolProperty(default=1)

    #general settings, common for some masks 

    axis : bpy.props.EnumProperty(
        default="z",
        name="",
        items=[("x","X","",1), ("y","Y","",2), ("z","Z","",3)] ,
        description=translate("Choose your calculation axis"),
        )

    absolute : bpy.props.BoolProperty(
        default=True,
        description=translate("Convert negative values to positive"),
        )

    normalize : bpy.props.BoolProperty(
        default=True,
        description=translate("Normalize values (remap min/max range between 0 and 1)"),
        )

    direction_vector : bpy.props.FloatVectorProperty(
        subtype="DIRECTION",
        default=(1,1,1),
        min=-1,
        max=1,
        )

    distance : bpy.props.FloatProperty(
        default=1,
        subtype="DISTANCE",
        min=0.01,
        soft_max=20,
        )

    mask_p_collection : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        )
    mask_p_collection2 : bpy.props.PointerProperty(
        type=bpy.types.Collection,
        )

    object_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object,
        )
    
    curve_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda s,o: o.type=="CURVE",
        )

    #psy proximity 

    psy_name : bpy.props.StringProperty()
    
    #mask specific 

    #aspect 

    aspec_angle : bpy.props.FloatProperty(
        default=0,
        subtype="ANGLE",
        description=translate("Choose your aspect map start angle"),
        )
    aspec_division : bpy.props.IntProperty(
        default=1,
        min=1,
        max=360,
        description=translate("By default the mask will analyse your terrain slope orientation from 0 to 360 degrees (360 = 1 division)."),
        )

    #normal 

    n_axis  : bpy.props.EnumProperty(
        name="", 
        default="x",
        items=[("x","X","",),
               ("y","Y","",),
               ("z","Z","",),
               ("xyz","XYZ","",),
               ("custom","Custom Direction","",),
              #("object","Object Direction","",),
               ("location","Object Location","",)],
        description=translate("Choose your normal orientation"),
        )

    #position 

    pos_space : bpy.props.EnumProperty(
        name="", 
        default="LOCAL",
        items=[("LOCAL"   ,translate("Local")                 ,"",1),
               ("GLOBAL"  ,translate("Global")                ,"",2),
               ("OBJECT"  ,translate("Object")                ,"",3),
               ("OBJECT_P",translate("Object (Location only)"),"",4),],
        description=translate("Choose the space of your coordinates"),
        )
    
    pos_mode : bpy.props.EnumProperty(
        name="", 
        default="DISTANCE",
        items=[("DISTANCE" ,translate("Euclidean Distance")   ,translate("Euclidean distance from given axis origin within given world-space"),1),
               ("QUADRAN"  ,translate("Position in Quadrant") ,translate("Quadrant Information from given axis origin within given world-space"),2),],
        description=translate("Choose your calculation method"),
        )

    pos_axis : bpy.props.EnumProperty(
        name="", 
        default="xyz",
        items=[("xy" ,translate("XY") ,"",1),
               ("xyz",translate("XYZ"),"",2),
               ("x"  ,translate("X")  ,"",3),
               ("y"  ,translate("Y")  ,"",4),
               ("z"  ,translate("Z")  ,"",5),],
        description=translate("Choose your Axis"),
        )

    #curvature
    
    cur_crop : bpy.props.FloatProperty(
        default=0, 
        min=0, 
        soft_max=5, 
        description=translate("Some angles may steal all the weight from your curvature map, you can crop extremes values with this property"),
        )
    cur_smooth : bpy.props.IntProperty(
        default=0, 
        min=0,
        soft_max=10, 
        description=translate("Smooth your mask vertex-groups. useful if your mask generate imperfections."),
        )

    #mesh data
    
    mesh_data_method : bpy.props.EnumProperty(
        name="", 
        default="face_material",
        items=[("face_smooth"    ,translate("Smooth")      ,"" ,"FACESEL" ,1),
               ("face_freestyle" ,translate("Freestyle")   ,"" ,"FACESEL" ,2),
               ("face_material"  ,translate("Material ID") ,"" ,"FACESEL" ,3),
               ("face_area"      ,translate("Area")        ,"" ,"FACESEL" ,4),
               ("face_index"     ,translate("Index")       ,"" ,"FACESEL" ,5), 
               ("edge_bevel"     ,translate("Bevel")       ,"" ,"EDGESEL" ,6),      
               ("edge_crease"    ,translate("Crease")      ,"" ,"EDGESEL" ,7),       
               ("edge_sharp"     ,translate("Sharp (+Distance)")     ,"" ,"EDGESEL" ,8),      
               ("edge_freestyle" ,translate("Freestyle (+Distance)") ,"" ,"EDGESEL" ,9),          
               ("edge_seam"      ,translate("Seam (+Distance)")      ,"" ,"EDGESEL" ,10),     
               ("edge_len"       ,translate("Length")      ,"" ,"EDGESEL" ,11),    
               ("edge_index"     ,translate("Index")       ,"" ,"EDGESEL" ,12),       
              ],
        description=translate("Calculate lighting of given lamps:"),
        )

    mesh_data_prox_distance : bpy.props.FloatProperty(
        default=1,
        subtype="DISTANCE",
        min=0,
        soft_max=20,
        )
    mesh_data_prox_offset : bpy.props.FloatProperty(
        description= translate("Offset your weight, Offset number always need to be below distance number"),
        default=0,
        subtype="DISTANCE",
        min=0,
        soft_max=20,
        )

    #camera visibility 

    visib_cam_method : bpy.props.EnumProperty(
        name="", 
        default="active",
        items=[("given" ,translate("Given Camera") ,"",1),
               ("active",translate("Active Camera") ,"",2),
               ("all"   ,translate("Every Camera(s)") ,"",3),],
        description=translate("Calculate visibility from given camera(s)"),
        )

    visib_calc_method : bpy.props.EnumProperty(
        name="", 
        default="self",
        items=[("self"  ,translate("Emitter Only")     ,translate("Rays will only collide with emitter geometry, ignoring every objects"),1),
               ("col"   ,translate("Given Collection") ,translate("Rays will only collide with emitter and objects inside given collection"),2),
               ("scene" ,translate("Whole Scene")      ,translate("Rays will take whole scene into consideration (might be heavy to calculate, you might want to hide some objects)"),3),],
        description=translate("Ray-casting from given camera will collide with:"),
        )
    
    visib_cam : bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda s,o: o.type=="CAMERA",
        )

    visib_clip_distance : bpy.props.BoolProperty(
        default=False,
        )
    visib_clip_distance_value : bpy.props.FloatProperty(
        name=translate("Clip Distance"),
        default=300,
        subtype="DISTANCE",
        )

    visib_expand : bpy.props.BoolProperty(
        default=False,
        description=translate("Expand the calculated weight by given steps below")
        )    
    visib_expand_steps : bpy.props.IntProperty(
        name=translate("steps"),
        default=2,
        min=1,
        soft_max=25
        )       

    visib_fov_boost : bpy.props.BoolProperty(
        description=translate("Boost your camera(s) FOV during calculation")
        )     
    visib_fov_boost_factor : bpy.props.FloatProperty(
        name=translate("factor"),
        default=1.25,
        min=1,
        soft_max=2
        )

    visib_culling : bpy.props.BoolProperty(
        default=False,
        )
    visib_culling_min : bpy.props.FloatProperty(
        name=translate("min distance"),
        default=10,
        min=0,
        subtype="DISTANCE",
        )
    visib_culling_max : bpy.props.FloatProperty(
        name=translate("max distance"),
        default=250,
        min=0,
        subtype="DISTANCE",
        )

    #masks that use baking 

    bake_obstacles : bpy.props.EnumProperty(
        name="", 
        default="scene",
        items=[("self"  ,translate("Emitter Only")     ,translate("Rays collision only with emitter geometry, ignoring every objects"),1),
               ("col"   ,translate("Given Collection") ,translate("Rays collision only with emitter and objects inside given collection"),2),
               ("scene" ,translate("Whole Scene")      ,translate("Rays collision on whole scene into consideration (might be heavy to calculate, you might want to hide some objects)"),3),],
        description=translate("AO Rays with collide with:"),
        )

    hide_particles : bpy.props.BoolProperty(
        default=True, 
        description=translate("Don't take scatter-system(s) into consideration during calculatation"),
        )

    bake_samples : bpy.props.IntProperty(
        default=32,
        soft_max=4000,
        min=1,
        )

    bake_light_method : bpy.props.EnumProperty(
        name="", 
        default="scene",
        items=[("selected"  ,translate("Selected")     ,"",1),
               ("ptr"   ,translate("Given Light")      ,"",2),
               ("col"   ,translate("Given Collection") ,"",3),
               ("scene" ,translate("Whole Scene")      ,"",4),],
        description=translate("Calculate lighting of given lamps:"),
        )

    def poll_light_type(self, object):
        return (object.type == "LIGHT")
    bake_light_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=poll_light_type,
        )


#if __name__ == "__main__":
#    register()
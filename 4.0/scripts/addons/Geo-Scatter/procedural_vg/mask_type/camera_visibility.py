
#####################################################################################################
#
#   .oooooo.                                    oooooo     oooo  o8o            o8o   .o8        o8o  oooo   o8o      .
#  d8P'  `Y8b                                    `888.     .8'   `"'            `"'  "888        `"'  `888   `"'    .o8
# 888           .oooo.   ooo. .oo.  .oo.          `888.   .8'   oooo   .oooo.o oooo   888oooo.  oooo   888  oooo  .o888oo oooo    ooo
# 888          `P  )88b  `888P"Y88bP"Y88b          `888. .8'    `888  d88(  "8 `888   d88' `88b `888   888  `888    888    `88.  .8'
# 888           .oP"888   888   888   888           `888.8'      888  `"Y88b.   888   888   888  888   888   888    888     `88..8'
# `88b    ooo  d8(  888   888   888   888            `888'       888  o.  )88b  888   888   888  888   888   888    888 .    `888'
#  `Y8bood8P'  `Y888""8o o888o o888o o888o            `8'       o888o 8""888P' o888o  `Y8bod8P' o888o o888o o888o   "888"     .8'
#                                                                                                                         .o..P'
#                                                                                                                         `Y8P'
#####################################################################################################



import bpy
import numpy as np 
from mathutils import Vector, Matrix

from ... import utils 
from ... utils.str_utils import no_names_in_double
from ... utils.str_utils import word_wrap

from ... resources.icons import cust_icon
from ... resources.translate import translate


url = "https://www.geoscatter.com/" #just link to website?



# oooooooooo.
# `888'   `Y8b
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888      888  888      .oP"888    `88..]88..8'
#  888     d88'  888     d8(  888     `888'`888'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'



def draw_settings(layout,i):

    scat_scene  = bpy.context.scene.scatter5
    emitter     = scat_scene.emitter
    masks       = emitter.scatter5.mask_systems
    m           = masks[i]

    layout.separator(factor=0.5)

    #layout setup 

    row = layout.row()
    row.row()
    row.scale_y = 0.9

    row1 = row.row()
    row1.scale_x = 0.85
    lbl = row1.column()
    lbl.alignment="RIGHT"

    row2 = row.row()
    prp = row2.column()

    #settings

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Camera(s)"))
    prp.prop(m,"visib_cam_method",text="")

    if m.visib_cam_method == "given":
        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text="")
        prp.prop(m,"visib_cam",text="",icon="CAMERA_DATA")

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Ray Collision"))
    prp.prop(m,"visib_calc_method",text="")

    if m.visib_calc_method == "col":
        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text="")
        prp.prop(m,"mask_p_collection",text="")

    if m.visib_calc_method!="self":
        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text="")
        prp.prop(m,"hide_particles",text=translate("Ignore Scatter"), icon="PARTICLE_DATA")

    lbl.separator(factor=2.7)
    prp.separator(factor=2.7)

    lbl.label(text=translate("Boost Fov"))
    col = prp.column(align=True)
    col.prop(m,"visib_fov_boost",text=translate("Boost Fov"),icon="BLANK1")
    if m.visib_fov_boost:
        lbl.label(text="")
        col.prop(m,"visib_fov_boost_factor")

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Expand"))
    col = prp.column(align=True)
    col.prop(m,"visib_expand",text=translate("Expand Area"),icon="BLANK1")
    if m.visib_expand:
        lbl.label(text="")
        col.prop(m,"visib_expand_steps")

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Clipping"))
    col = prp.column(align=True)
    col.prop(m,"visib_clip_distance",text=translate("Clip Distance"),icon="BLANK1")
    if m.visib_clip_distance:
        lbl.label(text="")
        col.prop(m,"visib_clip_distance_value")

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Culling"))
    col = prp.column(align=True)
    col.prop(m,"visib_culling",text=translate("Distance Cull"),icon="BLANK1")
    if m.visib_culling:
        lbl.label(text="")
        col.prop(m,"visib_culling_min")
        lbl.label(text="")
        col.prop(m,"visib_culling_max")

    if m.visib_culling:
        lbl.separator(factor=2.7)
    else:
        lbl.separator(factor=3.7)
    prp.separator(factor=3.7)

    lbl.label(text=translate("Data"))
    refresh = prp.row(align=True)
    re = refresh.operator("scatter5.refresh_mask",text=translate("Recalculate"),icon="FILE_REFRESH")
    re.mask_type = m.type
    re.mask_idx = i

    #remapping 

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Remap"))
    mod_name   = f"Scatter5 Remapping {m.name}"
    if (mod_name in emitter.modifiers) and (emitter.modifiers[mod_name].falloff_type=="CURVE"):
        mod = emitter.modifiers[mod_name]
        remap = prp.row(align=True)
        o = remap.operator("scatter5.graph_dialog",text=translate("Remap Values"),icon="FCURVE")
        o.source_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}']"
        o.mapping_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}'].map_curve"
        o.mask_name = m.name
        
        butt = remap.row(align=True)
        butt.operator("scatter5.property_toggle",
               text="",
               icon="RESTRICT_VIEW_OFF" if mod.show_viewport else"RESTRICT_VIEW_ON",
               depress=mod.show_viewport,
               ).api = f"bpy.context.scene.scatter5.emitter.modifiers['{mod_name}'].show_viewport"
    else:
        o = prp.operator("scatter5.vg_add_falloff",text=translate("Add Remap"),icon="FCURVE")
        o.mask_name = m.name
        

    #if (m.visib_culling and m.visib_cam_method=="all"):
    #    word_wrap(layout=layout, alignment="CENTER", max_char=45, string=translate("\nNote that distance culling with every cameras at the same time do not make a lot of sense."),)

    layout.separator()

    return 



#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"





#Support Vcol 
#cams = [so for so in scene.objects if so.type == 'CAMERA']
def camera_visibility(
        o,
        vg_name,
        cams=None,
        calc_method="", #self/col/scene
        hide_particles=True,
        collection=None,
        clip_distance=False,
        clip_distance_value=300,
        expand=False,
        expand_steps=2,
        fov_boost=False,
        fov_boost_factor=1.2, 
        culling=False,
        culling_min=5,#distance in meters
        culling_max=50,#distance in meters
        eval_modifiers=False,
        ):

    scene = bpy.context.scene

    # get mesh data
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eo  = o.evaluated_get(depsgraph)
    if eval_modifiers == True:
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    # fov boost
    fov_dict = {}
    if fov_boost:
        for c in  bpy.data.cameras:
            fov_dict[c.name] = c.lens
            c.lens /= fov_boost_factor

    # hide objects if not from coll if coll method
    col_dict = {}
    if (calc_method=="col"):
        if collection is not None:
            coll_objects = [o for o in collection.objects]
            coll_objects.append(o)
            for obj in bpy.context.scene.objects:
                col_dict[obj]=obj.hide_viewport
                if obj not in coll_objects:
                    obj.hide_viewport = True
                continue

    #hide particles?
    if (calc_method in ["col","scene"]) and (hide_particles==True):
        for obj in bpy.context.scene.objects:
            if obj.name.startswith("scatter_obj : "):
                if obj not in col_dict:
                    col_dict[obj]=obj.hide_viewport
                    obj.hide_viewport = True
            continue 

    #get correct clipping distance
    if not clip_distance:
        clip_distance_value = 1.70141e+38

    # create a new numpy array 
    l = len(ob.vertices)
    w = np.array( [0.0]*l)

    # calculate ray traced weight for each cam
    for i,cam in enumerate(cams):
        #self method
        if ( calc_method=='self'):
            camclipw = get_cam_self_raytrace_weights(depsgraph, scene, cam, eo, ob, distance=clip_distance_value, )
        #scene intersection
        elif ( calc_method in ["col","scene"] ) :
            camclipw = get_cam_scene_raytrace_weights(bpy.context.view_layer, scene, cam, eo, ob, distance=clip_distance_value, ) 

        w += camclipw
        continue

    #clamp because addition
    w = np.where((w>1.0),1.0,w)
    
    if culling:

        #get vertices coord 
        co = np.zeros((l * 3), dtype=np.float64, )
        ob.vertices.foreach_get("co", co, ) #going from -1 to 1
        co.shape = (l, 3, )
        co = utils.np_utils.np_apply_transforms(o,co)

        #get culling from weight
        for i,cam in enumerate(cams):
            if i==0:
                  cull = get_culling_distance(co, cam, mindist=culling_min, maxdist=culling_max,)
            else: cull = 1.0-(1.0-cull)*(1.0-get_culling_distance(co, cam, mindist=culling_min, maxdist=culling_max,))
            continue 

        #quickly remove negative values
        cull = np.where((cull<0.0),0.0,cull)
        #normalize & reverse
        cull = utils.np_utils.np_remap(cull, normalized_min=1.0, normalized_max=0.0, skip_denominator=True,)
        #substract culling from weight
        w -= cull

    # apply the new weight
    vg = utils.vg_utils.create_vg(o, vg_name, fill=w, method="REPLACE")

    # expand weight 
    if expand:
        utils.vg_utils.expand_weights(o, vg, iter=expand_steps )

    # reverse weight 
    utils.vg_utils.reverse_vg(o, vg)

    # restore fov if needed
    if fov_dict:
        for k,v in fov_dict.items():
            bpy.data.cameras[k].lens = v

    # restore obj if needed
    if col_dict:
        for obj,show in col_dict.items():
            obj.hide_viewport = show

    return vg

def weight_darken(w1,w2):
    return 1.0-(1.0-w1)*(1.0-w2)

def get_culling_distance(co, cull_obj, mindist=5, maxdist=50,):
    """remove culling distance from information from given weight array"""

    coord = co - cull_obj.location
    distance_field = np.sqrt( coord[:,0]*coord[:,0] + coord[:,1]*coord[:,1] + coord[:,2]*coord[:,2] ) #get hypotenus
    distance_field = utils.np_utils.np_remap(distance_field, array_min=mindist, array_max=maxdist, normalized_min=1.0, normalized_max=0.0, skip_denominator=True,)

    return distance_field

def cam_planes(scene, cam, ):

    cpos = cam.matrix_world.translation.copy()
    cm = cam.matrix_world
    vf = cam.data.view_frame(scene=scene, )
    vf = tuple([cm @ v for v in vf])
    planes_vs = vf + (cpos, )
    planes_fs = ((0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), )
    
    planes = []
    for f in planes_fs:
        a, b, c = tuple([planes_vs[i] for i in f])
        n = Vector(b - a).cross(c - a)
        n.normalize()
        planes.append(n)
    
    return cpos, planes

def get_cam_self_raytrace_weights(depsgraph, scene, cam, eo, eme, epsilon=0.0001, distance=300,):
    """get ray traced from cam info (rays can hit self mesh only)"""

    w = [0.0] * len(eme.vertices)
    cpos, planes = cam_planes(scene, cam, )
    
    eom = eo.matrix_world
    lcpos = eom.inverted() @ cpos
    
    for i, poly in enumerate(eme.polygons):
        v = poly.center
        
        cv = eom @ v
        cvv = cv - cpos
        in_cone = True
        for p in planes:
            if(cvv.dot(p) < 0.0):
                in_cone = False
        if(not in_cone):
            continue
        
        rpos = lcpos
        rdir = v - lcpos
        rdir.normalize()
        result, loc, nor, idx = eo.ray_cast(rpos, rdir, distance=distance, depsgraph=depsgraph, )
        
        if(result):
            if(poly.index == idx):
                if(nor.dot(rdir) < 0.0):
                    for vi in poly.vertices:
                        w[vi] = 1.0
    
    return np.array(w)

def get_cam_scene_raytrace_weights(view_layer, scene, cam, eo, eme, epsilon=0.0001, distance=300,):
    """get ray traced from cam info (rays can hit all scene)"""

    w = [0.0] * len(eme.vertices)
    cpos, planes = cam_planes(scene, cam, )
    
    if(bpy.app.version >= (2, 91, 0)):
        view_layer = view_layer.depsgraph

    eom = eo.matrix_world
    
    for i, poly in enumerate(eme.polygons):
        v = eom @ poly.center
        
        cvv = v - cpos
        in_cone = True
        for p in planes:
            if(cvv.dot(p) < 0.0):
                in_cone = False
        if(not in_cone):
            continue
        
        rpos = cpos
        rdir = v - cpos
        rdir.normalize()
        result, loc, nor, idx, rho, rhom = scene.ray_cast(view_layer, rpos, rdir, distance=distance)
        
        if(result):
            if(rho == eo.original):
                if(poly.index == idx):
                    if(nor.dot(rdir) < 0.0):
                        for vi in poly.vertices:
                            w[vi] = 1.0

    return np.array(w)


def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #only possible if context camera
    if bpy.context.scene.camera is None:
        bpy.ops.scatter5.popup_menu(msgs=translate("This mask need an active camera in order to work"),title=translate("No Scene Camera Detected"),icon="INFO")
        return 

    #add mask to list 
    m = masks.add()
    m.type = "camera_visibility"
    m.icon = "CAMERA_DATA"
    m.name = m.user_name = no_names_in_double("Camera Ray", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create the vertex group
    vg = camera_visibility(
            emitter,
            m.name,
            cams=[bpy.context.scene.camera],
            calc_method=m.visib_calc_method, #self/col/scene
            collection=m.mask_p_collection,
            clip_distance=m.visib_clip_distance,
            clip_distance_value=m.visib_clip_distance_value,
            expand=m.visib_expand,
            expand_steps=m.visib_expand_steps,
            fov_boost=m.visib_fov_boost,
            fov_boost_factor=m.visib_fov_boost_factor, 
            culling=m.visib_culling,
            culling_min=m.visib_culling_min,
            culling_max=m.visib_culling_max,
            )
    vg.lock_weight = True

    return 



# ooooooooo.              .o88o.                             oooo
# `888   `Y88.            888 `"                             `888
#  888   .d88'  .ooooo.  o888oo  oooo d8b  .ooooo.   .oooo.o  888 .oo.
#  888ooo88P'  d88' `88b  888    `888""8P d88' `88b d88(  "8  888P"Y88b
#  888`88b.    888ooo888  888     888     888ooo888 `"Y88b.   888   888
#  888  `88b.  888    .o  888     888     888    .o o.  )88b  888   888
# o888o  o888o `Y8bod8P' o888o   d888b    `Y8bod8P' 8""888P' o888o o888o



def refresh(i,obj=None):

    scat_scene = bpy.context.scene.scatter5

    if obj: 
          emitter = obj
    else: emitter = scat_scene.emitter

    masks    = emitter.scatter5.mask_systems
    m        = masks[i]

    # get cams 
    cams = []
    if (m.visib_cam_method == "given") and (m.visib_cam is not None):
        cams = [m.visib_cam]
    elif (m.visib_cam_method == "all"):
        cams = [o for o in bpy.context.scene.objects if o.type=="CAMERA"]
    elif (m.visib_cam_method == "active") and (bpy.context.scene.camera is not None):
        cams = [bpy.context.scene.camera]

    if len(cams)==0:
        bpy.ops.scatter5.popup_menu(msgs=translate("This mask need at least one camera in order to work"),title=translate("No Camera(s) Detected"),icon="INFO")
        return None 

    vg = camera_visibility(
            emitter,
            m.name,
            cams=cams,
            calc_method=m.visib_calc_method, #self/col/scene
            hide_particles=m.hide_particles,
            collection=m.mask_p_collection,
            clip_distance=m.visib_clip_distance,
            clip_distance_value=m.visib_clip_distance_value,
            expand=m.visib_expand,
            expand_steps=m.visib_expand_steps,
            fov_boost=m.visib_fov_boost,
            fov_boost_factor=m.visib_fov_boost_factor,
            culling=m.visib_culling,
            culling_min=m.visib_culling_min,
            culling_max=m.visib_culling_max,
            )
    vg.lock_weight = True

    return 



# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.  oooo    ooo  .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b  `88.  .8'  d88' `88b
#  888`88b.    888ooo888  888   888   888  888   888   `88..8'   888ooo888
#  888  `88b.  888    .o  888   888   888  888   888    `888'    888    .o
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'     `8'     `Y8bod8P'



def remove(i):
    from ..remove import general_mask_remove
    general_mask_remove(obj_name=bpy.context.scene.scatter5.emitter.name, mask_idx=i)
    return 



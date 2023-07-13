
#####################################################################################################
#
#Position
#
#####################################################################################################


import bpy 
import numpy as np

from ... import utils 
from ... utils.str_utils import no_names_in_double

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

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems
    m          = masks[i]

    layout.separator(factor=0.5)

    #layout setup 

    row = layout.row()
    row.row()
    row.scale_y = 0.9

    row1 = row.row()
    row1.scale_x = 1.201
    lbl = row1.column()
    lbl.alignment="RIGHT"

    row2 = row.row()
    prp = row2.column()

    #settings

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Space"))
    prp.prop(m,"pos_space",text="",)

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    if "OBJECT" in m.pos_space:

        lbl.label(text="")
        prp.prop(m,"object_ptr",text="",)

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

    lbl.label(text=translate("Mode"))
    prp.prop(m,"pos_mode",text="",)

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Axis"))
    prp.prop(m,"pos_axis",text="",)


    if m.pos_mode=="DISTANCE" and m.pos_axis in ["x","y","z"]:

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text=translate("Values"))
        prp.prop(m,"absolute",text="Absolute",icon="BLANK1")

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text=" ")
        prp.prop(m,"normalize",text="Normalize",icon="BLANK1")
    
    lbl.separator(factor=3.7)
    prp.separator(factor=3.7)

    lbl.label(text=translate("Data"))
    refresh = prp.row(align=True)
    re = refresh.operator("scatter5.refresh_mask",text=translate("Recalculate"),icon="FILE_REFRESH")
    re.mask_type = m.type
    re.mask_idx = i

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
        

    layout.separator()

    return 



#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"





def get_position_data(o ,absolute=False, normalize=False, space="LOCAL", mode="DISTANCE", axis="xyz", object=None, eval_modifiers=False, ):

    if "OBJECT" in space and object is None:
        return 0

    if eval_modifiers:
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    # get vertex locations

    l = len(ob.vertices)
    co = np.zeros((l * 3), dtype=np.float64, )
    ob.vertices.foreach_get("co", co, ) #going from -1 to 1
    co.shape = (l, 3, )
    result = np.zeros((l), dtype=np.float64, )

    #convert coordinates to space
    
    if (space=="GLOBAL"):
        co = utils.np_utils.np_apply_transforms(o,co)

    elif (space=="OBJECT_P"):
        co = utils.np_utils.np_apply_transforms(o,co)
        co = co - object.location #just from a position standpoint

    elif (space=="OBJECT"):
        co = utils.np_utils.np_apply_transforms(o,co)
        co = utils.np_utils.np_global_to_local(object, co)
    
    #calculate from given method 

    if (mode=="DISTANCE"):
        #
        if (axis=="xy"):
            result = np.sqrt( co[:,0]*co[:,0] + co[:,1]*co[:,1] ) #get hypotenus
            return utils.np_utils.np_remap(result, normalized_min=1.0, normalized_max=0.0, skip_denominator=True) #reverse
        #
        elif (axis=="xyz"):
            result = np.sqrt( co[:,0]*co[:,0] + co[:,1]*co[:,1] + co[:,2]*co[:,2] ) #get hypotenus
            return utils.np_utils.np_remap(result, normalized_min=1.0, normalized_max=0.0, skip_denominator=True) #reverse
        #
        elif (axis=="x"):
            result = co[:,0]
        #
        elif (axis=="y"):
            result = co[:,1]
        #
        elif (axis=="z"):
            result = co[:,2]
        #
    elif (mode=="QUADRAN"):
        #
        if (axis=="xy"):
            #add values from axis
            result = np.array( [0.25]*l)+ np.where( (co[:,0]<0)==0 ,0.25,0) + np.where( (co[:,1]<0)==1 ,0.25,0)  + np.where( ((co[:,0]<0)&(co[:,1]<0))==1 ,0.5,0)
        #
        elif (axis=="xyz"):
            #first get 2d then multiply by z quadran
            result =  np.where( (co[:,0]<0)==0 ,0.25,0) + np.where( (co[:,1]<0)==1 ,0.25,0)  + np.where( ((co[:,0]<0)&(co[:,1]<0))==1 ,0.5,0)
            result = (result / 2) + np.where( (co[:,2]>0), 0.65,0)
        #
        elif (axis=="x"):
            result = np.array( [0]*l) + np.where( (co[:,0]<0)==0 ,1,0)
        #
        elif (axis=="y"):
            result = np.array( [0]*l) + np.where( (co[:,1]<0)==0 ,1,0)
        #
        elif (axis=="z"):
            result = np.array( [0]*l) + np.where( (co[:,2]<0)==0 ,1,0)

    if absolute:
        result = abs(result)

    if normalize:
        return utils.np_utils.np_remap(result, normalized_min=0.0, normalized_max=1.0, skip_denominator=True)
        
    return result




def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type = "position"
    m.icon = "EMPTY_ARROWS"
    m.name = m.user_name = no_names_in_double("Position", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=get_position_data(emitter), )
    vg.lock_weight = True

    #ORDER MOD??? 
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

    masks     = emitter.scatter5.mask_systems
    m         = masks[i]

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, set_active=False, fill=get_position_data(emitter, absolute=m.absolute, normalize=m.normalize, object=m.object_ptr, space=m.pos_space, mode=m.pos_mode, axis=m.pos_axis,))
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
    general_mask_remove(obj_name=bpy.context.scene.scatter5.emitter.name,mask_idx=i) #remove vg, vgedit, mask from list, refresh viewport
    return 



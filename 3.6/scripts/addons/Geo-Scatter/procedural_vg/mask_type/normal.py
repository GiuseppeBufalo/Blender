
#####################################################################################################
#
# ooooo      ooo                                                oooo
# `888b.     `8'                                                `888
#  8 `88b.    8   .ooooo.  oooo d8b ooo. .oo.  .oo.    .oooo.    888
#  8   `88b.  8  d88' `88b `888""8P `888P"Y88bP"Y88b  `P  )88b   888
#  8     `88b.8  888   888  888      888   888   888   .oP"888   888
#  8       `888  888   888  888      888   888   888  d8(  888   888
# o8o        `8  `Y8bod8P' d888b    o888o o888o o888o `Y888""8o o888o
#
#####################################################################################################


import bpy 
import numpy as np

from math import tan 
from mathutils import Vector

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

    lbl.label(text=translate("Axis"))
    prp.prop(m,"n_axis",text="")

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    if m.n_axis == "custom":

        lbl.label(text=" ")
        lbl.label(text=" ")
        lbl.label(text=" ")
        prp.prop(m,"direction_vector",text="",icon="BLANK1")

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

    elif m.n_axis == "object" or m.n_axis == "location" :

        lbl.label(text=" ")
        prp.prop(m,"object_ptr",text="")

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



def get_normal_data(o, v=[0,0,0], axis=None, absolute=False, normalize=True, object=None, eval_modifiers=False,):

    if axis:

        if axis=='z':
            v = [0,0,1]

        elif axis=='y':
            v = [0,1,0]

        elif axis=='x':
            v = [1,0,0]

        elif axis=='xyz':
            v = [1,1,1]

        #get object direction
        elif axis=='object':
            if not object:
                return 0

            loc, rot, sca = object.matrix_world.decompose()
            v = rot.to_matrix().to_4x4() @ Vector((0.0, 0.0, 1.0)) 

        #get direction vector from a to b 
        elif axis=='location':
            if not object:
                return 0

            a = Vector(o.location[0:])
            b = Vector(object.location[0:])
            v = b-a #to origin
            v.normalize() #normalize

    if eval_modifiers:
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    # get vertex normal
    l = len(ob.vertices)
    n = np.zeros((l * 3), dtype=np.float64, )
    ob.vertices.foreach_get("normal", n, ) #going from -1 to 1
    n.shape = (l, 3, )

    # dot product 
    v = np.array( [v] * l )
    result = np.zeros(l,dtype=np.float64, )
    result = np.einsum("ij,ij->i", v,n)
    
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
    m.type = "normal"
    m.icon = "NORMALS_FACE"
    m.name = m.user_name = no_names_in_double("Normal", [vg.name for vg  in emitter.vertex_groups], startswith00=True)
    m.absolute  = False
    m.normalize = True 

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=get_normal_data(emitter,v=m.direction_vector,axis=m.n_axis,absolute=m.absolute,normalize=m.normalize), )
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

    masks    = emitter.scatter5.mask_systems
    m        = masks[i]

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, set_active=False, fill=get_normal_data(emitter, v=m.direction_vector, axis=m.n_axis, absolute=m.absolute, normalize=m.normalize, object=m.object_ptr,))
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



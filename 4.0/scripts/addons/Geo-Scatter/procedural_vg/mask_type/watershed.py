
#####################################################################################################
#
# oooooo   oooooo     oooo               .                               oooo                        .o8
#  `888.    `888.     .8'              .o8                               `888                       "888
#   `888.   .8888.   .8'    .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o  888 .oo.    .ooooo.   .oooo888
#    `888  .8'`888. .8'    `P  )88b    888   d88' `88b `888""8P d88(  "8  888P"Y88b  d88' `88b d88' `888
#     `888.8'  `888.8'      .oP"888    888   888ooo888  888     `"Y88b.   888   888  888ooo888 888   888
#      `888'    `888'      d8(  888    888 . 888    .o  888     o.  )88b  888   888  888    .o 888   888
#       `8'      `8'       `Y888""8o   "888" `Y8bod8P' d888b    8""888P' o888o o888o `Y8bod8P' `Y8bod88P"
#
#####################################################################################################


import bpy, bmesh, math
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

    lbl.label(text=translate("Values"))
    prp.prop(m,"cur_crop",text="Cropping")

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=" ")
    prp.prop(m,"cur_smooth",text="Smooth")
    
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




def is_convex(v):

    a = [e.calc_face_angle_signed(0.0) for e in v.link_edges]
    if(len(a)):
        return ((sum(a)/len(a))>0)
    return False



def get_watershed_data(o,crop=0, eval_modifiers=False,):

    if eval_modifiers == True:
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    bm = bmesh.new()
    bm.from_mesh(ob)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    values = np.zeros(len(bm.verts), np.float64, )

    for i,v in enumerate(bm.verts):

        if is_convex(v):
            values[i]=0
        else:
            #get neighbor vert
            neighbors = [ e.other_vert(v) for e in v.link_edges ]
            if (not len(neighbors)):
                continue
            #vert to flatten normal angle
            lna = [ abs( math.degrees( math.atan2( n.normal.x,n.normal.y ) ) ) for n in neighbors]
            #get max range of all flatten angles
            values[i] = abs( max(lna)-min(lna) )

    #custom normalization
    crop += 1
    mini = min(values) / crop
    maxi = max(values) / crop

    values = (values-mini) / (maxi-mini)

    return values





def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type = "watershed"
    m.icon = "MATFLUID"
    m.name = m.user_name = no_names_in_double("Watershed", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=get_watershed_data(emitter), )
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
    vg = utils.vg_utils.create_vg(emitter, m.name, set_active=False, fill=get_watershed_data(emitter, crop=m.cur_crop,))
    
    #smooth vg 
    utils.vg_utils.smooth_vg(emitter, vg, m.cur_smooth)
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



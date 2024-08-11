
#####################################################################################################
#
# ooooooooo.                          .    o8o            oooo                 ooooooooo.
# `888   `Y88.                      .o8    `"'            `888                 `888   `Y88.
#  888   .d88'  .oooo.   oooo d8b .o888oo oooo   .ooooo.   888   .ooooo.        888   .d88' oooo d8b  .ooooo.  oooo    ooo
#  888ooo88P'  `P  )88b  `888""8P   888   `888  d88' `"Y8  888  d88' `88b       888ooo88P'  `888""8P d88' `88b  `88b..8P'
#  888          .oP"888   888       888    888  888        888  888ooo888       888          888     888   888    Y888'
#  888         d8(  888   888       888 .  888  888   .o8  888  888    .o       888          888     888   888  .o8"'88b
# o888o        `Y888""8o d888b      "888" o888o `Y8bod8P' o888o `Y8bod8P'      o888o        d888b    `Y8bod8P' o88'   888o
#
#####################################################################################################


import bpy 
import numpy as np
import mathutils

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

    lbl.label(text=translate("System"))
    prp.prop_search(m, "psy_name", emitter.scatter5, "particle_systems" ,text="",icon="PARTICLES")

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Distance"))
    prp.prop(m, "distance",text="")

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



def get_particle_prox_data(o, psy_name, radius, eval_modifiers=False,):
    """create vertex group from particle system location proximity"""
    
    psy = o.scatter5.particle_systems.get(psy_name)
    if psy is None:
        return 0

    # Get the inverse of the object's world matrix
    inv_matrix_world = o.matrix_world.inverted()
    
    if eval_modifiers == False:
           depsgraph = bpy.context.evaluated_depsgraph_get()
           eo = o.evaluated_get(depsgraph)
           ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else:  ob = o.data

    l = len(ob.vertices)
    tree = mathutils.kdtree.KDTree(l)
    for v in ob.vertices:
        tree.insert(v.co, v.index)
    tree.balance()

    weights = [0.0] * len(ob.vertices)

    for p in psy.get_instancing_info(loc_data=True):
        p = inv_matrix_world @ p
        r = tree.find_range(p, radius)

        for v, i, d in r:
            w = 1.0 - (d / radius)
            if(weights[i] < w):
                weights[i] = w
                
            continue
        continue 

    return weights


def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type = "particle_proximity"
    m.icon = "W_ECOSYSTEM"
    m.name = m.user_name = no_names_in_double("Ecosystem", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=0, )
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

    masks = emitter.scatter5.mask_systems
    m     = masks[i]

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, set_active=False, fill=get_particle_prox_data(emitter, m.psy_name, m.distance, ),)
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



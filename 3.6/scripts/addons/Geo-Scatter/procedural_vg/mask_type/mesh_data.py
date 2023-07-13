
#####################################################################################################
#
# ooo        ooooo                    oooo             oooooooooo.                 .
# `88.       .888'                    `888             `888'   `Y8b              .o8
#  888b     d'888   .ooooo.   .oooo.o  888 .oo.         888      888  .oooo.   .o888oo  .oooo.
#  8 Y88. .P  888  d88' `88b d88(  "8  888P"Y88b        888      888 `P  )88b    888   `P  )88b
#  8  `888'   888  888ooo888 `"Y88b.   888   888        888      888  .oP"888    888    .oP"888
#  8    Y     888  888    .o o.  )88b  888   888        888     d88' d8(  888    888 . d8(  888
# o8o        o888o `Y8bod8P' 8""888P' o888o o888o      o888bood8P'   `Y888""8o   "888" `Y888""8o
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

    lbl.label(text=translate("Method"))
    prp.prop(m,"mesh_data_method",text="")

    if m.mesh_data_method in ["edge_sharp","edge_freestyle","edge_seam"]:

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text="")
        prp.prop(m,"mesh_data_prox_distance",text=translate("Distance"))   

        # lbl.separator(factor=0.7)
        # prp.separator(factor=0.7)

        # lbl.label(text="")
        # prp.prop(m,"mesh_data_prox_offset",text=translate("Offset"))    
    
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



def _normalize(maxi, mini, nbr):
    zone = (maxi-mini)
    if zone==0:
        return 1.0
    r = (nbr-mini)/zone
    return r


def _edge_length(o,e):
    v0 , v1 = e.vertices[0] , e.vertices[1]
    OWMatrix = o.matrix_world
    v0Pos = OWMatrix @ o.data.vertices[v0].co
    v1Pos = OWMatrix @ o.data.vertices[v1].co
    return  (v0Pos - v1Pos).length


def _material(idx, material_name, mat_id, slots_len, coef):
    if material_name:
        return 1.0 if (idx==mat_id) else 0.0
    if (idx==0):
        return 0.0
    if (idx==1) and (slots_len==2):
        return 1.0
    return coef*idx 


def get_mesh_data(o, method=None, material_name=None, ray_distance=1, ray_offset=1, eval_modifiers=False,):

    w = {}
    r = {}

    if eval_modifiers:
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    #prepare

    if   (method=="face_area"):
        _all = [f.area for f in ob.polygons]
        maxi, mini = max(_all), min(_all)
    elif (method=="face_index"):
        _all = [f.index for f in ob.polygons]
        maxi, mini = max(_all), min(_all)
    elif (method=='edge_index'):
        _all = [e.index for e in ob.edges]
        maxi, mini = max(_all), min(_all)
    elif (method=='edge_len'):
        _all = [_edge_length(o,e) for e in ob.edges]
        maxi, mini = max(_all), min(_all)
    elif (method=="face_material"):
        mat_id = None
        slots_len = len(o.material_slots)
        if not slots_len:
            return 0.0
        coef = 1/slots_len
        if material_name:
            for i,s in enumerate(o.material_slots):
                if s.name == material_name:
                    mat_id = i
                    break

    # get mesh data 

    if method.startswith("face_"):

        for f in ob.polygons:
            if   (method=="face_smooth"):
                val = f.use_smooth
            elif (method=="face_freestyle"):
                val = f.use_freestyle_mark
            elif (method=="face_material"):
                val = _material(f.material_index, material_name, mat_id, slots_len, coef)
            elif (method=="face_area"):
                val = _normalize(maxi, mini, f.area)
            elif (method=="face_index"):
                val = _normalize(maxi, mini, f.index)

            for v in f.vertices:
                if (v in w) and (w[v]>val):
                    continue
                w[v]=val

    elif method.startswith("edge_"):

        for e in ob.edges:
            if   (method=="edge_bevel"):
                val = e.bevel_weight
            elif (method=="edge_crease"):
                val = e.crease
            elif (method=="edge_sharp"):
                val = e.use_edge_sharp
            elif (method=="edge_freestyle"):
                val = e.use_freestyle_mark
            elif (method=="edge_seam"):
                val = e.use_seam
            elif (method=="edge_len"):
                val = _normalize(maxi, mini, _edge_length(o,e))
            elif (method=="edge_index"):
                val = _normalize(maxi, mini, e.index)

            for v in e.vertices:
                if (v in w) and (w[v]>val):
                    continue
                w[v]=val
                if (val==1.0):
                    r[v]=None

    if (method in ["edge_sharp","edge_freestyle","edge_seam"] ):
        return utils.vg_utils.kd_trees_rays(ob, verts_idx=r.keys(), distance=ray_distance, offset=ray_offset,)
    return w 



def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type = "mesh_data"
    m.icon = "MOD_DATA_TRANSFER"
    m.name = m.user_name = no_names_in_double("Mesh-Data", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name,  fill=get_mesh_data(emitter, method=m.mesh_data_method), )
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

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, set_active=False, fill=get_mesh_data(emitter, method=m.mesh_data_method, ray_distance=m.mesh_data_prox_distance, ray_offset=m.mesh_data_prox_offset, ))
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



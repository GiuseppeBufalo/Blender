
#####################################################################################################
#
# oooooooooo.                        o8o                                .o.
# `888'   `Y8b                       `"'                               .888.
#  888     888  .ooooo.    oooooooo oooo   .ooooo.  oooo d8b          .8"888.     oooo d8b  .ooooo.   .oooo.
#  888oooo888' d88' `88b  d'""7d8P  `888  d88' `88b `888""8P         .8' `888.    `888""8P d88' `88b `P  )88b
#  888    `88b 888ooo888    .d8P'    888  888ooo888  888            .88ooo8888.    888     888ooo888  .oP"888
#  888    .88P 888    .o  .d8P'  .P  888  888    .o  888           .8'     `888.   888     888    .o d8(  888
# o888bood8P'  `Y8bod8P' d8888888P  o888o `Y8bod8P' d888b         o88o     o8888o d888b    `Y8bod8P' `Y888""8o
#
#####################################################################################################


import bpy

import bmesh
import numpy as np 
from mathutils import Vector
from mathutils.geometry import intersect_point_tri_2d

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
    scat_win   = bpy.context.window_manager.scatter5
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

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Curve"))
    curve_mask = prp.row(align=True)
    curve_row = curve_mask.row(align=True)
    curve_row.alert = (m.curve_ptr is not None and m.curve_ptr.name not in bpy.context.scene.objects)
    curve_row.prop( m, "curve_ptr", text="", icon="CURVE_BEZCIRCLE")
    if (m.curve_ptr is not None):
        op = curve_mask.operator("scatter5.draw_bezier_area",text="", icon="BRUSH_DATA", depress=scat_win.mode=="DRAW_AREA")
        op.edit_existing = m.curve_ptr.name
        
        # from ..manual.debug import debug_mode
        # if(debug_mode()):
        #     op = curve_mask.operator("scatter5.brush_bezier_area",text="", icon="BRUSH_DATA", depress=scat_win.mode=="DRAW_AREA")
        #     op.edit_existing = m.curve_ptr.name
    else: 
        op = curve_mask.operator("scatter5.add_curve_area",text="", icon="ADD", )
        op.api = f"bpy.context.scene.scatter5.emitter.scatter5.mask_systems['{m.name}'].curve_ptr"


    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=" ")
    prp.prop(m,"cur_smooth",text=translate("Smoothing"))

    #settings
    
    lbl.separator(factor=3.7)
    prp.separator(factor=3.7)

    lbl.label(text=translate("Data"))
    re = prp.operator("scatter5.refresh_mask",text=translate("Recalculate"),icon="FILE_REFRESH")
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



def points_in_tris_intersect(curve,global_points,global_tris,reverse=False,bounding_box_optimization=True):
    """
    return :
        -array of booleans from points if pt intersect with bmesh tris
    input :
        -array of points (tuple)
        -array of tris points (array of array of tuples)
    """

    values = []

    if bounding_box_optimization: 
            #Note that it could even be faster using numpy batch-checking "global_points", removing points out of BB  

            def get_bb_range(o):
                points_x,points_y = [],[]
                for i in [0,2,4,6]:
                    p = o.matrix_world @ Vector((o.bound_box[i][0],o.bound_box[i][1],o.bound_box[i][2]))
                    points_x.append(p[0]) ; points_y.append(p[1])         
                return [ (min(points_x),max(points_x)) , (min(points_y),max(points_y)) ]

            def in_bb_range(point,bb_range): 
                return ( bb_range[0][0] < point[0] < bb_range[0][1] ) and ( bb_range[1][0] < point[1] < bb_range[1][1] )

            bb_range = get_bb_range(curve)

    for p in global_points: #check each points, if they intersect in any of each tris

        if bounding_box_optimization: #check if 2d point coordinate inside bounding box range area, if not then skip calculation

            if in_bb_range(p,bb_range):
                  intersect = [ intersect_point_tri_2d( p,t[0],t[1],t[2] ) for t in global_tris]
            else: intersect = [ False ]

        else: #do calculation on everything, no optimization 

            intersect = [ intersect_point_tri_2d( p,t[0],t[1],t[2] ) for t in global_tris]
        
        if reverse: values.append(not any(intersect))
        else:       values.append(any(intersect))
        
    return values 


def get_global_tris_from_ob(o, eval_modifiers=False):#->global_tris
    """return array of tris points from given object"""
    
    #eval object modifiers to mesh?
    if eval_modifiers == True:
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    #create mesh data
    bm = bmesh.new()
    bm.from_mesh(ob)
    bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts) #local to global coord
    
    #bmesh ensure lookup
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
    #triangulate bmesh
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    
    #get tris verts xy loc
    global_tris = []
    for f in bm.faces:
        global_tris.append( [(v.co.x,v.co.y) for v in f.verts] )
        
    return global_tris 


def get_global_pts_from_mesh_verts(o, eval_modifiers=False):#->global_points
    """return array of points from given object"""
        
    #eval object modifiers to mesh?
    if eval_modifiers == True:
          depsgraph = bpy.context.evaluated_depsgraph_get()
          eo = o.evaluated_get(depsgraph)
          ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    else: ob = o.data

    # get vertex locations
    l = len(ob.vertices)
    vs = np.zeros((l * 3), dtype=np.float64, )
    ob.vertices.foreach_get("co", vs, )
    vs.shape = (l, 3, )

    # numpy local to global
    global_points = utils.np_utils.np_apply_transforms(o,vs)

    return global_points.tolist() 


def curve_to_mesh(curve):
    """Create mesh copy of given curve"""

    #set to cyclic
    for spline in curve.data.splines:
        spline.use_cyclic_u = True
    
    #create copy 
    curve_copy = curve.copy()    
    curve_copy.data = curve.data.copy()
    bpy.context.scene.collection.objects.link(curve_copy)
    
    #change default curve params
    curve_copy.data.dimensions = '2D'
    curve_copy.rotation_euler.x = curve.rotation_euler.y = 0

    #set copy as active
    active = bpy.context.object
    bpy.context.view_layer.objects.active = curve_copy
    Selection = bpy.context.selected_objects
    bpy.ops.object.select_all(action='DESELECT')
    curve_copy.select_set(state=True)
    
    #set curve as 2D and fill
    curve_copy.data.dimensions = '2D'
    curve_copy.data.fill_mode = 'FRONT'

    #convert curve to mesh
    bpy.ops.object.convert(target='MESH', keep_original=False)
    
    #restore active and selection
    bpy.context.view_layer.objects.active = active
    bpy.ops.object.select_all(action='DESELECT')
    for o in Selection: o.select_set(state=True)
    
    return curve_copy
    

def bezier_boolean_2d(o,curve,reverse=False):    

    if (curve is None) or (curve.type!="CURVE"): 
        return 0

    with utils.override_utils.mode_override(selection=[o], active=o, mode="OBJECT"):

        #get points array from terrain
        global_points = get_global_pts_from_mesh_verts(o)

        #get boolean mesh from curve object
        boolean_obj = curve_to_mesh(curve)

        #get global tris from boolean mesh
        global_tris = get_global_tris_from_ob(boolean_obj)

        #get intersection values
        values = points_in_tris_intersect(curve,global_points, global_tris,reverse=reverse) #-> TODO ignore values outside of bounding box?

        #delete created curve mesh copy
        bpy.ops.object.delete({"selected_objects": [boolean_obj]})

    return values


def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type      = "bezier_area"
    m.icon      = "CURVE_BEZCIRCLE"                      
    m.name = m.user_name = no_names_in_double("Bezier Area", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

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

    masks     = emitter.scatter5.mask_systems
    m         = masks[i]

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=bezier_boolean_2d(emitter, m.curve_ptr,), )

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


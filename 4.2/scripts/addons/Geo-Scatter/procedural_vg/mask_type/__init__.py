


from . import (
        
    ao,
    light,
    slope, 
    height, 
    aspect,
    normal, 
    border,
    boolean,
    position,
    curvature,
    mesh_data,
    watershed,
    camera_visibility,
    layer_paint,
    bezier_path,
    bezier_area,
    particle_proximity,
    texture_mask,
    vcol_to_vgroup,
    vgroup_split,
    vgroup_merge,

    )



from . boolean import SCATTER5_OT_mask_boolean_add_to_coll, SCATTER5_OT_mask_boolean_parameters
from . layer_paint import SCATTER5_OT_layer_paint_mode, SCATTER5_OT_layer_paint_reverse, SCATTER5_OT_layer_paint_fill


classes = (
    
    SCATTER5_OT_mask_boolean_add_to_coll,  
    SCATTER5_OT_mask_boolean_parameters,  
    
    SCATTER5_OT_layer_paint_mode,
    SCATTER5_OT_layer_paint_reverse,
    SCATTER5_OT_layer_paint_fill,

    )
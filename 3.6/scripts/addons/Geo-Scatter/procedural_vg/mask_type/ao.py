
#####################################################################################################
#
#       .o.         .oooooo.
#      .888.       d8P'  `Y8b
#     .8"888.     888      888
#    .8' `888.    888      888
#   .88ooo8888.   888      888
#  .8'     `888.  `88b    d88'
# o88o     o8888o  `Y8bood8P'
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
    row1.scale_x = 0.85
    lbl = row1.column()
    lbl.alignment="RIGHT"

    row2 = row.row()
    prp = row2.column()

    #settings
    
    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Samples"))
    prp.prop(m,"bake_samples",text="",)
    
    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=" ")
    prp.prop(m,"cur_smooth",text=translate("Smoothing"))

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Ray Collision"))
    prp.prop(m,"bake_obstacles",text="",)

    if m.bake_obstacles=="col":
        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text="")
        prp.prop(m,"mask_p_collection",text="",)
    
    if m.bake_obstacles!="self":
        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text="")
        prp.prop(m,"hide_particles",text=translate("Ignore Scatter"), icon="PARTICLE_DATA")

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



#NOTE all baking mask (ao, shadow) use same principle

def prepare_and_bake_ao(o, obstacles, samples=32,):
    """bake ao in scene dupplicata, return ao vcol array"""

    to_restore={}
    scene = bpy.context.scene

    # create vcols to bake to
    vcol = o.data.vertex_colors.new()
    o.data.vertex_colors.active = vcol
        
    # set active and selected 
    bpy.context.view_layer.objects.active = o
    for obj in scene.objects:
        obj.select_set(False)
    o.select_set(True)

    if o not in obstacles:
        obstacles.append(o)

    # Hide / Show obstalces
    for obj in scene.objects:
        to_restore[obj]= {
            "hide_render":obj.hide_render, 
            "visible_camera":obj.visible_camera, 
            "visible_diffuse":obj.visible_diffuse, 
            "visible_glossy":obj.visible_glossy, 
            "visible_transmission":obj.visible_transmission, 
            "visible_volume_scatter":obj.visible_volume_scatter, 
            "visible_shadow":obj.visible_shadow,
        }
            
        boolean = (obj in obstacles)

        obj.hide_render                    = not boolean
        obj.visible_camera       = boolean
        obj.visible_diffuse      = boolean
        obj.visible_glossy       = boolean
        obj.visible_transmission = boolean
        obj.visible_volume_scatter      = boolean
        obj.visible_shadow       = boolean

    # dynacam special case
    # dyna_cam = bpy.data.objects.get(f"Scatter5 [{bpy.context.scene.name}] Dynamic Cam Clipping Cone")
    # if dyna_cam: 
    #     to_restore[dyna_cam] = {"hide_render":dyna_cam.hide_render}
    #     dyna_cam.hide_render = True
    
    # cycles settings
    to_restore[scene] = {
        "render.engine":scene.render.engine,
        "cycles.device":scene.cycles.device,
        "cycles.bake_type":scene.cycles.bake_type,
        "cycles.samples":scene.cycles.samples,
        "render.bake.target":scene.render.bake.target,
    }

    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.bake_type = 'AO'
    scene.cycles.samples = samples
    scene.render.bake.target = 'VERTEX_COLORS'

    # bake operator
    bpy.ops.object.bake(type='AO')
    
    # get baked values
    ao = np.zeros(len(o.data.vertices), dtype=np.float, )
    for i, l in enumerate(o.data.loops):
        ao[l.vertex_index] = np.sum( np.array(vcol.data[i].color[:3]) ) / 3
    
    # RESTORE bake vcol 
    o.data.vertex_colors.remove(vcol) 

    # RESTORE whole dict  
    for obj, d in to_restore.items():
        for k,v in d.items():
            if type(v) is str:
                  exec(f"obj.{k}='{v}'")
            else: exec(f"obj.{k}={v}")

    return ao



def get_ao(o, samples=1000, obstacles_method="scene", hide_particles=True, collection=None,):
    """get AO per vertices data"""

    with utils.override_utils.mode_override(selection=[o], active=o, mode="OBJECT"):

        obstacles = []
        if (obstacles_method=="scene"):
            obstacles = [i for i in bpy.context.scene.objects if i is not o and not i.hide_viewport]
        elif (obstacles_method=="self"):
            obstacles = []
        elif (obstacles_method=="col") and (collection):
            obstacles = [i for i in collection.objects]

        if (hide_particles==True):
            for obj in obstacles:
                if obj.name.startswith("scatter_obj : "):
                    obstacles.remove(obj)        

        ao = prepare_and_bake_ao(o=o, obstacles=obstacles, samples=samples,)

    return ao 



def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type      = "ao"
    m.icon      = "RENDER_STILL"                    
    m.name = m.user_name = no_names_in_double("Occlusion", [vg.name for vg  in emitter.vertex_groups], startswith00=True)
    
    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=get_ao(emitter, samples=m.bake_samples, obstacles_method=m.bake_obstacles, collection=m.mask_p_collection), )
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

    #update the vg
    vg = utils.vg_utils.create_vg(emitter, m.name, set_active=False, fill=get_ao(emitter, samples=m.bake_samples, obstacles_method=m.bake_obstacles,hide_particles=m.hide_particles, collection=m.mask_p_collection,), )

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



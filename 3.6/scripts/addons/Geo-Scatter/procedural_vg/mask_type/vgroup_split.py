
#####################################################################################################
#
# oooooo     oooo                                                            .oooooo..o            oooo   o8o      .
#  `888.     .8'                                                            d8P'    `Y8            `888   `"'    .o8
#   `888.   .8'    .oooooooo oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.       Y88bo.      oo.ooooo.   888  oooo  .o888oo
#    `888. .8'    888' `88b  `888""8P d88' `88b `888  `888   888' `88b       `"Y8888o.   888' `88b  888  `888    888
#     `888.8'     888   888   888     888   888  888   888   888   888           `"Y88b  888   888  888   888    888
#      `888'      `88bod8P'   888     888   888  888   888   888   888      oo     .d8P  888   888  888   888    888 .
#       `8'       `8oooooo.  d888b    `Y8bod8P'  `V88V"V8P'  888bod8P'      8""88888P'   888bod8P' o888o o888o   "888"
#                 d"     YD                                  888                         888
#                 "Y88888P'                                 o888o                       o888o
#
#####################################################################################################


import bpy

from ... import utils 
from ... utils.str_utils import no_names_in_double
from ... utils.vg_utils import is_vg_active

from ... resources.icons import cust_icon
from ... resources.translate import translate
from ... resources import directories


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

    modname = f"Scatter5 {m.name}"

    mod = emitter.modifiers.get(modname)
    if (mod is not None):

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text=translate("Input"))
        prprow = prp.row(align=True)
        prprow.prop_search(mod,'["Input_2_attribute_name"]', emitter,"vertex_groups",text="",)
        eval_ptr = mod["Input_2_attribute_name"]
        exists = (eval_ptr in emitter.vertex_groups)
        op = prprow.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if exists else "ADD", depress=is_vg_active(emitter,eval_ptr)) ; op.mode = "vg" ; op.group_name = eval_ptr ; op.api = f"emitter.modifiers['{modname}']['Input_2_attribute_name']" ; op.context_surfaces = "*EMITTER_CONTEXT*"

        lbl.separator(factor=1)
        prp.separator(factor=1)

        lbl.label(text=translate("Outputs"))
        prp.label(text="")

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        for i,vgptr in ((1,"Output_3_attribute_name"),(2,"Output_4_attribute_name"),(3,"Output_5_attribute_name"),(4,"Output_6_attribute_name"),(5,"Output_7_attribute_name"),):

            lbl.label(text=f"{i:02}")
            prprow = prp.row(align=True)
            prprow.prop_search(mod,f'["{vgptr}"]', emitter,"vertex_groups",text="",)
            eval_ptr = mod[vgptr]
            exists = (eval_ptr in emitter.vertex_groups)
            if exists:                    
                o = prprow.operator("scatter5.graph_dialog",text="",icon="FCURVE")
                o.source_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}'].node_group.nodes['{i}']"
                o.mapping_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}'].node_group.nodes['{i}'].mapping"
            op = prprow.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if exists else "ADD", depress=is_vg_active(emitter,eval_ptr)) ; op.mode = "vg" ; op.group_name = eval_ptr ; op.api = f"emitter.modifiers['{modname}']['{vgptr}']" ; op.context_surfaces = "*EMITTER_CONTEXT*"


            lbl.separator(factor=0.7)
            prp.separator(factor=0.7)

    layout.separator()

    return   



#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"



def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type      = "vgroup_split"
    m.icon      = "W_ARROW_SPLIT"                    
    m.name = m.user_name = no_names_in_double("VgroupSplit", [m.name for m  in masks], startswith00=True)

    modname = f"Scatter5 {m.name}"
    if (modname not in emitter.modifiers):
        
        mod = utils.import_utils.import_and_add_geonode(emitter, mod_name=modname, node_name=".Scatter5 VgroupSplit", blend_path=directories.addon_vgmasks_blend, copy=False,)
        mod.show_expanded = False
        mod["Input_2_use_attribute"] = True

        m.mod_list = modname

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
    m = masks[i]

    modname = f"Scatter5 {m.name}"
    mod = emitter.modifiers.get(modname)
    if mod is None:
        mod = utils.import_utils.import_and_add_geonode(emitter, mod_name=modname, node_name=".Scatter5 VgroupSplit", blend_path=directories.addon_vgmasks_blend, copy=False,)
        mod.show_expanded = False
        m.mod_list = modname
        
    #these should always be at the bottom
    utils.mod_utils.move_queue(emitter,mod, mode="bottom",)

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



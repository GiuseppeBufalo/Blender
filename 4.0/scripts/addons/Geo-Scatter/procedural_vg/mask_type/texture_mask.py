
#####################################################################################################
#
# ooooooooooooo                           .                                       ooo        ooooo                    oooo
# 8'   888   `8                         .o8                                       `88.       .888'                    `888
#      888       .ooooo.  oooo    ooo .o888oo oooo  oooo  oooo d8b  .ooooo.        888b     d'888   .oooo.    .oooo.o  888  oooo
#      888      d88' `88b  `88b..8P'    888   `888  `888  `888""8P d88' `88b       8 Y88. .P  888  `P  )88b  d88(  "8  888 .8P'
#      888      888ooo888    Y888'      888    888   888   888     888ooo888       8  `888'   888   .oP"888  `"Y88b.   888888.
#      888      888    .o  .o8"'88b     888 .  888   888   888     888    .o       8    Y     888  d8(  888  o.  )88b  888 `88b.
#     o888o     `Y8bod8P' o88'   888o   "888"  `V88V"V8P' d888b    `Y8bod8P'      o8o        o888o `Y888""8o 8""888P' o888o o888o
#
#####################################################################################################


import bpy 

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

    mod_name = f"Scatter5 TextureWeight {m.name}"
    mod = emitter.modifiers.get(mod_name)

    if (mod is None):

        warn = layout.row(align=True)
        warn.alignment = "CENTER"
        warn.active = False
        warn.scale_y = 0.9
        warn.label(text=translate("Modifier Missing, Please Refresh"),icon="ERROR")

        return 

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

    if mod is not None: 

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text=translate("Texture"))
        prp.template_ID(mod, "mask_texture", new="texture.new")

        #lbl.separator(factor=0.7)
        #prp.separator(factor=0.7)

        #lbl.label(text="")
        #prp.prop(mod,"mask_tex_use_channel",text="")

        lbl.separator(factor=0.7)
        prp.separator(factor=0.7)

        lbl.label(text=translate("Space"))
        prp.prop(mod,"mask_tex_mapping",text="")

        if (mod.mask_tex_mapping=="OBJECT"):

            lbl.separator(factor=0.7)
            prp.separator(factor=0.7)

            lbl.label(text="")
            prp.prop(mod,"mask_tex_map_object",text="")

        elif (mod.mask_tex_mapping=="UV"):
            
            lbl.separator(factor=0.7)
            prp.separator(factor=0.7)
    
            lbl.label(text="")
            prp.prop(mod,"mask_tex_uv_layer",text="")

    lbl.separator(factor=3.7)
    prp.separator(factor=3.7)

    # lbl.label(text=translate("Modifiers"))
    # refresh = prp.row(align=True)
    # re = refresh.operator("scatter5.refresh_mask",text=translate("Refresh"),icon="FILE_REFRESH")
    # re.mask_type = m.type
    # re.mask_idx = i 

    #lbl.separator(factor=0.7)
    #prp.separator(factor=0.7)

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




def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type      = "texture_mask"
    m.icon      = "TEXTURE"                      
    m.name = m.user_name = no_names_in_double("Texture Data", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=1, )
    vg.lock_weight = True

    mod_name = f"Scatter5 TextureWeight {m.name}"
    mod = emitter.modifiers.get(mod_name)
    if mod is None:
        mod = emitter.modifiers.new(name=mod_name,type="VERTEX_WEIGHT_MIX",)
        mod.show_expanded = False
        mod.mix_mode = 'DIF'
        mod.mix_set = 'ALL'
        mod.default_weight_b = 1
        mod.vertex_group_a = m.name
        m.mod_list += mod_name+"_!#!_"

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

    if (m.name not in emitter.vertex_groups):
        vg = utils.vg_utils.create_vg(emitter, m.name, fill=1, )
        vg.lock_weight = True

    mod_name = f"Scatter5 TextureWeight {m.name}"
    mod = emitter.modifiers.get(mod_name)
    if mod is None:
        mod = emitter.modifiers.new(name=mod_name,type="VERTEX_WEIGHT_MIX",)
        mod.show_expanded = False
        mod.mix_mode = 'DIF'
        mod.mix_set = 'ALL'
        mod.vertex_group_a = m.name
        mod.default_weight_b = 1
        m.mod_list += mod_name+"_!#!_"

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


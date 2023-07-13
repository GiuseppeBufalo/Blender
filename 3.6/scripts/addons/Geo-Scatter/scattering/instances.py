
#####################################################################################################
#
# ooooo                          .
# `888'                        .o8
#  888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.   .ooooo.   .oooo.o
#  888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 d88' `88b d88(  "8
#  888   888   888  `"Y88b.    888    .oP"888   888   888  888       888ooo888 `"Y88b.
#  888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8 888    .o o.  )88b
# o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' `Y8bod8P' 8""888P'
#
#####################################################################################################


import bpy

from .. utils.event_utils import get_event
from .. resources.translate import translate
from .. utils.import_utils import import_selected_assets


# oooooooooooo                                       .    o8o
# `888'     `8                                     .o8    `"'
#  888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#  888    "     888   888   888   888  888         888    888  888   888  888   888
#  888          888   888   888   888  888   .o8   888 .  888  888   888  888   888
# o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o


def collection_users(collection):
    """return all scatter5 psy that use this collection as s_instances_coll_ptr"""

    users = []
    for o in bpy.data.objects:
        if (len(o.scatter5.particle_systems)):
            for p in o.scatter5.particle_systems:
                if (p.s_instances_coll_ptr==collection):
                    users.append(p)
    return users

def is_compatible_instance(o, emitter=None,):
    """check if object compatible to be scattered"""

    #get emitter 
    if (emitter is None):
        emitter = bpy.context.scene.scatter5.emitter

    #emitter needs to exists!
    if (emitter is None):
        return False

    #cannot be active emitter
    if (o==emitter):
        return False

    #cannot be an emitter
    #ok?

    #cannot be a surface object?
    #ok?

    #cannot be a scatter object
    if o.name.startswith("scatter_obj : "):
        return False

    #un-supported meshes?
    if (o.type not in ("MESH","CURVE","LIGHT","LIGHT_PROBE","VOLUME","EMPTY","FONT","META","SURFACE")):
        return False

    return True 

def find_compatible_instances(obj_list, emitter=None,):
    """return a generator of compatible object"""

    for o in obj_list:
        if is_compatible_instance(o, emitter=emitter):
            yield o


# ooooo                          .                                    o8o                                .oooooo.                                               .
# `888'                        .o8                                    `"'                               d8P'  `Y8b                                            .o8
#  888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.  oooo  ooo. .oo.    .oooooooo      888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o
#  888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 `888  `888P"Y88b  888' `88b       888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P d88(  "8
#  888   888   888  `"Y88b.    888    .oP"888   888   888  888        888   888   888  888   888       888      888  888   888 888ooo888  888      .oP"888    888   888   888  888     `"Y88b.
#  888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8  888   888   888  `88bod8P'       `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888     o.  )88b
# o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' o888o o888o o888o `8oooooo.        `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b    8""888P'
#                                                                                      d"     YD                     888
#                                                                                      "Y88888P'                    o888o


class SCATTER5_OT_add_instances(bpy.types.Operator):
    """operator only for the insance list context"""

    bl_idname = "scatter5.add_instances"
    bl_label       = translate("Add New Instances")
    bl_description = translate("Add selected objects in Scatter instance collection, If multiple systems are selected press [ALT] to add to all selected system collections at the same time")
    bl_options     = {'INTERNAL','UNDO'}

    method : bpy.props.EnumProperty(
        name=translate("Add from"),
        default= "viewport", 
        items= [ ("viewport", translate("Viewport Selection"), translate("Add the selected compatible objects found in the viewport"), "VIEW3D",1 ),
                 ("browser", translate("Browser Selection"), translate("Add the selected object found in the asset browser"), "ASSET_MANAGER",2 ),
               ],
        )

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected(all_emitters=scat_scene.factory_alt_selection_method=="all_emitters")

        #alt for batch support
        event = get_event(nullevent=not scat_scene.factory_alt_allow)

        if (self.method=="browser"):
              obj_list = import_selected_assets(link=(scat_scene.objects_import_method=="LINK"),)
        else: obj_list = bpy.context.selected_objects 
        instances = list(find_compatible_instances(obj_list, emitter=emitter,))
             
        if (len(instances)==0):
            msg = translate("No valid object(s) found in selection.") if (not self.method=="browser") else translate("No asset(s) found in asset-browser.")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        if (event.alt):  
              colls = [ p.s_instances_coll_ptr for p in psys_sel]
        else: colls = [ psy_active.s_instances_coll_ptr ]

        for coll in colls:

            if (coll is None):
                continue

            for o in instances:
                if (o.name not in coll.objects):
                    coll.objects.link(o)
                continue

            #refresh signal needed for collection
            display = o.display_type
            o.display_type = "BOUNDS"
            o.display_type = display
            continue

        return {'FINISHED'}


class SCATTER5_OT_remove_instances(bpy.types.Operator):
    """operator only for the insance list context"""

    bl_idname = "scatter5.remove_instances"
    bl_label       = translate("Remove this instance")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    ins_name : bpy.props.StringProperty()

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected(all_emitters=scat_scene.factory_alt_selection_method=="all_emitters")

        #alt for batch support
        event = get_event(nullevent=not scat_scene.factory_alt_allow)

        if (event.alt):  
              colls = [ p.s_instances_coll_ptr for p in psys_sel]
        else: colls = [ psy_active.s_instances_coll_ptr ]

        for coll in colls:
            for o in coll.objects:
                if (o.name==self.ins_name):
                    coll.objects.unlink(o)
                continue
            continue
            
        #refresh signal needed for collection

        if (len(coll.objects)!=0):
            o = coll.objects[0]
            display = o.display_type
            o.display_type = "BOUNDS"
            o.display_type = display

        return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_add_instances,
    SCATTER5_OT_remove_instances,
    
    )
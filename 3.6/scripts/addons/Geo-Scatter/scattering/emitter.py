
##################################################################################################
#
# oooooooooooo                    o8o      .       .
# `888'     `8                    `"'    .o8     .o8
#  888         ooo. .oo.  .oo.   oooo  .o888oo .o888oo  .ooooo.  oooo d8b
#  888oooo8    `888P"Y88bP"Y88b  `888    888     888   d88' `88b `888""8P
#  888    "     888   888   888   888    888     888   888ooo888  888
#  888       o  888   888   888   888    888 .   888 . 888    .o  888
# o888ooooood8 o888o o888o o888o o888o   "888"   "888" `Y8bod8P' d888b
#
#####################################################################################################


import bpy
from mathutils import Vector

from .. utils.extra_utils import dprint
from .. utils import import_utils
from .. resources.directories import addon_logo_blend
from .. resources.translate import translate


def is_correct_emitter(object):
    """check if emitter emitter type is mesh"""
    return  ( 
               (object)  
               and (object.type=="MESH") 
               and (object.name in bpy.context.scene.objects) 
            )

def find_compatible_surfaces(objects):
    for o in objects:
        if (o.type=="MESH") : 
            if (o.name in bpy.context.scene.objects):
                yield o

def poll_emitter(self, object):
    """poll fct  for bpy.context.scene.scatter5.emitter prop"""

    dprint("PROP_FCT: poll 'scat_scene.emitter'")

    #don't poll if context object is not compatible
    return is_correct_emitter(object) 

def handler_emitter_check_if_deleted():
    """on each depsgraph update, check if user has removed the emitter, we need to update the main emitter prop of scene"""

    emitter = bpy.context.scene.scatter5.emitter
    if (not emitter):
        return None

    #remove emitter if somehow user deleted it
    if (emitter.name not in bpy.context.scene.objects):
        dprint("HANDLER: 'scatter5_depsgraph' -> 'handler_emitter_check_if_deleted'")
        bpy.context.scene.scatter5.emitter = None 

    return None

def handler_emitter_pin_mode_sync():
    """depsgraph: automatically update emitter pointer to context.object if in pineed mode"""

    #don't update if the options is not enabled
    if (bpy.context.preferences.addons["Geo-Scatter"].preferences.emitter_method!="pin"):
        return None 

    #don't update if no context object  
    a = bpy.context.object 
    if (not a):
        return None 

    #don't update if context object is not compatible
    if (not is_correct_emitter(a)):
        return None  

    scat_scene = bpy.context.scene.scatter5
    if (not scat_scene.emitter_pinned):
        if (scat_scene.emitter!=bpy.context.object):
            dprint("HANDLER: 'scatter5_depsgraph' -> 'handler_emitter_pin_mode_sync'")
            scat_scene.emitter = bpy.context.object

    return None

def handler_scene_emitter_cleanup():
    """depsgraph: clean up emitter objects that have been dupplicated (not instanced)"""

    for emitter in bpy.context.scene.scatter5.get_all_emitters():
        
        #if emitter is linked, then user is linking scatter_obj and we need to ignore
        if (emitter.library is not None):
            continue

        #if emitter no longer exists in any scene, then remove it!
        if (not bool(emitter.users_scene)):
            for p in emitter.scatter5.particle_systems:
                p.remove_psy()
            emitter.scatter5.particle_interface_refresh()
            continue 

        #Dupplicate Emitter == Clean Particle System That do not belongs to correct emitter
        if (emitter.scatter5.particle_systems[0].scatter_obj.scatter5.original_emitter is not emitter) :
            dprint("HANDLER: 'handler_scene_emitter_cleanup'",depsgraph=True)
            emitter.scatter5.particle_systems.clear()
            emitter.scatter5.particle_interface_refresh()
            break

    return None

def handler_f_surfaces_cleanup():
    """despgraph: check if no deleted surfaces in f_surfaces"""

    scene = bpy.context.scene
    op = scene.scatter5.operators.create_operators
        
    if (op.f_surface_method=="emitter"):
        return None 

    elif (op.f_surface_method=="collection"):
        for i in reversed(range(len(op.f_surfaces))):
            if (op.f_surfaces[i].name not in scene.objects):
                op.f_surfaces.remove(i)
        return None 

    elif (op.f_surface_method=="object"):
        if (op.f_surface_object is not None) and (op.f_surface_object.name not in scene.objects):
            op.f_surface_object = None
        return None 

    return None

# def handler_scene_emitter_hidden():
#     """depsgraph: hide scatter system(s) automatically when emitter is hidden"""

#     if not bpy.context.scene.scatter5.update_auto_hidden_emitter:
#         return None 

#     emitter = bpy.context.scene.scatter5.emitter
#     if (emitter is None):
#         return None 
        
#     psys = emitter.scatter5.particle_systems
#     is_hidden = emitter.hide_get()

#     if is_hidden:
#         for p in psys:
#             if not p.scatter_obj.hide_viewport:
#                 p.scatter_obj.hide_viewport = True 

#     else:
#         for p in psys:
#             if (p.hide_viewport != p.scatter_obj.hide_viewport):
#                 p.scatter_obj.hide_viewport = p.hide_viewport

#     return None 

def is_ready_for_scattering():
    """check if emitter is ok for scattering preset or biome"""
    
    scat_scene = bpy.context.scene.scatter5
    emitter = bpy.context.scene.scatter5.emitter

    if (emitter is None):
        return False
    if (emitter.name not in bpy.context.scene.objects):
        return False
    if (bpy.context.mode!="OBJECT"):
        return False

    return True


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_set_new_emitter(bpy.types.Operator):

    bl_idname      = "scatter5.set_new_emitter"
    bl_label       = translate("Define a new emitter object")
    bl_description = translate("Define a new emitter object")
    bl_options     = {'INTERNAL','UNDO'}

    obj_name : bpy.props.StringProperty()
    select : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter

        if (self.obj_name not in bpy.context.scene.objects): 
            print(self.obj_name, " -> emitter not found in scene")
            return {'FINISHED'}

        new = bpy.data.objects.get(self.obj_name)

        if (self.select and bpy.context.mode=="OBJECT"):
            bpy.ops.object.select_all(action='DESELECT')
            new.select_set(True)
            bpy.context.view_layer.objects.active = new

        if (new is emitter):
            return {'FINISHED'}

        scat_scene = bpy.context.scene.scatter5
        scat_scene.emitter = new

        return {'FINISHED'}


class SCATTER5_OT_new_nonlinear_emitter(bpy.types.Operator):

    bl_idname      = "scatter5.new_nonlinear_emitter"
    bl_label       = translate("Create a new empty emitter object used for a non-linear workflow. By default Geo-Scatter is using the emitter object as the surface for the scattering, it is what we call a linear workflow. However you are free to choose any other surface(s) in the surface panel, this will lead you to a non-linear workflow! In such workflow the emitter object is only used to store your scattering settings")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    zoom : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",})

    def execute(self, context):

        #get an non linear emit object
        coll_name = "Scatter5 User Col"
        emit_name = "EmptyEmit"
        emit = bpy.data.objects.get(emit_name)

        #import a new one if not already?
        if (emit is None):

            import_utils.import_objects(
                blend_path=addon_logo_blend,
                object_names=[emit_name],
                link=False,
                link_coll=coll_name,
                )
            emit = bpy.data.objects[emit_name]
            emit.location = (0,0,0)

        #create a dupplicate if already used 
        if (len(emit.scatter5.particle_systems)!=0):

            old_loc = emit.location
            emit = bpy.data.objects.new(name=emit_name, object_data=emit.data)
            emit.location = emit.location + Vector((2.5,0,0))
            bpy.data.collections[coll_name].objects.link(emit)

        #set emitter 
        scat_scene = bpy.context.scene.scatter5
        scat_scene.emitter = emit

        #selection & zoom
        bpy.ops.object.select_all(action='DESELECT')
        emit.select_set(state=True)
        bpy.context.view_layer.objects.active = emit
        
        if (self.zoom):
            bpy.ops.view3d.view_selected(use_all_regions=False)

        #change color 
        emit.color = (0.011564, 0.011564, 0.011564, 1.000000)

        return {'FINISHED'}
        

classes = (

    SCATTER5_OT_set_new_emitter,
    SCATTER5_OT_new_nonlinear_emitter,
    
    )
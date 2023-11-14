
#####################################################################################################
#
#  .oooooo..o           oooo                          .    o8o
# d8P'    `Y8           `888                        .o8    `"'
# Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#      `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888
# oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888
# 8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
#
#####################################################################################################


import bpy 

from .. utils.event_utils import get_event

from .. resources.icons import cust_icon
from .. resources.translate import translate

from .. handlers import on_particle_interface_interaction_handler


#####################################################################################################


def set_sel(psys,value):
    """batch set set all psy selection status""" #foreach_set() 'cound'nt access api for some reasons...
    for p in psys:
        p.sel = value
    return None 


def on_particle_interface_interaction(self,context):
    """function that run when user set a particle system as active, used for shift&alt shortcut, also change selection"""

    #get latest active interface item
    itm = self.get_interface_active_item()

    #special case for psys, we have a handy p.active read-only property that we update on each list interaction
    if (itm is None): 
        for p in self.particle_systems:
            p.active = False
        return None 

    #get source itm, interface itm are fake, they are only useful to send back the original item, 
    #this item can either be a `emitter.scatter5.particle_groups[x]` or a `emitter.scatter5.particle_systems[x]`
    source_itm = itm.get_interface_item_source()
    if (source_itm is None):
        for p in self.particle_systems:
            p.active = False
        raise Exception("We could't find the source object of this interface item,\nhow on earth did you manage that!?\nPlease report it, we need to fix this.")
        return None 

    elif (itm.interface_item_type=="GROUP"):
        for p in self.particle_systems:
            p.active = False

    elif (itm.interface_item_type=="SCATTER"):
        for p in self.particle_systems:
            p.active = (p.name==source_itm.name)

    #get event for shortcuts
    event = get_event()

    emitter = source_itm.id_data

    #setting as active will always trigger the reset of the selection, except using is pressing shifts
    if (not event.shift):
        set_sel(self.particle_systems,False,)

    #shortcuts if active itm psy: 
    if (itm.interface_item_type=="SCATTER"):
        p = source_itm

        #if we set active a psy item, always set sel the psy active
        p.sel = True

    #shortcuts if active itm is group! 
    elif (itm.interface_item_type=="GROUP"):
        g = source_itm
        gpsys = [p for p in emitter.scatter5.particle_systems if (p.group!="") and (p.group==g.name) ]

        #if we set active a group item, always set sel all group psys
        for p in gpsys:
            p.sel = True

    #alt support = we hide anything that is not selected
    if (event.alt):
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):
            for p in self.particle_systems:
                p.hide_viewport = not p.sel
                continue

    #run handler function on each system list interaction
    on_particle_interface_interaction_handler()

    return None 


class SCATTER5_OT_toggle_selection(bpy.types.Operator):
    """toggle select all"""
    bl_idname      = "scatter5.toggle_selection"
    bl_label       = translate("Scatter-System(s) Selection Toggle")
    bl_description = ""

    emitter_name : bpy.props.StringProperty()
    group_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    select : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    deselect : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return translate("Select/Deselect Every System(s)") if properties.group_name=="" else translate("Select/Deselect group system(s)")

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter != None)

    def execute(self, context):

        #find emitter object 
        if (self.emitter_name==""):
              emitter = bpy.context.scene.scatter5.emitter
        else: emitter = bpy.data.objects.get(self.emitter_name)

        #specified a group name? if not use all psys, else use all psys of group
        if (self.group_name==""):
              psys = emitter.scatter5.particle_systems[:]
        else: psys = [ p for p in emitter.scatter5.particle_systems if p.group==self.group_name ]

        #Select All?
        if (self.select==True):
            set_sel(psys,True)

        #Deselect All?
        elif (self.deselect==True):
            set_sel(psys,False)

        #if neither then Toggle automatically 
        else:
            if (False in set(p.sel for p in psys)):
                  set_sel(psys,True)
            else: set_sel(psys,False)

        return {'FINISHED'}


class SCATTER5_OT_select_object(bpy.types.Operator):
    """Select/Deselect an object"""

    bl_idname      = "scatter5.select_object"
    bl_label       = ""
    bl_description = translate("Select/Deselect this object, use [SHIFT] for multi selection, [ALT] to recenter viewport toward object, [ALT-SHIFT] for both")

    obj_name : bpy.props.StringProperty(default="")
    coll_name : bpy.props.StringProperty(default="")

    def invoke(self, context, event):

        #Object do not exists?
        obj = bpy.data.objects.get(self.obj_name)
        if (obj is None):
            return {'FINISHED'}

        #Object Not in scene? 
        if (obj.name not in bpy.context.scene.objects):
            bpy.ops.scatter5.popup_menu(msgs=translate("Object is not in scene"),title=translate("Action not Possible"),icon="ERROR",)
            return {'FINISHED'}

        #Object hidden in viewlayer?
        if (obj.name not in bpy.context.view_layer.objects):
            #try to unhide from collection ?
            if self.coll_name:
                obj_name, coll_name = self.obj_name, self.coll_name
                def draw(self, context):
                    nonlocal obj_name, coll_name
                    layout = self.layout
                    layout.operator("scatter5.exec_line",text=translate("Unhide Viewlayer Collection")).api = f"from ..utils.coll_utils import exclude_view_layers ; exclude_view_layers(bpy.data.collections['{coll_name}'], scenes=[bpy.context.scene], hide=False,) ; o = bpy.data.objects['{obj_name}'] ; bpy.context.view_layer.objects.active =o ; o.select_set(True)"
                    return 
                context.window_manager.popup_menu(draw, title=translate("Object is in Hidden Viewlayer"))
                return {'FINISHED'}    
            bpy.ops.scatter5.popup_menu(msgs=translate("Object is not in view layer"),title=translate("Action not Possible"),icon="ERROR",)
            return {'FINISHED'}

        def deselect_all():
            for o in bpy.context.selected_objects:
                o.select_set(state=False)

        #event shift+alt click
        if (event.shift and event.alt):
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.view3d.view_selected()

        #event shift click
        elif event.shift:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

        #event alt click
        elif event.alt:
            deselect_all()
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.view3d.view_selected()

        #event normal
        else:
            deselect_all()
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (

    SCATTER5_OT_toggle_selection,
    SCATTER5_OT_select_object,
    
    )



#if __name__ == "__main__":
#    register()
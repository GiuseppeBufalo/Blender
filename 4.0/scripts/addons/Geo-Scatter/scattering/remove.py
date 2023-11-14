
#####################################################################################################
#
# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.  oooo    ooo  .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b  `88.  .8'  d88' `88b
#  888`88b.    888ooo888  888   888   888  888   888   `88..8'   888ooo888
#  888  `88b.  888    .o  888   888   888  888   888    `888'    888    .o
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'     `8'     `Y8bod8P'
#
#####################################################################################################



import bpy 

from .. resources.icons import cust_icon
from .. resources.translate import translate


#####################################################################################################



class SCATTER5_OT_remove_system(bpy.types.Operator):
    """Remove the selected particle system(s)"""
    
    bl_idname      = "scatter5.remove_system" #this operator is stupid, prefer to use `p.remove_psy()`
    bl_label       = translate("Remove System(s)")
    bl_description = ""

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #mandatory argument
    scene_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #facultative, will override emitter

    method : bpy.props.StringProperty(default="selection", options={"SKIP_SAVE",},)  #mandatory argument in: selection|active|name|clear|group|dynamic_uilist
    name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #only if method is name or group
    undo_push : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},) 

    @classmethod
    def description(cls, context, properties): 
        if (properties.method=="dynamic_uilist"):
            return translate("Remove the active scatter-system or group. Press ALT to remove the selection.")
        elif (properties.scene_name!=""):
            if (properties.method=="clear"):
                translate("Clear all scatter-system(s) from this scene.")
            return translate("Remove the scatter-system(s) from this scene.")
        elif (properties.method=="selection"):
            return translate("Remove the selected scatter-system(s).")
        elif (properties.method=="clear"):
            return translate("Clear all scatter-system(s) from this emitter.")
        return ""

    def invoke(self, context, event):
        """only used if alt behavior == automatic selection|active"""

        if (self.method=="dynamic_uilist"):

            emitter      = bpy.data.objects[self.emitter_name]
            psy_active   = emitter.scatter5.get_psy_active()
            group_active = emitter.scatter5.get_group_active()
            
            if (event.alt):
                self.method = "selection"

            elif (group_active is not None):
                self.method = "group"
                self.name = group_active.name

            elif (psy_active is not None):
                self.method = "active"

        return self.execute(context)

    def execute(self, context):
            
        scat_scene = context.scene.scatter5

        if (self.scene_name!=""):
              psys = scat_scene.get_all_psys()
        else: psys = bpy.data.objects[self.emitter_name].scatter5.particle_systems

        # #save selection, this operation might f up sel
        # save_sel = [p.name for p in emitter.scatter5.get_psys_selected() if p.sel]

        #define what to del
        #need to remove by name as memory adress will keep changing, else might create crash
        to_del = []

        #remove selection?
        if (self.method=="selection"):
            to_del = [ p.name for p in psys if p.sel]
        #remove active?
        elif (self.method=="active"):
            to_del = [ p.name for p in psys if p.active]
        #remove by name?
        elif (self.method=="name"):
            to_del = [ p.name for p in psys if (p.name==self.name) ]
        #remove whole group members?
        elif (self.method=="group"):
            to_del = [ p.name for p in psys if (p.group==self.name) ]
        #remove everything?
        elif (self.method=="clear"):
            to_del = [ p.name for p in psys ]

        #cancel if nothing to remove 
        if (len(to_del)==0): 
            return {'FINISHED'}

        #remove each psy, pause user keyboard event listenting
        with context.scene.scatter5.factory_update_pause(event=True):
            
            #keep track of the emitters, in order to refresh their interfaces
            affected_emitters = set()
            
            for x in to_del:
                
                #we remove psys by name, otherwise will cause issues
                psy = scat_scene.get_psy_by_name(x)
                psy.remove_psy()
                
                #retain emitter, we need to refresh their interfaces
                emitter = psy.id_data
                affected_emitters.add(emitter)
                    
                continue

            #rebuild system-list interface, will take care of active index
            for e in affected_emitters:
                e.scatter5.particle_interface_refresh()
                continue
        
        # #restore selection ?
        # [setattr(p,"sel",p.name in save_sel) for p in emitter.scatter5.particle_systems]

        #UNDO_PUSH
        if (self.undo_push):
            bpy.ops.ed.undo_push(message=translate("Remove Scatter-System(s)"))

        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (

    SCATTER5_OT_remove_system,
    
    )



#if __name__ == "__main__":
#    register()
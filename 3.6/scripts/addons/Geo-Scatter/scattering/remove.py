
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
    bl_label       = ""
    bl_description = translate("Remove Scatter-System(s), will remove the active system by default, hold ALT for removing the selection")

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #mandatory argument
    method : bpy.props.StringProperty(default="selection", options={"SKIP_SAVE",},)  #mandatory argument in: selection|active|name|alt|clear
    name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #only if method is: name
    undo_push : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},) 

    def invoke(self, context, event):
        """only used if alt behavior == automatic selection|active"""

        if (self.method=="alt"):
            self.method = "selection" if (event.alt) else "active"

        return self.execute(context)

    def execute(self, context):

        if (self.emitter_name==""):
            return {'FINISHED'}
        if (self.emitter_name not in context.scene.objects):
            return {'FINISHED'}
        
        emitter = bpy.data.objects[self.emitter_name]
        psys = emitter.scatter5.particle_systems

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
        #remove everything?
        elif (self.method=="clear"):
            to_del = [ p.name for p in psys ]

        #cancel if nothing to remove 
        if (len(to_del)==0): 
            return {'FINISHED'}

        #remove each psy
        with context.scene.scatter5.factory_update_pause(event=True):
            #save old active, restore if needed, deletion operator will reset idx... (perhaps best to integrate this bit in remove_psy() fct directly)
            old_active = emitter.scatter5.get_psy_active().name
            #remove!
            for x in to_del:
                emitter.scatter5.particle_systems[x].remove_psy()
                continue
            #restore active?
            if (old_active in emitter.scatter5.particle_systems):
                for i,p in enumerate(emitter.scatter5.particle_systems):
                    if (p.name==old_active):
                        emitter.scatter5.particle_systems_idx = i
                        break

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
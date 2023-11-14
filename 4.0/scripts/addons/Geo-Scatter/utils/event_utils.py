
import bpy 

#   .oooooo.                  .        oooooooooooo                                       .
#  d8P'  `Y8b               .o8        `888'     `8                                     .o8
# 888            .ooooo.  .o888oo       888         oooo    ooo  .ooooo.  ooo. .oo.   .o888oo
# 888           d88' `88b   888         888oooo8     `88.  .8'  d88' `88b `888P"Y88b    888
# 888     ooooo 888ooo888   888         888    "      `88..8'   888ooo888  888   888    888
# `88.    .88'  888    .o   888 .       888       o    `888'    888    .o  888   888    888 .
#  `Y8bood8P'   `Y8bod8P'   "888"      o888ooooood8     `8'     `Y8bod8P' o888o o888o   "888"


# get_even() Hack to get even from non modal nor invoke

#https://blender.stackexchange.com/questions/211544/detect-user-event-bpy-types-event-anywhere-from-blender/211590#211590

class EventCopy():
    """empty event class, only use by singleton"""

    #imitate bpy.type.Event used attributes 

    def __init__(self, ):

        self.type = ""
        self.value = ""
        self.shift = False
        self.ctrl = False
        self.alt = False

    def update(self, event=None):
        
        #construct man-made event
        if (event is None):
            self.type = ""
            self.value = ""
            self.shift = False
            self.ctrl = False
            self.alt = False

        #or copy from existing blender event type
        else: 
            self.type = event.type
            self.value = event.value
            self.shift = event.shift
            self.ctrl = event.ctrl
            self.alt = event.alt

#Event Singleton

EVENT = EventCopy() 

#Get update value via operator as bpy.types.Event only accessible from invoke() or modal()

class SCATTER5_OT_get_event(bpy.types.Operator):
    """update event singleton, this is an internal operator"""

    bl_idname  = "scatter5.get_event"
    bl_label   = ""

    def invoke(self, context, event):
        
        global EVENT
        EVENT.update(event=event)

        return {'FINISHED'}
    
#access event singleton from all modules based on the 

def get_event(nullevent=False):
    """get rebuilt Event type via bpy.types.Operator invoke()"""
        
    global EVENT 

    if (not bpy.context.scene.scatter5.factory_event_listening_allow) or (bpy.context.window is None) or (nullevent==True):
        EVENT.update(event=None)
    else:
        bpy.ops.scatter5.get_event('INVOKE_DEFAULT')

    return EVENT

# ooo        ooooo                                                 .oooooo.                             .                             .
# `88.       .888'                                                d8P'  `Y8b                          .o8                           .o8
#  888b     d'888   .ooooo.  oooo  oooo   .oooo.o  .ooooo.       888           .ooooo.  ooo. .oo.   .o888oo  .ooooo.  oooo    ooo .o888oo
#  8 Y88. .P  888  d88' `88b `888  `888  d88(  "8 d88' `88b      888          d88' `88b `888P"Y88b    888   d88' `88b  `88b..8P'    888
#  8  `888'   888  888   888  888   888  `"Y88b.  888ooo888      888          888   888  888   888    888   888ooo888    Y888'      888
#  8    Y     888  888   888  888   888  o.  )88b 888    .o      `88b    ooo  888   888  888   888    888 . 888    .o  .o8"'88b     888 .
# o8o        o888o `Y8bod8P'  `V88V"V8P' 8""888P' `Y8bod8P'       `Y8bood8P'  `Y8bod8P' o888o o888o   "888" `Y8bod8P' o88'   888o   "888"

    
#FAIL??? goal is to get correct context from modal

CONTEXT = {}

class SCATTER5_OT_get_mouse_context(bpy.types.Operator):
    """update event singleton, this is an internal operator"""

    bl_idname  = "scatter5.get_mouse_context"
    bl_label   = ""

    def invoke(self, context, event):
        
        global CONTEXT
        CONTEXT.update({"area_type":bpy.context.area.type})

        return {'FINISHED'}

def get_mouse_context():
    """get rebuilt Event type via bpy.types.Operator invoke()"""
        
    global CONTEXT 

    bpy.ops.scatter5.get_mouse_context('INVOKE_DEFAULT')

    return CONTEXT

classes = (

    SCATTER5_OT_get_event,
    SCATTER5_OT_get_mouse_context,

    )
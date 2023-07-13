

import bpy

from . import presetting

from .. resources.translate import translate
from .. resources.icons import cust_icon

from .. utils.import_utils import serialization 
from .. utils.event_utils import get_event

from .. ui import ui_templates


#   .oooooo.                                         88 ooooooooo.                          .                   .oooooo..o               .       .
#  d8P'  `Y8b                                       .8' `888   `Y88.                      .o8                  d8P'    `Y8             .o8     .o8
# 888           .ooooo.  oo.ooooo.  oooo    ooo    .8'   888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.       Y88bo.       .ooooo.  .o888oo .o888oo
# 888          d88' `88b  888' `88b  `88.  .8'    .8'    888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b       `"Y8888o.  d88' `88b   888     888
# 888          888   888  888   888   `88..8'    .8'     888          .oP"888  `"Y88b.    888   888ooo888           `"Y88b 888ooo888   888     888
# `88b    ooo  888   888  888   888    `888'    .8'      888         d8(  888  o.  )88b   888 . 888    .o      oo     .d8P 888    .o   888 .   888 .
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'     88      o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"   "888"
#                         888       .o..P'
#                        o888o      `Y8P'

#universal copy paste following settings naming system 


BufferCategory = {}

def is_BufferCategory_filled(buffer_category):

    global BufferCategory

    return buffer_category in BufferCategory

def clear_BufferCategory(buffer_category):

    global BufferCategory

    if buffer_category in BufferCategory:
        del BufferCategory[buffer_category]

    return None 

def stringify_BufferCategory(buffer_category):

    global BufferCategory

    return "".join([f"   {k} : {str(v)}\n" for k,v in BufferCategory[buffer_category].items() if not k.startswith(">") and k!="name" ])


class SCATTER5_OT_copy_paste_category(bpy.types.Operator): #Old pasteall copyall was overkill and i disable the dialog box, user can simply copy/paste per category now 

    bl_idname      = "scatter5.copy_paste_category"
    bl_label       = translate("Copy/Paste Settings")
    bl_description = ""
    bl_options     = {'REGISTER', 'INTERNAL'}

    single_category : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    copy : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    paste : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    apply_selected : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
            
        emitter = bpy.context.scene.scatter5.emitter

        if properties.paste:
            if is_BufferCategory_filled(properties.single_category):
                  return translate("Paste buffer content to the settings below") +"\n"+ translate("Content of buffer") +" : \n"+ stringify_BufferCategory(properties.single_category)
            else: return translate("Paste buffer content to the settings below") +"\n"+ translate("The buffer is empty")
        
        if properties.copy:
            return translate("Copy settings below to buffer")

        if properties.apply_selected:
            return translate("Apply the active settings to the selected scatter-system(s)") + f" : {len([ p for p in emitter.scatter5.get_psys_selected() if not p.active ])} " + translate("System(s) Selected") 

        return None 

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()      

        LocalBuffer = None
        global BufferCategory

        if ( (self.copy==True) or (self.apply_selected==True) ):

            d = presetting.settings_to_dict(
                psy_active, 
                use_random_seed=False, 
                texture_is_unique=False, 
                texture_random_loc=False, 
                get_estimated_density=False, 
                s_filter={self.single_category:True},
                )

            #apply option? then will follow with paste of local buffer
            if (self.apply_selected==True):
                self.paste = True
                LocalBuffer = d
                
            else: 
                clear_BufferCategory(self.single_category)
                BufferCategory[self.single_category] = d 
                return {'FINISHED'}

        if (self.paste==True):

            if ( is_BufferCategory_filled(self.single_category) or (LocalBuffer!={}) ):

                psys_sel = emitter.scatter5.get_psys_selected()

                #apply option? 
                if (self.apply_selected==True):
                    psys = [p for p in psys_sel if (p is not psy_active)]
                    d = LocalBuffer

                #standard paste?
                else: 
                    psys = [ psy_active ]
                    d = BufferCategory[self.single_category]

                for p in psys:
                    presetting.dict_to_settings(d, p, s_filter={self.single_category:True},)
                    continue

                bpy.ops.ed.undo_push(message=translate("Pasting Buffer to Settings"))
            
        return {'FINISHED'}


#   .oooooo.                                         88 ooooooooo.                          .                  ooooooooo.
#  d8P'  `Y8b                                       .8' `888   `Y88.                      .o8                  `888   `Y88.
# 888           .ooooo.  oo.ooooo.  oooo    ooo    .8'   888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.        888   .d88'  .oooo.o oooo    ooo
# 888          d88' `88b  888' `88b  `88.  .8'    .8'    888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b       888ooo88P'  d88(  "8  `88.  .8'
# 888          888   888  888   888   `88..8'    .8'     888          .oP"888  `"Y88b.    888   888ooo888       888         `"Y88b.    `88..8'
# `88b    ooo  888   888  888   888    `888'    .8'      888         d8(  888  o.  )88b   888 . 888    .o       888         o.  )88b    `888'
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'     88      o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'      o888o        8""888P'     .8'
#                         888       .o..P'                                                                                           .o..P'
#                        o888o      `Y8P'                                                                                            `Y8P'


BufferSystems = {}

def is_BufferSystems_filled():

    global BufferSystems

    return len(BufferSystems)!=0

def clear_BufferSystems():

    global BufferSystems
    BufferSystems.clear()

    return None 


class SCATTER5_OT_copy_paste_systems(bpy.types.Operator):

    bl_idname      = "scatter5.copy_paste_systems"
    bl_label       = translate("Copy Selected/Paste scatter-system(s)")
    bl_description = translate("Copy Selected/Paste scatter-system(s)")
    bl_options     = {'INTERNAL', 'UNDO'}

    emitter_name : bpy.props.StringProperty()
    copy : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    paste : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    synchronize : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        txt =""
        if properties.copy:
              txt += translate("Copy the selected scatter-system(s)")
        else: txt += translate("Paste particle_system(s) from Buffer")
        if properties.synchronize:
              txt += " "
              txt += translate("and Synchronize their settings with the source")
        return txt

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None): 
            return {'FINISHED'}

        global BufferSystems

        if (self.copy==True):

            clear_BufferSystems()

            for p in emitter.scatter5.get_psys_selected():

                d = presetting.settings_to_dict(p,
                    use_random_seed=False,
                    texture_is_unique=False,
                    texture_random_loc=False,
                    get_estimated_density=False,
                    s_filter={ k:True for k in ("s_color","s_surface","s_distribution","s_mask","s_rot","s_scale","s_pattern","s_push","s_abiotic","s_proximity","s_ecosystem","s_wind","s_visibility","s_instances","s_display")}, #all settings cat are True
                    )

                #need to add extra information for instances, unfortunately instances names are not passed in presets... #TODO add kw argument for this option?
                d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> BUFFER_EXTRA"] = ""
                d["initial_instances"]= [o.name for o in p.s_instances_coll_ptr.objects] 

                #add dict to buffer
                initial_name = p.name
                BufferSystems[initial_name]= d 

                continue

        elif (self.paste==True):

            if is_BufferSystems_filled():

                bpy.ops.scatter5.toggle_selection(deselect=True, emitter_name=emitter.name,)

                for initial_name, d in BufferSystems.items():

                    #create a new psy with same instances
                    p = emitter.scatter5.add_psy_virgin(
                        psy_name=f"{initial_name}_copy",
                        instances=[ bpy.data.objects.get(n) for n in d["initial_instances"] if (n in bpy.data.objects) ],
                        )
                    
                    p.sel = True
                    p.hide_viewport = True

                    #TODO: what do we do if user copy/paste ecosystem ptr too? ugh need to re-evaluate

                    #apply same settings of initial_p to newly added psy
                    presetting.dict_to_settings(d, p, 
                        s_filter={ k:True for k in ("s_color","s_surface","s_distribution","s_mask","s_rot","s_scale","s_pattern","s_push","s_abiotic","s_proximity","s_ecosystem","s_wind","s_visibility","s_instances","s_display")}, #all settings cat are True
                        )

                    #synchronize? only if initial psy still exists
                    if (self.synchronize==True):

                        #find back our initial psy, from which we pasted the data
                        initial_p = scat_scene.get_psy_by_name(initial_name)
                        if (initial_p is None):
                            continue

                        #enable synchronization, will not be enabled by default
                        if (not scat_scene.factory_synchronization_allow):
                            scat_scene.factory_synchronization_allow = True 

                        #create new channel if needed
                        sync_channels = scat_scene.sync_channels
                        ch = scat_scene.sync_channels.get(initial_name)
                        if (ch is None):
                              ch = scat_scene.sync_channels.add()
                              ch.name = initial_name

                        #add the psys as members
                        ch.add_psys_members(initial_p, p)

                    continue

        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (

    SCATTER5_OT_copy_paste_category,
    SCATTER5_OT_copy_paste_systems,
    
    )
